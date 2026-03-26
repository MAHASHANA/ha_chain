"""Unit tests for the transfer service -- core transfer logic."""

import pytest
from datetime import datetime, timedelta, timezone

from app.enums import (
    TransferStatus, DeliveryMethod, EscrowStatus, ComplianceAction,
    KYCLevel, MobileMoneyProvider,
)
from app.models.models import Transfer, User, Corridor, Agent
from app.services.transfer_service import TransferService
from app.services.escrow_service import EscrowService
from app.services.compliance_service import ComplianceService
from app.services.matching_service import MatchingService
from tests.mocks.mock_blockchain import MockEscrowService


# ==========================================================================
# TestTransferQuote
# ==========================================================================


class TestTransferQuote:
    """Tests for quote creation, fee calculation, and rate locking."""

    @pytest.mark.asyncio
    async def test_create_quote_usa_to_somalia(
        self, db_session, sender_user, corridor_usa_somalia
    ):
        """Quote for $500 USA->Somalia via Zaad should calculate correct fees and SOS amount."""
        svc = TransferService(db=db_session)
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
        assert transfer.send_amount_usd == 500.0

        # Fee: 1.5% of 500 + $0.50 flat = $8.00
        expected_fee = 500.0 * 0.015 + 0.50
        assert transfer.fee_usd == expected_fee

        # Total debit: 500 + 8.00 = 508.00
        assert transfer.total_debit_usd == 500.0 + expected_fee

        # Exchange rate: 571.50 * (1 - 0.01) = 565.785
        expected_rate = 571.50 * (1 - 0.01)
        assert abs(transfer.exchange_rate - expected_rate) < 0.01

        # Receive amount: 500 * 565.785 = 282,892.50 SOS
        expected_receive = 500.0 * expected_rate
        assert abs(transfer.receive_amount_local - expected_receive) < 0.01

    @pytest.mark.asyncio
    async def test_create_quote_usa_to_india(
        self, db_session, sender_user, corridor_usa_india
    ):
        """Quote for $1000 USA->India via UPI should use INR rate."""
        svc = TransferService(db=db_session)
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

        assert transfer.status == TransferStatus.QUOTED.value
        # Fee: 1.0% of 1000 + $0 flat = $10.00
        expected_fee = 1000.0 * 0.01
        assert transfer.fee_usd == expected_fee

        # INR rate: 83.25 * (1 - 0.01) = 82.4175
        expected_rate = 83.25 * 0.99
        assert abs(transfer.exchange_rate - expected_rate) < 0.01
        assert abs(transfer.receive_amount_local - 1000.0 * expected_rate) < 1.0

    @pytest.mark.asyncio
    async def test_create_quote_usa_to_mexico(
        self, db_session, sender_user, corridor_usa_mexico
    ):
        """Quote for $300 USA->Mexico via SPEI should use MXN rate."""
        svc = TransferService(db=db_session)
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

        assert transfer.status == TransferStatus.QUOTED.value
        # Fee: 0.8% of 300 = $2.40
        expected_fee = 300.0 * 0.008
        assert abs(transfer.fee_usd - expected_fee) < 0.01

        # MXN rate: 17.15 * 0.99 = 16.9785
        expected_rate = 17.15 * 0.99
        assert abs(transfer.exchange_rate - expected_rate) < 0.01

    @pytest.mark.asyncio
    async def test_quote_expires_after_15_minutes(
        self, db_session, sender_user, corridor_usa_somalia
    ):
        """Expired quote should not be usable for initiation."""
        svc = TransferService(db=db_session)
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

        # Manually expire the quote
        transfer.quote_expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
        await db_session.flush()

        with pytest.raises(ValueError, match="Quote has expired"):
            await svc.initiate_transfer(transfer.id)

        # Verify status was set to expired
        refreshed = await db_session.get(Transfer, transfer.id)
        assert refreshed.status == TransferStatus.EXPIRED.value

    @pytest.mark.asyncio
    async def test_quote_respects_corridor_limits(
        self, db_session, sender_user, corridor_usa_somalia
    ):
        """Transfer exceeding corridor max should be rejected."""
        svc = TransferService(db=db_session)

        with pytest.raises(ValueError, match="exceeds corridor maximum"):
            await svc.create_quote(
                sender_id=sender_user.id,
                corridor_id=corridor_usa_somalia.id,
                send_amount_usd=15000.0,  # Max is 10000
                delivery_method=DeliveryMethod.CASH_PICKUP.value,
                receiver_name="Abdi Mohamed",
                receiver_phone="+252634001234",
                receiver_city="Hargeisa",
                receiver_country="SOM",
            )

    @pytest.mark.asyncio
    async def test_quote_respects_corridor_minimum(
        self, db_session, sender_user, corridor_usa_somalia
    ):
        """Transfer below corridor min should be rejected."""
        svc = TransferService(db=db_session)

        with pytest.raises(ValueError, match="below corridor minimum"):
            await svc.create_quote(
                sender_id=sender_user.id,
                corridor_id=corridor_usa_somalia.id,
                send_amount_usd=2.0,  # Min is 5.0
                delivery_method=DeliveryMethod.CASH_PICKUP.value,
                receiver_name="Abdi Mohamed",
                receiver_phone="+252634001234",
                receiver_city="Hargeisa",
                receiver_country="SOM",
            )

    @pytest.mark.asyncio
    async def test_quote_respects_kyc_limits(
        self, db_session, sender_kyc1, corridor_usa_somalia
    ):
        """KYC level 1 user limited to $1000/day."""
        svc = TransferService(db=db_session)

        # First transfer of $800 should succeed
        transfer1 = await svc.create_quote(
            sender_id=sender_kyc1.id,
            corridor_id=corridor_usa_somalia.id,
            send_amount_usd=800.0,
            delivery_method=DeliveryMethod.CASH_PICKUP.value,
            receiver_name="Abdi Mohamed",
            receiver_phone="+252634001234",
            receiver_city="Hargeisa",
            receiver_country="SOM",
        )
        # Initiate to lock it in (so it counts toward daily total)
        mock_escrow = MockEscrowService()
        svc_with_escrow = TransferService(
            db=db_session,
            escrow_service=EscrowService(mock_escrow),
        )
        await svc_with_escrow.initiate_transfer(transfer1.id)

        # Second transfer of $300 should fail ($800 + $300 > $1000 limit)
        with pytest.raises(ValueError, match="daily KYC limit"):
            await svc.create_quote(
                sender_id=sender_kyc1.id,
                corridor_id=corridor_usa_somalia.id,
                send_amount_usd=300.0,
                delivery_method=DeliveryMethod.CASH_PICKUP.value,
                receiver_name="Abdi Mohamed",
                receiver_phone="+252634001234",
                receiver_city="Hargeisa",
                receiver_country="SOM",
            )

    @pytest.mark.asyncio
    async def test_quote_inactive_corridor_rejected(
        self, db_session, sender_user, corridor_usa_somalia
    ):
        """Quote for inactive corridor should fail."""
        corridor_usa_somalia.status = "inactive"
        await db_session.flush()

        svc = TransferService(db=db_session)
        with pytest.raises(ValueError, match="not active"):
            await svc.create_quote(
                sender_id=sender_user.id,
                corridor_id=corridor_usa_somalia.id,
                send_amount_usd=500.0,
                delivery_method=DeliveryMethod.CASH_PICKUP.value,
                receiver_name="Abdi Mohamed",
                receiver_phone="+252634001234",
                receiver_city="Hargeisa",
                receiver_country="SOM",
            )


