"""Pool manager: real-time pool status, match rate estimates, and live feed.

Provides aggregate analytics for the matching pools used by the dashboard
and the pre-submission estimate endpoint.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.matching import (
    MatchOrder,
    Match,
    LiquidityPosition,
    PoolSnapshot,
)


@dataclass
class PoolStatus:
    currency: str
    tvl: float  # total value locked (LP deposits)
    order_count: int  # pending orders
    match_rate_24h: float  # % of orders matched in last 24h
    avg_wait_time: float  # average seconds from submission to match


@dataclass
class MatchEstimate:
    match_pct: float  # estimated % that will be peer-matched
    estimated_fee: float  # estimated total fee
    estimated_time: float  # estimated seconds to match


@dataclass
class RecentMatch:
    match_id: str
    match_type: str
    source_currency: str
    target_currency: str
    amount: float
    executed_at: Optional[datetime]


class PoolManager:
    """Provides pool analytics and match estimates."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_pool_status(self, currency: str) -> PoolStatus:
        """Get current status of a single currency pool."""
        # TVL: sum of active LP positions
        tvl_result = await self.db.execute(
            select(func.coalesce(func.sum(LiquidityPosition.amount), 0.0)).where(
                LiquidityPosition.currency == currency,
                LiquidityPosition.is_active == True,
            )
        )
        tvl = float(tvl_result.scalar() or 0.0)

        # Pending orders (source or target = this currency)
        order_count_result = await self.db.execute(
            select(func.count(MatchOrder.id)).where(
                MatchOrder.status.in_(["pending", "partially_matched"]),
                (MatchOrder.source_currency == currency)
                | (MatchOrder.target_currency == currency),
            )
        )
        order_count = order_count_result.scalar() or 0

        # Match rate: of orders created in last 24h, how many are fully matched/filled
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(hours=24)

        total_recent_result = await self.db.execute(
            select(func.count(MatchOrder.id)).where(
                MatchOrder.created_at >= cutoff,
                (MatchOrder.source_currency == currency)
                | (MatchOrder.target_currency == currency),
            )
        )
        total_recent = total_recent_result.scalar() or 0

        matched_recent_result = await self.db.execute(
            select(func.count(MatchOrder.id)).where(
                MatchOrder.created_at >= cutoff,
                MatchOrder.status.in_(["fully_matched", "filled"]),
                (MatchOrder.source_currency == currency)
                | (MatchOrder.target_currency == currency),
            )
        )
        matched_recent = matched_recent_result.scalar() or 0

        match_rate = (matched_recent / total_recent * 100.0) if total_recent > 0 else 0.0

        # Average wait time for matched orders in last 24h
        avg_wait_result = await self.db.execute(
            select(
                func.avg(
                    func.julianday(MatchOrder.matched_at) - func.julianday(MatchOrder.created_at)
                )
            ).where(
                MatchOrder.matched_at.isnot(None),
                MatchOrder.created_at >= cutoff,
                (MatchOrder.source_currency == currency)
                | (MatchOrder.target_currency == currency),
            )
        )
        avg_wait_days = avg_wait_result.scalar()
        avg_wait_seconds = (avg_wait_days * 86400.0) if avg_wait_days else 0.0

        return PoolStatus(
            currency=currency,
            tvl=tvl,
            order_count=order_count,
            match_rate_24h=match_rate,
            avg_wait_time=avg_wait_seconds,
        )

    async def estimate_match_rate(
        self,
        source: str,
        target: str,
        amount: float,
    ) -> MatchEstimate:
        """Estimate how much of an order would be peer-matched.

        Uses current pending order volumes to estimate the probability
        of a peer match vs LP fill.
        """
        # Count counterparty orders (target->source, pending)
        counter_result = await self.db.execute(
            select(func.coalesce(func.sum(MatchOrder.amount_unmatched), 0.0)).where(
                MatchOrder.source_currency == target,
                MatchOrder.target_currency == source,
                MatchOrder.status.in_(["pending", "partially_matched"]),
            )
        )
        counter_volume = float(counter_result.scalar() or 0.0)

        # LP liquidity in target currency
        lp_result = await self.db.execute(
            select(func.coalesce(func.sum(LiquidityPosition.amount), 0.0)).where(
                LiquidityPosition.currency == target,
                LiquidityPosition.is_active == True,
            )
        )
        lp_volume = float(lp_result.scalar() or 0.0)

        # Estimate peer match percentage
        if counter_volume >= amount:
            match_pct = 100.0
        elif counter_volume > 0:
            match_pct = (counter_volume / amount) * 100.0
        else:
            match_pct = 0.0

        # Fee estimate: peer-matched portion = 0.05% protocol fee only
        # LP-filled portion = 0.05% protocol + 0.2% LP spread
        from app.services.matching_engine import PROTOCOL_FEE
        from app.services.liquidity_service import LP_SPREAD

        peer_amount = min(counter_volume, amount)
        lp_amount = min(amount - peer_amount, lp_volume)
        estimated_fee = (peer_amount * PROTOCOL_FEE) + (lp_amount * (PROTOCOL_FEE + LP_SPREAD))

        # Estimate time based on pool depth
        if counter_volume >= amount:
            estimated_time = 5.0  # seconds, instant match likely
        elif counter_volume + lp_volume >= amount:
            estimated_time = 30.0  # quick with LP fill
        else:
            estimated_time = 3600.0  # may take a while

        return MatchEstimate(
            match_pct=round(match_pct, 2),
            estimated_fee=round(estimated_fee, 4),
            estimated_time=estimated_time,
        )

    async def get_all_pools(self) -> List[PoolStatus]:
        """Get status of all currency pools that have activity."""
        # Get distinct currencies from LP positions and orders
        lp_currencies = await self.db.execute(
            select(LiquidityPosition.currency).distinct()
        )
        order_src = await self.db.execute(
            select(MatchOrder.source_currency).distinct()
        )
        order_tgt = await self.db.execute(
            select(MatchOrder.target_currency).distinct()
        )

        currencies = set()
        for row in lp_currencies.scalars().all():
            currencies.add(row)
        for row in order_src.scalars().all():
            currencies.add(row)
        for row in order_tgt.scalars().all():
            currencies.add(row)

        pools = []
        for currency in sorted(currencies):
            status = await self.get_pool_status(currency)
            pools.append(status)

        return pools

    async def get_live_matches(self, limit: int = 20) -> List[RecentMatch]:
        """Get recent matches for the live feed."""
        result = await self.db.execute(
            select(Match)
            .order_by(Match.created_at.desc())
            .limit(limit)
        )
        matches = result.scalars().all()

        recent = []
        for m in matches:
            # Look up the first order to get currency pair
            order_result = await self.db.execute(
                select(MatchOrder).where(MatchOrder.id == m.order_id_1)
            )
            order = order_result.scalar_one_or_none()

            recent.append(RecentMatch(
                match_id=m.id,
                match_type=m.match_type,
                source_currency=order.source_currency if order else "???",
                target_currency=order.target_currency if order else "???",
                amount=m.amount,
                executed_at=m.executed_at,
            ))

        return recent
