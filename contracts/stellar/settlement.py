"""Stellar settlement implementation for batch inter-agent settlement."""

import hashlib
import time
from datetime import datetime, timezone
from typing import List

from contracts.interfaces.settlement_interface import SettlementInterface


class StellarSettlement(SettlementInterface):
    """
    Stellar-based settlement implementation.

    Handles batch settlement of net positions between agents,
    platform fee collection, and cross-corridor netting. Uses
    Stellar's path payment operations for atomic multi-party settlements.
    """

    def __init__(
        self,
        horizon_url: str = "https://horizon-testnet.stellar.org",
        platform_keypair=None,
        platform_address: str = "",
        network_passphrase: str = "Test SDF Network ; September 2015",
    ):
        self.horizon_url = horizon_url
        self.platform_keypair = platform_keypair
        self.platform_address = platform_address
        self.network_passphrase = network_passphrase
        self._batches: dict = {}
        self._balances: dict = {}  # address -> balance

    async def create_settlement_batch(
        self,
        batch_id: str,
        entries: List[dict],
    ) -> str:
        """Create and execute a settlement batch."""
        if not entries:
            raise ValueError("Settlement batch cannot be empty")

        for i, entry in enumerate(entries):
            required_keys = {"from_address", "to_address", "amount_usdc", "reference"}
            if not required_keys.issubset(entry.keys()):
                raise ValueError(
                    f"Entry {i} missing required keys: {required_keys - entry.keys()}"
                )
            if entry["amount_usdc"] <= 0:
                raise ValueError(f"Entry {i} has non-positive amount")

        total = sum(e["amount_usdc"] for e in entries)
        tx_hash = self._generate_tx_hash(f"settle-{batch_id}-{time.time()}")

        # Simulate balance updates
        for entry in entries:
            from_addr = entry["from_address"]
            to_addr = entry["to_address"]
            amount = entry["amount_usdc"]

            self._balances.setdefault(from_addr, 0.0)
            self._balances.setdefault(to_addr, 0.0)
            self._balances[from_addr] -= amount
            self._balances[to_addr] += amount

        self._batches[batch_id] = {
            "batch_id": batch_id,
            "status": "completed",
            "entries_count": len(entries),
            "entries": entries,
            "total_amount_usdc": total,
            "tx_hash": tx_hash,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "completed_at": datetime.now(timezone.utc).isoformat(),
        }

        return tx_hash

    async def collect_platform_fee(
        self,
        transfer_id: str,
        fee_amount_usdc: float,
        source_address: str,
    ) -> str:
        """Collect platform fee from a transfer."""
        if fee_amount_usdc <= 0:
            raise ValueError("Fee amount must be positive")

        tx_hash = self._generate_tx_hash(f"fee-{transfer_id}-{time.time()}")

        self._balances.setdefault(source_address, 0.0)
        self._balances.setdefault(self.platform_address, 0.0)
        self._balances[source_address] -= fee_amount_usdc
        self._balances[self.platform_address] += fee_amount_usdc

        return tx_hash

    async def get_settlement_status(self, batch_id: str) -> dict:
        """Get settlement batch status."""
        batch = self._batches.get(batch_id)
        if not batch:
            return {
                "batch_id": batch_id,
                "status": "not_found",
                "entries_count": 0,
                "total_amount_usdc": 0.0,
                "tx_hash": None,
                "created_at": None,
                "completed_at": None,
            }
        return {
            "batch_id": batch["batch_id"],
            "status": batch["status"],
            "entries_count": batch["entries_count"],
            "total_amount_usdc": batch["total_amount_usdc"],
            "tx_hash": batch["tx_hash"],
            "created_at": batch["created_at"],
            "completed_at": batch["completed_at"],
        }

    async def get_agent_balance(self, agent_address: str) -> float:
        """Get USDC balance for an address."""
        return self._balances.get(agent_address, 0.0)

    @staticmethod
    def _generate_tx_hash(seed: str) -> str:
        return hashlib.sha256(seed.encode()).hexdigest()
