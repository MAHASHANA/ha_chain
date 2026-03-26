// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "./interfaces/IERC20.sol";
import "./interfaces/IEscrow.sol";

/// @title Escrow - Immutable escrow for deposits during matching
/// @author Ha_Chain Protocol
/// @notice Funds are locked in this contract -- NOT in any company wallet.
///         Released to counterparty on match confirmation, or auto-refunded
///         after timeout. No admin keys, no pause, no upgrade mechanism.
/// @dev Once deployed, nobody can change anything. The matching contract
///      address is set at construction and cannot be modified.
contract Escrow is IEscrow {
    // ──────────────────────────────────────────────
    //  Constants
    // ──────────────────────────────────────────────

    /// @notice Protocol fee: 0.05% (5 basis points)
    /// @dev FEE_BPS / FEE_DENOMINATOR = 5 / 10000 = 0.05%
    uint256 public constant FEE_BPS = 5;
    uint256 public constant FEE_DENOMINATOR = 10_000;

    // ──────────────────────────────────────────────
    //  Immutable State
    // ──────────────────────────────────────────────

    /// @notice The MatchingPool contract -- only address authorized to lock/release
    address public immutable matchingPool;

    /// @notice Treasury address that receives protocol fees
    address public immutable treasury;

    // ──────────────────────────────────────────────
    //  Types
    // ──────────────────────────────────────────────

    struct EscrowDeposit {
        address depositor;
        address token;
        uint256 amount;         // gross amount deposited
        uint256 protocolFee;    // 0.05% of amount
        uint256 netAmount;      // amount - protocolFee (what recipient gets)
        uint256 depositTime;
        uint256 expiryTime;
        bool released;
        bool refunded;
    }

    // ──────────────────────────────────────────────
    //  State
    // ──────────────────────────────────────────────

    /// @notice All escrow deposits by ID
    mapping(bytes32 => EscrowDeposit) private _deposits;

    /// @notice Incrementing nonce for unique escrow IDs
    uint256 private _nonce;

    /// @notice Total fees collected per token (claimable by treasury)
    mapping(address => uint256) public accumulatedFees;

    // ──────────────────────────────────────────────
    //  Events
    // ──────────────────────────────────────────────

    /// @dev Emitted when funds are locked into escrow
    event FundsLocked(
        bytes32 indexed escrowId,
        address indexed depositor,
        address indexed token,
        uint256 amount,
        uint256 protocolFee,
        uint256 netAmount,
        uint256 expiryTime
    );

    /// @dev Emitted when escrowed funds are released to a recipient
    event FundsReleased(
        bytes32 indexed escrowId,
        address indexed recipient,
        uint256 amount
    );

    /// @dev Emitted when escrowed funds are refunded to the depositor
    event FundsRefunded(
        bytes32 indexed escrowId,
        address indexed depositor,
        uint256 amount
    );

    /// @dev Emitted when accumulated fees are withdrawn to treasury
    event FeesWithdrawn(
        address indexed token,
        uint256 amount
    );

    // ──────────────────────────────────────────────
    //  Errors
    // ──────────────────────────────────────────────

    error OnlyMatchingPool();
    error ZeroAmount();
    error ZeroAddress();
    error InvalidExpiry();
    error EscrowNotFound();
    error EscrowAlreadyReleased();
    error EscrowAlreadyRefunded();
    error EscrowNotExpired();
    error TransferFailed();

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

    /// @notice Deploy the escrow contract
    /// @param _matchingPool Address of the MatchingPool contract
    /// @param _treasury Address that receives protocol fees
    constructor(address _matchingPool, address _treasury) {
        if (_matchingPool == address(0)) revert ZeroAddress();
        if (_treasury == address(0)) revert ZeroAddress();
        matchingPool = _matchingPool;
        treasury = _treasury;
    }

    // ──────────────────────────────────────────────
    //  Core Functions
    // ──────────────────────────────────────────────

    /// @inheritdoc IEscrow
    /// @dev Tokens must already be transferred to this contract before calling.
    ///      The MatchingPool contract handles the transferFrom.
    function lockFunds(
        address token,
        address depositor,
        uint256 amount,
        uint256 expiryTime
    ) external override onlyMatchingPool returns (bytes32 escrowId) {
        if (token == address(0)) revert ZeroAddress();
        if (depositor == address(0)) revert ZeroAddress();
        if (amount == 0) revert ZeroAmount();
        if (expiryTime <= block.timestamp) revert InvalidExpiry();

        uint256 fee = (amount * FEE_BPS) / FEE_DENOMINATOR;
        uint256 net = amount - fee;

        unchecked { ++_nonce; }
        escrowId = keccak256(abi.encodePacked(depositor, token, amount, _nonce, block.timestamp));

        _deposits[escrowId] = EscrowDeposit({
            depositor: depositor,
            token: token,
            amount: amount,
            protocolFee: fee,
            netAmount: net,
            depositTime: block.timestamp,
            expiryTime: expiryTime,
            released: false,
            refunded: false
        });

        accumulatedFees[token] += fee;

        emit FundsLocked(escrowId, depositor, token, amount, fee, net, expiryTime);
    }

    /// @inheritdoc IEscrow
    function releaseFunds(bytes32 escrowId, address recipient) external override onlyMatchingPool {
        if (recipient == address(0)) revert ZeroAddress();
        EscrowDeposit storage dep = _deposits[escrowId];
        if (dep.depositor == address(0)) revert EscrowNotFound();
        if (dep.released) revert EscrowAlreadyReleased();
        if (dep.refunded) revert EscrowAlreadyRefunded();

        dep.released = true;

        bool success = IERC20(dep.token).transfer(recipient, dep.netAmount);
        if (!success) revert TransferFailed();

        emit FundsReleased(escrowId, recipient, dep.netAmount);
    }

    /// @inheritdoc IEscrow
    /// @dev Anyone can call this after the expiry time has passed.
    ///      Refunds the full amount (including fee) to the depositor.
    function refund(bytes32 escrowId) external override {
        EscrowDeposit storage dep = _deposits[escrowId];
        if (dep.depositor == address(0)) revert EscrowNotFound();
        if (dep.released) revert EscrowAlreadyReleased();
        if (dep.refunded) revert EscrowAlreadyRefunded();
        if (block.timestamp < dep.expiryTime) revert EscrowNotExpired();

        dep.refunded = true;

        // Refund full amount including fee (fee wasn't earned since no match)
        accumulatedFees[dep.token] -= dep.protocolFee;

        bool success = IERC20(dep.token).transfer(dep.depositor, dep.amount);
        if (!success) revert TransferFailed();

        emit FundsRefunded(escrowId, dep.depositor, dep.amount);
    }

    /// @notice Withdraw accumulated protocol fees to treasury
    /// @param token The token to withdraw fees for
    /// @dev Anyone can call this -- fees always go to the immutable treasury
    function withdrawFees(address token) external {
        uint256 fees = accumulatedFees[token];
        if (fees == 0) revert ZeroAmount();

        accumulatedFees[token] = 0;

        bool success = IERC20(token).transfer(treasury, fees);
        if (!success) revert TransferFailed();

        emit FeesWithdrawn(token, fees);
    }

    // ──────────────────────────────────────────────
    //  View Functions
    // ──────────────────────────────────────────────

    /// @inheritdoc IEscrow
    function getEscrowAmount(bytes32 escrowId) external view override returns (uint256) {
        return _deposits[escrowId].netAmount;
    }

    /// @inheritdoc IEscrow
    function isActive(bytes32 escrowId) external view override returns (bool) {
        EscrowDeposit storage dep = _deposits[escrowId];
        return dep.depositor != address(0) && !dep.released && !dep.refunded;
    }

    /// @notice Get full details of an escrow deposit
    /// @param escrowId The escrow deposit identifier
    /// @return The EscrowDeposit struct
    function getEscrowStatus(bytes32 escrowId) external view returns (EscrowDeposit memory) {
        return _deposits[escrowId];
    }

    /// @notice Calculate the protocol fee for a given amount
    /// @param amount The gross amount
    /// @return fee The protocol fee (0.05%)
    function calculateFee(uint256 amount) external pure returns (uint256 fee) {
        return (amount * FEE_BPS) / FEE_DENOMINATOR;
    }
}
