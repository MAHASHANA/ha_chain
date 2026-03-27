"""P2P currency matching engine.

The core algorithm that matches users with opposite currency needs:
- Direct match: A wants USD->INR, B wants INR->USD
- Partial match: Split across multiple counterparties
- Triangular match: A->B->C->A circular (graph cycle detection)
- LP fill: Remaining unmatched amount filled from liquidity pool

The matching cycle runs periodically (every few seconds) and processes
all pending orders in the pool.
"""

from __future__ import annotations

import uuid
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.matching import (
    MatchOrder,
    Match,
    LocalPayment,
    LiquidityPosition,
    LiquidityFill,
)
from app.services.local_settlement import execute_local_payment
from app.services.liquidity_service import LiquidityService, LP_SPREAD
from app.services import fx_rates


# Protocol fee on every matched amount: 0.05%
PROTOCOL_FEE = 0.0005


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _uuid() -> str:
    return str(uuid.uuid4())


class MatchingEngine:
    """Core P2P matching engine."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.liquidity_service = LiquidityService(db)

    # ------------------------------------------------------------------
    # Order submission
    # ------------------------------------------------------------------

    async def submit_order(
        self,
        user_id: str,
        source_currency: str,
        target_currency: str,
        amount: float,
        recipient_info: Optional[dict] = None,
        max_wait_hours: float = 4.0,
    ) -> MatchOrder:
        """Submit a new matching order to the pool.

        Args:
            user_id: The user placing the order.
            source_currency: Currency the user wants to send (e.g. USD).
            target_currency: Currency the recipient needs (e.g. INR).
            amount: Amount in source currency.
            recipient_info: JSON-serializable dict with recipient details.
            max_wait_hours: Maximum hours to wait for a match.

        Returns:
            The created MatchOrder.
        """
        if amount <= 0:
            raise ValueError("Amount must be positive")

        now = _utcnow()
        order = MatchOrder(
            id=_uuid(),
            user_id=user_id,
            source_currency=source_currency.upper(),
            target_currency=target_currency.upper(),
            amount=amount,
            amount_matched=0.0,
            amount_unmatched=amount,
            recipient_info=recipient_info or {},
            status="pending",
            max_wait_until=now + timedelta(hours=max_wait_hours),
            created_at=now,
            updated_at=now,
        )
        self.db.add(order)
        await self.db.flush()
        return order

    # ------------------------------------------------------------------
    # Direct matching: A wants X->Y, B wants Y->X
    # ------------------------------------------------------------------

    async def find_direct_match(self, order: MatchOrder) -> Optional[Match]:
        """Find a direct counterparty for the given order.

        A direct match is where order A wants USD->INR and order B wants
        INR->USD. The matched amount is the minimum of both unmatched
        amounts.
        """
        if order.amount_unmatched <= 0:
            return None

        # Find counterparty: opposite currency pair, pending
        result = await self.db.execute(
            select(MatchOrder)
            .where(
                MatchOrder.source_currency == order.target_currency,
                MatchOrder.target_currency == order.source_currency,
                MatchOrder.status.in_(["pending", "partially_matched"]),
                MatchOrder.amount_unmatched > 0,
                MatchOrder.id != order.id,
                MatchOrder.user_id != order.user_id,
            )
            .order_by(MatchOrder.created_at.asc())  # FIFO
            .limit(1)
        )
        counterparty = result.scalar_one_or_none()

        if not counterparty:
            return None

        # Convert both amounts to USD for fair comparison
        order_usd = await fx_rates.get_usd_value(order.amount_unmatched, order.source_currency)
        counter_usd = await fx_rates.get_usd_value(counterparty.amount_unmatched, counterparty.source_currency)

        # Matched value in USD
        matched_usd = min(order_usd, counter_usd)
        if matched_usd <= 0:
            return None

        # Convert matched USD back to each order's source currency
        rate_to_order = await fx_rates.get_rate("USD", order.source_currency)
        rate_to_counter = await fx_rates.get_rate("USD", counterparty.source_currency)
        order_matched_in_source = round(matched_usd * rate_to_order, 2)
        counter_matched_in_source = round(matched_usd * rate_to_counter, 2)

        # Get the FX rate between the two currencies
        fx_rate = await fx_rates.get_rate(order.source_currency, counterparty.source_currency)

        fee = matched_usd * PROTOCOL_FEE

        match_type = "direct" if (
            abs(order_usd - counter_usd) < 0.01
        ) else "partial"

        match = Match(
            id=_uuid(),
            order_id_1=order.id,
            order_id_2=counterparty.id,
            order_id_3=None,
            match_type=match_type,
            amount=round(matched_usd, 2),
            exchange_rate=fx_rate,
            protocol_fee=round(fee, 2),
            status="pending_execution",
        )
        self.db.add(match)

        # Update order amounts in their own currencies
        order.amount_matched += order_matched_in_source
        order.amount_unmatched -= order_matched_in_source
        counterparty.amount_matched += counter_matched_in_source
        counterparty.amount_unmatched -= counter_matched_in_source

        now = _utcnow()

        if order.amount_unmatched <= 0:
            order.amount_unmatched = 0.0
            order.status = "fully_matched"
            order.matched_at = now
        else:
            order.status = "partially_matched"

        if counterparty.amount_unmatched <= 0:
            counterparty.amount_unmatched = 0.0
            counterparty.status = "fully_matched"
            counterparty.matched_at = now
        else:
            counterparty.status = "partially_matched"

        order.updated_at = now
        counterparty.updated_at = now

        await self.db.flush()
        return match

    # ------------------------------------------------------------------
    # Partial matching: split across multiple counterparties
    # ------------------------------------------------------------------

    async def find_partial_matches(self, order: MatchOrder) -> List[Match]:
        """Find multiple counterparties to fill the order.

        Iterates through available counterparties in FIFO order and
        creates partial matches until the order is fully matched or no
        more counterparties exist.
        """
        matches = []

        while order.amount_unmatched > 0:
            match = await self.find_direct_match(order)
            if match is None:
                break
            matches.append(match)

        return matches

    # ------------------------------------------------------------------
    # Triangular matching: A->B->C->A cycle detection
    # ------------------------------------------------------------------

    async def find_triangular_match(self, order: MatchOrder) -> Optional[Match]:
        """Find a triangular match using cycle detection.

        Example: A wants USD->INR, B wants INR->EUR, C wants EUR->USD.
        This forms a cycle: USD->INR->EUR->USD.

        We build a directed graph of pending orders' currency flows and
        look for 3-node cycles that include the given order's pair.
        """
        if order.amount_unmatched <= 0:
            return None

        src = order.source_currency
        tgt = order.target_currency

        # Build adjacency from all pending orders (grouped by currency pair)
        result = await self.db.execute(
            select(MatchOrder)
            .where(
                MatchOrder.status.in_(["pending", "partially_matched"]),
                MatchOrder.amount_unmatched > 0,
                MatchOrder.id != order.id,
            )
        )
        all_orders = list(result.scalars().all())

        # Build graph: currency -> {target_currency: [orders]}
        graph = defaultdict(lambda: defaultdict(list))
        for o in all_orders:
            graph[o.source_currency][o.target_currency].append(o)

        # Look for path: tgt -> mid -> src (to complete: src -> tgt -> mid -> src)
        # That means: order B: tgt -> mid, order C: mid -> src
        for mid_currency in graph[tgt]:
            if mid_currency == src or mid_currency == tgt:
                continue
            # Check if there's an order mid -> src
            if src in graph[mid_currency]:
                b_orders = graph[tgt][mid_currency]
                c_orders = graph[mid_currency][src]

                if b_orders and c_orders:
                    b_order = b_orders[0]  # Pick first available
                    c_order = c_orders[0]

                    # The matched amount is the min across all three
                    matched_amount = min(
                        order.amount_unmatched,
                        b_order.amount_unmatched,
                        c_order.amount_unmatched,
                    )

                    if matched_amount <= 0:
                        continue

                    fee = matched_amount * PROTOCOL_FEE

                    match = Match(
                        id=_uuid(),
                        order_id_1=order.id,
                        order_id_2=b_order.id,
                        order_id_3=c_order.id,
                        match_type="triangular",
                        amount=matched_amount,
                        exchange_rate=1.0,
                        protocol_fee=fee,
                        status="pending_execution",
                    )
                    self.db.add(match)

                    now = _utcnow()

                    # Update all three orders
                    for o in [order, b_order, c_order]:
                        o.amount_matched += matched_amount
                        o.amount_unmatched -= matched_amount
                        o.updated_at = now
                        if o.amount_unmatched <= 0:
                            o.amount_unmatched = 0.0
                            o.status = "fully_matched"
                            o.matched_at = now
                        else:
                            o.status = "partially_matched"

                    await self.db.flush()
                    return match

        return None

    # ------------------------------------------------------------------
    # LP fill: fill remaining from liquidity pool
    # ------------------------------------------------------------------

    async def fill_from_liquidity(
        self,
        order: MatchOrder,
        remaining: Optional[float] = None,
    ) -> Optional[LiquidityFill]:
        """Fill unmatched order portion from LP liquidity.

        Args:
            order: The order with remaining unmatched amount.
            remaining: Override the amount to fill. Defaults to order.amount_unmatched.

        Returns:
            LiquidityFill record if successful.
        """
        fill_amount = remaining if remaining is not None else order.amount_unmatched
        if fill_amount <= 0:
            return None

        # Find LP position in the target currency
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
            return None

        spread = fill_amount * LP_SPREAD

        fill = LiquidityFill(
            id=_uuid(),
            order_id=order.id,
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
        now = _utcnow()
        order.updated_at = now
        if order.amount_unmatched <= 0:
            order.amount_unmatched = 0.0
            order.status = "filled"
            order.matched_at = now
        else:
            order.status = "partially_matched"

        await self.db.flush()
        return fill

    # ------------------------------------------------------------------
    # Match execution: trigger local settlements
    # ------------------------------------------------------------------

    async def execute_match(self, match: Match) -> List[LocalPayment]:
        """Execute a match by triggering local payments.

        For a direct/partial match between order1 (USD->INR) and order2 (INR->USD):
        - Payment 1: order1's user pays USD locally to order2's recipient
        - Payment 2: order2's user pays INR locally to order1's recipient

        For triangular matches, three local payments are created.
        """
        payments = []

        # Load the involved orders
        order1_result = await self.db.execute(
            select(MatchOrder).where(MatchOrder.id == match.order_id_1)
        )
        order1 = order1_result.scalar_one_or_none()

        order2_result = await self.db.execute(
            select(MatchOrder).where(MatchOrder.id == match.order_id_2)
        )
        order2 = order2_result.scalar_one_or_none()

        if not order1 or not order2:
            return payments

        # match.amount is in USD. Convert to each order's source currency.
        amount_in_order1_currency = await fx_rates.convert(match.amount, "USD", order1.source_currency)
        amount_in_order2_currency = await fx_rates.convert(match.amount, "USD", order2.source_currency)

        # Payment 1: order1's source currency to order2's recipient
        recipient_info_1 = order2.recipient_info or {}
        method_1 = recipient_info_1.get("method", None)
        result1 = await execute_local_payment(
            currency=order1.source_currency,
            amount=amount_in_order1_currency,
            recipient=recipient_info_1,
            method=method_1,
        )
        payment1 = LocalPayment(
            id=_uuid(),
            match_id=match.id,
            order_id=order1.id,
            currency=order1.source_currency,
            amount=amount_in_order1_currency,
            recipient_info=recipient_info_1,
            payment_method=result1.payment_method,
            payment_rail=result1.payment_method,
            tx_reference=result1.tx_id,
            status=result1.status,
            executed_at=result1.timestamp,
        )
        self.db.add(payment1)
        payments.append(payment1)

        # Payment 2: order2's source currency to order1's recipient
        recipient_info_2 = order1.recipient_info or {}
        method_2 = recipient_info_2.get("method", None)
        result2 = await execute_local_payment(
            currency=order2.source_currency,
            amount=amount_in_order2_currency,
            recipient=recipient_info_2,
            method=method_2,
        )
        payment2 = LocalPayment(
            id=_uuid(),
            match_id=match.id,
            order_id=order2.id,
            currency=order2.source_currency,
            amount=amount_in_order2_currency,
            recipient_info=recipient_info_2,
            payment_method=result2.payment_method,
            payment_rail=result2.payment_method,
            tx_reference=result2.tx_id,
            status=result2.status,
            executed_at=result2.timestamp,
        )
        self.db.add(payment2)
        payments.append(payment2)

        # Triangular: third leg
        if match.order_id_3:
            order3_result = await self.db.execute(
                select(MatchOrder).where(MatchOrder.id == match.order_id_3)
            )
            order3 = order3_result.scalar_one_or_none()
            if order3:
                recipient_info_3 = order3.recipient_info or {}
                method_3 = recipient_info_3.get("method", None)
                result3 = await execute_local_payment(
                    currency=order3.source_currency,
                    amount=match.amount,
                    recipient=recipient_info_3,
                    method=method_3,
                )
                payment3 = LocalPayment(
                    id=_uuid(),
                    match_id=match.id,
                    order_id=order3.id,
                    currency=order3.source_currency,
                    amount=match.amount,
                    recipient_info=recipient_info_3,
                    payment_method=result3.payment_method,
                    payment_rail=result3.payment_method,
                    tx_reference=result3.tx_id,
                    status=result3.status,
                    executed_at=result3.timestamp,
                )
                self.db.add(payment3)
                payments.append(payment3)

        # Update match status
        match.status = "settled"
        match.executed_at = _utcnow()

        # Record match on Stellar testnet (non-blocking — don't fail if Stellar is down)
        try:
            from app.services import stellar_service
            stellar_tx = await stellar_service.record_match_on_chain(
                match_id=match.id,
                order1_source_currency=order1.source_currency if order1 else "???",
                order1_target_currency=order1.target_currency if order1 else "???",
                amount_usd=match.amount,
                match_type=match.match_type,
                fee=match.protocol_fee,
            )
            if stellar_tx and stellar_tx.success:
                match.stellar_tx_hash = stellar_tx.tx_hash
        except Exception:
            pass  # Stellar recording is best-effort

        await self.db.flush()
        return payments

    # ------------------------------------------------------------------
    # Expiry: cancel orders past their max_wait_until
    # ------------------------------------------------------------------

    async def expire_orders(self) -> List[MatchOrder]:
        """Cancel all orders that have exceeded their max wait time."""
        now = _utcnow()
        result = await self.db.execute(
            select(MatchOrder).where(
                MatchOrder.status.in_(["pending", "partially_matched"]),
                MatchOrder.max_wait_until <= now,
            )
        )
        expired = list(result.scalars().all())

        for order in expired:
            order.status = "expired"
            order.cancelled_at = now
            order.updated_at = now

        if expired:
            await self.db.flush()

        return expired

    # ------------------------------------------------------------------
    # Main matching cycle
    # ------------------------------------------------------------------

    async def run_matching_cycle(self) -> dict:
        """Run one full matching cycle.

        1. Expire old orders
        2. For each pending order, try direct -> partial -> triangular
        3. Fill remaining from LP
        4. Execute settled matches

        Returns summary statistics.
        """
        stats = {
            "expired": 0,
            "direct_matches": 0,
            "partial_matches": 0,
            "triangular_matches": 0,
            "lp_fills": 0,
            "payments_executed": 0,
        }

        # Step 1: expire old orders
        expired = await self.expire_orders()
        stats["expired"] = len(expired)

        # Step 2: get all pending orders (FIFO)
        result = await self.db.execute(
            select(MatchOrder)
            .where(MatchOrder.status.in_(["pending", "partially_matched"]))
            .order_by(MatchOrder.created_at.asc())
        )
        pending_orders = list(result.scalars().all())

        for order in pending_orders:
            if order.amount_unmatched <= 0:
                continue

            # Try direct/partial matches
            matches = await self.find_partial_matches(order)
            for m in matches:
                if m.match_type == "direct":
                    stats["direct_matches"] += 1
                else:
                    stats["partial_matches"] += 1

            # Try triangular if still unmatched
            if order.amount_unmatched > 0:
                tri_match = await self.find_triangular_match(order)
                if tri_match:
                    stats["triangular_matches"] += 1

            # Fill remaining from LP
            if order.amount_unmatched > 0:
                fill = await self.fill_from_liquidity(order)
                if fill:
                    stats["lp_fills"] += 1

        # Step 3: execute all pending matches
        match_result = await self.db.execute(
            select(Match).where(Match.status == "pending_execution")
        )
        pending_matches = list(match_result.scalars().all())

        for match in pending_matches:
            payments = await self.execute_match(match)
            stats["payments_executed"] += len(payments)

        await self.db.flush()
        return stats
