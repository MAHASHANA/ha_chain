// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title IEscrow - Interface for the Escrow contract
/// @notice Defines the external functions that other contracts use to interact with Escrow
interface IEscrow {
    /// @notice Lock funds into escrow
    /// @param token The ERC20 token address
    /// @param depositor The address depositing funds
    /// @param amount The amount to lock (before protocol fee)
    /// @param expiryTime The timestamp after which funds can be refunded
    /// @return escrowId The unique identifier for this escrow deposit
    function lockFunds(
        address token,
        address depositor,
        uint256 amount,
        uint256 expiryTime
    ) external returns (bytes32 escrowId);

    /// @notice Release escrowed funds to a recipient
    /// @param escrowId The escrow deposit identifier
    /// @param recipient The address to receive the funds
    function releaseFunds(bytes32 escrowId, address recipient) external;

    /// @notice Refund escrowed funds after expiry
    /// @param escrowId The escrow deposit identifier
    function refund(bytes32 escrowId) external;

    /// @notice Get the net amount (after fee) for an escrow deposit
    /// @param escrowId The escrow deposit identifier
    /// @return The amount available for release
    function getEscrowAmount(bytes32 escrowId) external view returns (uint256);

    /// @notice Check if an escrow deposit is active (not released, not refunded)
    /// @param escrowId The escrow deposit identifier
    /// @return True if the escrow is still active
    function isActive(bytes32 escrowId) external view returns (bool);
}
