"""Transfer quoting, initiation, and tracking schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class QuoteRequest(BaseModel):
    receiver_country: str = Field(..., min_length=3, max_length=3, examples=["MEX"])
    amount: float = Field(..., gt=0, examples=[200.0])
    currency: str = Field("USD", max_length=10)
    delivery_method: str = Field("cash_pickup", max_length=30)


class QuoteResponse(BaseModel):
    id: uuid.UUID
    corridor_id: uuid.UUID
    source_currency: str
    destination_currency: str
    send_amount: float
    receive_amount: float
    exchange_rate: float
    base_fee: float
    corridor_fee: float
    delivery_fee: float
    total_fee: float
    total_cost: float
    delivery_method: str
    estimated_delivery_minutes: int
    expires_at: datetime

    model_config = {"from_attributes": True}


class TransferCreateRequest(BaseModel):
    quote_id: uuid.UUID
    receiver_phone: str = Field(..., max_length=20)
    receiver_name: str = Field(..., max_length=200)
    receiver_city: str | None = Field(None, max_length=100)
    delivery_method: str | None = Field(None, max_length=30)


class TransferResponse(BaseModel):
    id: uuid.UUID
    quote_id: uuid.UUID
    sender_id: uuid.UUID
    agent_id: uuid.UUID | None = None
    receiver_name: str
    receiver_phone: str
    receiver_country: str
    receiver_city: str | None = None
    source_currency: str
    destination_currency: str
    send_amount: float
    receive_amount: float
    exchange_rate: float
    total_fee: float
    delivery_method: str
    status: str
    pickup_code: str | None = None
    escrow_tx_hash: str | None = None
    settlement_tx_hash: str | None = None
    agent_accepted_at: datetime | None = None
    delivered_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ConfirmDeliveryRequest(BaseModel):
    verification_method: str = Field("pickup_code", examples=["pickup_code", "biometric", "receiver_confirm"])
    verification_data: str | None = Field(None, description="e.g. the pickup code value")


class DisputeRequest(BaseModel):
    reason: str = Field(..., min_length=10, max_length=1000)


class CancelRequest(BaseModel):
    reason: str = Field("User requested cancellation", max_length=500)


class TransferStatusLogResponse(BaseModel):
    id: uuid.UUID
    from_status: str | None
    to_status: str
    note: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
