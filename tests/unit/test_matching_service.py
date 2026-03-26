"""Unit tests for the agent matching service."""

import json
import pytest

from app.enums import (
    AgentStatus, DeliveryMethod, MobileMoneyProvider, TransferStatus,
)
from app.models.models import Agent, Transfer
from app.services.matching_service import MatchingService, AgentScore
from tests.factories import (
    AgentFactory, HargeisaAgentFactory, MumbaiAgentFactory,
    MexicoCityAgentFactory, TransferFactory,
)


class TestAgentMatching:
    """Tests for agent matching algorithm."""

    @pytest.mark.asyncio
    async def test_matches_agent_in_correct_city(
        self, db_session, corridor_usa_somalia, agent_hargeisa, sender_user,
    ):
        """Should only match agents in receiver's city."""
        # Create an agent in Mogadishu (wrong city)
        from tests.factories import UserFactory
        other_user = UserFactory.build(country="SOM")
        db_session.add(other_user)
        await db_session.flush()

        wrong_city_agent = AgentFactory.build(
            user_id=other_user.id,
            city="Mogadishu",
            country="SOM",
            delivery_methods=json.dumps([DeliveryMethod.CASH_PICKUP.value]),
        )
        db_session.add(wrong_city_agent)
        await db_session.flush()

        # Create transfer to Hargeisa
        transfer = TransferFactory.build(
            sender_id=sender_user.id,
            corridor_id=corridor_usa_somalia.id,
            receiver_city="Hargeisa",
            receiver_country="SOM",
            delivery_method=DeliveryMethod.CASH_PICKUP.value,
        )
        db_session.add(transfer)
        await db_session.flush()

        svc = MatchingService(db=db_session)
        best = await svc.find_best_agent(transfer)

        assert best is not None
        assert best.id == agent_hargeisa.id
        assert best.city == "Hargeisa"

    @pytest.mark.asyncio
    async def test_ranks_by_rating_primarily(
        self, db_session, corridor_usa_somalia, sender_user,
    ):
        """Higher rated agents should rank higher."""
        from tests.factories import UserFactory

        # Agent 1: high rating
        u1 = UserFactory.build(country="SOM")
        db_session.add(u1)
        await db_session.flush()
        agent_high = HargeisaAgentFactory.build(
            user_id=u1.id, rating=4.9, success_rate=0.95,
            avg_delivery_minutes=30.0, stake_amount_usdc=5000.0,
            commission_rate=0.005,
        )
        db_session.add(agent_high)

        # Agent 2: lower rating
        u2 = UserFactory.build(country="SOM")
        db_session.add(u2)
        await db_session.flush()
        agent_low = HargeisaAgentFactory.build(
            user_id=u2.id, rating=3.5, success_rate=0.95,
            avg_delivery_minutes=30.0, stake_amount_usdc=5000.0,
            commission_rate=0.005,
        )
        db_session.add(agent_low)
        await db_session.flush()

        transfer = TransferFactory.build(
            sender_id=sender_user.id,
            corridor_id=corridor_usa_somalia.id,
            receiver_city="Hargeisa",
            receiver_country="SOM",
            delivery_method=DeliveryMethod.CASH_PICKUP.value,
        )
        db_session.add(transfer)
        await db_session.flush()

        svc = MatchingService(db=db_session)
        ranked = await svc.get_ranked_agents(transfer)

        assert len(ranked) >= 2
        assert ranked[0].agent.id == agent_high.id
        assert ranked[0].total_score > ranked[1].total_score

    @pytest.mark.asyncio
    async def test_excludes_offline_agents(
        self, db_session, corridor_usa_somalia, sender_user,
    ):
        """Offline agents should not be matched."""
        from tests.factories import UserFactory
        u = UserFactory.build(country="SOM")
        db_session.add(u)
        await db_session.flush()

        offline_agent = HargeisaAgentFactory.build(
            user_id=u.id, is_online=False,
        )
        db_session.add(offline_agent)
        await db_session.flush()

        transfer = TransferFactory.build(
            sender_id=sender_user.id,
            corridor_id=corridor_usa_somalia.id,
            receiver_city="Hargeisa",
            receiver_country="SOM",
            delivery_method=DeliveryMethod.CASH_PICKUP.value,
        )
        db_session.add(transfer)
        await db_session.flush()

        svc = MatchingService(db=db_session)
        ranked = await svc.get_ranked_agents(transfer)

        agent_ids = [s.agent.id for s in ranked]
        assert offline_agent.id not in agent_ids

    @pytest.mark.asyncio
    async def test_excludes_agents_at_daily_limit(
        self, db_session, corridor_usa_somalia, sender_user,
    ):
        """Agents who hit daily limit should not be matched."""
        from tests.factories import UserFactory
        u = UserFactory.build(country="SOM")
        db_session.add(u)
        await db_session.flush()

        maxed_agent = HargeisaAgentFactory.build(
            user_id=u.id,
            daily_volume_usdc=9900.0,
            daily_limit_usdc=10000.0,
        )
        db_session.add(maxed_agent)
        await db_session.flush()

        transfer = TransferFactory.build(
            sender_id=sender_user.id,
            corridor_id=corridor_usa_somalia.id,
            send_amount_usd=500.0,  # 9900 + 500 > 10000
            receiver_city="Hargeisa",
            receiver_country="SOM",
            delivery_method=DeliveryMethod.CASH_PICKUP.value,
        )
        db_session.add(transfer)
        await db_session.flush()

        svc = MatchingService(db=db_session)
        ranked = await svc.get_ranked_agents(transfer)

        agent_ids = [s.agent.id for s in ranked]
        assert maxed_agent.id not in agent_ids

    @pytest.mark.asyncio
    async def test_excludes_agents_without_delivery_method(
        self, db_session, corridor_usa_somalia, sender_user,
    ):
        """Agent that doesn't handle mobile_money shouldn't match for mobile_money delivery."""
        from tests.factories import UserFactory
        u = UserFactory.build(country="SOM")
        db_session.add(u)
        await db_session.flush()

        # Agent only supports cash_pickup
        cash_only_agent = HargeisaAgentFactory.build(
            user_id=u.id,
            delivery_methods=json.dumps([DeliveryMethod.CASH_PICKUP.value]),
        )
        db_session.add(cash_only_agent)
        await db_session.flush()

        # Transfer wants mobile_money
        transfer = TransferFactory.build(
            sender_id=sender_user.id,
            corridor_id=corridor_usa_somalia.id,
            receiver_city="Hargeisa",
            receiver_country="SOM",
            delivery_method=DeliveryMethod.MOBILE_MONEY.value,
            mobile_money_provider=MobileMoneyProvider.ZAAD.value,
        )
        db_session.add(transfer)
        await db_session.flush()

        svc = MatchingService(db=db_session)
        ranked = await svc.get_ranked_agents(transfer)

        agent_ids = [s.agent.id for s in ranked]
        assert cash_only_agent.id not in agent_ids

    @pytest.mark.asyncio
    async def test_scoring_algorithm(self, db_session):
        """Test the weighted scoring: rating*0.35 + success*0.25 + speed*0.20 + stake*0.10 + price*0.10."""
        from tests.factories import UserFactory
        u = UserFactory.build(country="SOM")
        db_session.add(u)
        await db_session.flush()

        agent = HargeisaAgentFactory.build(
            user_id=u.id,
            rating=4.5,            # 4.5/5 * 0.35 = 0.315
            success_rate=0.90,     # 0.90 * 0.25 = 0.225
            avg_delivery_minutes=30.0,  # (1 - 30/120) * 0.20 = 0.15
            stake_amount_usdc=5000.0,   # 5000/10000 * 0.10 = 0.05
            commission_rate=0.005,      # (1 - 0.05) * 0.10 = 0.095
        )
        db_session.add(agent)
        await db_session.flush()

        score = AgentScore(agent)

        assert abs(score.rating_score - (4.5 / 5.0) * 0.35) < 0.001
        assert abs(score.success_score - 0.90 * 0.25) < 0.001
        assert abs(score.speed_score - (1.0 - 30.0 / 120.0) * 0.20) < 0.001
        assert abs(score.stake_score - 0.5 * 0.10) < 0.001
        assert abs(score.price_score - (1.0 - 0.05) * 0.10) < 0.001

        expected_total = (
            score.rating_score
            + score.success_score
            + score.speed_score
            + score.stake_score
            + score.price_score
        )
        assert abs(score.total_score - expected_total) < 0.001

    @pytest.mark.asyncio
    async def test_fallback_when_no_agents(
        self, db_session, corridor_usa_somalia, sender_user,
    ):
        """Should return None when no agents available."""
        transfer = TransferFactory.build(
            sender_id=sender_user.id,
            corridor_id=corridor_usa_somalia.id,
            receiver_city="Burao",  # No agents in Burao
            receiver_country="SOM",
            delivery_method=DeliveryMethod.CASH_PICKUP.value,
        )
        db_session.add(transfer)
        await db_session.flush()

        svc = MatchingService(db=db_session)
        best = await svc.find_best_agent(transfer)
        assert best is None

    @pytest.mark.asyncio
    async def test_multi_corridor_matching(
        self, db_session, all_corridors, sender_user,
        agent_hargeisa, agent_mumbai, agent_mexico_city,
    ):
        """Should find correct agents for India (UPI), Mexico (SPEI), Somalia (Zaad)."""
        svc = MatchingService(db=db_session)

        # Somalia transfer
        t_som = TransferFactory.build(
            sender_id=sender_user.id,
            corridor_id=all_corridors["SOM"].id,
            receiver_city="Hargeisa",
            receiver_country="SOM",
            delivery_method=DeliveryMethod.CASH_PICKUP.value,
        )
        db_session.add(t_som)

        # India transfer
        t_ind = TransferFactory.build(
            sender_id=sender_user.id,
            corridor_id=all_corridors["IND"].id,
            receiver_city="Mumbai",
            receiver_country="IND",
            delivery_method=DeliveryMethod.MOBILE_MONEY.value,
            mobile_money_provider=MobileMoneyProvider.UPI.value,
        )
        db_session.add(t_ind)

        # Mexico transfer
        t_mex = TransferFactory.build(
            sender_id=sender_user.id,
            corridor_id=all_corridors["MEX"].id,
            receiver_city="Mexico City",
            receiver_country="MEX",
            delivery_method=DeliveryMethod.MOBILE_MONEY.value,
            mobile_money_provider=MobileMoneyProvider.SPEI.value,
        )
        db_session.add(t_mex)
        await db_session.flush()

        best_som = await svc.find_best_agent(t_som)
        best_ind = await svc.find_best_agent(t_ind)
        best_mex = await svc.find_best_agent(t_mex)

        assert best_som is not None
        assert best_som.city == "Hargeisa"
        assert best_ind is not None
        assert best_ind.city == "Mumbai"
        assert best_mex is not None
        assert best_mex.city == "Mexico City"
