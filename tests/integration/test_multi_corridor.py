"""Integration tests for transfers across different corridors."""

import pytest

from app.enums import (
    TransferStatus, DeliveryMethod, EscrowStatus, MobileMoneyProvider,
)
from app.models.models import User
from app.services.transfer_service import TransferService
from app.services.matching_service import MatchingService
from app.services.corridor_service import CorridorService
from app.services.escrow_service import EscrowService
from tests.mocks.mock_blockchain import MockEscrowService


class TestMultiCorridorTransfers:
    """Tests for transfers across different corridors in the same session."""

    @pytest.mark.asyncio
    async def test_simultaneous_transfers_different_corridors(
        self, db_session, sender_user, all_corridors,
        agent_hargeisa, agent_mumbai, agent_mexico_city,
        agent_user_hargeisa, agent_user_mumbai, agent_user_mexico_city,
        mock_escrow,
    ):
        """
        Single sender initiates transfers to Somalia, India, and Mexico
        simultaneously. Each should route to the correct corridor with
        appropriate fees and exchange rates.
        """
        escrow_svc = EscrowService(mock_escrow)
        matching_svc = MatchingService(db=db_session)
        svc = TransferService(
            db=db_session,
            escrow_service=escrow_svc,
            matching_service=matching_svc,
        )

        # Create three transfers
        t_som = await svc.create_quote(
            sender_id=sender_user.id,
            corridor_id=all_corridors["SOM"].id,
            send_amount_usd=500.0,
            delivery_method=DeliveryMethod.CASH_PICKUP.value,
            receiver_name="Abdi Mohamed",
            receiver_phone="+252634001234",
            receiver_city="Hargeisa",
            receiver_country="SOM",
        )

        t_ind = await svc.create_quote(
            sender_id=sender_user.id,
            corridor_id=all_corridors["IND"].id,
            send_amount_usd=1000.0,
            delivery_method=DeliveryMethod.MOBILE_MONEY.value,
            receiver_name="Rahul Sharma",
            receiver_phone="+919876543210",
            receiver_city="Mumbai",
            receiver_country="IND",
            mobile_money_provider=MobileMoneyProvider.UPI.value,
        )

        t_mex = await svc.create_quote(
            sender_id=sender_user.id,
            corridor_id=all_corridors["MEX"].id,
            send_amount_usd=300.0,
            delivery_method=DeliveryMethod.MOBILE_MONEY.value,
            receiver_name="Carlos Garcia",
            receiver_phone="+525512345678",
            receiver_city="Mexico City",
            receiver_country="MEX",
            mobile_money_provider=MobileMoneyProvider.SPEI.value,
        )

        # Verify each has correct corridor-specific rates
        som_rate = 571.50 * 0.99
        ind_rate = 83.25 * 0.99
        mex_rate = 17.15 * 0.99

        assert abs(t_som.exchange_rate - som_rate) < 0.01
        assert abs(t_ind.exchange_rate - ind_rate) < 0.01
        assert abs(t_mex.exchange_rate - mex_rate) < 0.01

        # Verify each has correct corridor-specific fees
        # Somalia: 1.5% + $0.50
        assert abs(t_som.fee_usd - (500.0 * 0.015 + 0.50)) < 0.01
        # India: 1.0%
        assert abs(t_ind.fee_usd - (1000.0 * 0.01)) < 0.01
        # Mexico: 0.8%
        assert abs(t_mex.fee_usd - (300.0 * 0.008)) < 0.01

        # Initiate all three
        await svc.initiate_transfer(t_som.id)
        await svc.initiate_transfer(t_ind.id)
        await svc.initiate_transfer(t_mex.id)

        # Match each to correct agent
        t_som = await svc.match_agent(t_som.id)
        t_ind = await svc.match_agent(t_ind.id)
        t_mex = await svc.match_agent(t_mex.id)

        assert t_som.agent_id == agent_hargeisa.id
        assert t_ind.agent_id == agent_mumbai.id
        assert t_mex.agent_id == agent_mexico_city.id

        # Complete all three
        for transfer, agent in [
            (t_som, agent_hargeisa),
            (t_ind, agent_mumbai),
            (t_mex, agent_mexico_city),
        ]:
            transfer = await svc.agent_accept(transfer.id, agent.id)
            kwargs = {"transfer_id": transfer.id, "agent_id": agent.id}
            if transfer.pickup_code:
                kwargs["pickup_code"] = transfer.pickup_code
            await svc.confirm_delivery(**kwargs)

        # Verify all completed
        for tid in [t_som.id, t_ind.id, t_mex.id]:
            from app.models.models import Transfer
            t = await db_session.get(Transfer, tid)
            assert t.status == TransferStatus.DELIVERED.value

        # Verify sender balance was correctly debited for all three
        sender_after = await db_session.get(User, sender_user.id)
        total_debited = t_som.total_debit_usd + t_ind.total_debit_usd + t_mex.total_debit_usd
        expected_balance = 10000.0 - total_debited
        assert abs(sender_after.wallet_balance_usdc - expected_balance) < 0.01

    @pytest.mark.asyncio
    async def test_corridor_fee_comparison(
        self, db_session, all_corridors,
    ):
        """Verify corridors have correct relative fee ordering."""
        svc = CorridorService(db=db_session)

        fee_som = await svc.calculate_fee(all_corridors["SOM"].id, 500.0)
        fee_ind = await svc.calculate_fee(all_corridors["IND"].id, 500.0)
        fee_mex = await svc.calculate_fee(all_corridors["MEX"].id, 500.0)

        # Mexico (highest volume) should be cheapest
        # India (high volume) should be mid
        # Somalia (lower volume + flat fee) should be most expensive
        assert fee_mex["fee_usd"] < fee_ind["fee_usd"]
        assert fee_ind["fee_usd"] < fee_som["fee_usd"]

    @pytest.mark.asyncio
    async def test_receive_amounts_correct_per_corridor(
        self, db_session, all_corridors,
    ):
        """Each corridor should produce correct local currency amount."""
        svc = CorridorService(db=db_session)

        result_som = await svc.calculate_fee(all_corridors["SOM"].id, 500.0)
        result_ind = await svc.calculate_fee(all_corridors["IND"].id, 500.0)
        result_mex = await svc.calculate_fee(all_corridors["MEX"].id, 500.0)

        assert result_som["receive_currency"] == "SOS"
        assert result_ind["receive_currency"] == "INR"
        assert result_mex["receive_currency"] == "MXN"

        # SOS receive should be much larger than MXN
        assert result_som["receive_amount"] > result_ind["receive_amount"]
        assert result_ind["receive_amount"] > result_mex["receive_amount"]

    @pytest.mark.asyncio
    async def test_corridor_limits_enforced_per_corridor(
        self, db_session, sender_user, all_corridors, mock_escrow,
    ):
        """Each corridor should enforce its own limits independently."""
        # Upgrade sender to KYC level 3 so the $9000 amount isn't KYC-blocked
        from app.enums import KYCLevel
        sender_user.kyc_level = KYCLevel.FULL.value
        await db_session.flush()

        escrow_svc = EscrowService(mock_escrow)
        svc = TransferService(db=db_session, escrow_service=escrow_svc)

        # All corridors have $10,000 max. A $9000 transfer should work.
        transfer = await svc.create_quote(
            sender_id=sender_user.id,
            corridor_id=all_corridors["IND"].id,
            send_amount_usd=9000.0,
            delivery_method=DeliveryMethod.MOBILE_MONEY.value,
            receiver_name="Rahul Sharma",
            receiver_phone="+919876543210",
            receiver_city="Mumbai",
            receiver_country="IND",
            mobile_money_provider=MobileMoneyProvider.UPI.value,
        )
        assert transfer is not None

        # Over-limit should fail
        with pytest.raises(ValueError, match="exceeds corridor maximum"):
            await svc.create_quote(
                sender_id=sender_user.id,
                corridor_id=all_corridors["MEX"].id,
                send_amount_usd=15000.0,
                delivery_method=DeliveryMethod.MOBILE_MONEY.value,
                receiver_name="Carlos Garcia",
                receiver_phone="+525512345678",
                receiver_city="Mexico City",
                receiver_country="MEX",
                mobile_money_provider=MobileMoneyProvider.SPEI.value,
            )
