"""Integration tests for investment flows: buy, hold, sell tokenized assets."""

import pytest

from app.enums import InvestmentStatus
from app.models.models import User, TokenizedAsset, Investment
from app.services.investment_service import InvestmentService
from app.services.escrow_service import EscrowService
from tests.mocks.mock_blockchain import MockEscrowService
from tests.factories import UserFactory, TokenizedAssetFactory


class TestInvestmentFlow:
    """Integration tests for the full investment lifecycle."""

    @pytest.mark.asyncio
    async def test_buy_hold_sell_sukuk(
        self, db_session, sender_user, sukuk_asset, mock_escrow,
    ):
        """
        Complete investment flow:
        1. User buys 10 sukuk tokens at $100 each ($1000 total)
        2. Price appreciates to $120
        3. User sells, receives $1200
        4. Net profit: $200
        """
        escrow_svc = EscrowService(mock_escrow)
        svc = InvestmentService(db=db_session, escrow_service=escrow_svc)
        original_balance = sender_user.wallet_balance_usdc

        # Step 1: Buy
        investment = await svc.buy_asset(
            user_id=sender_user.id,
            asset_id=sukuk_asset.id,
            quantity=10.0,
        )
        assert investment.status == InvestmentStatus.ACTIVE.value
        assert investment.purchase_price_usd == 1000.0

        sender_after_buy = await db_session.get(User, sender_user.id)
        assert abs(sender_after_buy.wallet_balance_usdc - (original_balance - 1000.0)) < 0.01

        # Step 2: Price appreciates
        sukuk_asset.price_per_token_usd = 120.0
        await db_session.flush()

        portfolio = await svc.get_portfolio_value(sender_user.id)
        assert portfolio["total_current_value_usd"] == 1200.0
        assert portfolio["total_return_usd"] == 200.0
        assert portfolio["total_return_percent"] == 20.0

        # Step 3: Sell
        sold = await svc.sell_asset(investment.id, sender_user.id)
        assert sold.status == InvestmentStatus.SOLD.value
        assert sold.current_value_usd == 1200.0

        # Step 4: Verify profit
        sender_final = await db_session.get(User, sender_user.id)
        assert abs(sender_final.wallet_balance_usdc - (original_balance + 200.0)) < 0.01

    @pytest.mark.asyncio
    async def test_buy_hold_sell_real_estate(
        self, db_session, sender_user, real_estate_asset, mock_escrow,
    ):
        """Buy and sell real estate tokens."""
        escrow_svc = EscrowService(mock_escrow)
        svc = InvestmentService(db=db_session, escrow_service=escrow_svc)

        investment = await svc.buy_asset(
            user_id=sender_user.id,
            asset_id=real_estate_asset.id,
            quantity=4.0,  # 4 * $250 = $1000
        )
        assert investment.purchase_price_usd == 1000.0

        # Sell at same price (no gain)
        sold = await svc.sell_asset(investment.id, sender_user.id)
        assert sold.current_value_usd == 1000.0

    @pytest.mark.asyncio
    async def test_multiple_buy_and_portfolio(
        self, db_session, sender_user, sukuk_asset, real_estate_asset, mock_escrow,
    ):
        """User builds a diversified portfolio across asset types."""
        escrow_svc = EscrowService(mock_escrow)
        svc = InvestmentService(db=db_session, escrow_service=escrow_svc)

        # Buy sukuk
        inv1 = await svc.buy_asset(sender_user.id, sukuk_asset.id, 5.0)    # $500
        # Buy real estate
        inv2 = await svc.buy_asset(sender_user.id, real_estate_asset.id, 2.0)  # $500

        # Verify portfolio
        portfolio = await svc.get_portfolio_value(sender_user.id)
        assert portfolio["total_invested_usd"] == 1000.0
        assert portfolio["positions"] == 2

        # Sukuk goes up, real estate goes down
        sukuk_asset.price_per_token_usd = 120.0
        real_estate_asset.price_per_token_usd = 200.0
        await db_session.flush()

        portfolio = await svc.get_portfolio_value(sender_user.id)
        # Sukuk: 5 * 120 = 600, Real estate: 2 * 200 = 400
        assert portfolio["total_current_value_usd"] == 1000.0
        # Net: no change overall
        assert portfolio["total_return_usd"] == 0.0

    @pytest.mark.asyncio
    async def test_sell_partial_portfolio(
        self, db_session, sender_user, sukuk_asset, real_estate_asset, mock_escrow,
    ):
        """Sell one position while keeping another."""
        escrow_svc = EscrowService(mock_escrow)
        svc = InvestmentService(db=db_session, escrow_service=escrow_svc)

        inv1 = await svc.buy_asset(sender_user.id, sukuk_asset.id, 10.0)
        inv2 = await svc.buy_asset(sender_user.id, real_estate_asset.id, 4.0)

        # Sell sukuk only
        await svc.sell_asset(inv1.id, sender_user.id)

        # Check remaining positions
        active = await svc.get_user_investments(
            sender_user.id, status=InvestmentStatus.ACTIVE.value
        )
        assert len(active) == 1
        assert active[0].asset_id == real_estate_asset.id

    @pytest.mark.asyncio
    async def test_investment_with_price_decline(
        self, db_session, sender_user, sukuk_asset, mock_escrow,
    ):
        """Investment with price decline: user sells at a loss."""
        escrow_svc = EscrowService(mock_escrow)
        svc = InvestmentService(db=db_session, escrow_service=escrow_svc)
        original_balance = sender_user.wallet_balance_usdc

        investment = await svc.buy_asset(sender_user.id, sukuk_asset.id, 10.0)

        # Price drops 20%
        sukuk_asset.price_per_token_usd = 80.0
        await db_session.flush()

        sold = await svc.sell_asset(investment.id, sender_user.id)
        assert sold.current_value_usd == 800.0  # 10 * $80

        sender_final = await db_session.get(User, sender_user.id)
        assert abs(sender_final.wallet_balance_usdc - (original_balance - 200.0)) < 0.01

    @pytest.mark.asyncio
    async def test_cannot_buy_without_balance(
        self, db_session, sukuk_asset, mock_escrow,
    ):
        """User with insufficient funds cannot buy assets."""
        poor_user = UserFactory.build(wallet_balance_usdc=50.0)
        db_session.add(poor_user)
        await db_session.flush()

        escrow_svc = EscrowService(mock_escrow)
        svc = InvestmentService(db=db_session, escrow_service=escrow_svc)

        with pytest.raises(ValueError, match="Insufficient balance"):
            await svc.buy_asset(poor_user.id, sukuk_asset.id, 10.0)

    @pytest.mark.asyncio
    async def test_investment_balance_accounting(
        self, db_session, sender_user, sukuk_asset, mock_escrow,
    ):
        """
        Verify balance accounting across buy and sell operations.
        Start: $10,000
        Buy 10 @ $100 = -$1000 -> $9,000
        Asset rises to $150
        Sell 10 @ $150 = +$1500 -> $10,500
        """
        escrow_svc = EscrowService(mock_escrow)
        svc = InvestmentService(db=db_session, escrow_service=escrow_svc)

        inv = await svc.buy_asset(sender_user.id, sukuk_asset.id, 10.0)

        sender_after_buy = await db_session.get(User, sender_user.id)
        assert abs(sender_after_buy.wallet_balance_usdc - 9000.0) < 0.01

        sukuk_asset.price_per_token_usd = 150.0
        await db_session.flush()

        await svc.sell_asset(inv.id, sender_user.id)

        sender_after_sell = await db_session.get(User, sender_user.id)
        assert abs(sender_after_sell.wallet_balance_usdc - 10500.0) < 0.01
