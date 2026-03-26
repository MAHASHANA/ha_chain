"""Unit tests for the P2P matching engine.

All tests use an in-memory async SQLite database that is created fresh
for each test function.
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
    PoolSnapshot,
)
from app.services.matching_engine import MatchingEngine, PROTOCOL_FEE
from app.services.liquidity_service import LiquidityService, LP_SPREAD
from app.services.pool_manager import PoolManager
from app.services.local_settlement import execute_local_payment
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
    """Create an async in-memory SQLite engine."""
    eng = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await eng.dispose()


@pytest_asyncio.fixture
async def session(engine) -> AsyncSession:
    """Fresh async session per test."""
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as sess:
        yield sess
        await sess.rollback()


@pytest_asyncio.fixture
async def matching_engine(session) -> MatchingEngine:
    return MatchingEngine(session)


@pytest_asyncio.fixture
async def liquidity_service(session) -> LiquidityService:
    return LiquidityService(session)


@pytest_asyncio.fixture
async def pool_manager(session) -> PoolManager:
    return PoolManager(session)


def _uid() -> str:
    return str(uuid.uuid4())


# ===========================================================================
# Tests
# ===========================================================================


class TestDirectMatch:
    """Tests for direct matching (A wants USD->INR, B wants INR->USD)."""

    @pytest.mark.asyncio
    async def test_direct_match_usd_inr(self, matching_engine: MatchingEngine, session):
        """Submit USD->INR and INR->USD orders; verify they match."""
        user_a = _uid()
        user_b = _uid()

        order_a = await matching_engine.submit_order(
            user_id=user_a,
            source_currency="USD",
            target_currency="INR",
            amount=500.0,
            recipient_info={"account": "raj@upi", "method": "upi"},
        )
        order_b = await matching_engine.submit_order(
            user_id=user_b,
            source_currency="INR",
            target_currency="USD",
            amount=500.0,
            recipient_info={"account": "1234567890", "method": "ach"},
        )

        match = await matching_engine.find_direct_match(order_a)

        assert match is not None
        assert match.order_id_1 == order_a.id
        assert match.order_id_2 == order_b.id
        assert match.amount == 500.0
        assert match.match_type in ("direct", "partial")

    @pytest.mark.asyncio
    async def test_direct_match_exact_amounts(self, matching_engine: MatchingEngine, session):
        """Both orders $500 -- verify zero remainder after match."""
        user_a = _uid()
        user_b = _uid()

        order_a = await matching_engine.submit_order(
            user_id=user_a,
            source_currency="USD",
            target_currency="INR",
            amount=500.0,
        )
        order_b = await matching_engine.submit_order(
            user_id=user_b,
            source_currency="INR",
            target_currency="USD",
            amount=500.0,
        )

        match = await matching_engine.find_direct_match(order_a)

        assert match is not None
        assert match.amount == 500.0
        assert order_a.amount_unmatched == 0.0
        assert order_b.amount_unmatched == 0.0
        assert order_a.status == "fully_matched"
        assert order_b.status == "fully_matched"
        assert match.match_type == "direct"


class TestPartialMatch:
    """Tests for partial matching."""

    @pytest.mark.asyncio
    async def test_partial_match(self, matching_engine: MatchingEngine, session):
        """$500 vs $300 -- verify $300 matched + $200 remaining."""
        user_a = _uid()
        user_b = _uid()

        order_a = await matching_engine.submit_order(
            user_id=user_a,
            source_currency="USD",
            target_currency="INR",
            amount=500.0,
        )
        order_b = await matching_engine.submit_order(
            user_id=user_b,
            source_currency="INR",
            target_currency="USD",
            amount=300.0,
        )

        match = await matching_engine.find_direct_match(order_a)

        assert match is not None
        assert match.amount == 300.0
        assert match.match_type == "partial"
        assert order_a.amount_matched == 300.0
        assert order_a.amount_unmatched == 200.0
        assert order_a.status == "partially_matched"
        assert order_b.amount_unmatched == 0.0
        assert order_b.status == "fully_matched"

    @pytest.mark.asyncio
    async def test_partial_match_multiple(self, matching_engine: MatchingEngine, session):
        """$1000 matched by 3 smaller orders ($400 + $350 + $250)."""
        user_a = _uid()

        order_a = await matching_engine.submit_order(
            user_id=user_a,
            source_currency="USD",
            target_currency="INR",
            amount=1000.0,
        )

        # Create 3 counterparty orders
        for amt in [400.0, 350.0, 250.0]:
            await matching_engine.submit_order(
                user_id=_uid(),
                source_currency="INR",
                target_currency="USD",
                amount=amt,
            )

        matches = await matching_engine.find_partial_matches(order_a)

        assert len(matches) == 3
        total_matched = sum(m.amount for m in matches)
        assert total_matched == 1000.0
        assert order_a.amount_unmatched == 0.0
        assert order_a.status == "fully_matched"


class TestTriangularMatch:
    """Tests for triangular matching (A->B->C->A cycle)."""

    @pytest.mark.asyncio
    async def test_triangular_match(self, matching_engine: MatchingEngine, session):
        """USD->INR + INR->EUR + EUR->USD should form a triangular match."""
        order_a = await matching_engine.submit_order(
            user_id=_uid(),
            source_currency="USD",
            target_currency="INR",
            amount=500.0,
        )
        await matching_engine.submit_order(
            user_id=_uid(),
            source_currency="INR",
            target_currency="EUR",
            amount=500.0,
        )
        await matching_engine.submit_order(
            user_id=_uid(),
            source_currency="EUR",
            target_currency="USD",
            amount=500.0,
        )

        match = await matching_engine.find_triangular_match(order_a)

        assert match is not None
        assert match.match_type == "triangular"
        assert match.order_id_3 is not None
        assert match.amount == 500.0


class TestNoMatch:
    """Tests for orders that have no counterparty."""

    @pytest.mark.asyncio
    async def test_no_match_waits(self, matching_engine: MatchingEngine, session):
        """Order with no counterparty stays pending."""
        order = await matching_engine.submit_order(
            user_id=_uid(),
            source_currency="USD",
            target_currency="INR",
            amount=500.0,
        )

        match = await matching_engine.find_direct_match(order)

        assert match is None
        assert order.status == "pending"
        assert order.amount_unmatched == 500.0


class TestOrderExpiry:
    """Tests for order expiration."""

    @pytest.mark.asyncio
    async def test_order_expiry(self, matching_engine: MatchingEngine, session):
        """Order past max_wait gets expired."""
        order = await matching_engine.submit_order(
            user_id=_uid(),
            source_currency="USD",
            target_currency="INR",
            amount=500.0,
            max_wait_hours=0.001,  # ~3.6 seconds
        )

        # Manually push the max_wait_until into the past
        order.max_wait_until = datetime.now(timezone.utc) - timedelta(minutes=1)
        await session.flush()

        expired = await matching_engine.expire_orders()

        assert len(expired) == 1
        assert expired[0].id == order.id
        assert order.status == "expired"
        assert order.cancelled_at is not None


class TestLiquidityFill:
    """Tests for LP fills."""

    @pytest.mark.asyncio
    async def test_liquidity_fill(self, matching_engine: MatchingEngine, session):
        """Unmatched portion filled by LP."""
        # Add liquidity
        lp = LiquidityPosition(
            id=_uid(),
            user_id=_uid(),
            currency="INR",
            amount=10000.0,
            earned_fees=0.0,
            is_active=True,
        )
        session.add(lp)
        await session.flush()

        order = await matching_engine.submit_order(
            user_id=_uid(),
            source_currency="USD",
            target_currency="INR",
            amount=500.0,
        )

        fill = await matching_engine.fill_from_liquidity(order)

        assert fill is not None
        assert fill.amount == 500.0
        assert fill.spread_earned == 500.0 * LP_SPREAD
        assert order.amount_unmatched == 0.0
        assert order.status == "filled"

    @pytest.mark.asyncio
    async def test_liquidity_fill_partial_order(self, matching_engine: MatchingEngine, session):
        """LP with less liquidity than needed fills partially."""
        lp = LiquidityPosition(
            id=_uid(),
            user_id=_uid(),
            currency="INR",
            amount=200.0,
            earned_fees=0.0,
            is_active=True,
        )
        session.add(lp)
        await session.flush()

        order = await matching_engine.submit_order(
            user_id=_uid(),
            source_currency="USD",
            target_currency="INR",
            amount=500.0,
        )

        fill = await matching_engine.fill_from_liquidity(order, remaining=200.0)

        assert fill is not None
        assert fill.amount == 200.0
        assert order.amount_matched == 200.0
        assert order.amount_unmatched == 300.0
        assert order.status == "partially_matched"


class TestFees:
    """Tests for fee calculations."""

    @pytest.mark.asyncio
    async def test_protocol_fee_0_05_percent(self, matching_engine: MatchingEngine, session):
        """Verify protocol fee is exactly 0.05% of matched amount."""
        user_a = _uid()
        user_b = _uid()

        order_a = await matching_engine.submit_order(
            user_id=user_a,
            source_currency="USD",
            target_currency="INR",
            amount=1000.0,
        )
        await matching_engine.submit_order(
            user_id=user_b,
            source_currency="INR",
            target_currency="USD",
            amount=1000.0,
        )

        match = await matching_engine.find_direct_match(order_a)

        assert match is not None
        expected_fee = 1000.0 * PROTOCOL_FEE
        assert abs(match.protocol_fee - expected_fee) < 0.0001
        assert abs(match.protocol_fee - 0.50) < 0.0001  # $1000 * 0.05% = $0.50

    @pytest.mark.asyncio
    async def test_lp_spread_earned(self, matching_engine: MatchingEngine, session):
        """LP earns 0.2% spread on fills."""
        lp = LiquidityPosition(
            id=_uid(),
            user_id=_uid(),
            currency="INR",
            amount=10000.0,
            earned_fees=0.0,
            is_active=True,
        )
        session.add(lp)
        await session.flush()

        order = await matching_engine.submit_order(
            user_id=_uid(),
            source_currency="USD",
            target_currency="INR",
            amount=1000.0,
        )

        fill = await matching_engine.fill_from_liquidity(order)

        assert fill is not None
        expected_spread = 1000.0 * LP_SPREAD
        assert abs(fill.spread_earned - expected_spread) < 0.0001
        assert abs(fill.spread_earned - 2.0) < 0.0001  # $1000 * 0.2% = $2.00

        # Verify LP position was credited
        result = await session.execute(
            select(LiquidityPosition).where(LiquidityPosition.id == lp.id)
        )
        updated_lp = result.scalar_one()
        assert abs(updated_lp.earned_fees - expected_spread) < 0.0001

    @pytest.mark.asyncio
    async def test_zero_fee_on_full_match(self, matching_engine: MatchingEngine, session):
        """Fully peer-matched orders have only the small protocol fee (0.05%)."""
        user_a = _uid()
        user_b = _uid()

        order_a = await matching_engine.submit_order(
            user_id=user_a,
            source_currency="USD",
            target_currency="INR",
            amount=1000.0,
        )
        await matching_engine.submit_order(
            user_id=user_b,
            source_currency="INR",
            target_currency="USD",
            amount=1000.0,
        )

        match = await matching_engine.find_direct_match(order_a)

        assert match is not None
        # Only 0.05% protocol fee, no LP spread
        assert match.protocol_fee == 1000.0 * PROTOCOL_FEE
        # No liquidity fills should exist
        fills_result = await session.execute(
            select(LiquidityFill).where(LiquidityFill.order_id == order_a.id)
        )
        fills = fills_result.scalars().all()
        assert len(fills) == 0


class TestPoolStats:
    """Tests for pool analytics."""

    @pytest.mark.asyncio
    async def test_pool_stats_accurate(self, pool_manager: PoolManager, session):
        """Pool status reflects actual state."""
        # Add LP
        lp = LiquidityPosition(
            id=_uid(),
            user_id=_uid(),
            currency="USD",
            amount=5000.0,
            earned_fees=0.0,
            is_active=True,
        )
        session.add(lp)

        # Add pending order
        now = datetime.now(timezone.utc)
        order = MatchOrder(
            id=_uid(),
            user_id=_uid(),
            source_currency="USD",
            target_currency="INR",
            amount=500.0,
            amount_matched=0.0,
            amount_unmatched=500.0,
            status="pending",
            max_wait_until=now + timedelta(hours=4),
            created_at=now,
        )
        session.add(order)
        await session.flush()

        status = await pool_manager.get_pool_status("USD")

        assert status.currency == "USD"
        assert status.tvl == 5000.0
        assert status.order_count == 1

    @pytest.mark.asyncio
    async def test_match_rate_estimation(self, pool_manager: PoolManager, session):
        """Estimate accuracy: should detect available counterparties."""
        # Add a counterparty order
        now = datetime.now(timezone.utc)
        counter = MatchOrder(
            id=_uid(),
            user_id=_uid(),
            source_currency="INR",
            target_currency="USD",
            amount=500.0,
            amount_matched=0.0,
            amount_unmatched=500.0,
            status="pending",
            max_wait_until=now + timedelta(hours=4),
            created_at=now,
        )
        session.add(counter)
        await session.flush()

        estimate = await pool_manager.estimate_match_rate(
            source="USD",
            target="INR",
            amount=500.0,
        )

        assert estimate.match_pct == 100.0
        assert estimate.estimated_fee > 0
        assert estimate.estimated_time <= 10.0  # instant match

    @pytest.mark.asyncio
    async def test_match_rate_estimation_partial(self, pool_manager: PoolManager, session):
        """Estimate shows partial match when counterparty volume is less."""
        now = datetime.now(timezone.utc)
        counter = MatchOrder(
            id=_uid(),
            user_id=_uid(),
            source_currency="INR",
            target_currency="USD",
            amount=300.0,
            amount_matched=0.0,
            amount_unmatched=300.0,
            status="pending",
            max_wait_until=now + timedelta(hours=4),
            created_at=now,
        )
        session.add(counter)
        await session.flush()

        estimate = await pool_manager.estimate_match_rate(
            source="USD",
            target="INR",
            amount=500.0,
        )

        assert estimate.match_pct == 60.0  # 300/500 = 60%


class TestConcurrent:
    """Tests for concurrent order handling."""

    @pytest.mark.asyncio
    async def test_concurrent_orders(self, matching_engine: MatchingEngine, session):
        """Multiple orders submitted simultaneously are all matched."""
        # Submit 5 USD->INR and 5 INR->USD orders
        usd_orders = []
        for _ in range(5):
            o = await matching_engine.submit_order(
                user_id=_uid(),
                source_currency="USD",
                target_currency="INR",
                amount=100.0,
            )
            usd_orders.append(o)

        inr_orders = []
        for _ in range(5):
            o = await matching_engine.submit_order(
                user_id=_uid(),
                source_currency="INR",
                target_currency="USD",
                amount=100.0,
            )
            inr_orders.append(o)

        # Run matching cycle
        stats = await matching_engine.run_matching_cycle()

        # All should be matched
        for o in usd_orders + inr_orders:
            await session.refresh(o)
            assert o.status == "fully_matched", f"Order {o.id} status = {o.status}"
            assert o.amount_unmatched == 0.0


class TestMatchExecution:
    """Tests for match execution and local payments."""

    @pytest.mark.asyncio
    async def test_match_execution_triggers_local_payments(
        self, matching_engine: MatchingEngine, session
    ):
        """Match creates LocalPayment records when executed."""
        user_a = _uid()
        user_b = _uid()

        order_a = await matching_engine.submit_order(
            user_id=user_a,
            source_currency="USD",
            target_currency="INR",
            amount=500.0,
            recipient_info={"account": "raj@upi", "name": "Raj", "method": "upi"},
        )
        order_b = await matching_engine.submit_order(
            user_id=user_b,
            source_currency="INR",
            target_currency="USD",
            amount=500.0,
            recipient_info={"account": "1234567890", "name": "Ali", "method": "ach"},
        )

        match = await matching_engine.find_direct_match(order_a)
        assert match is not None

        payments = await matching_engine.execute_match(match)

        assert len(payments) == 2
        assert match.status == "settled"
        assert match.executed_at is not None

        # Verify payment details
        usd_payment = next(p for p in payments if p.currency == "USD")
        inr_payment = next(p for p in payments if p.currency == "INR")

        assert usd_payment.amount == 500.0
        assert usd_payment.payment_method == "ach"
        assert usd_payment.tx_reference is not None
        assert usd_payment.status == "completed"

        assert inr_payment.amount == 500.0
        assert inr_payment.payment_method == "upi"
        assert inr_payment.tx_reference is not None
        assert inr_payment.status == "completed"


class TestMatchingCycle:
    """Tests for the full matching cycle."""

    @pytest.mark.asyncio
    async def test_full_matching_cycle(self, matching_engine: MatchingEngine, session):
        """Run a complete matching cycle and verify stats."""
        # Submit orders
        await matching_engine.submit_order(
            user_id=_uid(),
            source_currency="USD",
            target_currency="INR",
            amount=500.0,
            recipient_info={"method": "upi"},
        )
        await matching_engine.submit_order(
            user_id=_uid(),
            source_currency="INR",
            target_currency="USD",
            amount=500.0,
            recipient_info={"method": "ach"},
        )

        stats = await matching_engine.run_matching_cycle()

        assert stats["direct_matches"] + stats["partial_matches"] >= 1
        assert stats["payments_executed"] >= 2

    @pytest.mark.asyncio
    async def test_matching_cycle_with_lp_fill(self, matching_engine: MatchingEngine, session):
        """Matching cycle fills from LP when no counterparty exists."""
        # Add LP
        lp = LiquidityPosition(
            id=_uid(),
            user_id=_uid(),
            currency="INR",
            amount=10000.0,
            earned_fees=0.0,
            is_active=True,
        )
        session.add(lp)
        await session.flush()

        await matching_engine.submit_order(
            user_id=_uid(),
            source_currency="USD",
            target_currency="INR",
            amount=500.0,
        )

        stats = await matching_engine.run_matching_cycle()

        assert stats["lp_fills"] == 1
        assert stats["direct_matches"] == 0

    @pytest.mark.asyncio
    async def test_matching_cycle_expires_old_orders(self, matching_engine: MatchingEngine, session):
        """Matching cycle expires orders past their deadline."""
        order = await matching_engine.submit_order(
            user_id=_uid(),
            source_currency="USD",
            target_currency="INR",
            amount=500.0,
        )
        # Push expiry into the past
        order.max_wait_until = datetime.now(timezone.utc) - timedelta(minutes=5)
        await session.flush()

        stats = await matching_engine.run_matching_cycle()

        assert stats["expired"] == 1
        await session.refresh(order)
        assert order.status == "expired"


class TestLocalSettlement:
    """Tests for local settlement service."""

    @pytest.mark.asyncio
    async def test_execute_local_payment_upi(self):
        """UPI payment returns completed result."""
        result = await execute_local_payment(
            currency="INR",
            amount=10000.0,
            recipient={"account": "user@upi"},
            method="upi",
        )
        assert result.status == "completed"
        assert result.payment_method == "upi"
        assert result.tx_id.startswith("UPI_")

    @pytest.mark.asyncio
    async def test_execute_local_payment_ach(self):
        """ACH payment returns completed result."""
        result = await execute_local_payment(
            currency="USD",
            amount=500.0,
            recipient={"account": "1234567890"},
            method="ach",
        )
        assert result.status == "completed"
        assert result.payment_method == "ach"
        assert result.tx_id.startswith("ACH_")

    @pytest.mark.asyncio
    async def test_execute_local_payment_default_method(self):
        """Without explicit method, currency determines rail."""
        result = await execute_local_payment(
            currency="EUR",
            amount=1000.0,
            recipient={"iban": "DE89..."},
        )
        assert result.status == "completed"
        assert result.payment_method == "sepa"

    @pytest.mark.asyncio
    async def test_execute_local_payment_unknown_method(self):
        """Unknown method returns failed result."""
        result = await execute_local_payment(
            currency="USD",
            amount=100.0,
            recipient={},
            method="carrier_pigeon",
        )
        assert result.status == "failed"
        assert result.error is not None


class TestSubmitOrder:
    """Tests for order submission validation."""

    @pytest.mark.asyncio
    async def test_submit_order_creates_order(self, matching_engine: MatchingEngine, session):
        """Submitting an order persists it correctly."""
        order = await matching_engine.submit_order(
            user_id="user-123",
            source_currency="usd",
            target_currency="inr",
            amount=250.0,
            recipient_info={"name": "Test"},
            max_wait_hours=2.0,
        )

        assert order.id is not None
        assert order.source_currency == "USD"
        assert order.target_currency == "INR"
        assert order.amount == 250.0
        assert order.amount_unmatched == 250.0
        assert order.amount_matched == 0.0
        assert order.status == "pending"

    @pytest.mark.asyncio
    async def test_submit_order_rejects_zero_amount(self, matching_engine: MatchingEngine):
        """Zero or negative amount raises ValueError."""
        with pytest.raises(ValueError, match="positive"):
            await matching_engine.submit_order(
                user_id="user-123",
                source_currency="USD",
                target_currency="INR",
                amount=0.0,
            )

        with pytest.raises(ValueError, match="positive"):
            await matching_engine.submit_order(
                user_id="user-123",
                source_currency="USD",
                target_currency="INR",
                amount=-100.0,
            )
