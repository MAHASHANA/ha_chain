"""User, wallet, and beneficiary schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class UserProfile(BaseModel):
    id: uuid.UUID
    email: str
    phone: str
    full_name: str
    country_code: str
    kyc_level: int
    is_verified: bool
    default_currency: str
    created_at: datetime

    model_config = {"from_attributes": True}


class UpdateProfileRequest(BaseModel):
    full_name: str | None = Field(None, max_length=200)
    phone: str | None = Field(None, max_length=20)
    country_code: str | None = Field(None, min_length=3, max_length=3)


class WalletResponse(BaseModel):
    id: uuid.UUID
    currency: str
    balance: float
    wallet_address: str | None = None
    is_primary: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class BeneficiaryCreate(BaseModel):
    beneficiary_name: str = Field(..., max_length=200)
    phone: str = Field(..., max_length=20)
    country_code: str = Field(..., min_length=3, max_length=3)
    default_delivery_method: str = Field("mobile_money", max_length=30)


class BeneficiaryResponse(BaseModel):
    id: uuid.UUID
    beneficiary_name: str
    phone: str
    country_code: str
    default_delivery_method: str
    created_at: datetime

    model_config = {"from_attributes": True}