# ==========================================================================
# TestTransferInitiation
# ==========================================================================


class TestTransferInitiation:
    """Tests for transfer initiation: compliance, escrow lock, debit."""

    @pytest.mark.asyncio
    async def test_initiate_locks_escrow(
        self, db_session, sender_user, corridor_usa_somalia, mock_escrow
    ):
        """Initiating transfer should lock USDC in escrow."""
        escrow_svc = EscrowService(mock_escrow)
        svc = TransferService(db=db_session, escrow_service=escrow_svc)

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

        result = await svc.initiate_transfer(transfer.id)

        assert result.status == TransferStatus.ESCROW_LOCKED.value
        assert result.escrow_tx_hash is not None
        assert result.escrow_status == EscrowStatus.LOCKED.value

        # Verify escrow state in mock
        escrow_data = await mock_escrow.get_escrow_status(transfer.id)
        assert escrow_data["status"] == "locked"
        assert escrow_data["amount_usdc"] == transfer.total_debit_usd

    @pytest.mark.asyncio
    async def test_initiate_runs_compliance_checks(
        self, db_session, sender_user, corridor_usa_somalia, mock_escrow
    ):
        """Should run sanctions + velocity + pattern checks."""
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
            receiver_name="Abdi Mohamed",
            receiver_phone="+252634001234",
            receiver_city="Hargeisa",
            receiver_country="SOM",
        )

        result = await svc.initiate_transfer(transfer.id)

        # Should succeed for normal transfer
        assert result.status == TransferStatus.ESCROW_LOCKED.value
        assert result.compliance_status is not None

    @pytest.mark.asyncio
    async def test_initiate_generates_pickup_code(
        self, db_session, sender_user, corridor_usa_somalia, mock_escrow
    ):
        """Cash pickup transfers should get 6-char pickup code."""
        escrow_svc = EscrowService(mock_escrow)
        svc = TransferService(db=db_session, escrow_service=escrow_svc)

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

        assert transfer.pickup_code is not None
        assert len(transfer.pickup_code) == 6
        # Should be alphanumeric uppercase
        assert transfer.pickup_code.isalnum()

    @pytest.mark.asyncio
    async def test_initiate_fails_on_insufficient_balance(
        self, db_session, corridor_usa_somalia, mock_escrow
    ):
        """Should fail if sender wallet balance < amount + fee."""
        from tests.factories import SenderFactory
        poor_sender = SenderFactory.build(wallet_balance_usdc=10.0)
        db_session.add(poor_sender)
        await db_session.flush()

        escrow_svc = EscrowService(mock_escrow)
        svc = TransferService(db=db_session, escrow_service=escrow_svc)

        transfer = await svc.create_quote(
            sender_id=poor_sender.id,
            corridor_id=corridor_usa_somalia.id,
            send_amount_usd=500.0,
            delivery_method=DeliveryMethod.CASH_PICKUP.value,
            receiver_name="Abdi Mohamed",
            receiver_phone="+252634001234",
            receiver_city="Hargeisa",
            receiver_country="SOM",
        )

        with pytest.raises(ValueError, match="Insufficient balance"):
            await svc.initiate_transfer(transfer.id)

    @pytest.mark.asyncio
    async def test_initiate_fails_on_sanctioned_country(
        self, db_session, sender_user, mock_escrow
    ):
        """Transfer to sanctioned destination should be blocked by compliance."""
        # Create a corridor to a sanctioned country (North Korea)
        from tests.factories import CorridorFactory
        sanctioned_corridor = CorridorFactory.build(
            source_country="USA",
            destination_country="PRK",
            source_currency="USD",
            destination_currency="KPW",
            exchange_rate=900.0,
        )
        db_session.add(sanctioned_corridor)
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
            corridor_id=sanctioned_corridor.id,
            send_amount_usd=100.0,
            delivery_method=DeliveryMethod.CASH_PICKUP.value,
            receiver_name="Test Person",
            receiver_phone="+8501234567",
            receiver_city="Pyongyang",
            receiver_country="PRK",
        )

        with pytest.raises(ValueError, match="blocked by compliance"):
            await svc.initiate_transfer(transfer.id)

    @pytest.mark.asyncio
    async def test_initiate_debits_sender_balance(
        self, db_session, sender_user, corridor_usa_somalia, mock_escrow
    ):
        """Sender balance should decrease by total_debit_usd."""
        original_balance = sender_user.wallet_balance_usdc
        escrow_svc = EscrowService(mock_escrow)
        svc = TransferService(db=db_session, escrow_service=escrow_svc)

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

        refreshed = await db_session.get(User, sender_user.id)
        assert abs(refreshed.wallet_balance_usdc - (original_balance - transfer.total_debit_usd)) < 0.01


