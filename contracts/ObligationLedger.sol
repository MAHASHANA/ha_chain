// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "./interfaces/IObligationLedger.sol";

/// @title ObligationLedger - Immutable on-chain audit trail for all matches
/// @author Ha_Chain Protocol
/// @notice Records who matched with whom, amounts, timestamps, and net
///         obligations between currency pools. Permanently immutable --
///         no admin functions, no upgrades, no deletions.
/// @dev Only the authorized MatchingPool contract can write records.
contract ObligationLedger is IObligationLedger {
    // ──────────────────────────────────────────────
    //  Types
    // ──────────────────────────────────────────────

    struct MatchRecord {
        bytes32 orderId1;
        bytes32 orderId2;
        bytes32 orderId3;       // bytes32(0) if direct/partial match
        uint256 amount;
        uint256 exchangeRate;   // scaled by 1e18
        uint256 timestamp;
        bytes32 matchType;      // keccak256("direct"), keccak256("partial"), keccak256("triangular")
    }

    // ──────────────────────────────────────────────
    //  Constants
    // ──────────────────────────────────────────────

    bytes32 public constant MATCH_DIRECT = keccak256("direct");
    bytes32 public constant MATCH_PARTIAL = keccak256("partial");
    bytes32 public constant MATCH_TRIANGULAR = keccak256("triangular");

    // ──────────────────────────────────────────────
    //  Immutable State
    // ──────────────────────────────────────────────

    /// @notice The MatchingPool contract -- only writer
    address public immutable matchingPool;

    // ──────────────────────────────────────────────
    //  State
    // ──────────────────────────────────────────────

    /// @notice All match records by ID
    mapping(bytes32 => MatchRecord) private _matches;

    /// @notice Sequential list of all match IDs
    bytes32[] private _matchIds;

    /// @notice Net obligation from poolA to poolB (poolA => poolB => amount)
    /// @dev Positive value means poolA owes poolB; tracked in token-agnostic units
    mapping(bytes32 => mapping(bytes32 => uint256)) private _obligations;

    /// @notice Total protocol volume (sum of all match amounts)
    uint256 public totalVolume;

    /// @notice Volume per pool
    mapping(bytes32 => uint256) public poolVolume;

    /// @notice Match IDs associated with a user address (for history queries)
    mapping(address => bytes32[]) private _userMatches;

    /// @notice Total number of matches
    uint256 public matchCount;

    // ──────────────────────────────────────────────
    //  Events
    // ──────────────────────────────────────────────

    /// @dev Emitted for every recorded match
    event MatchRecorded(
        bytes32 indexed matchId,
        bytes32 indexed orderId1,
        bytes32 indexed orderId2,
        bytes32 orderId3,
        uint256 amount,
        uint256 exchangeRate,
        bytes32 matchType
    );

    /// @dev Emitted when pool obligation is updated
    event ObligationUpdated(
        bytes32 indexed poolIdA,
        bytes32 indexed poolIdB,
        uint256 newObligation
    );

    // ──────────────────────────────────────────────
    //  Errors
    // ──────────────────────────────────────────────

    error OnlyMatchingPool();
    error ZeroAmount();
    error InvalidOrderId();
    error MatchNotFound();

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

    /// @notice Deploy the ledger
    /// @param _matchingPool Address of the authorized MatchingPool contract
    constructor(address _matchingPool) {
        if (_matchingPool == address(0)) revert InvalidOrderId();
        matchingPool = _matchingPool;
    }

    // ──────────────────────────────────────────────
    //  Write Functions
    // ──────────────────────────────────────────────

    /// @inheritdoc IObligationLedger
    function recordMatch(
        bytes32 orderId1,
        bytes32 orderId2,
        uint256 amount,
        uint256 exchangeRate,
        bytes32 matchType
    ) external override onlyMatchingPool {
        if (orderId1 == bytes32(0) || orderId2 == bytes32(0)) revert InvalidOrderId();
        if (amount == 0) revert ZeroAmount();

        bytes32 matchId = keccak256(
            abi.encodePacked(orderId1, orderId2, amount, block.timestamp, matchCount)
        );

        _matches[matchId] = MatchRecord({
            orderId1: orderId1,
            orderId2: orderId2,
            orderId3: bytes32(0),
            amount: amount,
            exchangeRate: exchangeRate,
            timestamp: block.timestamp,
            matchType: matchType
        });

        _matchIds.push(matchId);
        totalVolume += amount;
        unchecked { ++matchCount; }

        emit MatchRecorded(matchId, orderId1, orderId2, bytes32(0), amount, exchangeRate, matchType);
    }

    /// @inheritdoc IObligationLedger
    function recordTriangularMatch(
        bytes32 orderId1,
        bytes32 orderId2,
        bytes32 orderId3,
        uint256 amount,
        uint256 exchangeRate
    ) external override onlyMatchingPool {
        if (orderId1 == bytes32(0) || orderId2 == bytes32(0) || orderId3 == bytes32(0)) {
            revert InvalidOrderId();
        }
        if (amount == 0) revert ZeroAmount();

        bytes32 matchId = keccak256(
            abi.encodePacked(orderId1, orderId2, orderId3, amount, block.timestamp, matchCount)
        );

        _matches[matchId] = MatchRecord({
            orderId1: orderId1,
            orderId2: orderId2,
            orderId3: orderId3,
            amount: amount,
            exchangeRate: exchangeRate,
            timestamp: block.timestamp,
            matchType: MATCH_TRIANGULAR
        });

        _matchIds.push(matchId);
        totalVolume += amount;
        unchecked { ++matchCount; }

        emit MatchRecorded(matchId, orderId1, orderId2, orderId3, amount, exchangeRate, MATCH_TRIANGULAR);
    }

    /// @notice Update net obligation between two pools
    /// @param poolIdA Source pool
    /// @param poolIdB Destination pool
    /// @param amount Amount to add to the obligation
    /// @dev Only callable by MatchingPool
    function updateObligation(
        bytes32 poolIdA,
        bytes32 poolIdB,
        uint256 amount
    ) external onlyMatchingPool {
        _obligations[poolIdA][poolIdB] += amount;
        emit ObligationUpdated(poolIdA, poolIdB, _obligations[poolIdA][poolIdB]);
    }

    /// @notice Associate a match with a user address for history queries
    /// @param user The user address
    /// @param matchId The match ID
    /// @dev Only callable by MatchingPool
    function addUserMatch(address user, bytes32 matchId) external onlyMatchingPool {
        _userMatches[user].push(matchId);
    }

    // ──────────────────────────────────────────────
    //  View Functions
    // ──────────────────────────────────────────────

    /// @notice Get a match record by ID
    /// @param matchId The match identifier
    /// @return The MatchRecord struct
    function getMatch(bytes32 matchId) external view returns (MatchRecord memory) {
        if (_matches[matchId].timestamp == 0) revert MatchNotFound();
        return _matches[matchId];
    }

    /// @notice Get the net obligation from poolA to poolB
    /// @param poolIdA The source pool
    /// @param poolIdB The destination pool
    /// @return The net obligation amount
    function getPoolObligation(bytes32 poolIdA, bytes32 poolIdB) external view returns (uint256) {
        return _obligations[poolIdA][poolIdB];
    }

    /// @notice Get match history for a user with pagination
    /// @param user The user address
    /// @param offset Starting index
    /// @param limit Maximum number of records to return
    /// @return matchIds Array of match IDs
    function getMatchHistory(
        address user,
        uint256 offset,
        uint256 limit
    ) external view returns (bytes32[] memory matchIds) {
        bytes32[] storage userMatchIds = _userMatches[user];
        uint256 total = userMatchIds.length;

        if (offset >= total) {
            return new bytes32[](0);
        }

        uint256 remaining = total - offset;
        uint256 count = remaining < limit ? remaining : limit;
        matchIds = new bytes32[](count);

        for (uint256 i; i < count; ) {
            matchIds[i] = userMatchIds[offset + i];
            unchecked { ++i; }
        }
    }

    /// @notice Get total protocol volume
    /// @return The cumulative volume of all matches
    function getTotalVolume() external view returns (uint256) {
        return totalVolume;
    }

    /// @notice Get volume for a specific pool
    /// @param poolId The pool identifier
    /// @return The cumulative volume for that pool
    function getPoolVolume(bytes32 poolId) external view returns (uint256) {
        return poolVolume[poolId];
    }

    /// @notice Update pool volume (called by MatchingPool during match recording)
    /// @param poolId The pool to update
    /// @param amount Amount to add
    function addPoolVolume(bytes32 poolId, uint256 amount) external onlyMatchingPool {
        poolVolume[poolId] += amount;
    }

    /// @notice Get the match ID at a given index
    /// @param index The index in the sequential list
    /// @return The match ID
    function getMatchIdAt(uint256 index) external view returns (bytes32) {
        return _matchIds[index];
    }
}
