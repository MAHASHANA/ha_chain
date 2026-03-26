"""Stellar escrow implementation using multi-sig accounts."""

import hashlib
import time
from datetime import datetime, timezone
from typing import Optional

from contracts.interfaces.escrow_interface import EscrowInterface


class StellarEscrowAccount(EscrowInterface):
    """
    Stellar-based escrow implementation.

    Uses multi-sig escrow accounts (2-of-3: sender, agent, platform) on
    the Stellar network. USDC is represented as a Stellar asset issued
    by a trusted anchor.

    For production, this integrates with the Stellar SDK. For testnet
    development, we use horizon-testnet.stellar.org.
    """

    USDC_ASSET_CODE = "USDC"
    USDC_ISSUER = "GBBD47IF6LWK7P7MDEVSCWR7DPUWV3NY3DTQEVFL4NAT4AQH3ZLLFLA5"
    TIMEOUT_SECONDS = 86400  # 24 hours

    def __init__(
        self,
        horizon_url: str = "https://horizon-testnet.stellar.org",
        platform_keypair=None,
        network_passphrase: str = "Test SDF Network ; September 2015",
    ):
        self.horizon_url = horizon_url
        self.platform_keypair = platform_keypair
        self.network_passphrase = network_passphrase
        self._escrows: dict = {}  # In-memory store for dev/test

    async def lock_funds(
        self,
        transfer_id: str,
        amount_usdc: float,
        sender_address: str,
    ) -> str:
        """
        Lock USDC in a Stellar escrow account.

        In production, this would:
        1. Create a new Stellar account for the escrow
        2. Set up multi-sig (2-of-3) with sender, platform, and future agent
        3. Send USDC from sender to escrow account
        4. Set a time-bound pre-authorized refund transaction (24h timeout)

        For development, we simulate this with an in-memory store.
        """
        if amount_usdc <= 0:
            raise ValueError("Amount must be positive")

        escrow_address = self._generate_escrow_address(transfer_id)
        tx_hash = self._generate_tx_hash(f"lock-{transfer_id}-{time.time()}")

        self._escrows[transfer_id] = {
            "status": "locked",
            "amount_usdc": amount_usdc,
            "transfer_id": transfer_id,
            "escrow_address": escrow_address,
            "sender_address": sender_address,
            "recipient_address": None,
            "lock_tx_hash": tx_hash,
            "release_tx_hash": None,
            "refund_tx_hash": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "timeout_at": datetime.fromtimestamp(
                time.time() + self.TIMEOUT_SECONDS, tz=timezone.utc
            ).isoformat(),
        }

        return tx_hash

    async def release_funds(
        self,
        transfer_id: str,
        recipient_address: str,
    ) -> str:
        """
        Release USDC from escrow to the delivery agent.

        In production, this requires 2-of-3 signatures on the Stellar
        multi-sig account to authorize the payment to the agent.
        """
        escrow = self._escrows.get(transfer_id)
        if not escrow:
            raise ValueError(f"No escrow found for transfer {transfer_id}")
        if escrow["status"] != "locked":
            raise ValueError(f"Escrow status is {escrow['status']}, expected 'locked'")

        tx_hash = self._generate_tx_hash(f"release-{transfer_id}-{time.time()}")

        escrow["status"] = "released"
        escrow["recipient_address"] = recipient_address
        escrow["release_tx_hash"] = tx_hash
        escrow["released_at"] = datetime.now(timezone.utc).isoformat()

        return tx_hash

    async def refund_funds(
        self,
        transfer_id: str,
        sender_address: str,
    ) -> str:
        """
        Refund USDC from escrow back to sender.

        In production, this uses either:
        - A pre-authorized refund transaction (after timeout)
        - A 2-of-3 multi-sig authorization (manual refund)
        """
        escrow = self._escrows.get(transfer_id)
        if not escrow:
            raise ValueError(f"No escrow found for transfer {transfer_id}")
        if escrow["status"] != "locked":
            raise ValueError(f"Escrow status is {escrow['status']}, expected 'locked'")

        tx_hash = self._generate_tx_hash(f"refund-{transfer_id}-{time.time()}")

        escrow["status"] = "refunded"
        escrow["refund_tx_hash"] = tx_hash
        escrow["refunded_at"] = datetime.now(timezone.utc).isoformat()

        return tx_hash

    async def get_escrow_status(self, transfer_id: str) -> dict:
        """Get the current escrow status."""
        escrow = self._escrows.get(transfer_id)
        if not escrow:
            return {
                "status": "pending",
                "amount_usdc": 0.0,
                "transfer_id": transfer_id,
                "escrow_address": None,
                "created_at": None,
                "tx_hash": None,
            }

        return {
            "status": escrow["status"],
            "amount_usdc": escrow["amount_usdc"],
            "transfer_id": transfer_id,
            "escrow_address": escrow["escrow_address"],
            "created_at": escrow["created_at"],
            "tx_hash": escrow.get("lock_tx_hash"),
        }

    def _generate_escrow_address(self, transfer_id: str) -> str:
        """Generate a deterministic escrow address from the transfer ID."""
        hash_bytes = hashlib.sha256(f"escrow-{transfer_id}".encode()).hexdigest()[:48]
        return f"G{hash_bytes.upper()}"

    @staticmethod
    def _generate_tx_hash(seed: str) -> str:
        """Generate a fake but deterministic transaction hash."""
        return hashlib.sha256(seed.encode()).hexdigest()
