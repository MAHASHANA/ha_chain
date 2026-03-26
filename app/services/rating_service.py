"""Rating and feedback service for transfers."""

from __future__ import annotations

import uuid
from typing import Sequence

from sqlalchemy import select, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent import Agent
from app.models.rating import Rating


class RatingService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_rating(
        self,
        *,
        transfer_id: uuid.UUID,
        rater_id: uuid.UUID,
        rated_agent_id: uuid.UUID | None = None,
        rated_user_id: uuid.UUID | None = None,
        score: int,
        category: str = "overall",
        comment: str | None = None,
    ) -> Rating:
        if not 1 <= score <= 5:
            raise ValueError("Score must be between 1 and 5")

        rating = Rating(
            transfer_id=transfer_id,
            rater_id=rater_id,
            rated_agent_id=rated_agent_id,
            rated_user_id=rated_user_id,
            score=score,
            category=category,
            comment=comment,
        )
        self.db.add(rating)
        await self.db.flush()

        # Update agent aggregate rating
        if rated_agent_id:
            await self._update_agent_rating(rated_agent_id)

        return rating

    async def get_agent_ratings(
        self, agent_id: uuid.UUID, *, limit: int = 50, offset: int = 0
    ) -> Sequence[Rating]:
        result = await self.db.execute(
            select(Rating)
            .where(Rating.rated_agent_id == agent_id)
            .order_by(Rating.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()

    async def _update_agent_rating(self, agent_id: uuid.UUID) -> None:
        """Recompute the agent's aggregate rating from all ratings."""
        agg_q = await self.db.execute(
            select(
                sa_func.avg(Rating.score),
                sa_func.count(Rating.id),
            ).where(Rating.rated_agent_id == agent_id)
        )
        row = agg_q.one()
        avg_score = float(row[0]) if row[0] else 0.0
        count = int(row[1])

        agent_q = await self.db.execute(select(Agent).where(Agent.id == agent_id))
        agent = agent_q.scalar_one_or_none()
        if agent:
            agent.rating_avg = round(avg_score, 2)
            agent.rating_count = count
            await self.db.flush()