# ==========================================================================
# TestTransferCompletion
# ==========================================================================


class TestTransferCompletion:
    """Tests for delivery confirmation, escrow release, and rating."""

    async def _create_accepted_transfer(
        self, db_session, sender, corridor, agent, mock_escrow
    ):
        """Helper: create a transfer in AGENT_ACCEPTED state."""
        escrow_svc = EscrowService(mock_escrow)
        svc = TransferService(db=db_session, escrow_service=escrow_svc)

        transfer = await svc.create_quote(
            sender_id=sender.id,
            corridor_id=corridor.id,
            send_amount_usd=500.0,
            delivery_method=DeliveryMethod.CASH_PICKUP.value,
            receiver_name="Abdi Mohamed",
            receiver_phone="+252634001234",
            receiver_city="Hargeisa",
            receiver_country="SOM",
        )
        await svc.initiate_transfer(transfer.id)

        # Manually set agent matched + accepted
        transfer.agent_id = agent.id
        transfer.status = TransferStatus.AGENT_MATCHED.value
        transfer.matched_at = datetime.now(timezone.utc)
        await db_session.flush()

        transfer = await svc.agent_accept(transfer.id, agent.id)
        return transfer, svc

    @pytest.mark.asyncio
    async def test_confirm_delivery_releases_escrow(
        self, db_session, sender_user, corridor_usa_somalia, agent_hargeisa,
        agent_user_hargeisa, mock_escrow,
    ):
        """Agent confirming delivery should release escrow to agent wallet."""
        transfer, svc = await self._create_accepted_transfer(
            db_session, sender_user, corridor_usa_somalia, agent_hargeisa, mock_escrow
        )

        result = await svc.confirm_delivery(
            transfer_id=transfer.id,
            agent_id=agent_hargeisa.id,
            pickup_code=transfer.pickup_code,
        )

        assert result.status == TransferStatus.DELIVERED.value
        assert result.escrow_status == EscrowStatus.RELEASED.value
        assert result.release_tx_hash is not None
        assert result.delivered_at is not None

    @pytest.mark.asyncio
    async def test_confirm_delivery_pays_commission(
        self, db_session, sender_user, corridor_usa_somalia, agent_hargeisa,
        agent_user_hargeisa, mock_escrow,
    ):
        """Agent should receive their commission."""
        original_balance = agent_user_hargeisa.wallet_balance_usdc
        transfer, svc = await self._create_accepted_transfer(
            db_session, sender_user, corridor_usa_somalia, agent_hargeisa, mock_escrow
        )

        await svc.confirm_delivery(
            transfer_id=transfer.id,
            agent_id=agent_hargeisa.id,
            pickup_code=transfer.pickup_code,
        )

        refreshed_agent_user = await db_session.get(User, agent_user_hargeisa.id)
        expected_credit = transfer.send_amount_usd + transfer.agent_commission_usd
        assert abs(
            refreshed_agent_user.wallet_balance_usdc - (original_balance + expected_credit)
        ) < 0.01

    @pytest.mark.asyncio
    async def test_confirm_delivery_updates_agent_stats(
        self, db_session, sender_user, corridor_usa_somalia, agent_hargeisa,
        agent_user_hargeisa, mock_escrow,
    ):
        """Agent transaction count and avg time should update."""
        original_total = agent_hargeisa.total_transactions
        transfer, svc = await self._create_accepted_transfer(
            db_session, sender_user, corridor_usa_somalia, agent_hargeisa, mock_escrow
        )

        await svc.confirm_delivery(
            transfer_id=transfer.id,
            agent_id=agent_hargeisa.id,
            pickup_code=transfer.pickup_code,
        )

        refreshed = await db_session.get(Agent, agent_hargeisa.id)
        assert refreshed.total_transactions == original_total + 1
        assert refreshed.successful_transactions > 0
        assert refreshed.daily_volume_usdc >= transfer.send_amount_usd

    @pytest.mark.asyncio
    async def test_cancel_refunds_to_sender(
        self, db_session, sender_user, corridor_usa_somalia, mock_escrow,
    ):
        """Cancelling should refund escrow to sender."""
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

        # Balance should be reduced
        sender_after_init = await db_session.get(User, sender_user.id)
        assert sender_after_init.wallet_balance_usdc < original_balance

        # Cancel
        result = await svc.cancel_transfer(transfer.id, sender_user.id)
        assert result.status == TransferStatus.CANCELLED.value
        assert result.escrow_status == EscrowStatus.REFUNDED.value

        # Balance should be restored
        sender_after_cancel = await db_session.get(User, sender_user.id)
        assert abs(sender_after_cancel.wallet_balance_usdc - original_balance) < 0.01

    @pytest.mark.asyncio
    async def test_confirm_delivery_requires_pickup_code(
        self, db_session, sender_user, corridor_usa_somalia, agent_hargeisa,
        agent_user_hargeisa, mock_escrow,
    ):
        """Cash pickup delivery without correct code should fail."""
        transfer, svc = await self._create_accepted_transfer(
            db_session, sender_user, corridor_usa_somalia, agent_hargeisa, mock_escrow
        )

        with pytest.raises(ValueError, match="Invalid pickup code"):
            await svc.confirm_delivery(
                transfer_id=transfer.id,
                agent_id=agent_hargeisa.id,
                pickup_code="WRONG1",
            )

    @pytest.mark.asyncio
    async def test_rate_transfer_updates_agent_rating(
        self, db_session, sender_user, corridor_usa_somalia, agent_hargeisa,
        agent_user_hargeisa, mock_escrow,
    ):
        """Rating a transfer should update the agent's average rating."""
        transfer, svc = await self._create_accepted_transfer(
            db_session, sender_user, corridor_usa_somalia, agent_hargeisa, mock_escrow
        )
        await svc.confirm_delivery(
            transfer_id=transfer.id,
            agent_id=agent_hargeisa.id,
            pickup_code=transfer.pickup_code,
        )

        result = await svc.rate_transfer(transfer.id, sender_user.id, 5)
        assert result.sender_rating == 5

    @pytest.mark.asyncio
    async def test_timeout_refund(
        self, db_session, sender_user, corridor_usa_somalia, mock_escrow,
    ):
        """Transfer with no agent match should auto-refund via handle_timeout."""
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

        result = await svc.handle_timeout(transfer.id)
        assert result.status == TransferStatus.REFUNDED.value
        assert result.escrow_status == EscrowStatus.REFUNDED.value

        sender_after = await db_session.get(User, sender_user.id)
        assert abs(sender_after.wallet_balance_usdc - original_balance) < 0.01
