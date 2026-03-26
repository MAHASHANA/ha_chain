"""Stellar staking implementation for agent collateral."""

import hashlib
import time
from datetime import datetime, timezone
from typing import List

from contracts.interfaces.staking_interface import StakingInterface


class StellarStakingAccount(StakingInterface):
    """
    Stellar-based staking implementation.

    Agents lock USDC as collateral in a staking account on Stellar.
    The platform can slash the stake for bad behavior and return it
    when the agent exits in good standing.

    In production, uses Stellar claimable balances with conditions.
    """

    MINIMUM_STAKE_USDC = 100.0

    def __init__(
        self,
        horizon_url: str = "https://horizon-testnet.stellar.org",
        platform_keypair=None,
        network_passphrase: str = "Test SDF Network ; September 2015",
    ):
        self.horizon_url = horizon_url
        self.platform_keypair = platform_keypair
        self.network_passphrase = network_passphrase
        self._stakes: dict = {}  # agent_id -> stake info

    async def stake(
        self,
        agent_id: str,
        amount_usdc: float,
        wallet_address: str,
    ) -> str:
        """Lock agent collateral in a staking account."""
        if amount_usdc < self.MINIMUM_STAKE_USDC:
            raise ValueError(
                f"Minimum stake is ${self.MINIMUM_STAKE_USDC}. Got ${amount_usdc}."
            )

        if agent_id in self._stakes and self._stakes[agent_id]["status"] == "active":
            raise ValueError(f"Agent {agent_id} already has an active stake")

        tx_hash = self._generate_tx_hash(f"stake-{agent_id}-{time.time()}")

        self._stakes[agent_id] = {
            "agent_id": agent_id,
            "staked_amount_usdc": amount_usdc,
            "original_amount_usdc": amount_usdc,
            "total_slashed_usdc": 0.0,
            "slash_count": 0,
            "slash_history": [],
            "staked_at": datetime.now(timezone.utc).isoformat(),
            "wallet_address": wallet_address,
            "status": "active",
            "tx_hash": tx_hash,
        }

        return tx_hash

    async def slash(
        self,
        agent_id: str,
        amount_usdc: float,
        reason: str,
    ) -> str:
        """Slash agent's stake as penalty."""
        stake = self._stakes.get(agent_id)
        if not stake:
            raise ValueError(f"No stake found for agent {agent_id}")
        if stake["status"] != "active":
            raise ValueError(f"Stake status is {stake['status']}, cannot slash")
        if amount_usdc > stake["staked_amount_usdc"]:
            raise ValueError(
                f"Slash amount ${amount_usdc} exceeds remaining stake "
                f"${stake['staked_amount_usdc']}"
            )

        tx_hash = self._generate_tx_hash(f"slash-{agent_id}-{time.time()}")

        stake["staked_amount_usdc"] -= amount_usdc
        stake["total_slashed_usdc"] += amount_usdc
        stake["slash_count"] += 1
        stake["slash_history"].append({
            "amount_usdc": amount_usdc,
            "reason": reason,
            "tx_hash": tx_hash,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        # If stake is fully depleted, mark as depleted
        if stake["staked_amount_usdc"] <= 0:
            stake["status"] = "depleted"

        return tx_hash

    async def unstake(self, agent_id: str) -> str:
        """Return remaining stake to agent."""
        stake = self._stakes.get(agent_id)
        if not stake:
            raise ValueError(f"No stake found for agent {agent_id}")
        if stake["status"] not in ("active",):
            raise ValueError(
                f"Cannot unstake: status is {stake['status']}. "
                "Must be 'active' to unstake."
            )

        tx_hash = self._generate_tx_hash(f"unstake-{agent_id}-{time.time()}")

        stake["status"] = "unstaked"
        stake["unstaked_at"] = datetime.now(timezone.utc).isoformat()
        stake["unstake_tx_hash"] = tx_hash

        return tx_hash

    async def get_stake_info(self, agent_id: str) -> dict:
        """Get current staking information."""
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
        """Get slash history for an agent."""
        stake = self._stakes.get(agent_id)
        if not stake:
            return []
        return stake.get("slash_history", [])

    @staticmethod
    def _generate_tx_hash(seed: str) -> str:
        return hashlib.sha256(seed.encode()).hexdigest()
