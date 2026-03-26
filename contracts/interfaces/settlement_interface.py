"""Abstract settlement interface for inter-agent and platform settlement."""

from abc import ABC, abstractmethod
from typing import List, Optional


class SettlementInterface(ABC):
    """
    Abstract interface for settlement operations.

    Handles batch settlement between agents, platform fee collection,
    and cross-corridor netting.
    """

    @abstractmethod
    async def create_settlement_batch(
        self,
        batch_id: str,
        entries: List[dict],
    ) -> str:
        """
        Create a settlement batch with multiple entries.

        Each entry specifies a from_address, to_address, and amount.
        The batch is executed atomically.

        Args:
            batch_id: Unique batch identifier.
            entries: List of dicts with keys:
                - from_address: Source wallet
                - to_address: Destination wallet
                - amount_usdc: Amount to transfer
                - reference: Transfer/fee reference ID

        Returns:
            Transaction hash of the batch settlement.

        Raises:
            ValueError: If batch is empty or has invalid entries.
            BlockchainError: If the on-chain transaction fails.
        """
        ...

    @abstractmethod
    async def collect_platform_fee(
        self,
        transfer_id: str,
        fee_amount_usdc: float,
        source_address: str,
    ) -> str:
        """
        Collect platform fee from a transfer into the platform treasury.

        Args:
            transfer_id: The transfer this fee relates to.
            fee_amount_usdc: Fee amount.
            source_address: Address to collect from (escrow or agent).

        Returns:
            Transaction hash.
        """
        ...

    @abstractmethod
    async def get_settlement_status(self, batch_id: str) -> dict:
        """
        Get the status of a settlement batch.

        Returns:
            Dictionary with keys:
                - batch_id: The batch identifier
                - status: 'pending', 'processing', 'completed', 'failed'
                - entries_count: Number of entries
                - total_amount_usdc: Sum of all entry amounts
                - tx_hash: Transaction hash (if submitted)
                - created_at: ISO timestamp
                - completed_at: ISO timestamp (if completed)
        """
        ...

    @abstractmethod
    async def get_agent_balance(self, agent_address: str) -> float:
        """
        Get the USDC balance for an agent's address.

        Args:
            agent_address: Agent's blockchain wallet address.

        Returns:
            Current USDC balance.
        """
        ...
