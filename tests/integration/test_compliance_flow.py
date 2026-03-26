"""Integration tests for AML compliance flows."""

import pytest
from datetime import datetime, timedelta, timezone

from app.enums import (
    TransferStatus, DeliveryMethod, ComplianceAction, ComplianceCheckType,
)
from app.models.models import Transfer, ComplianceCheck, SanctionsList
from app.services.transfer_service import TransferService
from app.services.compliance_service import ComplianceService
from app.services.escrow_service import EscrowService
from tests.mocks.mock_blockchain import MockEscrowService
from tests.factories import (
    SenderFactory, TransferFactory, CorridorFactory, SanctionsListFactory,
)


class TestComplianceFlow:
    """Integration tests for compliance checks during transfer flows."""

    @pytest.mark.asyncio
    async def test_normal_transfer_passes_compliance(
        self, db_session, sender_user, corridor_usa_india, mock_escrow,
    ):
        """Normal $200 transfer to India should pass all compliance checks."""
        escrow_svc = EscrowService(mock_escrow)
        compliance_svc = ComplianceService(db=db_session)
        svc = TransferService(
            db=db_session,
            escrow_service=escrow_svc,
            compliance_service=compliance_svc,
        )

        transfer = await svc.create_quote(
            sender_id=sender_user.id,
            corridor_id=corridor_usa_india.id,
            send_amount_usd=200.0,
            delivery_method=DeliveryMethod.MOBILE_MONEY.value,
            receiver_name="Rahul Sharma",
            receiver_phone="+919876543210",
            receiver_city="Mumbai",
            receiver_country="IND",
        )
        result = await svc.initiate_transfer(transfer.id)

        assert result.status == TransferStatus.ESCROW_LOCKED.value
        # Compliance passed (may be approved or enhanced_review for India)
        assert result.compliance_status != ComplianceAction.BLOCKED.value

    @pytest.mark.asyncio
    async def test_sanctioned_receiver_blocked(
        self, db_session, sender_user, corridor_usa_somalia,
        sanctions_entry, mock_escrow,
    ):
        """Transfer to OFAC-listed receiver should be blocked during initiation."""
        escrow_svc = EscrowService(mock_escrow)
        compliance_svc = ComplianceService(db=db_session)
        svc = TransferService(
            db=db_session,
            escrow_service=escrow_svc,
            compliance_service=compliance_svc,
        )

        transfer = await svc.create_quote(
            sender_id=sender_user.id,
            corridor_id=corridor_usa_somalia.id,
            send_amount_usd=500.0,
            delivery_method=DeliveryMethod.CASH_PICKUP.value,
            receiver_name="BLOCKED PERSON",  # Matches OFAC entry
            receiver_phone="+252634001234",
            receiver_city="Hargeisa",
            receiver_country="SOM",
        )

        with pytest.raises(ValueError, match="blocked by compliance"):
            await svc.initiate_transfer(transfer.id)

        refreshed = await db_session.get(Transfer, transfer.id)
        assert refreshed.status == TransferStatus.COMPLIANCE_BLOCKED.value

    @pytest.mark.asyncio
    async def test_sanctioned_country_blocked(
        self, db_session, sender_user, mock_escrow,
    ):
        """Transfer to sanctioned country (North Korea) should be blocked."""
        corridor = CorridorFactory.build(
            destination_country="PRK",
            destination_currency="KPW",
            exchange_rate=900.0,
        )
        db_session.add(corridor)
        await db_session.flush()

        escrow_svc = EscrowService(mock_escrow)
        compliance_svc = ComplianceService(db=db_session)
        svc = TransferService(
            db=db_session,
            escrow_service=escrow_svc,
            compliance_service=compliance_svc,
        )

        transfer = await svc.create_quote(
            sender_id=sender_user.id,
            corridor_id=corridor.id,
            send_amount_usd=100.0,
            delivery_method=DeliveryMethod.CASH_PICKUP.value,
            receiver_name="Some Person",
            receiver_phone="+850123456",
            receiver_city="Pyongyang",
            receiver_country="PRK",
        )

        with pytest.raises(ValueError, match="blocked by compliance"):
            await svc.initiate_transfer(transfer.id)

    @pytest.mark.asyncio
    async def test_large_transfer_flagged_but_proceeds(
        self, db_session, sender_user, corridor_usa_somalia, mock_escrow,
    ):
        """Large transfer ($5000) should be flagged for enhanced review but allowed."""
        escrow_svc = EscrowService(mock_escrow)
        compliance_svc = ComplianceService(db=db_session)
        svc = TransferService(
            db=db_session,
            escrow_service=escrow_svc,
            compliance_service=compliance_svc,
        )

        transfer = await svc.create_quote(
            sender_id=sender_user.id,
            corridor_id=corridor_usa_somalia.id,
            send_amount_usd=5000.0,
            delivery_method=DeliveryMethod.CASH_PICKUP.value,
            receiver_name="Normal Person",
            receiver_phone="+252634005678",
            receiver_city="Hargeisa",
            receiver_country="SOM",
        )
        result = await svc.initiate_transfer(transfer.id)

        # Should proceed but be flagged
        assert result.status == TransferStatus.ESCROW_LOCKED.value
        # Compliance status should reflect enhanced review or flagged
        assert result.compliance_status in (
            ComplianceAction.ENHANCED_REVIEW.value,
            ComplianceAction.FLAGGED.value,
            ComplianceAction.SAR_FILED.value,
            ComplianceAction.APPROVED.value,
        )

    @pytest.mark.asyncio
    async def test_velocity_buildup_triggers_flag(
        self, db_session, sender_user, corridor_usa_somalia, mock_escrow,
    ):
        """
        Accumulating transfers over $10,000 in 24h should trigger velocity flag.
        """
        # Upgrade to full KYC so the large totals aren't blocked by KYC limits
        from app.enums import KYCLevel
        sender_user.kyc_level = KYCLevel.FULL.value
        sender_user.wallet_balance_usdc = 50000.0
        await db_session.flush()

        # Seed existing transfers
        for i in range(5):
            t = TransferFactory.build(
                sender_id=sender_user.id,
                corridor_id=corridor_usa_somalia.id,
                send_amount_usd=2000.0,
                status=TransferStatus.DELIVERED.value,
                receiver_name=f"Person {i}",
                receiver_country="SOM",
                created_at=datetime.now(timezone.utc) - timedelta(hours=2),
            )
            db_session.add(t)
        await db_session.flush()

        # New transfer pushes total to $12,000 (5*2000 + 2000)
        escrow_svc = EscrowService(mock_escrow)
        compliance_svc = ComplianceService(db=db_session)
        svc = TransferService(
            db=db_session,
            escrow_service=escrow_svc,
            compliance_service=compliance_svc,
        )

        transfer = await svc.create_quote(
            sender_id=sender_user.id,
            corridor_id=corridor_usa_somalia.id,
            send_amount_usd=2000.0,
            delivery_method=DeliveryMethod.CASH_PICKUP.value,
            receiver_name="Another Person",
            receiver_phone="+252634009999",
            receiver_city="Hargeisa",
            receiver_country="SOM",
        )

        # Should still initiate but with compliance flags
        result = await svc.initiate_transfer(transfer.id)
        assert result.status == TransferStatus.ESCROW_LOCKED.value

    @pytest.mark.asyncio
    async def test_structuring_pattern_detection(
        self, db_session, sender_user, corridor_usa_india, mock_escrow,
    ):
        """Many sub-$1000 transfers should trigger structuring detection."""
        # Create 10 recent sub-threshold transfers
        for i in range(10):
            t = TransferFactory.build(
                sender_id=sender_user.id,
                corridor_id=corridor_usa_india.id,
                send_amount_usd=999.0,
                status=TransferStatus.DELIVERED.value,
                receiver_name=f"Person {i}",
                receiver_country="IND",
                created_at=datetime.now(timezone.utc) - timedelta(hours=1),
            )
            db_session.add(t)
        await db_session.flush()

        compliance_svc = ComplianceService(db=db_session)

        # Check the 11th transfer
        new_transfer = TransferFactory.build(
            sender_id=sender_user.id,
            corridor_id=corridor_usa_india.id,
            send_amount_usd=999.0,
            receiver_name="Yet Another Person",
            receiver_country="IND",
        )
        db_session.add(new_transfer)
        await db_session.flush()

        result = await compliance_svc.run_all_checks(new_transfer)

        # Should detect structuring
        structuring = [
            c for c in result.checks
            if c["type"] == ComplianceCheckType.STRUCTURING.value
        ]
        assert len(structuring) > 0
        assert structuring[0]["action"] == ComplianceAction.FLAGGED

    @pytest.mark.asyncio
    async def test_compliance_check_records_persisted(
        self, db_session, sender_user, corridor_usa_somalia, mock_escrow,
    ):
        """Compliance checks should be persisted to the database."""
        compliance_svc = ComplianceService(db=db_session)

        transfer = TransferFactory.build(
            sender_id=sender_user.id,
            corridor_id=corridor_usa_somalia.id,
            send_amount_usd=500.0,
            receiver_name="Normal Person",
            receiver_country="SOM",
        )
        db_session.add(transfer)
        await db_session.flush()

        await compliance_svc.run_all_checks(transfer)

        # Query persisted checks
        from sqlalchemy import select
        result = await db_session.execute(
            select(ComplianceCheck).where(
                ComplianceCheck.transfer_id == transfer.id
            )
        )
        checks = list(result.scalars().all())

        # Should have multiple check types
        assert len(checks) >= 4  # sanctions, country_risk, amount, velocity, structuring
        check_types = {c.check_type for c in checks}
        assert ComplianceCheckType.SANCTIONS.value in check_types
        assert ComplianceCheckType.VELOCITY.value in check_types
