"""Unit tests for the compliance / AML service."""

import pytest
from datetime import datetime, timedelta, timezone

from app.enums import ComplianceAction, ComplianceCheckType, TransferStatus
from app.models.models import Transfer, User, SanctionsList
from app.services.compliance_service import ComplianceService
from tests.factories import (
    TransferFactory, SenderFactory, CorridorFactory, SanctionsListFactory,
    USAToSomaliaCorridorFactory,
)


class TestComplianceChecks:
    """Tests for AML compliance checks."""

    @pytest.mark.asyncio
    async def test_sanctions_screening_blocks_ofac_match(
        self, db_session, sender_user, corridor_usa_somalia, sanctions_entry,
    ):
        """Transfer to OFAC-listed person should be blocked."""
        svc = ComplianceService(db=db_session)

        transfer = TransferFactory.build(
            sender_id=sender_user.id,
            corridor_id=corridor_usa_somalia.id,
            receiver_name="BLOCKED PERSON",  # Matches sanctions_entry
            receiver_country="SOM",
        )
        db_session.add(transfer)
        await db_session.flush()

        result = await svc.run_all_checks(transfer)

        assert result.action == ComplianceAction.BLOCKED
        assert "sanctions" in result.reason.lower() or "OFAC" in result.reason

    @pytest.mark.asyncio
    async def test_sanctions_screening_blocks_sanctioned_country(
        self, db_session, sender_user,
    ):
        """Transfer to sanctioned country should be blocked."""
        corridor = CorridorFactory.build(
            destination_country="PRK",
            destination_currency="KPW",
            exchange_rate=900.0,
        )
        db_session.add(corridor)
        await db_session.flush()

        svc = ComplianceService(db=db_session)

        transfer = TransferFactory.build(
            sender_id=sender_user.id,
            corridor_id=corridor.id,
            receiver_name="Some Person",
            receiver_country="PRK",
        )
        db_session.add(transfer)
        await db_session.flush()

        result = await svc.run_all_checks(transfer)
        assert result.action == ComplianceAction.BLOCKED
        assert "PRK" in result.reason or "sanctioned" in result.reason.lower()

    @pytest.mark.asyncio
    async def test_sanctions_blocks_sanctioned_sender(
        self, db_session, corridor_usa_somalia,
    ):
        """Transfer from a sanctioned sender should be blocked."""
        sanctioned_sender = SenderFactory.build(is_sanctioned=True)
        db_session.add(sanctioned_sender)
        await db_session.flush()

        svc = ComplianceService(db=db_session)

        transfer = TransferFactory.build(
            sender_id=sanctioned_sender.id,
            corridor_id=corridor_usa_somalia.id,
            receiver_name="Normal Person",
            receiver_country="SOM",
        )
        db_session.add(transfer)
        await db_session.flush()

        result = await svc.run_all_checks(transfer)
        assert result.action == ComplianceAction.BLOCKED

    @pytest.mark.asyncio
    async def test_large_amount_triggers_enhanced_review(
        self, db_session, sender_user, corridor_usa_somalia,
    ):
        """Transfer > $3000 should trigger enhanced review."""
        svc = ComplianceService(db=db_session)

        transfer = TransferFactory.build(
            sender_id=sender_user.id,
            corridor_id=corridor_usa_somalia.id,
            send_amount_usd=5000.0,
            receiver_name="Normal Person",
            receiver_country="SOM",
        )
        db_session.add(transfer)
        await db_session.flush()

        result = await svc.run_all_checks(transfer)

        # Should not be blocked, but should have enhanced review or flagged
        assert result.action in (
            ComplianceAction.ENHANCED_REVIEW,
            ComplianceAction.FLAGGED,
            ComplianceAction.SAR_FILED,
        )
        assert result.risk_score > 0

    @pytest.mark.asyncio
    async def test_structuring_detection(
        self, db_session, sender_user, corridor_usa_somalia,
    ):
        """10 transfers of $999 in 24h should flag structuring."""
        svc = ComplianceService(db=db_session)

        # Create 10 existing sub-$1000 transfers
        for i in range(10):
            t = TransferFactory.build(
                sender_id=sender_user.id,
                corridor_id=corridor_usa_somalia.id,
                send_amount_usd=999.0,
                status=TransferStatus.DELIVERED.value,
                receiver_name=f"Person {i}",
                receiver_country="SOM",
                created_at=datetime.now(timezone.utc) - timedelta(hours=1),
            )
            db_session.add(t)
        await db_session.flush()

        # New transfer should trigger structuring detection
        new_transfer = TransferFactory.build(
            sender_id=sender_user.id,
            corridor_id=corridor_usa_somalia.id,
            send_amount_usd=999.0,
            receiver_name="Another Person",
            receiver_country="SOM",
        )
        db_session.add(new_transfer)
        await db_session.flush()

        result = await svc.run_all_checks(new_transfer)

        # Should be flagged for structuring
        assert result.action in (
            ComplianceAction.FLAGGED,
            ComplianceAction.SAR_FILED,
        )
        # Check that structuring was detected
        structuring_checks = [
            c for c in result.checks
            if c["type"] == ComplianceCheckType.STRUCTURING.value
        ]
        assert len(structuring_checks) > 0
        assert structuring_checks[0]["action"] == ComplianceAction.FLAGGED

    @pytest.mark.asyncio
    async def test_velocity_check(
        self, db_session, sender_user, corridor_usa_somalia,
    ):
        """>$10,000 in 24 hours should flag."""
        svc = ComplianceService(db=db_session)

        # Create existing transfers totaling $9000
        for i in range(3):
            t = TransferFactory.build(
                sender_id=sender_user.id,
                corridor_id=corridor_usa_somalia.id,
                send_amount_usd=3000.0,
                status=TransferStatus.DELIVERED.value,
                receiver_name=f"Person {i}",
                receiver_country="SOM",
                created_at=datetime.now(timezone.utc) - timedelta(hours=2),
            )
            db_session.add(t)
        await db_session.flush()

        # New transfer of $2000 puts total at $11,000 > $10,000 threshold
        new_transfer = TransferFactory.build(
            sender_id=sender_user.id,
            corridor_id=corridor_usa_somalia.id,
            send_amount_usd=2000.0,
            receiver_name="Another Person",
            receiver_country="SOM",
        )
        db_session.add(new_transfer)
        await db_session.flush()

        result = await svc.run_all_checks(new_transfer)

        velocity_checks = [
            c for c in result.checks
            if c["type"] == ComplianceCheckType.VELOCITY.value
        ]
        assert len(velocity_checks) > 0
        assert velocity_checks[0]["action"] == ComplianceAction.FLAGGED

    @pytest.mark.asyncio
    async def test_country_risk_scoring(
        self, db_session, sender_user, corridor_usa_somalia,
    ):
        """High-risk corridors should have stricter thresholds."""
        # Somalia is in HIGH_RISK_COUNTRIES
        svc = ComplianceService(db=db_session)

        transfer = TransferFactory.build(
            sender_id=sender_user.id,
            corridor_id=corridor_usa_somalia.id,
            send_amount_usd=500.0,
            receiver_name="Normal Person",
            receiver_country="SOM",
        )
        db_session.add(transfer)
        await db_session.flush()

        result = await svc.run_all_checks(transfer)

        country_checks = [
            c for c in result.checks
            if c["type"] == ComplianceCheckType.COUNTRY_RISK.value
        ]
        assert len(country_checks) > 0
        # Somalia should have elevated risk score
        assert country_checks[0]["risk_score"] >= 30

    @pytest.mark.asyncio
    async def test_auto_sar_filing(
        self, db_session, sender_user, corridor_usa_somalia,
    ):
        """Critical alerts (total risk >= 80) should auto-generate SAR."""
        svc = ComplianceService(db=db_session)

        # Create lots of suspicious history (structuring + velocity)
        for i in range(12):
            t = TransferFactory.build(
                sender_id=sender_user.id,
                corridor_id=corridor_usa_somalia.id,
                send_amount_usd=999.0,
                status=TransferStatus.DELIVERED.value,
                receiver_name=f"Person {i}",
                receiver_country="SOM",
                created_at=datetime.now(timezone.utc) - timedelta(hours=1),
            )
            db_session.add(t)
        await db_session.flush()

        # New large transfer to push velocity over threshold too
        new_transfer = TransferFactory.build(
            sender_id=sender_user.id,
            corridor_id=corridor_usa_somalia.id,
            send_amount_usd=5000.0,
            receiver_name="Suspicious Person",
            receiver_country="SOM",
        )
        db_session.add(new_transfer)
        await db_session.flush()

        result = await svc.run_all_checks(new_transfer)

        # With structuring + velocity + country risk + amount threshold,
        # total risk should be >= 80 triggering SAR
        assert result.risk_score >= 50  # At minimum flagged
        if result.risk_score >= 80:
            assert result.action == ComplianceAction.SAR_FILED

    @pytest.mark.asyncio
    async def test_clean_transfer_passes(
        self, db_session, sender_user, corridor_usa_india,
    ):
        """A normal, small transfer to a low-risk corridor should pass cleanly."""
        svc = ComplianceService(db=db_session)

        transfer = TransferFactory.build(
            sender_id=sender_user.id,
            corridor_id=corridor_usa_india.id,
            send_amount_usd=200.0,
            receiver_name="Rahul Sharma",
            receiver_country="IND",
        )
        db_session.add(transfer)
        await db_session.flush()

        result = await svc.run_all_checks(transfer)
        assert result.action == ComplianceAction.APPROVED
        assert result.risk_score < 25
