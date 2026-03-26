"""Investment endpoints: browse assets, buy, sell, portfolio."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.investment import (
    AssetResponse,
    BuyRequest,
    InvestmentTransactionResponse,
    PortfolioPositionResponse,
    PortfolioResponse,
    SellRequest,
)
from app.dependencies import get_current_user_id, get_db
from app.enums import InvestmentStatus
from app.models.models import (
    Investment as ModelsInvestment,
    TokenizedAsset as ModelsAsset,
    User as ModelsUser,
)

router = APIRouter(prefix="/investments", tags=["investments"])


# ------------------------------------------------------------------
# Browse assets
# ------------------------------------------------------------------


@router.get("/assets", summary="List available tokenized assets")
async def list_assets(
    asset_type: str | None = Query(None, description="Filter by asset type"),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(ModelsAsset).where(ModelsAsset.is_active.is_(True))
    if asset_type:
        stmt = stmt.where(ModelsAsset.asset_type == asset_type)
    stmt = stmt.order_by(ModelsAsset.asset_type, ModelsAsset.symbol)

    result = await db.execute(stmt)
    assets = result.scalars().all()

    return {
        "assets": [
            {
                "id": a.id,
                "symbol": a.symbol,
                "name": a.name,
                "asset_type": a.asset_type,
                "issuer": a.issuer,
                "price_per_token_usd": a.price_per_token_usd,
                "annual_yield_percent": a.annual_yield_percent,
                "total_supply": a.total_supply,
                "is_active": a.is_active,
            }
            for a in assets
        ],
        "total": len(assets),
    }


@router.get("/assets/{asset_id}", summary="Get asset details")
async def get_asset(
    asset_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(ModelsAsset).where(ModelsAsset.id == asset_id))
    asset = result.scalar_one_or_none()
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")

    return {
        "id": asset.id,
        "symbol": asset.symbol,
        "name": asset.name,
        "asset_type": asset.asset_type,
        "issuer": asset.issuer,
        "price_per_token_usd": asset.price_per_token_usd,
        "annual_yield_percent": asset.annual_yield_percent,
        "total_supply": asset.total_supply,
        "stellar_asset_code": asset.stellar_asset_code,
        "stellar_issuer": asset.stellar_issuer,
        "is_active": asset.is_active,
    }


# ------------------------------------------------------------------
# Buy
# ------------------------------------------------------------------


@router.post("/buy", status_code=status.HTTP_201_CREATED, summary="Purchase a tokenized asset")
async def buy_asset(
    body: BuyRequest,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Buy tokenized assets using USDC from wallet balance.

    Calculates quantity based on current price and deducts from wallet.
    A 0.1% trading fee is applied.
    """
    # Get asset
    result = await db.execute(select(ModelsAsset).where(ModelsAsset.id == str(body.asset_id)))
    asset = result.scalar_one_or_none()
    if not asset or not asset.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found or inactive")

    # Get user
    user_q = await db.execute(select(ModelsUser).where(ModelsUser.id == str(user_id)))
    user = user_q.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if user.wallet_balance_usdc < body.amount_usdc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient balance: have {user.wallet_balance_usdc}, need {body.amount_usdc}",
        )

    # Calculate
    fee = round(body.amount_usdc * 0.001, 6)  # 0.1% fee
    net_amount = body.amount_usdc - fee
    quantity = net_amount / asset.price_per_token_usd

    # Debit wallet
    user.wallet_balance_usdc -= body.amount_usdc

    # Create investment
    investment = ModelsInvestment(
        user_id=str(user_id),
        asset_id=str(body.asset_id),
        quantity=quantity,
        purchase_price_usd=net_amount,
        current_value_usd=net_amount,
        status=InvestmentStatus.ACTIVE.value,
    )
    db.add(investment)
    await db.flush()

    return {
        "investment_id": investment.id,
        "asset_symbol": asset.symbol,
        "quantity": quantity,
        "price_per_unit": asset.price_per_token_usd,
        "total_amount": net_amount,
        "fee": fee,
        "status": investment.status,
    }


