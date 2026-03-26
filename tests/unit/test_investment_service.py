"""Unit tests for the investment service -- buy/sell tokenized assets."""

import pytest

from app.enums import InvestmentStatus
from app.models.models import User, TokenizedAsset, Investment
from app.services.investment_service import InvestmentService
from tests.factories import UserFactory, TokenizedAssetFactory


class TestInvestmentBuy:
    """Tests for purchasing tokenized assets."""

    @pytest.mark.asyncio
    async def test_buy_asset_succeeds(
        self, db_session, sender_user, sukuk_asset,
    ):
        """Buying tokens should debit user and create investment."""
        svc = InvestmentService(db=db_session)
        original_balance = sender_user.wallet_balance_usdc

        investment = await svc.buy_asset(
            user_id=sender_user.id,
            asset_id=sukuk_asset.id,
            quantity=10.0,
        )

        assert investment.status == InvestmentStatus.ACTIVE.value
        assert investment.quantity == 10.0
        assert investment.purchase_price_usd == 10.0 * 100.0  # 10 * $100
        assert investment.current_value_usd == 1000.0

        refreshed = await db_session.get(User, sender_user.id)
        assert abs(refreshed.wallet_balance_usdc - (original_balance - 1000.0)) < 0.01

    @pytest.mark.asyncio
    async def test_buy_fails_on_insufficient_balance(
        self, db_session, sukuk_asset,
    ):
        """Should fail if user cannot afford the purchase."""
        poor_user = UserFactory.build(wallet_balance_usdc=50.0)
        db_session.add(poor_user)
        await db_session.flush()

        svc = InvestmentService(db=db_session)
        with pytest.raises(ValueError, match="Insufficient balance"):
            await svc.buy_asset(
                user_id=poor_user.id,
                asset_id=sukuk_asset.id,
                quantity=10.0,  # Would cost $1000
            )

    @pytest.mark.asyncio
    async def test_buy_fails_on_inactive_asset(
        self, db_session, sender_user,
    ):
        """Should fail if asset is not active."""
        inactive_asset = TokenizedAssetFactory.build(is_active=False, symbol="DEAD1")
        db_session.add(inactive_asset)
        await db_session.flush()

        svc = InvestmentService(db=db_session)
        with pytest.raises(ValueError, match="not available"):
            await svc.buy_asset(
                user_id=sender_user.id,
                asset_id=inactive_asset.id,
                quantity=5.0,
            )

    @pytest.mark.asyncio
    async def test_buy_fails_on_zero_quantity(
        self, db_session, sender_user, sukuk_asset,
    ):
        """Should fail on zero or negative quantity."""
        svc = InvestmentService(db=db_session)
        with pytest.raises(ValueError, match="positive"):
            await svc.buy_asset(
                user_id=sender_user.id,
                asset_id=sukuk_asset.id,
                quantity=0.0,
            )

    @pytest.mark.asyncio
    async def test_buy_multiple_positions(
        self, db_session, sender_user, sukuk_asset, real_estate_asset,
    ):
        """User should be able to buy multiple different assets."""
        svc = InvestmentService(db=db_session)

        inv1 = await svc.buy_asset(sender_user.id, sukuk_asset.id, 5.0)
        inv2 = await svc.buy_asset(sender_user.id, real_estate_asset.id, 2.0)

        assert inv1.asset_id == sukuk_asset.id
        assert inv2.asset_id == real_estate_asset.id

        positions = await svc.get_user_investments(sender_user.id)
        assert len(positions) == 2


