"""Authentication request / response schemas."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    phone: str = Field(..., min_length=7, max_length=20, examples=["+12125551234"])
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str = Field(..., min_length=1, max_length=200)
    country_code: str = Field(..., min_length=3, max_length=3, examples=["USA"])
    default_currency: str = Field("USD", max_length=10)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class RefreshRequest(BaseModel):
    refresh_token: str


class RegisterResponse(BaseModel):
    id: uuid.UUID
    email: str
    phone: str
    full_name: str
    country_code: str
    access_token: str
    refresh_token: str
