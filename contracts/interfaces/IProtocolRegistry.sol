// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title IProtocolRegistry - Interface for the ProtocolRegistry contract
/// @notice Defines external functions for querying pool configurations
interface IProtocolRegistry {
    /// @notice Check if a pool is active and registered
    /// @param poolId The pool identifier
    /// @return True if the pool exists and is active
    function isPoolActive(bytes32 poolId) external view returns (bool);

    /// @notice Get the token address for a pool
    /// @param poolId The pool identifier
    /// @return The ERC20 token address associated with this pool
    function getPoolToken(bytes32 poolId) external view returns (address);

    /// @notice Get the minimum deposit for a pool
    /// @param poolId The pool identifier
    /// @return The minimum deposit amount
    function getMinDeposit(bytes32 poolId) external view returns (uint256);

    /// @notice Get the maximum deposit for a pool
    /// @param poolId The pool identifier
    /// @return The maximum deposit amount
    function getMaxDeposit(bytes32 poolId) external view returns (uint256);
}
