"""
Test fixtures for ha_chain test suite.

Provides:
- Async SQLite test database with fresh schema per test
- Factory helpers that persist to the test DB
- Sample corridor, user, and agent fixtures
- Mock blockchain and external service fixtures
- Dependency overrides for testing
"""

import json
import sys
import os
from datetime import datetime, timedelta, timezone
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

# Ensure project root is on sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.database import Base
from app.enums import (
    AgentStatus, CorridorStatus, DeliveryMethod, KYCLevel, MobileMoneyProvider,
)
from app.models.models import (
    User, Agent, Corridor, Transfer, TokenizedAsset, Investment,
    SanctionsList, ComplianceCheck, Dispute,
)
from app.services.transfer_service import TransferService
from app.services.matching_service import MatchingService
from app.services.compliance_service import ComplianceService
from app.services.corridor_service import CorridorService
from app.services.escrow_service import EscrowService
from app.services.investment_service import InvestmentService
from app.services.exchange_rate_service import ExchangeRateService

from tests.mocks.mock_blockchain import MockEscrowService, MockStakingService
from tests.mocks.mock_kyc_provider import MockKYCProvider
from tests.mocks.mock_exchange_rate import MockExchangeRateProvider
from tests.mocks.mock_mobile_money import MockMobileMoneyProvider
from tests.factories import (
    UserFactory, SenderFactory, AgentFactory, CorridorFactory,
    HargeisaAgentFactory, MumbaiAgentFactory, MexicoCityAgentFactory,
    ManilaAgentFactory,
    USAToSomaliaCorridorFactory, USAToIndiaCorridorFactory,
    USAToMexicoCorridorFactory, USAToPhilippinesCorridorFactory,
    TokenizedAssetFactory, SanctionsListFactory,
)


