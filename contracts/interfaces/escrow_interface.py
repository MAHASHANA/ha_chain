"""Abstract escrow contract interface for blockchain-backed escrow."""

from abc import ABC, abstractmethod
from typing import Optional


class EscrowInterface(ABC):
    """
    Abstract interface for escrow smart contract operations.

    Implementations must handle locking, releasing, and refunding USDC
    for transfer escrow accounts. Each implementation targets a specific
    blockchain (Stellar, Ethereum, etc.).
    """

    @abstractmethod
    async def lock_funds(
        self,
        transfer_id: str,
        amount_usdc: float,
        sender_address: str,
    ) -> str:
        """
        Lock USDC in escrow for a specific transfer.

        Creates or uses a pre-existing escrow account, then moves
        the specified amount of USDC from the sender to the escrow.

        Args:
            transfer_id: Unique transfer identifier.
            amount_usdc: Amount of USDC to lock.
            sender_address: Blockchain address of the sender.

        Returns:
            Transaction hash of the lock operation.

        Raises:
            ValueError: If amount is invalid or sender has insufficient funds.
            BlockchainError: If the on-chain transaction fails.
        """
        ...

    @abstractmethod
    async def release_funds(
        self,
        transfer_id: str,
        recipient_address: str,
    ) -> str:
        """
        Release escrowed USDC to the delivery agent.

        Should only succeed if the escrow is in LOCKED state and
        the release is authorized (e.g., 2-of-3 multi-sig).

        Args:
            transfer_id: Unique transfer identifier.
            recipient_address: Blockchain address of the agent.

        Returns:
            Transaction hash of the release operation.

        Raises:
            ValueError: If escrow is not in LOCKED state.
            BlockchainError: If the on-chain transaction fails.
        """
        ...

    @abstractmethod
    async def refund_funds(
        self,
        transfer_id: str,
        sender_address: str,
    ) -> str:
        """
        Refund escrowed USDC back to the sender.

        Can be triggered by cancellation, timeout, or dispute resolution.

        Args:
            transfer_id: Unique transfer identifier.
            sender_address: Blockchain address of the sender.

        Returns:
            Transaction hash of the refund operation.

        Raises:
            ValueError: If escrow is not in a refundable state.
            BlockchainError: If the on-chain transaction fails.
        """
        ...

    @abstractmethod
    async def get_escrow_status(self, transfer_id: str) -> dict:
        """
        Get the current status and balance of an escrow.

        Returns:
            Dictionary with keys:
                - status: EscrowStatus value ('pending', 'locked', 'released', 'refunded')
                - amount_usdc: Amount held in escrow
                - transfer_id: The transfer ID
                - escrow_address: Blockchain address of escrow account (if any)
                - created_at: ISO timestamp of creation
                - tx_hash: Most recent transaction hash
        """
        ...
