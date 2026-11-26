"""
API-level tests for authentication, ownership and compliance gating on the
P2P matching endpoints (/api/v1/matching/*) and the demo flows that use them.

Unlike the service-level tests (which use the legacy ``app.database.Base``
schema from conftest), these exercise the real FastAPI app, so they need both
metadata objects with the platform ``users`` table -- the same setup that
``app.main.lifespan`` performs for SQLite.
"""

import uuid
from typing import AsyncGenerator

import httpx
import pytest
import pytest_asyncio
from sqlalchemy import JSON, String, select
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

import app.main  # noqa: F401 -- registers the sqlite3 UUID adapter
import app.models  # noqa: F401 -- populate platform metadata
from app.api.v1 import matching as matching_api
from app.core.security import create_access_token
from app.database import Base as MatchingBase
from app.db.base import Base as MainBase
from app.dependencies import get_db
from app.models.kyc import SanctionsCheck
from app.models.matching import LiquidityPosition, MatchOrder
from app.models.models import SanctionsList
from app.models.user import User


ORDER_BODY = {
    "source_currency": "USD",
    "target_currency": "INR",
    "amount": 250.0,
    "recipient_info": {"name": "Priya Sharma", "account": "priya@upi", "method": "upi"},
    "max_wait_hours": 4,
}


def _patch_sqlite_types() -> None:
    """Mirror app.main.lifespan: make Postgres-only column types SQLite-safe."""
    for base in (MainBase, MatchingBase):
        for table in base.metadata.tables.values():
            for col in table.columns:
                if isinstance(col.type, UUID):
                    col.type = String(36)
                elif isinstance(col.type, JSONB):
                    col.type = JSON()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def api_session_factory():
    _patch_sqlite_types()
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        # Platform schema first so its ``users`` table wins (as in lifespan)
        await conn.run_sync(MainBase.metadata.create_all)
        await conn.run_sync(MatchingBase.metadata.create_all)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    yield factory
    await engine.dispose()


