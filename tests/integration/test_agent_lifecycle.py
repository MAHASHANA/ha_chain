"""Integration tests for agent lifecycle: register, stake, accept, deliver, rate."""

import json
import pytest
from datetime import datetime, timezone

from app.enums import (
    AgentStatus, DeliveryMethod, MobileMoneyProvider, TransferStatus,
    EscrowStatus,
)
from app.models.models import Agent, User
from app.services.transfer_service import TransferService
from app.services.matching_service import MatchingService
from app.services.escrow_service import EscrowService
from tests.mocks.mock_blockchain import MockEscrowService, MockStakingService
from tests.factories import UserFactory, AgentFactory


class TestAgentLifecycle:
    """Tests for the complete agent lifecycle."""

    @pytest.mark.asyncio
    async def test_register_stake_accept_deliver_rate(
        self, db_session, sender_user, corridor_usa_somalia, mock_escrow, mock_staking,
    ):
        """
        Full agent lifecycle:
        1. New user registers as agent
        2. Agent stakes collateral
        3. Agent goes online
        4. Transfer comes in, agent is matched
        5. Agent accepts and delivers
        6. Agent gets rated
        7. Agent stats updated
        """
        # Step 1: Create agent user and register as agent
        agent_user = UserFactory.build(
            country="SOM",
            wallet_address="G" + "X" * 55,
            wallet_balance_usdc=10000.0,
        )
        db_session.add(agent_user)
        await db_session.flush()

        agent = Agent(
            user_id=agent_user.id,
            city="Hargeisa",
            country="SOM",
            status=AgentStatus.PENDING.value,
            is_online=False,
            delivery_methods=json.dumps([
                DeliveryMethod.CASH_PICKUP.value,
                DeliveryMethod.MOBILE_MONEY.value,
            ]),
            supported_providers=json.dumps([
                MobileMoneyProvider.ZAAD.value,
            ]),
            stake_amount_usdc=0.0,
        )
        db_session.add(agent)
        await db_session.flush()

        assert agent.status == AgentStatus.PENDING.value

        # Step 2: Stake collateral
        tx_hash = await mock_staking.stake(
            agent_id=agent.id,
            amount_usdc=1000.0,
            wallet_address=agent_user.wallet_address,
        )
        assert tx_hash is not None

        agent.stake_amount_usdc = 1000.0
        agent.staking_tx_hash = tx_hash
        agent.status = AgentStatus.ACTIVE.value
        await db_session.flush()

        stake_info = await mock_staking.get_stake_info(agent.id)
        assert stake_info["staked_amount_usdc"] == 1000.0
        assert stake_info["status"] == "active"

        # Step 3: Go online
        agent.is_online = True
        await db_session.flush()

        # Step 4: Transfer comes in, agent matched
        escrow_svc = EscrowService(mock_escrow)
        matching_svc = MatchingService(db=db_session)
        svc = TransferService(
            db=db_session,
            escrow_service=escrow_svc,
            matching_service=matching_svc,
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
        await svc.initiate_transfer(transfer.id)
        transfer = await svc.match_agent(transfer.id)
        assert transfer.agent_id == agent.id

        # Step 5: Accept and deliver
        transfer = await svc.agent_accept(transfer.id, agent.id)
        assert transfer.status == TransferStatus.AGENT_ACCEPTED.value

        transfer = await svc.confirm_delivery(
            transfer.id, agent.id, transfer.pickup_code
        )
        assert transfer.status == TransferStatus.DELIVERED.value

        # Step 6: Get rated
        transfer = await svc.rate_transfer(transfer.id, sender_user.id, 4)
        assert transfer.sender_rating == 4

        # Step 7: Verify agent stats
        refreshed_agent = await db_session.get(Agent, agent.id)
        assert refreshed_agent.total_transactions >= 1
        assert refreshed_agent.successful_transactions >= 1
        assert refreshed_agent.daily_volume_usdc >= 500.0

    @pytest.mark.asyncio
    async def test_agent_stake_and_slash(
        self, db_session, mock_staking,
    ):
        """Agent stake should be slashable for bad behavior."""
        agent_user = UserFactory.build(country="SOM", wallet_address="G" + "Z" * 55)
        db_session.add(agent_user)
        await db_session.flush()

        agent = Agent(
            user_id=agent_user.id,
            city="Hargeisa",
            country="SOM",
            status=AgentStatus.ACTIVE.value,
        )
        db_session.add(agent)
        await db_session.flush()

        # Stake
        await mock_staking.stake(agent.id, 1000.0, agent_user.wallet_address)

        # Slash for failed delivery
        await mock_staking.slash(agent.id, 200.0, "Failed to deliver transfer T-123")

        info = await mock_staking.get_stake_info(agent.id)
        assert info["staked_amount_usdc"] == 800.0
        assert info["total_slashed_usdc"] == 200.0
        assert info["slash_count"] == 1

        history = await mock_staking.get_slash_history(agent.id)
        assert len(history) == 1
        assert history[0]["amount_usdc"] == 200.0
        assert "Failed to deliver" in history[0]["reason"]

    @pytest.mark.asyncio
    async def test_agent_unstake(
        self, db_session, mock_staking,
    ):
        """Agent in good standing should be able to unstake."""
        agent_user = UserFactory.build(country="SOM", wallet_address="G" + "Y" * 55)
        db_session.add(agent_user)
        await db_session.flush()

        agent = Agent(
            user_id=agent_user.id,
            city="Hargeisa",
            country="SOM",
            status=AgentStatus.ACTIVE.value,
        )
        db_session.add(agent)
        await db_session.flush()

        await mock_staking.stake(agent.id, 500.0, agent_user.wallet_address)
        tx_hash = await mock_staking.unstake(agent.id)

        assert tx_hash is not None
        info = await mock_staking.get_stake_info(agent.id)
        assert info["status"] == "unstaked"

    @pytest.mark.asyncio
    async def test_agent_offline_not_matched(
        self, db_session, sender_user, corridor_usa_somalia, mock_escrow,
    ):
        """Offline agent should not be matched to transfers."""
        agent_user = UserFactory.build(country="SOM", wallet_address="G" + "W" * 55)
        db_session.add(agent_user)
        await db_session.flush()

        agent = Agent(
            user_id=agent_user.id,
            city="Hargeisa",
            country="SOM",
            status=AgentStatus.ACTIVE.value,
            is_online=False,  # Offline
            delivery_methods=json.dumps([DeliveryMethod.CASH_PICKUP.value]),
        )
        db_session.add(agent)
        await db_session.flush()

        escrow_svc = EscrowService(mock_escrow)
        matching_svc = MatchingService(db=db_session)
        svc = TransferService(
            db=db_session,
            escrow_service=escrow_svc,
            matching_service=matching_svc,
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
        await svc.initiate_transfer(transfer.id)

        transfer = await svc.match_agent(transfer.id)
        # Should not have matched the offline agent
        assert transfer.agent_id is None or transfer.status != TransferStatus.AGENT_MATCHED.value

    @pytest.mark.asyncio
    async def test_agent_multiple_transfers(
        self, db_session, sender_user, corridor_usa_somalia,
        agent_hargeisa, agent_user_hargeisa, mock_escrow,
    ):
        """Agent should handle multiple sequential transfers correctly."""
        escrow_svc = EscrowService(mock_escrow)
        matching_svc = MatchingService(db=db_session)
        svc = TransferService(
            db=db_session,
            escrow_service=escrow_svc,
            matching_service=matching_svc,
        )

        original_txn_count = agent_hargeisa.total_transactions

        for i in range(3):
            transfer = await svc.create_quote(
                sender_id=sender_user.id,
                corridor_id=corridor_usa_somalia.id,
                send_amount_usd=100.0,
                delivery_method=DeliveryMethod.CASH_PICKUP.value,
                receiver_name=f"Receiver {i}",
                receiver_phone=f"+25263400{i:04d}",
                receiver_city="Hargeisa",
                receiver_country="SOM",
            )
            await svc.initiate_transfer(transfer.id)
            transfer = await svc.match_agent(transfer.id)
            transfer = await svc.agent_accept(transfer.id, agent_hargeisa.id)
            await svc.confirm_delivery(
                transfer.id, agent_hargeisa.id, transfer.pickup_code
            )

        refreshed = await db_session.get(Agent, agent_hargeisa.id)
        assert refreshed.total_transactions == original_txn_count + 3
        assert refreshed.daily_volume_usdc >= 300.0
