"""Corridor and exchange-rate schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel


class DeliveryMethodInfo(BaseModel):
    code: str
    provider: str | None = None
    extra_fee_flat: float = 0.0
    extra_fee_percent: float = 0.0


class CorridorResponse(BaseModel):
    id: uuid.UUID
    source_country: str
    destination_country: str
    source_currency: str
    destination_currency: str
    is_active: bool
    base_fee_flat: float
    base_fee_percent: float
    min_transfer: float
    max_transfer: float
    risk_level: str
    required_kyc_level: int
    estimated_minutes_bank: int
    estimated_minutes_mobile: int
    estimated_minutes_cash: int
    delivery_methods: list[DeliveryMethodInfo] = []
    created_at: datetime

    model_config = {"from_attributes": True}


class CorridorRatesResponse(BaseModel):
    corridor_id: str
    source_currency: str
    destination_currency: str
    exchange_rate: float
    mid_market_rate: float
    base_fee_flat: float
    base_fee_percent: float
    corridor_fee_flat: float
    corridor_fee_percent: float
    min_transfer: float
    max_transfer: float
    delivery_methods: list[DeliveryMethodInfo] = []
