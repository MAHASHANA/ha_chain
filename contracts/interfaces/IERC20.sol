// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title IERC20 - Standard ERC20 Interface
/// @notice Minimal ERC20 interface for Ha_Chain protocol token interactions
interface IERC20 {
    /// @notice Returns the total token supply
    function totalSupply() external view returns (uint256);

    /// @notice Returns the token balance of an account
    /// @param account The address to query
    function balanceOf(address account) external view returns (uint256);

    /// @notice Transfers tokens to a recipient
    /// @param to The recipient address
    /// @param amount The amount to transfer
    /// @return True if the transfer succeeded
    function transfer(address to, uint256 amount) external returns (bool);

    /// @notice Returns the remaining allowance for a spender
    /// @param owner The token owner
    /// @param spender The approved spender
    function allowance(address owner, address spender) external view returns (uint256);

    /// @notice Approves a spender to transfer tokens
    /// @param spender The spender address
    /// @param amount The approved amount
    /// @return True if the approval succeeded
    function approve(address spender, uint256 amount) external returns (bool);

    /// @notice Transfers tokens from one address to another using allowance
    /// @param from The source address
    /// @param to The destination address
    /// @param amount The amount to transfer
    /// @return True if the transfer succeeded
    function transferFrom(address from, address to, uint256 amount) external returns (bool);

    /// @notice Returns the number of decimals the token uses
    function decimals() external view returns (uint8);

    /// @dev Emitted when tokens are transferred
    event Transfer(address indexed from, address indexed to, uint256 value);

    /// @dev Emitted when an allowance is set
    event Approval(address indexed owner, address indexed spender, uint256 value);
}