class TestInvestmentSell:
    """Tests for selling investment positions."""

    @pytest.mark.asyncio
    async def test_sell_asset_succeeds(
        self, db_session, sender_user, sukuk_asset,
    ):
        """Selling should credit user and mark investment as sold."""
        svc = InvestmentService(db=db_session)
        investment = await svc.buy_asset(sender_user.id, sukuk_asset.id, 10.0)

        balance_after_buy = (await db_session.get(User, sender_user.id)).wallet_balance_usdc

        sold = await svc.sell_asset(investment.id, sender_user.id)

        assert sold.status == InvestmentStatus.SOLD.value
        assert sold.sold_at is not None

        # User should have been credited back
        refreshed = await db_session.get(User, sender_user.id)
        assert refreshed.wallet_balance_usdc > balance_after_buy

    @pytest.mark.asyncio
    async def test_sell_wrong_user_fails(
        self, db_session, sender_user, sukuk_asset,
    ):
        """Cannot sell someone else's investment."""
        svc = InvestmentService(db=db_session)
        investment = await svc.buy_asset(sender_user.id, sukuk_asset.id, 5.0)

        other_user = UserFactory.build()
        db_session.add(other_user)
        await db_session.flush()

        with pytest.raises(ValueError, match="does not belong"):
            await svc.sell_asset(investment.id, other_user.id)

    @pytest.mark.asyncio
    async def test_sell_already_sold_fails(
        self, db_session, sender_user, sukuk_asset,
    ):
        """Cannot sell an already-sold investment."""
        svc = InvestmentService(db=db_session)
        investment = await svc.buy_asset(sender_user.id, sukuk_asset.id, 5.0)
        await svc.sell_asset(investment.id, sender_user.id)

        with pytest.raises(ValueError, match="cannot sell"):
            await svc.sell_asset(investment.id, sender_user.id)

    @pytest.mark.asyncio
    async def test_sell_reflects_current_price(
        self, db_session, sender_user, sukuk_asset,
    ):
        """Sale value should use current asset price, not purchase price."""
        svc = InvestmentService(db=db_session)
        investment = await svc.buy_asset(sender_user.id, sukuk_asset.id, 10.0)

        # Simulate price increase
        sukuk_asset.price_per_token_usd = 120.0
        await db_session.flush()

        sold = await svc.sell_asset(investment.id, sender_user.id)

        # Current value should be 10 * $120 = $1200 (not the $1000 purchase price)
        assert sold.current_value_usd == 1200.0


class TestPortfolio:
    """Tests for portfolio valuation."""

    @pytest.mark.asyncio
    async def test_portfolio_value_calculation(
        self, db_session, sender_user, sukuk_asset, real_estate_asset,
    ):
        """Portfolio should correctly sum all active positions."""
        svc = InvestmentService(db=db_session)
        await svc.buy_asset(sender_user.id, sukuk_asset.id, 10.0)     # $1000
        await svc.buy_asset(sender_user.id, real_estate_asset.id, 4.0)  # $1000

        portfolio = await svc.get_portfolio_value(sender_user.id)

        assert portfolio["total_invested_usd"] == 2000.0
        assert portfolio["total_current_value_usd"] == 2000.0
        assert portfolio["total_return_usd"] == 0.0
        assert portfolio["positions"] == 2

    @pytest.mark.asyncio
    async def test_portfolio_with_price_change(
        self, db_session, sender_user, sukuk_asset,
    ):
        """Portfolio return should reflect asset price changes."""
        svc = InvestmentService(db=db_session)
        await svc.buy_asset(sender_user.id, sukuk_asset.id, 10.0)  # $1000

        # Price goes up 10%
        sukuk_asset.price_per_token_usd = 110.0
        await db_session.flush()

        portfolio = await svc.get_portfolio_value(sender_user.id)

        assert portfolio["total_invested_usd"] == 1000.0
        assert portfolio["total_current_value_usd"] == 1100.0
        assert portfolio["total_return_usd"] == 100.0
        assert portfolio["total_return_percent"] == 10.0

    @pytest.mark.asyncio
    async def test_empty_portfolio(self, db_session, sender_user):
        """Empty portfolio should return zeros."""
        svc = InvestmentService(db=db_session)
        portfolio = await svc.get_portfolio_value(sender_user.id)

        assert portfolio["total_invested_usd"] == 0.0
        assert portfolio["total_current_value_usd"] == 0.0
        assert portfolio["positions"] == 0
