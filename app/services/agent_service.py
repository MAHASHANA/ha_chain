"""Agent registration, staking, dashboard, and status management."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Sequence

from sqlalchemy import select, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants import AgentLicenseStatus, StakeStatus
from app.exceptions import (
    AgentNotFoundError,
    AgentSuspendedError,
    InsufficientFundsError,
    InsufficientStakeError,
)
from app.models.agent import Agent, AgentStake
from app.models.transfer import Transfer
from app.models.user import User


class AgentService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    async def register_agent(
        self,
        user_id: uuid.UUID,
        *,
        business_name: str,
        country: str,
        city: str,
        address: str | None = None,
        license_number: str | None = None,
        supported_delivery_methods: list[str] | None = None,
        supported_currencies: list[str] | None = None,
        commission_rate: float = 0.005,
    ) -> Agent:
        """Register a user as an agent. The user's role is unchanged at this step
        (promoted when license becomes active)."""
        agent = Agent(
            user_id=user_id,
            business_name=business_name,
            country=country,
            city=city,
            address=address,
            license_number=license_number,
            license_status=AgentLicenseStatus.PENDING.value,
            supported_delivery_methods=supported_delivery_methods or ["cash_pickup", "mobile_money"],
            supported_currencies=supported_currencies or ["USDC"],
            commission_rate=commission_rate,
        )
        self.db.add(agent)
        await self.db.flush()
        return agent

    # ------------------------------------------------------------------
    # Lookup
    # ------------------------------------------------------------------

    async def get_by_id(self, agent_id: uuid.UUID) -> Agent:
        result = await self.db.execute(select(Agent).where(Agent.id == agent_id))
        agent = result.scalar_one_or_none()
        if not agent:
            raise AgentNotFoundError(str(agent_id))
        return agent

    async def get_by_user_id(self, user_id: uuid.UUID) -> Agent:
        result = await self.db.execute(select(Agent).where(Agent.user_id == user_id))
        agent = result.scalar_one_or_none()
        if not agent:
            raise AgentNotFoundError(f"user_id={user_id}")
        return agent

    # ------------------------------------------------------------------
    # Staking
    # ------------------------------------------------------------------

    async def stake(
        self,
        agent_id: uuid.UUID,
        amount: float,
        tx_hash: str | None = None,
    ) -> AgentStake:
        """Record a new stake deposit and update the agent's aggregate staked amount."""
        agent = await self.get_by_id(agent_id)
        stake_record = AgentStake(
            agent_id=agent_id,
            amount=amount,
            currency="USDC",
            tx_hash=tx_hash,
            status=StakeStatus.LOCKED.value,
        )
        self.db.add(stake_record)
        agent.staked_amount = float(agent.staked_amount) + amount

        # Auto-activate license when minimum stake is met (500 USDC)
        if float(agent.staked_amount) >= 500 and agent.license_status == AgentLicenseStatus.PENDING.value:
            agent.license_status = AgentLicenseStatus.ACTIVE.value

        await self.db.flush()
        return stake_record

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------

    async def set_online(self, agent_id: uuid.UUID, online: bool) -> Agent:
        agent = await self.get_by_id(agent_id)
        if agent.license_status != AgentLicenseStatus.ACTIVE.value:
            raise AgentSuspendedError(str(agent_id))
        agent.is_online = online
        await self.db.flush()
        return agent

    # ------------------------------------------------------------------
    # Dashboard stats
    # ------------------------------------------------------------------

    async def get_dashboard(self, agent_id: uuid.UUID) -> dict:
        agent = await self.get_by_id(agent_id)

        # Active transfers (agent_matched or in_delivery)
        active_q = await self.db.execute(
            select(sa_func.count(Transfer.id)).where(
                Transfer.agent_id == agent_id,
                Transfer.status.in_(["agent_matched", "in_delivery"]),
            )
        )
        active_count = active_q.scalar() or 0

        # Today's volume
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        vol_q = await self.db.execute(
            select(sa_func.coalesce(sa_func.sum(Transfer.send_amount), 0)).where(
                Transfer.agent_id == agent_id,
                Transfer.status == "completed",
                Transfer.completed_at >= today_start,
            )
        )
        today_volume = float(vol_q.scalar() or 0)

        return {
            "agent_id": str(agent.id),
            "business_name": agent.business_name,
            "license_status": agent.license_status,
            "is_online": agent.is_online,
            "staked_amount": float(agent.staked_amount),
            "total_transactions": agent.total_transactions,
            "total_volume": float(agent.total_volume),
            "rating_avg": float(agent.rating_avg),
            "rating_count": agent.rating_count,
            "success_rate": float(agent.success_rate),
            "avg_delivery_minutes": agent.avg_delivery_minutes,
            "active_transfers": active_count,
            "today_volume": today_volume,
            "daily_limit": float(agent.daily_limit),
            "remaining_capacity": float(agent.daily_limit) - today_volume,
        }

    # ------------------------------------------------------------------
    # Stats update (called after transfer completion)
    # ------------------------------------------------------------------

    async def update_stats_after_delivery(
        self, agent_id: uuid.UUID, delivery_minutes: int, amount: float
    ) -> None:
        agent = await self.get_by_id(agent_id)
        old_count = agent.total_transactions
        agent.total_transactions = old_count + 1
        agent.total_volume = float(agent.total_volume) + amount

        # Running average of delivery time
        if old_count > 0:
            agent.avg_delivery_minutes = int(
                (agent.avg_delivery_minutes * old_count + delivery_minutes) / (old_count + 1)
            )
        else:
            agent.avg_delivery_minutes = delivery_minutes

        await self.db.flush()

    async def list_pending_transfers(self, agent_id: uuid.UUID) -> Sequence[Transfer]:
        """Transfers assigned to this agent that await delivery."""
        result = await self.db.execute(
            select(Transfer).where(
                Transfer.agent_id == agent_id,
                Transfer.status.in_(["agent_matched", "in_delivery"]),
            ).order_by(Transfer.created_at.desc())
        )
        return result.scalars().all()