# ------------------------------------------------------------------
# Sell
# ------------------------------------------------------------------


@router.post("/sell", summary="Sell a tokenized asset position")
async def sell_asset(
    body: SellRequest,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Sell units from a position and receive USDC to wallet.

    A 0.1% trading fee is applied on the proceeds.
    """
    # Get investment position
    result = await db.execute(
        select(ModelsInvestment).where(
            ModelsInvestment.id == str(body.position_id),
            ModelsInvestment.user_id == str(user_id),
            ModelsInvestment.status == InvestmentStatus.ACTIVE.value,
        )
    )
    investment = result.scalar_one_or_none()
    if not investment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Investment position not found")

    if investment.quantity < body.quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient quantity: have {investment.quantity}, want to sell {body.quantity}",
        )

    # Get current price
    asset_q = await db.execute(select(ModelsAsset).where(ModelsAsset.id == investment.asset_id))
    asset = asset_q.scalar_one_or_none()
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")

    # Calculate proceeds
    gross = body.quantity * asset.price_per_token_usd
    fee = round(gross * 0.001, 6)
    net_proceeds = gross - fee

    # Credit wallet
    user_q = await db.execute(select(ModelsUser).where(ModelsUser.id == str(user_id)))
    user = user_q.scalar_one_or_none()
    user.wallet_balance_usdc += net_proceeds

    # Update position
    investment.quantity -= body.quantity
    if investment.quantity <= 0:
        investment.quantity = 0
        investment.status = InvestmentStatus.SOLD.value
        investment.sold_at = datetime.now(timezone.utc)
    investment.current_value_usd = investment.quantity * asset.price_per_token_usd

    await db.flush()

    return {
        "investment_id": investment.id,
        "asset_symbol": asset.symbol,
        "quantity_sold": body.quantity,
        "price_per_unit": asset.price_per_token_usd,
        "gross_proceeds": gross,
        "fee": fee,
        "net_proceeds": net_proceeds,
        "remaining_quantity": investment.quantity,
        "status": investment.status,
    }


# ------------------------------------------------------------------
# Portfolio
# ------------------------------------------------------------------


@router.get("/portfolio", summary="Get user's investment portfolio")
async def get_portfolio(
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Return all active investment positions with current values and P&L."""
    result = await db.execute(
        select(ModelsInvestment).where(
            ModelsInvestment.user_id == str(user_id),
            ModelsInvestment.status == InvestmentStatus.ACTIVE.value,
        )
    )
    investments = result.scalars().all()

    positions = []
    total_invested = 0.0
    total_current = 0.0

    for inv in investments:
        # Get current asset price
        asset_q = await db.execute(select(ModelsAsset).where(ModelsAsset.id == inv.asset_id))
        asset = asset_q.scalar_one_or_none()
        if not asset:
            continue

        current_value = inv.quantity * asset.price_per_token_usd
        pnl = current_value - inv.purchase_price_usd
        pnl_pct = (pnl / inv.purchase_price_usd * 100) if inv.purchase_price_usd > 0 else 0

        # Update stored current value
        inv.current_value_usd = current_value

        total_invested += inv.purchase_price_usd
        total_current += current_value

        positions.append({
            "position_id": inv.id,
            "asset_symbol": asset.symbol,
            "asset_name": asset.name,
            "asset_type": asset.asset_type,
            "quantity": inv.quantity,
            "avg_buy_price": inv.purchase_price_usd / inv.quantity if inv.quantity > 0 else 0,
            "current_price": asset.price_per_token_usd,
            "current_value": round(current_value, 6),
            "total_invested": round(inv.purchase_price_usd, 6),
            "pnl": round(pnl, 6),
            "pnl_percent": round(pnl_pct, 2),
            "annual_yield": asset.annual_yield_percent,
        })

    await db.flush()

    return {
        "positions": positions,
        "total_value": round(total_current, 6),
        "total_invested": round(total_invested, 6),
        "total_pnl": round(total_current - total_invested, 6),
    }
