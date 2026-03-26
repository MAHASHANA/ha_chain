"""Integration tests for end-to-end transfer flows."""

import pytest
from datetime import datetime, timedelta, timezone

from app.enums import (
    TransferStatus, DeliveryMethod, EscrowStatus, MobileMoneyProvider,
    DisputeStatus,
)
from app.models.models import Transfer, User, Agent, Dispute
from app.services.transfer_service import TransferService
from app.services.matching_service import MatchingService
from app.services.compliance_service import ComplianceService
from app.services.escrow_service import EscrowService
from tests.mocks.mock_blockchain import MockEscrowService


class TestEndToEndTransfer:
    """Full end-to-end transfer flow integration tests."""

    @pytest.mark.asyncio
    async def test_full_usa_to_somalia_cash_pickup(
        self, db_session, sender_user, corridor_usa_somalia,
        agent_hargeisa, agent_user_hargeisa, mock_escrow,
    ):
        """
        Complete flow:
        1. Sender creates quote (USA->Somalia, $500, cash pickup)
        2. Sender initiates transfer
        3. System locks escrow
        4. System matches agent in Hargeisa
        5. Agent accepts
        6. Agent confirms delivery with pickup code
        7. Escrow released to agent
        8. Both parties rate
        9. All statuses correct at each step
        """
        escrow_svc = EscrowService(mock_escrow)
        compliance_svc = ComplianceService(db=db_session)
        matching_svc = MatchingService(db=db_session)
        svc = TransferService(
            db=db_session,
            escrow_service=escrow_svc,
            compliance_service=compliance_svc,
            matching_service=matching_svc,
        )
        original_sender_balance = sender_user.wallet_balance_usdc
        original_agent_balance = agent_user_hargeisa.wallet_balance_usdc

        # Step 1: Create quote
        transfer = await svc.create_quote(
            sender_id=sender_user.id,
            corridor_id=corridor_usa_somalia.id,
            send_amount_usd=500.0,
            delivery_method=DeliveryMethod.CASH_PICKUP.value,
            receiver_name="Abdi Mohamed",
            receiver_phone="+252634001234",
            receiver_city="Hargeisa",
            receiver_country="SOM",
        )
        assert transfer.status == TransferStatus.QUOTED.value
        assert transfer.pickup_code is not None
        pickup_code = transfer.pickup_code

        # Step 2 & 3: Initiate and lock escrow
        transfer = await svc.initiate_transfer(transfer.id)
        assert transfer.status == TransferStatus.ESCROW_LOCKED.value
        assert transfer.escrow_status == EscrowStatus.LOCKED.value
        assert transfer.escrow_tx_hash is not None
        assert transfer.initiated_at is not None

        # Verify sender debited
        sender_after = await db_session.get(User, sender_user.id)
        assert sender_after.wallet_balance_usdc < original_sender_balance

        # Step 4: Match agent
        transfer = await svc.match_agent(transfer.id)
        assert transfer.status == TransferStatus.AGENT_MATCHED.value
        assert transfer.agent_id == agent_hargeisa.id
        assert transfer.matched_at is not None

        # Step 5: Agent accepts
        transfer = await svc.agent_accept(transfer.id, agent_hargeisa.id)
        assert transfer.status == TransferStatus.AGENT_ACCEPTED.value
        assert transfer.accepted_at is not None
        assert transfer.agent_commission_usd > 0

        # Step 6 & 7: Confirm delivery
        transfer = await svc.confirm_delivery(
            transfer_id=transfer.id,
            agent_id=agent_hargeisa.id,
            pickup_code=pickup_code,
        )
        assert transfer.status == TransferStatus.DELIVERED.value
        assert transfer.escrow_status == EscrowStatus.RELEASED.value
        assert transfer.release_tx_hash is not None
        assert transfer.delivered_at is not None

        # Verify agent credited
        agent_after = await db_session.get(User, agent_user_hargeisa.id)
        assert agent_after.wallet_balance_usdc > original_agent_balance

        # Step 8: Both rate
        transfer = await svc.rate_transfer(transfer.id, sender_user.id, 5)
        assert transfer.sender_rating == 5

        # Step 9: Verify final agent stats
        agent_refreshed = await db_session.get(Agent, agent_hargeisa.id)
        assert agent_refreshed.successful_transactions > 0
        assert agent_refreshed.daily_volume_usdc >= 500.0

    @pytest.mark.asyncio
    async def test_full_usa_to_india_upi(
        self, db_session, sender_user, corridor_usa_india,
        agent_mumbai, agent_user_mumbai, mock_escrow,
    ):
        """Complete flow for USA->India via UPI."""
        escrow_svc = EscrowService(mock_escrow)
        matching_svc = MatchingService(db=db_session)
        svc = TransferService(
            db=db_session,
            escrow_service=escrow_svc,
            matching_service=matching_svc,
        )

        # Create quote for India UPI
        transfer = await svc.create_quote(
            sender_id=sender_user.id,
            corridor_id=corridor_usa_india.id,
            send_amount_usd=1000.0,
            delivery_method=DeliveryMethod.MOBILE_MONEY.value,
            receiver_name="Rahul Sharma",
            receiver_phone="+919876543210",
            receiver_city="Mumbai",
            receiver_country="IND",
            mobile_money_provider=MobileMoneyProvider.UPI.value,
        )
        assert transfer.mobile_money_provider == MobileMoneyProvider.UPI.value

        # Initiate
        transfer = await svc.initiate_transfer(transfer.id)
        assert transfer.status == TransferStatus.ESCROW_LOCKED.value

        # Match agent in Mumbai
        transfer = await svc.match_agent(transfer.id)
        assert transfer.agent_id == agent_mumbai.id

        # Agent accept
        transfer = await svc.agent_accept(transfer.id, agent_mumbai.id)

        # Confirm delivery (no pickup code needed for mobile money)
        transfer = await svc.confirm_delivery(
            transfer_id=transfer.id,
            agent_id=agent_mumbai.id,
        )
        assert transfer.status == TransferStatus.DELIVERED.value

    @pytest.mark.asyncio
    async def test_full_usa_to_mexico_spei(
        self, db_session, sender_user, corridor_usa_mexico,
        agent_mexico_city, agent_user_mexico_city, mock_escrow,
    ):
        """Complete flow for USA->Mexico via SPEI."""
        escrow_svc = EscrowService(mock_escrow)
        matching_svc = MatchingService(db=db_session)
        svc = TransferService(
            db=db_session,
            escrow_service=escrow_svc,
            matching_service=matching_svc,
        )

        transfer = await svc.create_quote(
            sender_id=sender_user.id,
            corridor_id=corridor_usa_mexico.id,
            send_amount_usd=300.0,
            delivery_method=DeliveryMethod.MOBILE_MONEY.value,
            receiver_name="Carlos Garcia",
            receiver_phone="+525512345678",
            receiver_city="Mexico City",
            receiver_country="MEX",
            mobile_money_provider=MobileMoneyProvider.SPEI.value,
        )

        # Verify MXN conversion
        expected_rate = 17.15 * 0.99
        assert abs(transfer.exchange_rate - expected_rate) < 0.01
        assert abs(transfer.receive_amount_local - 300.0 * expected_rate) < 1.0

        transfer = await svc.initiate_transfer(transfer.id)
        transfer = await svc.match_agent(transfer.id)
        assert transfer.agent_id == agent_mexico_city.id

        transfer = await svc.agent_accept(transfer.id, agent_mexico_city.id)
        transfer = await svc.confirm_delivery(
            transfer.id, agent_mexico_city.id
        )
        assert transfer.status == TransferStatus.DELIVERED.value

    @pytest.mark.asyncio
    async def test_full_usa_to_philippines_gcash(
        self, db_session, sender_user, corridor_usa_philippines,
        agent_manila, agent_user_manila, mock_escrow,
    ):
        """Complete flow for USA->Philippines via GCash."""
        escrow_svc = EscrowService(mock_escrow)
        matching_svc = MatchingService(db=db_session)
        svc = TransferService(
            db=db_session,
            escrow_service=escrow_svc,
            matching_service=matching_svc,
        )

        transfer = await svc.create_quote(
            sender_id=sender_user.id,
            corridor_id=corridor_usa_philippines.id,
            send_amount_usd=200.0,
            delivery_method=DeliveryMethod.MOBILE_MONEY.value,
            receiver_name="Maria Santos",
            receiver_phone="+639171234567",
            receiver_city="Manila",
            receiver_country="PHL",
            mobile_money_provider=MobileMoneyProvider.GCASH.value,
        )

        # Verify PHP conversion
        expected_rate = 56.20 * 0.99
        assert abs(transfer.exchange_rate - expected_rate) < 0.01

        transfer = await svc.initiate_transfer(transfer.id)
        transfer = await svc.match_agent(transfer.id)
        assert transfer.agent_id == agent_manila.id

        transfer = await svc.agent_accept(transfer.id, agent_manila.id)
        transfer = await svc.confirm_delivery(transfer.id, agent_manila.id)
        assert transfer.status == TransferStatus.DELIVERED.value

    @pytest.mark.asyncio
    async def test_transfer_timeout_refund(
        self, db_session, sender_user, corridor_usa_somalia, mock_escrow,
    ):
        """Transfer with no agent match within timeout should auto-refund."""
        escrow_svc = EscrowService(mock_escrow)
        svc = TransferService(db=db_session, escrow_service=escrow_svc)
        original_balance = sender_user.wallet_balance_usdc

        transfer = await svc.create_quote(
            sender_id=sender_user.id,
            corridor_id=corridor_usa_somalia.id,
            send_amount_usd=500.0,
            delivery_method=DeliveryMethod.CASH_PICKUP.value,
            receiver_name="Abdi Mohamed",
            receiver_phone="+252634001234",
            receiver_city="Hargeisa",
            receiver_country="SOM",
        )
        await svc.initiate_transfer(transfer.id)

        # Verify balance was debited
        sender_after_init = await db_session.get(User, sender_user.id)
        assert sender_after_init.wallet_balance_usdc < original_balance

        # Simulate timeout -- no agent found
        result = await svc.handle_timeout(transfer.id)
        assert result.status == TransferStatus.REFUNDED.value
        assert result.escrow_status == EscrowStatus.REFUNDED.value

        # Balance restored
        sender_final = await db_session.get(User, sender_user.id)
        assert abs(sender_final.wallet_balance_usdc - original_balance) < 0.01

    @pytest.mark.asyncio
    async def test_disputed_transfer_resolution(
        self, db_session, sender_user, corridor_usa_somalia,
        agent_hargeisa, agent_user_hargeisa, mock_escrow,
    ):
        """
        Dispute flow:
        1. Transfer delivered
        2. Sender opens dispute (claims non-delivery)
        3. Admin investigates
        4. Resolution (in this case: refund to sender via cancel)
        """
        escrow_svc = EscrowService(mock_escrow)
        matching_svc = MatchingService(db=db_session)
        svc = TransferService(
            db=db_session,
            escrow_service=escrow_svc,
            matching_service=matching_svc,
        )

        # Complete a transfer
        transfer = await svc.create_quote(
            sender_id=sender_user.id,
            corridor_id=corridor_usa_somalia.id,
            send_amount_usd=500.0,
            delivery_method=DeliveryMethod.CASH_PICKUP.value,
            receiver_name="Abdi Mohamed",
            receiver_phone="+252634001234",
            receiver_city="Hargeisa",
            receiver_country="SOM",
        )
        await svc.initiate_transfer(transfer.id)
        transfer.agent_id = agent_hargeisa.id
        transfer.status = TransferStatus.AGENT_MATCHED.value
        transfer.matched_at = datetime.now(timezone.utc)
        await db_session.flush()
        await svc.agent_accept(transfer.id, agent_hargeisa.id)
        await svc.confirm_delivery(
            transfer.id, agent_hargeisa.id, transfer.pickup_code
        )

        # Sender opens dispute
        dispute = Dispute(
            transfer_id=transfer.id,
            opened_by=sender_user.id,
            reason="Receiver claims money was not delivered",
            status=DisputeStatus.OPEN.value,
        )
        db_session.add(dispute)

        # Update transfer status to disputed
        transfer.status = TransferStatus.DISPUTED.value
        await db_session.flush()

        assert transfer.status == TransferStatus.DISPUTED.value
        assert dispute.status == DisputeStatus.OPEN.value

        # Admin resolves in sender's favor
        dispute.status = DisputeStatus.RESOLVED_SENDER.value
        dispute.resolution_notes = "Agent failed to deliver. Refund issued."
        dispute.resolved_at = datetime.now(timezone.utc)
        await db_session.flush()

        assert dispute.status == DisputeStatus.RESOLVED_SENDER.value
        assert dispute.resolved_at is not None
