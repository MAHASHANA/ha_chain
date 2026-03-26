"""Integration tests for the full P2P matching flow.

These tests exercise the complete flow from order submission through
matching, LP fill, and local payment execution.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.database import Base
from app.models.matching import (
    MatchOrder,
    Match,
    LiquidityPosition,
    LiquidityFill,
    LocalPayment,
)
from app.services.matching_engine import MatchingEngine, PROTOCOL_FEE
from app.services.liquidity_service import LiquidityService, LP_SPREAD
from app.services.pool_manager import PoolManager
from app.services import fx_rates


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def mock_fx_rates(monkeypatch):
    """Mock FX rates to 1:1 for all currencies in tests."""
    async def _get_rate(src, tgt):
        return 1.0
    async def _get_usd_value(amount, currency):
        return amount
    async def _convert(amount, src, tgt):
        return amount
    monkeypatch.setattr(fx_rates, "get_rate", _get_rate)
    monkeypatch.setattr(fx_rates, "get_usd_value", _get_usd_value)
    monkeypatch.setattr(fx_rates, "convert", _convert)


@pytest_asyncio.fixture
async def engine():
    eng = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await eng.dispose()


@pytest_asyncio.fixture
async def session(engine) -> AsyncSession:
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as sess:
        yield sess
        await sess.rollback()


def _uid() -> str:
    return str(uuid.uuid4())


# ===========================================================================
# Integration tests
# ===========================================================================


class TestEndToEndDirectMatch:
    """Full flow from order submission to local payment for a direct match."""

    @pytest.mark.asyncio
    async def test_end_to_end_usd_inr_direct(self, session):
        """Complete USD->INR direct match flow.

        1. Ali (USA) submits USD->INR order
        2. Raj (India) submits INR->USD order
        3. Engine matches them
        4. Engine executes: creates two local payments
        5. Verify all records are consistent
        """
        engine = MatchingEngine(session)

        # Step 1: Ali submits
        ali_order = await engine.submit_order(
            user_id="ali-usa",
            source_currency="USD",
            target_currency="INR",
            amount=500.0,
            recipient_info={
                "account": "raj@upi",
                "name": "Raj Patel",
                "method": "upi",
            },
        )
        assert ali_order.status == "pending"

        # Step 2: Raj submits
        raj_order = await engine.submit_order(
            user_id="raj-india",
            source_currency="INR",
            target_currency="USD",
            amount=500.0,
            recipient_info={
                "account": "1234567890",
                "name": "Ali Hassan",
                "method": "ach",
            },
        )
        assert raj_order.status == "pending"

        # Step 3: Run matching cycle
        stats = await engine.run_matching_cycle()

        # Step 4: Verify match was created
        match_result = await session.execute(
            select(Match).where(Match.status == "settled")
        )
        matches = match_result.scalars().all()
        assert len(matches) >= 1

        settled_match = matches[0]
        assert settled_match.amount == 500.0
        assert settled_match.protocol_fee == 500.0 * PROTOCOL_FEE

        # Step 5: Verify local payments were created
        payment_result = await session.execute(
            select(LocalPayment).where(LocalPayment.match_id == settled_match.id)
        )
        payments = payment_result.scalars().all()
        assert len(payments) == 2

        # One USD payment (Ali pays Raj's US recipient)
        usd_payments = [p for p in payments if p.currency == "USD"]
        assert len(usd_payments) == 1
        assert usd_payments[0].amount == 500.0
        assert usd_payments[0].status == "completed"

        # One INR payment (Raj pays Ali's India recipient)
        inr_payments = [p for p in payments if p.currency == "INR"]
        assert len(inr_payments) == 1
        assert inr_payments[0].amount == 500.0
        assert inr_payments[0].status == "completed"

        # Verify order statuses
        await session.refresh(ali_order)
        await session.refresh(raj_order)
        assert ali_order.status == "fully_matched"
        assert raj_order.status == "fully_matched"
        assert ali_order.amount_unmatched == 0.0
        assert raj_order.amount_unmatched == 0.0


class TestEndToEndPartialWithLiquidity:
    """Partial match + LP fill integration test."""

    @pytest.mark.asyncio
    async def test_end_to_end_partial_with_liquidity(self, session):
        """
        1. LP deposits INR liquidity
        2. Ali submits $500 USD->INR
        3. Raj submits $300 INR->USD
        4. Engine matches $300 peer-to-peer
        5. Engine fills remaining $200 from LP
        6. Verify all records
        """
        engine = MatchingEngine(session)
        liq_service = LiquidityService(session)

        # Step 1: LP deposits INR
        lp_position = await liq_service.add_liquidity(
            user_id="lp-provider",
            currency="INR",
            amount=10000.0,
        )
        assert lp_position.is_active is True

        # Step 2: Ali submits
        ali_order = await engine.submit_order(
            user_id="ali-usa",
            source_currency="USD",
            target_currency="INR",
            amount=500.0,
            recipient_info={"method": "upi", "account": "raj@upi"},
        )

        # Step 3: Raj submits (only $300)
        raj_order = await engine.submit_order(
            user_id="raj-india",
            source_currency="INR",
            target_currency="USD",
            amount=300.0,
            recipient_info={"method": "ach", "account": "9876543210"},
        )

        # Step 4+5: Run matching cycle
        stats = await engine.run_matching_cycle()

        # Verify peer match happened
        assert stats["direct_matches"] + stats["partial_matches"] >= 1

        # Verify LP fill happened
        assert stats["lp_fills"] >= 1

        # Verify Ali's order is fully resolved
        await session.refresh(ali_order)
        assert ali_order.amount_unmatched == 0.0
        assert ali_order.status in ("fully_matched", "filled")

        # Verify LP position was drawn down
        await session.refresh(lp_position)
        assert lp_position.amount < 10000.0

        # Verify LP earned fees
        assert lp_position.earned_fees > 0
        expected_lp_fee = 200.0 * LP_SPREAD  # $200 filled from LP
        assert abs(lp_position.earned_fees - expected_lp_fee) < 0.01

        # Verify local payments created
        payment_result = await session.execute(select(LocalPayment))
        payments = list(payment_result.scalars().all())
        assert len(payments) >= 2  # At least 2 from the peer match


class TestMultiCorridorSimultaneous:
    """Multiple corridors matching simultaneously."""

    @pytest.mark.asyncio
    async def test_multi_corridor_simultaneous(self, session):
        """USD->INR and EUR->GBP matching at the same time.

        Both corridors should be matched independently without
        interfering with each other.
        """
        engine = MatchingEngine(session)

        # Corridor 1: USD <-> INR
        await engine.submit_order(
            user_id="user-us-1",
            source_currency="USD",
            target_currency="INR",
            amount=1000.0,
            recipient_info={"method": "upi"},
        )
        await engine.submit_order(
            user_id="user-in-1",
            source_currency="INR",
            target_currency="USD",
            amount=1000.0,
            recipient_info={"method": "ach"},
        )

        # Corridor 2: EUR <-> GBP
        await engine.submit_order(
            user_id="user-de-1",
            source_currency="EUR",
            target_currency="GBP",
            amount=800.0,
            recipient_info={"method": "sepa"},
        )
        await engine.submit_order(
            user_id="user-uk-1",
            source_currency="GBP",
            target_currency="EUR",
            amount=800.0,
            recipient_info={"method": "sepa"},
        )

        # Run matching
        stats = await engine.run_matching_cycle()

        total_matches = stats["direct_matches"] + stats["partial_matches"]
        assert total_matches >= 2  # At least one match per corridor

        # Verify all orders resolved
        result = await session.execute(
            select(MatchOrder).where(
                MatchOrder.status.in_(["pending", "partially_matched"])
            )
        )
        remaining = result.scalars().all()
        assert len(remaining) == 0, f"Unresolved orders: {[o.id for o in remaining]}"

        # Verify matches are corridor-specific (no cross-corridor matching)
        match_result = await session.execute(select(Match))
        matches = match_result.scalars().all()

        for m in matches:
            o1_result = await session.execute(
                select(MatchOrder).where(MatchOrder.id == m.order_id_1)
            )
            o2_result = await session.execute(
                select(MatchOrder).where(MatchOrder.id == m.order_id_2)
            )
            o1 = o1_result.scalar_one()
            o2 = o2_result.scalar_one()

            # order1's target = order2's source (they are counterparties)
            assert o1.target_currency == o2.source_currency
            assert o1.source_currency == o2.target_currency

        # Verify local payments
        payment_result = await session.execute(select(LocalPayment))
        payments = payment_result.scalars().all()
        assert len(payments) >= 4  # 2 per corridor


class TestTriangularIntegration:
    """Integration test for triangular matching."""

    @pytest.mark.asyncio
    async def test_triangular_full_flow(self, session):
        """Three-way cycle: USD->INR->EUR->USD.

        1. Submit three orders forming a cycle
        2. Direct matching finds nothing
        3. Triangular matching finds the cycle
        4. Execute and verify payments
        """
        engine = MatchingEngine(session)

        order_a = await engine.submit_order(
            user_id="user-a",
            source_currency="USD",
            target_currency="INR",
            amount=300.0,
            recipient_info={"method": "upi"},
        )
        order_b = await engine.submit_order(
            user_id="user-b",
            source_currency="INR",
            target_currency="EUR",
            amount=300.0,
            recipient_info={"method": "sepa"},
        )
        order_c = await engine.submit_order(
            user_id="user-c",
            source_currency="EUR",
            target_currency="USD",
            amount=300.0,
            recipient_info={"method": "ach"},
        )

        # Run cycle
        stats = await engine.run_matching_cycle()

        assert stats["triangular_matches"] >= 1

        # Verify all orders resolved
        for order in [order_a, order_b, order_c]:
            await session.refresh(order)
            assert order.status == "fully_matched"
            assert order.amount_unmatched == 0.0

        # Verify triangular match record
        match_result = await session.execute(
            select(Match).where(Match.match_type == "triangular")
        )
        tri_matches = match_result.scalars().all()
        assert len(tri_matches) >= 1
        assert tri_matches[0].order_id_3 is not None

        # Verify 3 local payments (one per leg)
        payment_result = await session.execute(select(LocalPayment))
        payments = payment_result.scalars().all()
        assert len(payments) >= 3
