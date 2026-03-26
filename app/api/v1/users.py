"""User profile, wallet, and beneficiary endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.common import MessageResponse
from app.api.schemas.user import (
    BeneficiaryCreate,
    BeneficiaryResponse,
    UpdateProfileRequest,
    UserProfile,
    WalletResponse,
)
from app.dependencies import get_current_user_id, get_db
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])


# ------------------------------------------------------------------
# Profile
# ------------------------------------------------------------------


@router.get("/me", response_model=UserProfile, summary="Get current user profile")
async def get_profile(
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    svc = UserService(db)
    user = await svc.get_by_id(user_id)
    return UserProfile.model_validate(user)


@router.patch("/me", response_model=UserProfile, summary="Update current user profile")
async def update_profile(
    body: UpdateProfileRequest,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    svc = UserService(db)
    user = await svc.update_profile(
        user_id,
        full_name=body.full_name,
        phone=body.phone,
        country_code=body.country_code,
    )
    return UserProfile.model_validate(user)


# ------------------------------------------------------------------
# Wallets
# ------------------------------------------------------------------


@router.get("/me/wallets", response_model=list[WalletResponse], summary="List user wallets")
async def list_wallets(
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    svc = UserService(db)
    wallets = await svc.get_wallets(user_id)
    return [WalletResponse.model_validate(w) for w in wallets]


# ------------------------------------------------------------------
# Beneficiaries
# ------------------------------------------------------------------


@router.get(
    "/me/beneficiaries",
    response_model=list[BeneficiaryResponse],
    summary="List saved beneficiaries",
)
async def list_beneficiaries(
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    svc = UserService(db)
    bens = await svc.list_beneficiaries(user_id)
    return [BeneficiaryResponse.model_validate(b) for b in bens]


@router.post(
    "/me/beneficiaries",
    response_model=BeneficiaryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a beneficiary",
)
async def add_beneficiary(
    body: BeneficiaryCreate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    svc = UserService(db)
    ben = await svc.add_beneficiary(
        user_id,
        beneficiary_name=body.beneficiary_name,
        phone=body.phone,
        country_code=body.country_code,
        default_delivery_method=body.default_delivery_method,
    )
    return BeneficiaryResponse.model_validate(ben)


@router.delete(
    "/me/beneficiaries/{beneficiary_id}",
    response_model=MessageResponse,
    summary="Delete a beneficiary",
)
async def delete_beneficiary(
    beneficiary_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    svc = UserService(db)
    await svc.delete_beneficiary(user_id, beneficiary_id)
    return MessageResponse(message="Beneficiary deleted")
