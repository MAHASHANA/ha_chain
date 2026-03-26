"""Agent matching service: finds the best agent for a transfer."""

import json
from typing import Optional, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.enums import AgentStatus
from app.models.models import Transfer, Agent


class AgentScore:
    """Weighted score for agent ranking."""

    WEIGHT_RATING = 0.35
    WEIGHT_SUCCESS = 0.25
    WEIGHT_SPEED = 0.20
    WEIGHT_STAKE = 0.10
    WEIGHT_PRICE = 0.10

    def __init__(self, agent: Agent, max_stake: float = 10000.0, max_speed: float = 120.0):
        self.agent = agent
        self.rating_score = (agent.rating / 5.0) * self.WEIGHT_RATING
        self.success_score = agent.success_rate * self.WEIGHT_SUCCESS

        # Speed: lower is better, normalize inversely
        speed_normalized = max(0.0, 1.0 - (agent.avg_delivery_minutes / max_speed))
        self.speed_score = speed_normalized * self.WEIGHT_SPEED

        # Stake: higher is better
        stake_normalized = min(1.0, agent.stake_amount_usdc / max_stake) if max_stake > 0 else 0
        self.stake_score = stake_normalized * self.WEIGHT_STAKE

        # Price (commission): lower is better (inverted)
        self.price_score = max(0.0, 1.0 - agent.commission_rate * 10) * self.WEIGHT_PRICE

        self.total_score = (
            self.rating_score
            + self.success_score
            + self.speed_score
            + self.stake_score
            + self.price_score
        )


class MatchingService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def find_best_agent(self, transfer: Transfer) -> Optional[Agent]:
        """Find the best available agent for the given transfer."""
        candidates = await self._get_eligible_agents(transfer)
        if not candidates:
            return None

        scored = [AgentScore(agent) for agent in candidates]
        scored.sort(key=lambda s: s.total_score, reverse=True)
        return scored[0].agent

    async def get_ranked_agents(self, transfer: Transfer) -> List[AgentScore]:
        """Return all eligible agents with their scores, ranked best first."""
        candidates = await self._get_eligible_agents(transfer)
        scored = [AgentScore(agent) for agent in candidates]
        scored.sort(key=lambda s: s.total_score, reverse=True)
        return scored

    async def _get_eligible_agents(self, transfer: Transfer) -> List[Agent]:
        """Get all agents eligible for this transfer."""
        result = await self.db.execute(
            select(Agent).where(
                Agent.country == transfer.receiver_country,
                Agent.city == transfer.receiver_city,
                Agent.status == AgentStatus.ACTIVE.value,
                Agent.is_online == True,
            )
        )
        agents = list(result.scalars().all())

        eligible = []
        for agent in agents:
            # Check daily limit
            if agent.daily_volume_usdc + transfer.send_amount_usd > agent.daily_limit_usdc:
                continue

            # Check delivery method support
            try:
                delivery_methods = json.loads(agent.delivery_methods)
            except (json.JSONDecodeError, TypeError):
                delivery_methods = []
            if transfer.delivery_method not in delivery_methods:
                continue

            # Check mobile money provider support
            if transfer.mobile_money_provider:
                try:
                    providers = json.loads(agent.supported_providers)
                except (json.JSONDecodeError, TypeError):
                    providers = []
                if transfer.mobile_money_provider not in providers:
                    continue

            eligible.append(agent)

        return eligible
