"""Mock blockchain services for testing without real network calls."""

import hashlib
import time
from datetime import datetime, timezone
from typing import Dict, Optional

from contracts.interfaces.escrow_interface import EscrowInterface
from contracts.interfaces.staking_interface import StakingInterface


class MockEscrowService(EscrowInterface):
    """
    In-memory mock of the escrow blockchain interface.

    Tracks all escrow state in dictionaries, enabling deterministic
    testing of escrow flows without any blockchain network calls.
    """

    def __init__(self):
        self._escrows: Dict[str, dict] = {}
        self._tx_counter: int = 0

    def _next_tx_hash(self, prefix: str = "mock") -> str:
        self._tx_counter += 1
        seed = f"{prefix}-{self._tx_counter}-{time.time()}"
        return hashlib.sha256(seed.encode()).hexdigest()

    async def lock_funds(
        self,
        transfer_id: str,
        amount_usdc: float,
        sender_address: str,
    ) -> str:
        if amount_usdc <= 0:
            raise ValueError("Amount must be positive")
        if not sender_address:
            raise ValueError("Sender address required")

        tx_hash = self._next_tx_hash("lock")

        self._escrows[transfer_id] = {
            "status": "locked",
            "amount_usdc": amount_usdc,
            "sender_address": sender_address,
            "recipient_address": None,
            "lock_tx_hash": tx_hash,
            "release_tx_hash": None,
            "refund_tx_hash": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        return tx_hash

    async def release_funds(
        self,
        transfer_id: str,
        recipient_address: str,
    ) -> str:
        escrow = self._escrows.get(transfer_id)
        if not escrow:
            raise ValueError(f"No escrow for transfer {transfer_id}")
        if escrow["status"] != "locked":
            raise ValueError(f"Cannot release: status is {escrow['status']}")

        tx_hash = self._next_tx_hash("release")
        escrow["status"] = "released"
        escrow["recipient_address"] = recipient_address
        escrow["release_tx_hash"] = tx_hash
        return tx_hash

    async def refund_funds(
        self,
        transfer_id: str,
        sender_address: str,
    ) -> str:
        escrow = self._escrows.get(transfer_id)
        if not escrow:
            raise ValueError(f"No escrow for transfer {transfer_id}")
        if escrow["status"] != "locked":
            raise ValueError(f"Cannot refund: status is {escrow['status']}")

        tx_hash = self._next_tx_hash("refund")
        escrow["status"] = "refunded"
        escrow["refund_tx_hash"] = tx_hash
        return tx_hash

    async def get_escrow_status(self, transfer_id: str) -> dict:
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
            "escrow_address": f"GMOCK{transfer_id[:20].upper()}",
            "created_at": escrow["created_at"],
            "tx_hash": escrow["lock_tx_hash"],
        }

    # Test helpers
    def get_all_escrows(self) -> Dict[str, dict]:
        return dict(self._escrows)

    def reset(self):
        self._escrows.clear()
        self._tx_counter = 0


class MockStakingService(StakingInterface):
    """
    In-memory mock of the staking blockchain interface.

    Tracks all staking state in dictionaries for deterministic testing.
    """

    MINIMUM_STAKE = 100.0

    def __init__(self):
        self._stakes: Dict[str, dict] = {}
        self._tx_counter: int = 0

    def _next_tx_hash(self, prefix: str = "mock") -> str:
        self._tx_counter += 1
        seed = f"{prefix}-{self._tx_counter}-{time.time()}"
        return hashlib.sha256(seed.encode()).hexdigest()

    async def stake(
        self,
        agent_id: str,
        amount_usdc: float,
        wallet_address: str,
    ) -> str:
        if amount_usdc < self.MINIMUM_STAKE:
            raise ValueError(f"Minimum stake is ${self.MINIMUM_STAKE}")
        if agent_id in self._stakes and self._stakes[agent_id]["status"] == "active":
            raise ValueError(f"Agent {agent_id} already has an active stake")

        tx_hash = self._next_tx_hash("stake")
        self._stakes[agent_id] = {
            "agent_id": agent_id,
            "staked_amount_usdc": amount_usdc,
            "original_amount_usdc": amount_usdc,
            "total_slashed_usdc": 0.0,
            "slash_count": 0,
            "slash_history": [],
            "wallet_address": wallet_address,
            "status": "active",
            "staked_at": datetime.now(timezone.utc).isoformat(),
            "tx_hash": tx_hash,
        }
        return tx_hash

    async def slash(
        self,
        agent_id: str,
        amount_usdc: float,
        reason: str,
    ) -> str:
        stake = self._stakes.get(agent_id)
        if not stake:
            raise ValueError(f"No stake for agent {agent_id}")
        if stake["status"] != "active":
            raise ValueError(f"Stake is {stake['status']}, cannot slash")
        if amount_usdc > stake["staked_amount_usdc"]:
            raise ValueError(
                f"Slash ${amount_usdc} exceeds remaining ${stake['staked_amount_usdc']}"
            )

        tx_hash = self._next_tx_hash("slash")
        stake["staked_amount_usdc"] -= amount_usdc
        stake["total_slashed_usdc"] += amount_usdc
        stake["slash_count"] += 1
        stake["slash_history"].append({
            "amount_usdc": amount_usdc,
            "reason": reason,
            "tx_hash": tx_hash,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        if stake["staked_amount_usdc"] <= 0:
            stake["status"] = "depleted"
        return tx_hash

    async def unstake(self, agent_id: str) -> str:
        stake = self._stakes.get(agent_id)
        if not stake:
            raise ValueError(f"No stake for agent {agent_id}")
        if stake["status"] != "active":
            raise ValueError(f"Cannot unstake: status is {stake['status']}")

        tx_hash = self._next_tx_hash("unstake")
        stake["status"] = "unstaked"
        return tx_hash

    async def get_stake_info(self, agent_id: str) -> dict:
        stake = self._stakes.get(agent_id)
        if not stake:
            return {
                "agent_id": agent_id,
                "staked_amount_usdc": 0.0,
                "original_amount_usdc": 0.0,
                "total_slashed_usdc": 0.0,
                "slash_count": 0,
                "staked_at": None,
                "wallet_address": None,
                "status": "none",
            }
        return {
            "agent_id": stake["agent_id"],
            "staked_amount_usdc": stake["staked_amount_usdc"],
            "original_amount_usdc": stake["original_amount_usdc"],
            "total_slashed_usdc": stake["total_slashed_usdc"],
            "slash_count": stake["slash_count"],
            "staked_at": stake["staked_at"],
            "wallet_address": stake["wallet_address"],
            "status": stake["status"],
        }

    async def get_slash_history(self, agent_id: str) -> list:
        stake = self._stakes.get(agent_id)
        if not stake:
            return []
        return stake.get("slash_history", [])

    # Test helpers
    def reset(self):
        self._stakes.clear()
        self._tx_counter = 0