@pytest_asyncio.fixture
async def client(api_session_factory) -> AsyncGenerator[httpx.AsyncClient, None]:
    async def _override_db():
        async with api_session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    fastapi_app = app.main.app
    fastapi_app.dependency_overrides[get_db] = _override_db
    fastapi_app.dependency_overrides[matching_api._get_db] = _override_db
    transport = httpx.ASGITransport(app=fastapi_app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    fastapi_app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def make_user(api_session_factory):
    """Create a platform user; returns (user_id, auth_headers)."""
    counter = {"n": 0}

    async def _make(
        *,
        verified: bool = True,
        kyc_level: int = 1,
        full_name: str | None = None,
        country_code: str = "USA",
    ):
        counter["n"] += 1
        n = counter["n"]
        uid = str(uuid.uuid4())
        async with api_session_factory() as s:
            s.add(User(
                id=uid,
                email=f"u{n}_{uid[:6]}@test.io",
                phone=f"+1555{uid[:7].replace('-', '0')}{n}",
                password_hash="x",
                full_name=full_name or f"Test User {n}",
                country_code=country_code,
                kyc_level=kyc_level if verified else 0,
                is_verified=verified,
            ))
            await s.commit()
        token = create_access_token(uid, {"role": "user"})
        return uid, {"Authorization": f"Bearer {token}"}

    return _make


async def _count_orders(factory) -> int:
    async with factory() as s:
        return len((await s.execute(select(MatchOrder))).scalars().all())


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------

class TestAuthentication:

    @pytest.mark.asyncio
    async def test_unauthenticated_order_rejected(self, client, api_session_factory):
        resp = await client.post("/api/v1/matching/orders", json=ORDER_BODY)
        assert resp.status_code == 401
        assert await _count_orders(api_session_factory) == 0

    @pytest.mark.asyncio
    async def test_user_id_query_param_no_longer_authenticates(self, client, make_user):
        victim_id, _ = await make_user()
        resp = await client.post(
            f"/api/v1/matching/orders?user_id={victim_id}", json=ORDER_BODY,
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_invalid_token_rejected(self, client):
        resp = await client.post(
            "/api/v1/matching/orders", json=ORDER_BODY,
            headers={"Authorization": "Bearer not-a-real-jwt"},
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    @pytest.mark.parametrize("method,path", [
        ("POST", "/api/v1/matching/liquidity"),
        ("GET", "/api/v1/matching/liquidity/positions"),
        ("DELETE", "/api/v1/matching/orders/some-id"),
        ("DELETE", "/api/v1/matching/liquidity/some-id"),
        ("GET", "/api/v1/matching/orders/some-id"),
    ])
    async def test_other_user_endpoints_require_auth(self, client, method, path):
        kwargs = {"json": {"currency": "USD", "amount": 100}} if method == "POST" else {}
        resp = await client.request(method, path, **kwargs)
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_order_owned_by_token_subject_not_query_param(
        self, client, make_user, api_session_factory,
    ):
        caller_id, headers = await make_user()
        victim_id, _ = await make_user()
        resp = await client.post(
            f"/api/v1/matching/orders?user_id={victim_id}",
            json=ORDER_BODY, headers=headers,
        )
        assert resp.status_code == 201
        assert resp.json()["user_id"] == caller_id


# ---------------------------------------------------------------------------
# Ownership
# ---------------------------------------------------------------------------

class TestOwnership:

    @pytest.mark.asyncio
    async def test_cancel_other_users_order_forbidden(
        self, client, make_user, api_session_factory,
    ):
        _, owner_headers = await make_user()
        _, attacker_headers = await make_user()
        order_id = (await client.post(
            "/api/v1/matching/orders", json=ORDER_BODY, headers=owner_headers,
        )).json()["id"]

        resp = await client.delete(
            f"/api/v1/matching/orders/{order_id}", headers=attacker_headers,
        )
        assert resp.status_code == 403

        async with api_session_factory() as s:
            order = await s.get(MatchOrder, order_id)
            assert order.status == "pending"

        # Reading someone else's order (recipient PII) is also forbidden
        resp = await client.get(
            f"/api/v1/matching/orders/{order_id}", headers=attacker_headers,
        )
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_owner_can_cancel_own_order(self, client, make_user):
        _, headers = await make_user()
        order_id = (await client.post(
            "/api/v1/matching/orders", json=ORDER_BODY, headers=headers,
        )).json()["id"]
        resp = await client.delete(f"/api/v1/matching/orders/{order_id}", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["status"] == "cancelled"

    @pytest.mark.asyncio
    async def test_cancel_missing_order_is_404(self, client, make_user):
        _, headers = await make_user()
        resp = await client.delete(
            f"/api/v1/matching/orders/{uuid.uuid4()}", headers=headers,
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_withdraw_other_users_position_forbidden(
        self, client, make_user, api_session_factory,
    ):
        _, owner_headers = await make_user()
        _, attacker_headers = await make_user()
        resp = await client.post(
            "/api/v1/matching/liquidity",
            json={"currency": "USD", "amount": 1000}, headers=owner_headers,
        )
        assert resp.status_code == 201
        position_id = resp.json()["id"]

        resp = await client.delete(
            f"/api/v1/matching/liquidity/{position_id}", headers=attacker_headers,
        )
        assert resp.status_code == 403

        async with api_session_factory() as s:
            pos = await s.get(LiquidityPosition, position_id)
            assert pos.amount == 1000
            assert pos.is_active is True

    @pytest.mark.asyncio
    async def test_owner_can_withdraw_own_position(self, client, make_user):
        _, headers = await make_user()
        position_id = (await client.post(
            "/api/v1/matching/liquidity",
            json={"currency": "USD", "amount": 1000}, headers=headers,
        )).json()["id"]
        resp = await client.delete(f"/api/v1/matching/liquidity/{position_id}", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["amount_withdrawn"] == 1000

        positions = await client.get("/api/v1/matching/liquidity/positions", headers=headers)
        assert positions.status_code == 200

    @pytest.mark.asyncio
    async def test_withdraw_missing_position_is_404(self, client, make_user):
        _, headers = await make_user()
        resp = await client.delete(
            f"/api/v1/matching/liquidity/{uuid.uuid4()}", headers=headers,
        )
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# KYC and sanctions gating
# ---------------------------------------------------------------------------

class TestComplianceGate:

    @pytest.mark.asyncio
    async def test_unverified_user_cannot_submit_order(
        self, client, make_user, api_session_factory,
    ):
        _, headers = await make_user(verified=False)
        resp = await client.post("/api/v1/matching/orders", json=ORDER_BODY, headers=headers)
        assert resp.status_code == 403
        assert "KYC" in resp.json()["detail"]
        assert await _count_orders(api_session_factory) == 0

    @pytest.mark.asyncio
    async def test_unverified_user_cannot_add_liquidity(self, client, make_user):
        _, headers = await make_user(verified=False)
        resp = await client.post(
            "/api/v1/matching/liquidity",
            json={"currency": "USD", "amount": 1000}, headers=headers,
        )
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_token_for_deleted_user_rejected(self, client):
        token = create_access_token(uuid.uuid4(), {"role": "user"})
        resp = await client.post(
            "/api/v1/matching/orders", json=ORDER_BODY,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_sanctioned_user_cannot_submit_order(
        self, client, make_user, api_session_factory,
    ):
        uid, headers = await make_user()
        async with api_session_factory() as s:
            s.add(SanctionsCheck(
                user_id=uid, provider="chainalysis", result="match",
                details_json={"list": "SDN"},
            ))
            await s.commit()

        resp = await client.post("/api/v1/matching/orders", json=ORDER_BODY, headers=headers)
        assert resp.status_code == 403
        detail = resp.json()["detail"]
        # No tipping off: generic message, no internal compliance details
        assert detail == matching_api.COMPLIANCE_REJECTION_DETAIL
        for leaked in ("sanction", "SAR", "match", "chainalysis", "SDN"):
            assert leaked.lower() not in detail.lower()
        assert await _count_orders(api_session_factory) == 0

    @pytest.mark.asyncio
    async def test_user_on_sanctions_list_cannot_submit_order(
        self, client, make_user, api_session_factory,
    ):
        _, headers = await make_user(full_name="Sanctioned Person")
        async with api_session_factory() as s:
            s.add(SanctionsList(full_name="Sanctioned Person", source="OFAC"))
            await s.commit()
        resp = await client.post("/api/v1/matching/orders", json=ORDER_BODY, headers=headers)
        assert resp.status_code == 403
        assert resp.json()["detail"] == matching_api.COMPLIANCE_REJECTION_DETAIL

    @pytest.mark.asyncio
    async def test_sanctioned_recipient_blocks_order(
        self, client, make_user, api_session_factory,
    ):
        _, headers = await make_user()
        async with api_session_factory() as s:
            s.add(SanctionsList(full_name="Bad Actor", source="UN"))
            await s.commit()
        body = {**ORDER_BODY, "recipient_info": {"name": "Bad Actor", "account": "x", "method": "upi"}}
        resp = await client.post("/api/v1/matching/orders", json=body, headers=headers)
        assert resp.status_code == 403
        assert resp.json()["detail"] == matching_api.COMPLIANCE_REJECTION_DETAIL

    @pytest.mark.asyncio
    async def test_user_in_sanctioned_country_blocked(self, client, make_user):
        _, headers = await make_user(country_code="PRK")
        resp = await client.post("/api/v1/matching/orders", json=ORDER_BODY, headers=headers)
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_sanctioned_user_cannot_add_liquidity(
        self, client, make_user, api_session_factory,
    ):
        uid, headers = await make_user()
        async with api_session_factory() as s:
            s.add(SanctionsCheck(user_id=uid, provider="elliptic", result="pending_review"))
            await s.commit()
        resp = await client.post(
            "/api/v1/matching/liquidity",
            json={"currency": "USD", "amount": 1000}, headers=headers,
        )
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_verified_clear_user_happy_path(
        self, client, make_user, api_session_factory,
    ):
        uid, headers = await make_user()
        async with api_session_factory() as s:
            s.add(SanctionsCheck(user_id=uid, provider="chainalysis", result="clear"))
            await s.commit()

        resp = await client.post("/api/v1/matching/orders", json=ORDER_BODY, headers=headers)
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["user_id"] == uid
        assert data["status"] == "pending"

        resp = await client.get(f"/api/v1/matching/orders/{data['id']}", headers=headers)
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Demo flows keep working
# ---------------------------------------------------------------------------

class TestDemoFlows:

    @pytest.mark.asyncio
    async def test_web_demo_register_kyc_verify_then_order(self, client):
        reg = await client.post("/api/v1/auth/register", json={
            "full_name": "Web Demo User",
            "email": "webdemo@test.io",
            "phone": "+15550001111",
            "password": "demo12345",
            "country_code": "USA",
            "default_currency": "USD",
        })
        assert reg.status_code == 201, reg.text
        headers = {"Authorization": f"Bearer {reg.json()['access_token']}"}

        # Fresh accounts are not KYC-verified
        resp = await client.post("/api/v1/matching/orders", json=ORDER_BODY, headers=headers)
        assert resp.status_code == 403

        kyc = await client.post("/api/v1/demo/kyc-verify", headers=headers)
        assert kyc.status_code == 200, kyc.text
        assert kyc.json()["is_verified"] is True

        resp = await client.post("/api/v1/matching/orders", json=ORDER_BODY, headers=headers)
        assert resp.status_code == 201, resp.text

    @pytest.mark.asyncio
    async def test_demo_kyc_verify_requires_auth(self, client):
        resp = await client.post("/api/v1/demo/kyc-verify")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_investor_scenario_still_matches(self, client, monkeypatch):
        from app.services import fx_rates, stellar_service

        async def _no_live_rate(*_a, **_k):
            return None

        async def _no_chain(*_a, **_k):
            return None

        monkeypatch.setattr(fx_rates, "_fetch_live_rate", _no_live_rate)
        monkeypatch.setattr(stellar_service, "record_match_on_chain", _no_chain)

        resp = await client.post("/api/v1/demo/scenario")
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["matching"]["stats"]["direct_matches"] >= 1

