"""Liquidity service: LP deposits, withdrawals, fills, and earnings.

Liquidity providers deposit single-currency capital that the matching engine
can draw on to fill unmatched order portions.  LPs earn a 0.2% spread on
every fill.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional, List

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.matching import LiquidityPosition, LiquidityFill, MatchOrder


# Spread earned by LPs on every fill (0.2%)
LP_SPREAD = 0.002


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------

@dataclass
class WithdrawalResult:
    position_id: str
    amount_withdrawn: float
    remaining: float
    success: bool
    error: Optional[str] = None


@dataclass
class FillResult:
    fill_id: str
    order_id: str
    amount_filled: float
    spread_earned: float
    success: bool
    error: Optional[str] = None


@dataclass
class EarningsReport:
    user_id: str
    total_deposited: float
    total_earned: float
    total_fills: int
    positions: list


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------

class LiquidityService:
    """Manages liquidity provider operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def add_liquidity(
        self,
        user_id: str,
        currency: str,
        amount: float,
    ) -> LiquidityPosition:
        """Deposit liquidity into a currency pool.

        Creates a new LiquidityPosition or could add to existing -- for
        simplicity each deposit is a separate position.
        """
        if amount <= 0:
            raise ValueError("Amount must be positive")

        position = LiquidityPosition(
            id=str(uuid.uuid4()),
            user_id=user_id,
            currency=currency.upper(),
            amount=amount,
            earned_fees=0.0,
            is_active=True,
        )
        self.db.add(position)
        await self.db.flush()
        return position

    async def remove_liquidity(
        self,
        position_id: str,
        amount: Optional[float] = None,
    ) -> WithdrawalResult:
        """Withdraw liquidity from a position.

        If amount is None, withdraw the full remaining amount.
        """
        result = await self.db.execute(
            select(LiquidityPosition).where(LiquidityPosition.id == position_id)
        )
        position = result.scalar_one_or_none()

        if not position:
            return WithdrawalResult(
                position_id=position_id,
                amount_withdrawn=0,
                remaining=0,
                success=False,
                error="Position not found",
            )

        if not position.is_active:
            return WithdrawalResult(
                position_id=position_id,
                amount_withdrawn=0,
                remaining=0,
                success=False,
                error="Position is already closed",
            )

        withdraw_amount = amount if amount is not None else position.amount

        if withdraw_amount > position.amount:
            return WithdrawalResult(
                position_id=position_id,
                amount_withdrawn=0,
                remaining=position.amount,
                success=False,
                error="Insufficient balance in position",
            )

        position.amount -= withdraw_amount
        if position.amount <= 0:
            position.is_active = False
            position.amount = 0.0

        await self.db.flush()

        return WithdrawalResult(
            position_id=position_id,
            amount_withdrawn=withdraw_amount,
            remaining=position.amount,
            success=True,
        )

    async def fill_order(
        self,
        order_id: str,
        amount: float,
    ) -> FillResult:
        """Fill an order (or portion) from available LP liquidity.

        Finds the best available LP position for the order's target
        currency and creates a LiquidityFill record.
        """
        # Look up the order
        result = await self.db.execute(
            select(MatchOrder).where(MatchOrder.id == order_id)
        )
        order = result.scalar_one_or_none()
        if not order:
            return FillResult(
                fill_id="",
                order_id=order_id,
                amount_filled=0,
                spread_earned=0,
                success=False,
                error="Order not found",
            )

        fill_amount = min(amount, order.amount_unmatched)
        if fill_amount <= 0:
            return FillResult(
                fill_id="",
                order_id=order_id,
                amount_filled=0,
                spread_earned=0,
                success=False,
                error="Nothing to fill",
            )

        # Find LP position with enough liquidity in the target currency
        lp_result = await self.db.execute(
            select(LiquidityPosition)
            .where(
                LiquidityPosition.currency == order.target_currency,
                LiquidityPosition.is_active == True,
                LiquidityPosition.amount >= fill_amount,
            )
            .order_by(LiquidityPosition.amount.desc())
            .limit(1)
        )
        position = lp_result.scalar_one_or_none()

        if not position:
            return FillResult(
                fill_id="",
                order_id=order_id,
                amount_filled=0,
                spread_earned=0,
                success=False,
                error="No LP liquidity available",
            )

        spread = fill_amount * LP_SPREAD

        # Create fill record
        fill = LiquidityFill(
            id=str(uuid.uuid4()),
            order_id=order_id,
            lp_position_id=position.id,
            amount=fill_amount,
            spread_earned=spread,
            status="settled",
        )
        self.db.add(fill)

        # Update LP position
        position.amount -= fill_amount
        position.earned_fees += spread
        if position.amount <= 0:
            position.is_active = False
            position.amount = 0.0

        # Update order
        order.amount_matched += fill_amount
        order.amount_unmatched -= fill_amount
        if order.amount_unmatched <= 0:
            order.amount_unmatched = 0.0
            order.status = "filled"
        else:
            order.status = "partially_matched"

        await self.db.flush()

        return FillResult(
            fill_id=fill.id,
            order_id=order_id,
            amount_filled=fill_amount,
            spread_earned=spread,
            success=True,
        )

    async def get_lp_earnings(self, user_id: str) -> EarningsReport:
        """Get earnings report for a liquidity provider."""
        result = await self.db.execute(
            select(LiquidityPosition).where(LiquidityPosition.user_id == user_id)
        )
        positions = list(result.scalars().all())

        total_deposited = sum(p.amount for p in positions)
        total_earned = sum(p.earned_fees for p in positions)

        # Count fills
        position_ids = [p.id for p in positions]
        total_fills = 0
        if position_ids:
            fill_result = await self.db.execute(
                select(func.count(LiquidityFill.id)).where(
                    LiquidityFill.lp_position_id.in_(position_ids)
                )
            )
            total_fills = fill_result.scalar() or 0

        return EarningsReport(
            user_id=user_id,
            total_deposited=total_deposited,
            total_earned=total_earned,
            total_fills=total_fills,
            positions=[
                {
                    "id": p.id,
                    "currency": p.currency,
                    "amount": p.amount,
                    "earned_fees": p.earned_fees,
                    "is_active": p.is_active,
                }
                for p in positions
            ],
        )

    async def get_positions(self, user_id: str) -> List[LiquidityPosition]:
        """Get all LP positions for a user."""
        result = await self.db.execute(
            select(LiquidityPosition)
            .where(LiquidityPosition.user_id == user_id)
            .order_by(LiquidityPosition.created_at.desc())
        )
        return list(result.scalars().all())
