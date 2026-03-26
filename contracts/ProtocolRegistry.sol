// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "./interfaces/IProtocolRegistry.sol";

/// @title ProtocolRegistry - Immutable registry of supported currency pools
/// @author Ha_Chain Protocol
/// @notice Stores pool configurations set at deployment. No admin functions exist
///         after construction -- the registry is permanently immutable.
/// @dev All pool configs are set in the constructor. No setter functions exist.
contract ProtocolRegistry is IProtocolRegistry {
    // ──────────────────────────────────────────────
    //  Types
    // ──────────────────────────────────────────────

    struct PoolConfig {
        bytes32 poolId;
        address token;
        uint256 minDeposit;
        uint256 maxDeposit;
        bool active;
    }

    // ──────────────────────────────────────────────
    //  State
    // ──────────────────────────────────────────────

    /// @notice Mapping from poolId to its configuration
    mapping(bytes32 => PoolConfig) private _pools;

    /// @notice Array of all registered pool IDs for enumeration
    bytes32[] private _poolIds;

    /// @notice Total number of registered pools
    uint256 public poolCount;

    // ──────────────────────────────────────────────
    //  Events
    // ──────────────────────────────────────────────

    /// @dev Emitted once per pool during construction
    event PoolRegistered(
        bytes32 indexed poolId,
        address indexed token,
        uint256 minDeposit,
        uint256 maxDeposit
    );

    // ──────────────────────────────────────────────
    //  Errors
    // ──────────────────────────────────────────────

    error PoolNotFound(bytes32 poolId);
    error InvalidPoolConfig();
    error DuplicatePool(bytes32 poolId);
    error EmptyPoolList();

    // ──────────────────────────────────────────────
    //  Constructor (only opportunity to set state)
    // ──────────────────────────────────────────────

    /// @notice Deploy the registry with all supported pools
    /// @param poolIds Array of pool identifiers (e.g., keccak256("USD"))
    /// @param tokens Array of ERC20 token addresses for each pool
    /// @param minDeposits Array of minimum deposit amounts
    /// @param maxDeposits Array of maximum deposit amounts
    constructor(
        bytes32[] memory poolIds,
        address[] memory tokens,
        uint256[] memory minDeposits,
        uint256[] memory maxDeposits
    ) {
        uint256 len = poolIds.length;
        if (len == 0) revert EmptyPoolList();
        if (len != tokens.length || len != minDeposits.length || len != maxDeposits.length) {
            revert InvalidPoolConfig();
        }

        for (uint256 i; i < len; ) {
            bytes32 pid = poolIds[i];
            if (tokens[i] == address(0)) revert InvalidPoolConfig();
            if (minDeposits[i] == 0 || maxDeposits[i] == 0) revert InvalidPoolConfig();
            if (minDeposits[i] > maxDeposits[i]) revert InvalidPoolConfig();
            if (_pools[pid].active) revert DuplicatePool(pid);

            _pools[pid] = PoolConfig({
                poolId: pid,
                token: tokens[i],
                minDeposit: minDeposits[i],
                maxDeposit: maxDeposits[i],
                active: true
            });
            _poolIds.push(pid);

            emit PoolRegistered(pid, tokens[i], minDeposits[i], maxDeposits[i]);

            unchecked { ++i; }
        }

        poolCount = len;
    }

    // ──────────────────────────────────────────────
    //  View Functions
    // ──────────────────────────────────────────────

    /// @inheritdoc IProtocolRegistry
    function isPoolActive(bytes32 poolId) external view override returns (bool) {
        return _pools[poolId].active;
    }

    /// @inheritdoc IProtocolRegistry
    function getPoolToken(bytes32 poolId) external view override returns (address) {
        if (!_pools[poolId].active) revert PoolNotFound(poolId);
        return _pools[poolId].token;
    }

    /// @inheritdoc IProtocolRegistry
    function getMinDeposit(bytes32 poolId) external view override returns (uint256) {
        if (!_pools[poolId].active) revert PoolNotFound(poolId);
        return _pools[poolId].minDeposit;
    }

    /// @inheritdoc IProtocolRegistry
    function getMaxDeposit(bytes32 poolId) external view override returns (uint256) {
        if (!_pools[poolId].active) revert PoolNotFound(poolId);
        return _pools[poolId].maxDeposit;
    }

    /// @notice Get the full configuration for a pool
    /// @param poolId The pool identifier
    /// @return config The complete PoolConfig struct
    function getPoolConfig(bytes32 poolId) external view returns (PoolConfig memory config) {
        if (!_pools[poolId].active) revert PoolNotFound(poolId);
        return _pools[poolId];
    }

    /// @notice Get the pool ID at a given index (for enumeration)
    /// @param index The index in the pool list
    /// @return The pool ID at that index
    function getPoolIdAt(uint256 index) external view returns (bytes32) {
        return _poolIds[index];
    }

    /// @notice Get all registered pool IDs
    /// @return Array of all pool IDs
    function getAllPoolIds() external view returns (bytes32[] memory) {
        return _poolIds;
    }
}
