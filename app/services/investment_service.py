"""Investment service: buy/sell tokenized assets (sukuk, real estate, equity)."""

from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.enums import InvestmentStatus
from app.models.models import Investment, TokenizedAsset, User


class InvestmentService:
    def __init__(self, db: AsyncSession, escrow_service=None):
        self.db = db
        self.escrow_service = escrow_service

    async def buy_asset(
        self,
        user_id: str,
        asset_id: str,
        quantity: float,
    ) -> Investment:
        """Purchase tokenized asset tokens."""
        user = await self.db.get(User, user_id)
        if not user:
            raise ValueError("User not found")

        asset = await self.db.get(TokenizedAsset, asset_id)
        if not asset:
            raise ValueError("Asset not found")
        if not asset.is_active:
            raise ValueError("Asset is not available for purchase")

        total_cost = quantity * asset.price_per_token_usd
        if user.wallet_balance_usdc < total_cost:
            raise ValueError(
                f"Insufficient balance. Required: ${total_cost:.2f}, "
                f"Available: ${user.wallet_balance_usdc:.2f}"
            )

        if quantity <= 0:
            raise ValueError("Quantity must be positive")

        # Debit user
        user.wallet_balance_usdc -= total_cost

        # Record blockchain transaction (if escrow available)
        tx_hash = None
        if self.escrow_service:
            tx_hash = await self.escrow_service.lock_funds(
                transfer_id=f"invest-{user_id}-{asset_id}",
                amount_usdc=total_cost,
                sender_address=user.wallet_address or "",
            )

        investment = Investment(
            user_id=user_id,
            asset_id=asset_id,
            quantity=quantity,
            purchase_price_usd=total_cost,
            current_value_usd=total_cost,
            status=InvestmentStatus.ACTIVE.value,
            purchase_tx_hash=tx_hash,
        )

        self.db.add(investment)
        await self.db.flush()
        return investment

    async def sell_asset(self, investment_id: str, user_id: str) -> Investment:
        """Sell an active investment position."""
        investment = await self.db.get(Investment, investment_id)
        if not investment:
            raise ValueError("Investment not found")
        if investment.user_id != user_id:
            raise ValueError("Investment does not belong to this user")
        if investment.status != InvestmentStatus.ACTIVE.value:
            raise ValueError(f"Investment is {investment.status}, cannot sell")

        # Get current asset price for valuation
        asset = await self.db.get(TokenizedAsset, investment.asset_id)
        current_value = investment.quantity * asset.price_per_token_usd

        # Credit user
        user = await self.db.get(User, user_id)
        user.wallet_balance_usdc += current_value

        tx_hash = None
        if self.escrow_service:
            tx_hash = await self.escrow_service.release_funds(
                transfer_id=f"invest-{user_id}-{investment.asset_id}",
                recipient_address=user.wallet_address or "",
            )

        investment.current_value_usd = current_value
        investment.status = InvestmentStatus.SOLD.value
        investment.sale_tx_hash = tx_hash
        investment.sold_at = datetime.now(timezone.utc)

        await self.db.flush()
        return investment

    async def get_user_investments(
        self, user_id: str, status: Optional[str] = None
    ) -> List[Investment]:
        """Get all investments for a user, optionally filtered by status."""
        query = select(Investment).where(Investment.user_id == user_id)
        if status:
            query = query.where(Investment.status == status)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_portfolio_value(self, user_id: str) -> dict:
        """Calculate total portfolio value for a user."""
        investments = await self.get_user_investments(
            user_id, status=InvestmentStatus.ACTIVE.value
        )
        total_invested = sum(i.purchase_price_usd for i in investments)
        total_current = 0.0

        for inv in investments:
            asset = await self.db.get(TokenizedAsset, inv.asset_id)
            current = inv.quantity * asset.price_per_token_usd
            inv.current_value_usd = current
            total_current += current

        await self.db.flush()

        return {
            "total_invested_usd": round(total_invested, 2),
            "total_current_value_usd": round(total_current, 2),
            "total_return_usd": round(total_current - total_invested, 2),
            "total_return_percent": (
                round(((total_current - total_invested) / total_invested) * 100, 2)
                if total_invested > 0
                else 0.0
            ),
            "positions": len(investments),
        }
