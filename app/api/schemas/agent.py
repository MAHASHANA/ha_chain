"""Agent registration, staking, and dashboard schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class AgentRegisterRequest(BaseModel):
    business_name: str = Field(..., max_length=200)
    country: str = Field(..., min_length=3, max_length=3)
    city: str = Field(..., max_length=100)
    address: str | None = None
    license_number: str | None = None
    supported_delivery_methods: list[str] = Field(default=["cash_pickup", "mobile_money"])
    supported_currencies: list[str] = Field(default=["USDC"])
    commission_rate: float = Field(0.005, ge=0, le=0.1)


class AgentResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    business_name: str
    country: str
    city: str
    license_status: str
    is_online: bool
    commission_rate: float
    staked_amount: float
    rating_avg: float
    rating_count: int
    total_transactions: int
    created_at: datetime

    model_config = {"from_attributes": True}


class StakeRequest(BaseModel):
    amount: float = Field(..., gt=0, description="Amount of USDC to stake")
    tx_hash: str | None = Field(None, description="On-chain transaction hash")


class StakeResponse(BaseModel):
    id: uuid.UUID
    agent_id: uuid.UUID
    amount: float
    currency: str
    status: str
    tx_hash: str | None
    staked_at: datetime

    model_config = {"from_attributes": True}


class AgentDashboardResponse(BaseModel):
    agent_id: str
    business_name: str
    license_status: str
    is_online: bool
    staked_amount: float
    total_transactions: int
    total_volume: float
    rating_avg: float
    rating_count: int
    success_rate: float
    avg_delivery_minutes: int
    active_transfers: int
    today_volume: float
    daily_limit: float
    remaining_capacity: float


class SetOnlineRequest(BaseModel):
    is_online: bool
