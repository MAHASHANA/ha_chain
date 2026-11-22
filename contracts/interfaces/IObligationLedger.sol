// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title IObligationLedger - Interface for the ObligationLedger contract
/// @notice Defines external functions for recording and querying match records
interface IObligationLedger {
    /// @notice Record a direct or partial match
    /// @param orderId1 First order in the match
    /// @param orderId2 Second order in the match
    /// @param amount The matched amount
    /// @param exchangeRate The rate applied (scaled by 1e18)
    /// @param matchType The type of match ("direct" or "partial")
    function recordMatch(
        bytes32 orderId1,
        bytes32 orderId2,
        uint256 amount,
        uint256 exchangeRate,
        bytes32 matchType
    ) external;

    /// @notice Record a triangular match
    /// @param orderId1 First order in the triangular match
    /// @param orderId2 Second order in the triangular match
    /// @param orderId3 Third order in the triangular match
    /// @param amount The matched amount
    /// @param exchangeRate The rate applied (scaled by 1e18)
    function recordTriangularMatch(
        bytes32 orderId1,
        bytes32 orderId2,
        bytes32 orderId3,
        uint256 amount,
        uint256 exchangeRate
    ) external;

    /// @notice Add matched volume to a pool's running total
    function addPoolVolume(bytes32 poolId, uint256 amount) external;

    /// @notice Add to the running obligation from poolIdA to poolIdB
    function updateObligation(bytes32 poolIdA, bytes32 poolIdB, uint256 amount) external;

    /// @notice Associate a match with a user for history queries
    function addUserMatch(address user, bytes32 matchId) external;
}
