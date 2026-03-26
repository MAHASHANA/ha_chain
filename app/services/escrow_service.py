"""Escrow service: wraps blockchain escrow interface for the application layer."""

from typing import Optional

from app.enums import EscrowStatus


class EscrowService:
    """Application-level escrow service that delegates to a blockchain implementation."""

    def __init__(self, blockchain_escrow):
        """
        Args:
            blockchain_escrow: An implementation of EscrowInterface
                (e.g., StellarEscrowAccount or MockEscrowService).
        """
        self.blockchain = blockchain_escrow

    async def lock_funds(
        self, transfer_id: str, amount_usdc: float, sender_address: str
    ) -> str:
        """Lock USDC in escrow for a transfer. Returns tx_hash."""
        if amount_usdc <= 0:
            raise ValueError("Escrow amount must be positive")
        if not sender_address:
            raise ValueError("Sender address is required")

        tx_hash = await self.blockchain.lock_funds(
            transfer_id=transfer_id,
            amount_usdc=amount_usdc,
            sender_address=sender_address,
        )
        return tx_hash

    async def release_funds(
        self, transfer_id: str, recipient_address: str
    ) -> str:
        """Release escrowed funds to the agent. Returns tx_hash."""
        status = await self.blockchain.get_escrow_status(transfer_id)
        if status.get("status") != EscrowStatus.LOCKED.value:
            raise ValueError(
                f"Cannot release: escrow status is {status.get('status')}"
            )

        tx_hash = await self.blockchain.release_funds(
            transfer_id=transfer_id,
            recipient_address=recipient_address,
        )
        return tx_hash

    async def refund_funds(self, transfer_id: str, sender_address: str) -> str:
        """Refund escrowed funds back to sender. Returns tx_hash."""
        status = await self.blockchain.get_escrow_status(transfer_id)
        if status.get("status") != EscrowStatus.LOCKED.value:
            raise ValueError(
                f"Cannot refund: escrow status is {status.get('status')}"
            )

        tx_hash = await self.blockchain.refund_funds(
            transfer_id=transfer_id,
            sender_address=sender_address,
        )
        return tx_hash

    async def get_status(self, transfer_id: str) -> dict:
        """Get escrow status for a transfer."""
        return await self.blockchain.get_escrow_status(transfer_id)
