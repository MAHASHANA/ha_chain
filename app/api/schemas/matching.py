"""Pydantic schemas for the P2P matching engine API."""

from __future__ import annotations

from datetime import datetime
from typing import Optional, List, Dict, Any

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Order Estimate
# ---------------------------------------------------------------------------

class OrderEstimateRequest(BaseModel):
    source_currency: str = Field(..., min_length=3, max_length=3, examples=["USD"])
    target_currency: str = Field(..., min_length=3, max_length=3, examples=["INR"])
    amount: float = Field(..., gt=0, examples=[500.0])


class OrderEstimateResponse(BaseModel):
    source_currency: str
    target_currency: str
    amount: float
    match_pct: float = Field(description="Estimated % that will be peer-matched")
    estimated_fee: float = Field(description="Estimated total fee")
    estimated_time: float = Field(description="Estimated seconds to match")


# ---------------------------------------------------------------------------
# Order Create / Response
# ---------------------------------------------------------------------------

class OrderCreateRequest(BaseModel):
    source_currency: str = Field(..., min_length=3, max_length=3, examples=["USD"])
    target_currency: str = Field(..., min_length=3, max_length=3, examples=["INR"])
    amount: float = Field(..., gt=0, examples=[500.0])
    recipient_info: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Recipient details: account, name, method, etc.",
        examples=[{"account": "user@upi", "name": "Raj", "method": "upi"}],
    )
    max_wait_hours: float = Field(default=4.0, gt=0, le=72)


class OrderCreateResponse(BaseModel):
    id: str
    user_id: str
    source_currency: str
    target_currency: str
    amount: float
    amount_matched: float
    amount_unmatched: float
    status: str
    max_wait_until: datetime
    created_at: datetime

    model_config = {"from_attributes": True}


class OrderDetailResponse(BaseModel):
    id: str
    user_id: str
    source_currency: str
    target_currency: str
    amount: float
    amount_matched: float
    amount_unmatched: float
    recipient_info: Optional[Dict[str, Any]] = None
    status: str
    max_wait_until: datetime
    created_at: datetime
    matched_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Pool Status
# ---------------------------------------------------------------------------

class PoolStatusResponse(BaseModel):
    currency: str
    tvl: float = Field(description="Total value locked by LPs")
    order_count: int = Field(description="Number of pending orders")
    match_rate_24h: float = Field(description="Match rate over last 24 hours (%)")
    avg_wait_time: float = Field(description="Average wait time in seconds")


# ---------------------------------------------------------------------------
# Liquidity
# ---------------------------------------------------------------------------

class LiquidityRequest(BaseModel):
    currency: str = Field(..., min_length=3, max_length=3, examples=["USD"])
    amount: float = Field(..., gt=0, examples=[10000.0])


class LiquidityResponse(BaseModel):
    id: str
    user_id: str
    currency: str
    amount: float
    earned_fees: float
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class LiquidityPositionResponse(BaseModel):
    id: str
    user_id: str
    currency: str
    amount: float
    earned_fees: float
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class LiquidityWithdrawRequest(BaseModel):
    amount: Optional[float] = Field(default=None, gt=0, description="Amount to withdraw; null = full withdrawal")


# ---------------------------------------------------------------------------
# Match Events (live feed)
# ---------------------------------------------------------------------------

class MatchEventResponse(BaseModel):
    match_id: str
    match_type: str
    source_currency: str
    target_currency: str
    amount: float
    executed_at: Optional[datetime] = None
