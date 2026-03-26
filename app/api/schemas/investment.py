"""Investment and portfolio schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class AssetResponse(BaseModel):
    id: uuid.UUID
    symbol: str
    name: str
    asset_type: str
    provider: str
    description: str | None = None
    chain: str
    current_price_usdc: float
    price_change_24h: float
    apy: float | None = None
    min_investment: float
    is_active: bool

    model_config = {"from_attributes": True}


class BuyRequest(BaseModel):
    asset_id: uuid.UUID
    amount_usdc: float = Field(..., gt=0, description="Amount of USDC to invest")


class SellRequest(BaseModel):
    position_id: uuid.UUID
    quantity: float = Field(..., gt=0, description="Number of units to sell")


class InvestmentTransactionResponse(BaseModel):
    id: uuid.UUID
    asset_id: uuid.UUID
    side: str
    quantity: float
    price_per_unit: float
    total_amount: float
    fee: float
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class PortfolioPositionResponse(BaseModel):
    position_id: str
    asset_symbol: str
    asset_name: str
    asset_type: str
    quantity: float
    avg_buy_price: float
    current_price: float
    current_value: float
    total_invested: float
    pnl: float
    pnl_percent: float
    apy: float | None = None


class PortfolioResponse(BaseModel):
    positions: list[PortfolioPositionResponse]
    total_value: float = 0.0
    total_invested: float = 0.0
    total_pnl: float = 0.0
