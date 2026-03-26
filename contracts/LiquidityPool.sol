// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "./interfaces/IERC20.sol";
import "./interfaces/IProtocolRegistry.sol";

/// @title LiquidityPool - Immutable liquidity pool for unmatched remittance portions
/// @author Ha_Chain Protocol
/// @notice Liquidity providers deposit tokens and earn spread fees when their
///         liquidity is used to fill unmatched order portions. Spread is set
///         at deployment per pool and cannot be changed.
/// @dev No admin keys, no pause, no upgrade mechanism. Once deployed, the
///      spread rates and authorized contracts are permanent.
contract LiquidityPool {
    // ──────────────────────────────────────────────
    //  Types
    // ──────────────────────────────────────────────

    struct LiquidityPosition {
        address provider;
        address token;
        uint256 amount;
        uint256 earnedFees;
        uint256 depositTime;
    }

    struct PoolStats {
        uint256 totalLiquidity;
        uint256 availableLiquidity;
        uint256 totalUtilized;
        uint256 totalFeesGenerated;
        uint256 providerCount;
    }

    // ──────────────────────────────────────────────
    //  Constants
    // ──────────────────────────────────────────────

    /// @notice Spread basis points denominator
    uint256 public constant SPREAD_DENOMINATOR = 10_000;

    /// @notice Minimum spread: 0.1% = 10 bps
    uint256 public constant MIN_SPREAD_BPS = 10;

    /// @notice Maximum spread: 0.3% = 30 bps
    uint256 public constant MAX_SPREAD_BPS = 30;

    // ──────────────────────────────────────────────
    //  Immutable State
    // ──────────────────────────────────────────────

    /// @notice The MatchingPool contract -- authorized to fill orders
    address public immutable matchingPool;

    /// @notice The ProtocolRegistry contract
    IProtocolRegistry public immutable registry;

    // ──────────────────────────────────────────────
    //  State
    // ──────────────────────────────────────────────

    /// @notice Spread in basis points per token (set at deployment)
    mapping(address => uint256) public spreadBps;

    /// @notice Whether a token's spread has been initialized
    mapping(address => bool) public spreadInitialized;

    /// @notice All liquidity positions by ID
    mapping(bytes32 => LiquidityPosition) private _positions;

    /// @notice Position nonce for unique IDs
    uint256 private _positionNonce;

    /// @notice Total liquidity per token
    mapping(address => uint256) public totalLiquidity;

    /// @notice Available (non-utilized) liquidity per token
    mapping(address => uint256) public availableLiquidity;

    /// @notice Total utilized liquidity per token
    mapping(address => uint256) public totalUtilized;

    /// @notice Total fees generated per token
    mapping(address => uint256) public totalFeesGenerated;

    /// @notice Number of active providers per token
    mapping(address => uint256) public providerCount;

    /// @notice User positions for enumeration
    mapping(address => bytes32[]) private _userPositions;

    // ──────────────────────────────────────────────
    //  Events
    // ──────────────────────────────────────────────

    /// @dev Emitted when liquidity is added
    event LiquidityAdded(
        bytes32 indexed positionId,
        address indexed provider,
        address indexed token,
        uint256 amount
    );

    /// @dev Emitted when liquidity is removed
    event LiquidityRemoved(
        bytes32 indexed positionId,
        address indexed provider,
        uint256 amount
    );

    /// @dev Emitted when an order is filled from the LP
    event OrderFilled(
        address indexed token,
        address indexed recipient,
        uint256 amount,
        uint256 spreadFee
    );

    /// @dev Emitted when fees are claimed by a provider
    event FeesClaimed(
        bytes32 indexed positionId,
        address indexed provider,
        uint256 amount
    );

    /// @dev Emitted when spread is set for a token (only during construction)
    event SpreadSet(address indexed token, uint256 spreadBps);

    // ──────────────────────────────────────────────
    //  Errors
    // ──────────────────────────────────────────────

    error OnlyMatchingPool();
    error ZeroAmount();
    error ZeroAddress();
    error InvalidSpread();
    error SpreadAlreadySet();
    error PositionNotFound();
    error NotPositionOwner();
    error InsufficientLiquidity();
    error InsufficientPosition();
    error NoFeesToClaim();
    error TransferFailed();
    error SpreadNotInitialized();

    // ──────────────────────────────────────────────
    //  Modifiers
    // ──────────────────────────────────────────────

    modifier onlyMatchingPool() {
        if (msg.sender != matchingPool) revert OnlyMatchingPool();
        _;
    }

    // ──────────────────────────────────────────────
    //  Constructor
    // ──────────────────────────────────────────────

    /// @notice Deploy the liquidity pool with initial spread configurations
    /// @param _matchingPool Address of the MatchingPool contract
    /// @param _registry Address of the ProtocolRegistry contract
    /// @param tokens Array of token addresses to configure spreads for
    /// @param spreads Array of spread values in basis points (10-30)
    constructor(
        address _matchingPool,
        address _registry,
        address[] memory tokens,
        uint256[] memory spreads
    ) {
        if (_matchingPool == address(0)) revert ZeroAddress();
        if (_registry == address(0)) revert ZeroAddress();

        matchingPool = _matchingPool;
        registry = IProtocolRegistry(_registry);

        uint256 len = tokens.length;
        if (len != spreads.length) revert InvalidSpread();

        for (uint256 i; i < len; ) {
            if (tokens[i] == address(0)) revert ZeroAddress();
            if (spreads[i] < MIN_SPREAD_BPS || spreads[i] > MAX_SPREAD_BPS) revert InvalidSpread();

            spreadBps[tokens[i]] = spreads[i];
            spreadInitialized[tokens[i]] = true;

            emit SpreadSet(tokens[i], spreads[i]);

            unchecked { ++i; }
        }
    }

    // ──────────────────────────────────────────────
    //  Core Functions
    // ──────────────────────────────────────────────

    /// @notice Add liquidity to the pool
    /// @param token The ERC20 token to provide liquidity for
    /// @param amount The amount of tokens to deposit
    /// @return positionId The unique identifier for this liquidity position
    function addLiquidity(address token, uint256 amount) external returns (bytes32 positionId) {
        if (token == address(0)) revert ZeroAddress();
        if (amount == 0) revert ZeroAmount();
        if (!spreadInitialized[token]) revert SpreadNotInitialized();

        // Transfer tokens from provider to this contract
        bool success = IERC20(token).transferFrom(msg.sender, address(this), amount);
        if (!success) revert TransferFailed();

        unchecked { ++_positionNonce; }
        positionId = keccak256(
            abi.encodePacked(msg.sender, token, amount, _positionNonce, block.timestamp)
        );

        _positions[positionId] = LiquidityPosition({
            provider: msg.sender,
            token: token,
            amount: amount,
            earnedFees: 0,
            depositTime: block.timestamp
        });

        totalLiquidity[token] += amount;
        availableLiquidity[token] += amount;

        // Track if this is a new provider for this token
        if (_userPositions[msg.sender].length == 0) {
            providerCount[token] += 1;
        }
        _userPositions[msg.sender].push(positionId);

        emit LiquidityAdded(positionId, msg.sender, token, amount);
    }

    /// @notice Remove liquidity from the pool
    /// @param positionId The position to withdraw from
    /// @param amount The amount to withdraw
    function removeLiquidity(bytes32 positionId, uint256 amount) external {
        if (amount == 0) revert ZeroAmount();

        LiquidityPosition storage pos = _positions[positionId];
        if (pos.provider == address(0)) revert PositionNotFound();
        if (pos.provider != msg.sender) revert NotPositionOwner();
        if (pos.amount < amount) revert InsufficientPosition();

        address token = pos.token;
        if (availableLiquidity[token] < amount) revert InsufficientLiquidity();

        pos.amount -= amount;
        totalLiquidity[token] -= amount;
        availableLiquidity[token] -= amount;

        bool success = IERC20(token).transfer(msg.sender, amount);
        if (!success) revert TransferFailed();

        emit LiquidityRemoved(positionId, msg.sender, amount);
    }

    /// @notice Fill an unmatched order portion from LP liquidity
    /// @param token The token to use for filling
    /// @param recipient The address that receives the tokens
    /// @param amount The amount to fill (before spread)
    /// @dev Only callable by the MatchingPool contract. The spread is deducted
    ///      and distributed pro-rata to all LPs of this token.
    function fillOrder(
        address token,
        address recipient,
        uint256 amount
    ) external onlyMatchingPool {
        if (token == address(0)) revert ZeroAddress();
        if (recipient == address(0)) revert ZeroAddress();
        if (amount == 0) revert ZeroAmount();
        if (!spreadInitialized[token]) revert SpreadNotInitialized();
        if (availableLiquidity[token] < amount) revert InsufficientLiquidity();

        uint256 spread = (amount * spreadBps[token]) / SPREAD_DENOMINATOR;
        uint256 netAmount = amount - spread;

        availableLiquidity[token] -= amount;
        totalUtilized[token] += amount;
        totalFeesGenerated[token] += spread;

        // Transfer net amount to recipient
        bool success = IERC20(token).transfer(recipient, netAmount);
        if (!success) revert TransferFailed();

        emit OrderFilled(token, recipient, amount, spread);
    }

    /// @notice Distribute earned fees to a specific position
    /// @param positionId The position to credit fees to
    /// @param feeAmount The fee amount to credit
    /// @dev Only callable by MatchingPool
    function creditFees(bytes32 positionId, uint256 feeAmount) external onlyMatchingPool {
        LiquidityPosition storage pos = _positions[positionId];
        if (pos.provider == address(0)) revert PositionNotFound();
        pos.earnedFees += feeAmount;
    }

    /// @notice Claim accumulated fees for a position
    /// @param positionId The position to claim fees for
    function claimFees(bytes32 positionId) external {
        LiquidityPosition storage pos = _positions[positionId];
        if (pos.provider == address(0)) revert PositionNotFound();
        if (pos.provider != msg.sender) revert NotPositionOwner();

        uint256 fees = pos.earnedFees;
        if (fees == 0) revert NoFeesToClaim();

        pos.earnedFees = 0;

        bool success = IERC20(pos.token).transfer(msg.sender, fees);
        if (!success) revert TransferFailed();

        emit FeesClaimed(positionId, msg.sender, fees);
    }

    /// @notice Return utilized liquidity back to available pool
    /// @param token The token address
    /// @param amount The amount being returned
    /// @dev Called by MatchingPool when an LP-filled order completes settlement
    function returnLiquidity(address token, uint256 amount) external onlyMatchingPool {
        if (amount == 0) revert ZeroAmount();
        availableLiquidity[token] += amount;
        if (totalUtilized[token] >= amount) {
            totalUtilized[token] -= amount;
        }
    }

    // ──────────────────────────────────────────────
    //  View Functions
    // ──────────────────────────────────────────────

    /// @notice Get pool statistics for a token
    /// @param token The token address
    /// @return stats The PoolStats struct
    function getPoolStats(address token) external view returns (PoolStats memory stats) {
        return PoolStats({
            totalLiquidity: totalLiquidity[token],
            availableLiquidity: availableLiquidity[token],
            totalUtilized: totalUtilized[token],
            totalFeesGenerated: totalFeesGenerated[token],
            providerCount: providerCount[token]
        });
    }

    /// @notice Get a liquidity position
    /// @param positionId The position identifier
    /// @return The LiquidityPosition struct
    function getPosition(bytes32 positionId) external view returns (LiquidityPosition memory) {
        return _positions[positionId];
    }

    /// @notice Get all position IDs for a user
    /// @param user The user address
    /// @return Array of position IDs
    function getUserPositions(address user) external view returns (bytes32[] memory) {
        return _userPositions[user];
    }

    /// @notice Get the spread for a token in basis points
    /// @param token The token address
    /// @return The spread in basis points
    function getSpread(address token) external view returns (uint256) {
        return spreadBps[token];
    }

    /// @notice Calculate estimated APY based on utilization
    /// @param token The token address
    /// @return Estimated APY scaled by 1e18 (e.g., 5e16 = 5%)
    function getEstimatedAPY(address token) external view returns (uint256) {
        uint256 total = totalLiquidity[token];
        if (total == 0) return 0;

        uint256 utilized = totalUtilized[token];
        uint256 utilization = (utilized * 1e18) / total;
        uint256 spread = spreadBps[token];

        // Simple APY estimate: utilization * spread * turns_per_year
        // Assumes ~365 turns per year for daily utilization
        return (utilization * spread * 365) / SPREAD_DENOMINATOR;
    }
}
