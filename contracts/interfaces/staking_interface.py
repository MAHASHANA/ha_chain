"""Abstract staking contract interface for agent collateral management."""

from abc import ABC, abstractmethod
from typing import Optional


class StakingInterface(ABC):
    """
    Abstract interface for agent staking smart contract operations.

    Agents must stake USDC as collateral to participate in the network.
    The stake can be slashed for bad behavior (failed deliveries,
    fraud, SLA violations) and returned when the agent exits.
    """

    @abstractmethod
    async def stake(
        self,
        agent_id: str,
        amount_usdc: float,
        wallet_address: str,
    ) -> str:
        """
        Lock agent's collateral stake.

        The agent must stake a minimum amount of USDC to become active
        on the platform. Higher stakes unlock higher daily limits and
        improve matching score.

        Args:
            agent_id: Platform agent identifier.
            amount_usdc: Amount of USDC to stake.
            wallet_address: Agent's blockchain wallet address.

        Returns:
            Transaction hash of the staking operation.

        Raises:
            ValueError: If amount is below minimum or agent already staked.
            BlockchainError: If the on-chain transaction fails.
        """
        ...

    @abstractmethod
    async def slash(
        self,
        agent_id: str,
        amount_usdc: float,
        reason: str,
    ) -> str:
        """
        Slash agent's stake as penalty for bad behavior.

        Reasons include: failed delivery, fraudulent confirmation,
        SLA violations, compliance failures.

        Args:
            agent_id: Platform agent identifier.
            amount_usdc: Amount to slash from stake.
            reason: Human-readable reason for the slash.

        Returns:
            Transaction hash of the slash operation.

        Raises:
            ValueError: If slash amount exceeds remaining stake.
            BlockchainError: If the on-chain transaction fails.
        """
        ...

    @abstractmethod
    async def unstake(self, agent_id: str) -> str:
        """
        Return remaining stake to the agent.

        Can only be called if the agent is in good standing and has
        no pending transfers. There may be a cooldown period.

        Args:
            agent_id: Platform agent identifier.

        Returns:
            Transaction hash of the unstake operation.

        Raises:
            ValueError: If agent has pending obligations or is not eligible.
            BlockchainError: If the on-chain transaction fails.
        """
        ...

    @abstractmethod
    async def get_stake_info(self, agent_id: str) -> dict:
        """
        Get current staking information for an agent.

        Returns:
            Dictionary with keys:
                - agent_id: The agent's platform ID
                - staked_amount_usdc: Current stake balance
                - original_amount_usdc: Original stake amount
                - total_slashed_usdc: Total amount slashed
                - slash_count: Number of slash events
                - staked_at: ISO timestamp of initial stake
                - wallet_address: Agent's wallet address
                - status: 'active', 'unstaking', 'unstaked', 'depleted'
        """
        ...

    @abstractmethod
    async def get_slash_history(self, agent_id: str) -> list:
        """
        Get the slash history for an agent.

        Returns:
            List of dictionaries, each with:
                - amount_usdc: Slashed amount
                - reason: Slash reason
                - tx_hash: Transaction hash
                - timestamp: ISO timestamp
        """
        ...
