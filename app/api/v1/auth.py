"""Authentication endpoints: register, login, token refresh."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.auth import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    RegisterResponse,
    TokenResponse,
)
from app.config import get_settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.dependencies import get_db
from app.models.user import User, UserWallet

router = APIRouter(prefix="/auth", tags=["auth"])

settings = get_settings()


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    # Check uniqueness
    existing = await db.execute(
        select(User).where((User.email == body.email) | (User.phone == body.phone))
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email or phone already exists",
        )

    user = User(
        email=body.email,
        phone=body.phone,
        password_hash=hash_password(body.password),
        full_name=body.full_name,
        country_code=body.country_code,
        default_currency=body.default_currency,
    )
    db.add(user)
    await db.flush()

    # Provision default USDC wallet
    wallet = UserWallet(user_id=user.id, currency="USDC", balance=0, is_primary=True)
    db.add(wallet)
    await db.flush()

    access_token = create_access_token(user.id, {"role": "user"})
    refresh_token = create_refresh_token(user.id)

    return RegisterResponse(
        id=user.id,
        email=user.email,
        phone=user.phone,
        full_name=user.full_name,
        country_code=user.country_code,
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post("/login", response_model=TokenResponse, summary="Authenticate with email & password")
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(User).where(User.email == body.email, User.deleted_at.is_(None))
    )
    user = result.scalar_one_or_none()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )

    # Determine role for token claims
    role = "user"
    # Check if user is an agent (via relationship or DB lookup)
    from app.models.agent import Agent

    agent_q = await db.execute(select(Agent).where(Agent.user_id == user.id))
    agent = agent_q.scalar_one_or_none()
    if agent and agent.license_status == "active":
        role = "agent"

    access_token = create_access_token(user.id, {"role": role})
    refresh_token = create_refresh_token(user.id)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/refresh", response_model=TokenResponse, summary="Refresh an access token")
async def refresh_token(body: RefreshRequest, db: AsyncSession = Depends(get_db)):
    try:
        payload = decode_token(body.refresh_token)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is not a refresh token",
        )

    user_id = payload["sub"]
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

    access_token = create_access_token(user.id, {"role": payload.get("role", "user")})
    new_refresh = create_refresh_token(user.id)

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh,
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