# ---------------------------------------------------------------------------
# Database fixtures
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def db_engine():
    """Create an async in-memory SQLite engine for each test."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh async session for each test."""
    session_factory = async_sessionmaker(
        db_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with session_factory() as session:
        yield session
        await session.rollback()


# ---------------------------------------------------------------------------
# Mock service fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_escrow() -> MockEscrowService:
    """In-memory mock escrow blockchain service."""
    return MockEscrowService()


@pytest.fixture
def mock_staking() -> MockStakingService:
    """In-memory mock staking blockchain service."""
    return MockStakingService()


@pytest.fixture
def mock_kyc() -> MockKYCProvider:
    """Mock KYC verification provider."""
    return MockKYCProvider()


@pytest.fixture
def mock_rate_provider() -> MockExchangeRateProvider:
    """Mock exchange rate provider with default rates."""
    return MockExchangeRateProvider()


@pytest.fixture
def mock_mobile_money() -> MockMobileMoneyProvider:
    """Mock mobile money provider."""
    return MockMobileMoneyProvider()


# ---------------------------------------------------------------------------
# Application service fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def escrow_service(mock_escrow) -> EscrowService:
    """Escrow service wired to mock blockchain."""
    return EscrowService(blockchain_escrow=mock_escrow)


@pytest.fixture
def compliance_service_factory():
    """Factory that creates a ComplianceService given a db session."""
    def _make(db: AsyncSession, kyc_provider=None) -> ComplianceService:
        return ComplianceService(db=db, kyc_provider=kyc_provider)
    return _make


@pytest.fixture
def matching_service_factory():
    """Factory that creates a MatchingService given a db session."""
    def _make(db: AsyncSession) -> MatchingService:
        return MatchingService(db=db)
    return _make


@pytest.fixture
def transfer_service_factory():
    """Factory that creates a TransferService with all dependencies."""
    def _make(
        db: AsyncSession,
        escrow_svc=None,
        compliance_svc=None,
        matching_svc=None,
    ) -> TransferService:
        return TransferService(
            db=db,
            escrow_service=escrow_svc,
            compliance_service=compliance_svc,
            matching_service=matching_svc,
        )
    return _make


@pytest.fixture
def corridor_service_factory():
    """Factory that creates a CorridorService given a db session."""
    def _make(db: AsyncSession, rate_provider=None) -> CorridorService:
        return CorridorService(db=db, rate_provider=rate_provider)
    return _make


@pytest.fixture
def investment_service_factory():
    """Factory that creates an InvestmentService given a db session."""
    def _make(db: AsyncSession, escrow_svc=None) -> InvestmentService:
        return InvestmentService(db=db, escrow_service=escrow_svc)
    return _make


# ---------------------------------------------------------------------------
# Data seeding helpers
# ---------------------------------------------------------------------------

async def _add_and_flush(session: AsyncSession, obj):
    """Add an ORM object to session and flush to get ID generated."""
    session.add(obj)
    await session.flush()
    return obj


# ---------------------------------------------------------------------------
# Corridor fixtures
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def corridor_usa_somalia(db_session) -> Corridor:
    """USA -> Somalia corridor."""
    c = USAToSomaliaCorridorFactory.build()
    return await _add_and_flush(db_session, c)


@pytest_asyncio.fixture
async def corridor_usa_india(db_session) -> Corridor:
    """USA -> India corridor."""
    c = USAToIndiaCorridorFactory.build()
    return await _add_and_flush(db_session, c)


@pytest_asyncio.fixture
async def corridor_usa_mexico(db_session) -> Corridor:
    """USA -> Mexico corridor."""
    c = USAToMexicoCorridorFactory.build()
    return await _add_and_flush(db_session, c)


@pytest_asyncio.fixture
async def corridor_usa_philippines(db_session) -> Corridor:
    """USA -> Philippines corridor."""
    c = USAToPhilippinesCorridorFactory.build()
    return await _add_and_flush(db_session, c)


@pytest_asyncio.fixture
async def all_corridors(
    corridor_usa_somalia,
    corridor_usa_india,
    corridor_usa_mexico,
    corridor_usa_philippines,
) -> dict:
    """All test corridors as a dict keyed by destination country."""
    return {
        "SOM": corridor_usa_somalia,
        "IND": corridor_usa_india,
        "MEX": corridor_usa_mexico,
        "PHL": corridor_usa_philippines,
    }


# ---------------------------------------------------------------------------
# User fixtures
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def sender_user(db_session) -> User:
    """A USA-based sender with $10,000 balance and KYC level 2."""
    u = SenderFactory.build()
    return await _add_and_flush(db_session, u)


@pytest_asyncio.fixture
async def sender_kyc1(db_session) -> User:
    """A USA-based sender with KYC level 1 ($1000/day limit)."""
    u = SenderFactory.build(kyc_level=KYCLevel.BASIC.value, wallet_balance_usdc=5000.0)
    return await _add_and_flush(db_session, u)


# ---------------------------------------------------------------------------
# Agent fixtures
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def agent_user_hargeisa(db_session) -> User:
    """User account for the Hargeisa agent."""
    u = UserFactory.build(
        country="SOM",
        wallet_address="G" + "B" * 55,
        wallet_balance_usdc=5000.0,
    )
    return await _add_and_flush(db_session, u)


@pytest_asyncio.fixture
async def agent_hargeisa(db_session, agent_user_hargeisa) -> Agent:
    """Active agent in Hargeisa, Somalia."""
    a = HargeisaAgentFactory.build(user_id=agent_user_hargeisa.id)
    return await _add_and_flush(db_session, a)


@pytest_asyncio.fixture
async def agent_user_mumbai(db_session) -> User:
    """User account for the Mumbai agent."""
    u = UserFactory.build(
        country="IND",
        wallet_address="G" + "C" * 55,
        wallet_balance_usdc=8000.0,
    )
    return await _add_and_flush(db_session, u)


@pytest_asyncio.fixture
async def agent_mumbai(db_session, agent_user_mumbai) -> Agent:
    """Active agent in Mumbai, India."""
    a = MumbaiAgentFactory.build(user_id=agent_user_mumbai.id)
    return await _add_and_flush(db_session, a)


@pytest_asyncio.fixture
async def agent_user_mexico_city(db_session) -> User:
    """User account for the Mexico City agent."""
    u = UserFactory.build(
        country="MEX",
        wallet_address="G" + "D" * 55,
        wallet_balance_usdc=12000.0,
    )
    return await _add_and_flush(db_session, u)


@pytest_asyncio.fixture
async def agent_mexico_city(db_session, agent_user_mexico_city) -> Agent:
    """Active agent in Mexico City, Mexico."""
    a = MexicoCityAgentFactory.build(user_id=agent_user_mexico_city.id)
    return await _add_and_flush(db_session, a)


@pytest_asyncio.fixture
async def agent_user_manila(db_session) -> User:
    """User account for the Manila agent."""
    u = UserFactory.build(
        country="PHL",
        wallet_address="G" + "E" * 55,
        wallet_balance_usdc=6000.0,
    )
    return await _add_and_flush(db_session, u)


@pytest_asyncio.fixture
async def agent_manila(db_session, agent_user_manila) -> Agent:
    """Active agent in Manila, Philippines."""
    a = ManilaAgentFactory.build(user_id=agent_user_manila.id)
    return await _add_and_flush(db_session, a)


# ---------------------------------------------------------------------------
# Sanctions fixtures
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def sanctions_entry(db_session) -> SanctionsList:
    """An OFAC sanctions list entry."""
    s = SanctionsListFactory.build()
    return await _add_and_flush(db_session, s)


# ---------------------------------------------------------------------------
# Tokenized asset fixtures
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def sukuk_asset(db_session) -> TokenizedAsset:
    """A Somali sukuk bond asset."""
    a = TokenizedAssetFactory.build(
        name="Somali Sukuk Bond",
        symbol="SSB1",
        asset_type="sukuk",
        price_per_token_usd=100.0,
        annual_yield_percent=5.0,
    )
    return await _add_and_flush(db_session, a)


@pytest_asyncio.fixture
async def real_estate_asset(db_session) -> TokenizedAsset:
    """A tokenized real estate asset."""
    a = TokenizedAssetFactory.build(
        name="Dubai Property Fund",
        symbol="DPF1",
        asset_type="real_estate",
        price_per_token_usd=250.0,
        annual_yield_percent=8.0,
        issuer="Dubai RE Holdings",
    )
    return await _add_and_flush(db_session, a)
