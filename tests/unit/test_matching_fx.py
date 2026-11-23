"""Matching with realistic (non-1:1) FX rates.

The other matching tests mock every rate to 1.0, which hides any place where
amounts in different currencies are compared directly. These tests use a fixed
rate table so value conservation can be checked across currencies.
"""

from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base
from app.models.matching import LocalPayment
from app.services import fx_rates
from app.services.matching_engine import MatchingEngine

# units of currency per 1 USD
RATES = {"USD": 1.0, "INR": 83.5, "EUR": 0.92}


@pytest.fixture(autouse=True)
def fixed_fx(monkeypatch):
    async def _get_rate(src, tgt):
        return RATES[tgt.upper()] / RATES[src.upper()]
    # get_usd_value and convert call get_rate internally
    monkeypatch.setattr(fx_rates, "get_rate", _get_rate)


@pytest_asyncio.fixture
async def session():
    eng = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(eng, class_=AsyncSession, expire_on_commit=False)
    async with factory() as sess:
        yield sess
    await eng.dispose()


def _uid() -> str:
    return str(uuid.uuid4())


def usd(amount: float, currency: str) -> float:
    return amount / RATES[currency]


async def test_direct_partial_match_conserves_value(session):
    me = MatchingEngine(session)
    a = await me.submit_order(_uid(), "USD", "INR", 100.0)       # $100
    b = await me.submit_order(_uid(), "INR", "USD", 4175.0)      # ~$50

    match = await me.find_direct_match(a)

    assert match.amount == pytest.approx(50.0, abs=0.01)         # USD value
    assert a.amount_unmatched == pytest.approx(50.0, abs=0.01)   # $50 left
    assert b.amount_unmatched == pytest.approx(0.0, abs=0.01)


async def test_triangular_match_compares_value_not_raw_units(session):
    """$100 USD->INR, Rs 50,000 INR->EUR (~$599), EUR 80 EUR->USD (~$87).

    Smallest leg by VALUE is the EUR order (~$86.96). Comparing raw units
    would pick 80 (the EUR number) and take only Rs 80 (~$0.96) from the INR
    side while taking $80 from the USD side.
    """
    me = MatchingEngine(session)
    a = await me.submit_order(_uid(), "USD", "INR", 100.0)
    b = await me.submit_order(_uid(), "INR", "EUR", 50_000.0)
    c = await me.submit_order(_uid(), "EUR", "USD", 80.0)

    match = await me.find_triangular_match(a)
    assert match is not None

    matched_usd = usd(80.0, "EUR")                               # ~86.96
    assert match.amount == pytest.approx(matched_usd, abs=0.01)

    # Each order is reduced by the same USD value, in its own currency.
    assert usd(a.amount_matched, "USD") == pytest.approx(matched_usd, abs=0.02)
    assert usd(b.amount_matched, "INR") == pytest.approx(matched_usd, abs=0.02)
    assert usd(c.amount_matched, "EUR") == pytest.approx(matched_usd, abs=0.02)
    assert c.status == "fully_matched"


async def test_triangular_execution_pays_each_leg_in_its_own_currency(session):
    me = MatchingEngine(session)
    a = await me.submit_order(_uid(), "USD", "INR", 100.0)
    await me.submit_order(_uid(), "INR", "EUR", 50_000.0)
    await me.submit_order(_uid(), "EUR", "USD", 80.0)

    match = await me.find_triangular_match(a)
    await me.execute_match(match)

    rows = (await session.execute(
        select(LocalPayment).where(LocalPayment.match_id == match.id)
    )).scalars().all()
    assert len(rows) == 3
    for p in rows:
        assert usd(p.amount, p.currency) == pytest.approx(match.amount, abs=0.02), p.currency


async def test_triangular_routes_each_currency_to_who_wants_it(session):
    """USD->INR (A), INR->EUR (B), EUR->USD (C).
    A's USD must reach C's recipient, B's INR must reach A's, C's EUR must reach B's.
    """
    me = MatchingEngine(session)
    a = await me.submit_order(_uid(), "USD", "INR", 100.0, recipient_info={"who": "A-recipient"})
    await me.submit_order(_uid(), "INR", "EUR", 50_000.0, recipient_info={"who": "B-recipient"})
    await me.submit_order(_uid(), "EUR", "USD", 80.0, recipient_info={"who": "C-recipient"})

    match = await me.find_triangular_match(a)
    await me.execute_match(match)

    rows = (await session.execute(
        select(LocalPayment).where(LocalPayment.match_id == match.id)
    )).scalars().all()
    paid_to = {p.currency: p.recipient_info["who"] for p in rows}
    assert paid_to == {"USD": "C-recipient", "INR": "A-recipient", "EUR": "B-recipient"}
