"""FastAPI routes for the P2P matching engine.

All endpoints are under /api/v1/matching/.
"""

from __future__ import annotations

import logging
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.matching import (
    OrderEstimateRequest,
    OrderEstimateResponse,
    OrderCreateRequest,
    OrderCreateResponse,
    OrderDetailResponse,
    PoolStatusResponse,
    LiquidityRequest,
    LiquidityResponse,
    LiquidityPositionResponse,
    LiquidityWithdrawRequest,
    MatchEventResponse,
)
from app.dependencies import get_current_user_id
from app.exceptions import KYCRequiredError
from app.models.matching import MatchOrder, LiquidityPosition
from app.services.compliance_service import ComplianceService
from app.services.kyc_service import KYCService
from app.services.matching_engine import MatchingEngine
from app.services.pool_manager import PoolManager
from app.services.liquidity_service import LiquidityService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/matching", tags=["matching"])

# Minimum KYC level required to place orders or provide liquidity.
MATCHING_MIN_KYC_LEVEL = 1

# Generic message for compliance rejections. Deliberately says nothing about
# *why* (sanctions hit, SAR, review) to avoid tipping off the subject.
COMPLIANCE_REJECTION_DETAIL = (
    "This request cannot be processed at this time. Please contact support."
)
KYC_REQUIRED_DETAIL = "Identity verification (KYC) is required before using the matching pool."


# ---------------------------------------------------------------------------
# Dependency helpers
# ---------------------------------------------------------------------------

async def _get_db():
    """Get async DB session — uses the same engine as auth/users."""
    from app.dependencies import get_db
    async for session in get_db():
        yield session


async def enforce_matching_compliance(
    db: AsyncSession,
    user_id: uuid.UUID | str,
    recipient_info: Optional[dict] = None,
) -> None:
    """Gate entry to the matching pool: KYC first, then sanctions screening.

    Raises HTTP 403 on failure. Internal reasons are logged, never returned.
    """
    try:
        await KYCService(db).check_kyc_level(user_id, MATCHING_MIN_KYC_LEVEL)
    except (KYCRequiredError, ValueError):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=KYC_REQUIRED_DETAIL)

    screening = await ComplianceService(db).screen_user_for_matching(
        user_id, recipient_info=recipient_info,
    )
    if not screening.allowed:
        logger.warning(
            "Matching pool entry blocked by compliance: user=%s reason=%s",
            user_id, screening.reason,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=COMPLIANCE_REJECTION_DETAIL,
        )


# ---------------------------------------------------------------------------
# POST /matching/estimate -- Get match estimate before committing
# ---------------------------------------------------------------------------

@router.post(
    "/estimate",
    response_model=OrderEstimateResponse,
    summary="Estimate match probability and fees",
)
async def estimate_match(
    body: OrderEstimateRequest,
    db: AsyncSession = Depends(_get_db),
):
    """Get an estimate of how likely an order would be peer-matched,
    the expected fee, and wait time -- before the user commits.
    """
    pool_mgr = PoolManager(db)
    estimate = await pool_mgr.estimate_match_rate(
        source=body.source_currency,
        target=body.target_currency,
        amount=body.amount,
    )
    return OrderEstimateResponse(
        source_currency=body.source_currency,
        target_currency=body.target_currency,
        amount=body.amount,
        match_pct=estimate.match_pct,
        estimated_fee=estimate.estimated_fee,
        estimated_time=estimate.estimated_time,
    )


# ---------------------------------------------------------------------------
# POST /matching/orders -- Submit order
# ---------------------------------------------------------------------------

@router.post(
    "/orders",
    response_model=OrderCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a matching order",
)
async def create_order(
    body: OrderCreateRequest,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(_get_db),
):
    """Submit an order to the P2P matching pool (KYC + sanctions gated)."""
    await enforce_matching_compliance(db, user_id, body.recipient_info)
    engine = MatchingEngine(db)
    try:
        order = await engine.submit_order(
            user_id=str(user_id),
            source_currency=body.source_currency,
            target_currency=body.target_currency,
            amount=body.amount,
            recipient_info=body.recipient_info,
            max_wait_hours=body.max_wait_hours,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    return OrderCreateResponse.model_validate(order)


# ---------------------------------------------------------------------------
# GET /matching/orders/{id} -- Track order
# ---------------------------------------------------------------------------

@router.get(
    "/orders/{order_id}",
    response_model=OrderDetailResponse,
    summary="Get order details",
)
async def get_order(
    order_id: str,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(_get_db),
):
    """Retrieve current status and details of one of the caller's orders."""
    order = await _get_owned_order(db, order_id, user_id)
    return OrderDetailResponse.model_validate(order)


async def _get_owned_order(
    db: AsyncSession, order_id: str, user_id: uuid.UUID,
) -> MatchOrder:
    """Load an order, 404 if missing, 403 if it belongs to someone else."""
    result = await db.execute(
        select(MatchOrder).where(MatchOrder.id == order_id)
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )
    if order.user_id != str(user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not own this order",
        )
    return order


# ---------------------------------------------------------------------------
# DELETE /matching/orders/{id} -- Cancel order
# ---------------------------------------------------------------------------

@router.delete(
    "/orders/{order_id}",
    response_model=OrderDetailResponse,
    summary="Cancel a pending order",
)
async def cancel_order(
    order_id: str,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(_get_db),
):
    """Cancel one of the caller's pending or partially matched orders."""
    order = await _get_owned_order(db, order_id, user_id)
    if order.status not in ("pending", "partially_matched"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel order in status: {order.status}",
        )

    from datetime import datetime, timezone
    order.status = "cancelled"
    order.cancelled_at = datetime.now(timezone.utc)
    await db.flush()

    return OrderDetailResponse.model_validate(order)


# ---------------------------------------------------------------------------
# GET /matching/pools -- All pool statuses
# ---------------------------------------------------------------------------

@router.get(
    "/pools",
    response_model=List[PoolStatusResponse],
    summary="Get all pool statuses",
)
async def list_pools(
    db: AsyncSession = Depends(_get_db),
):
    """Get status of all active currency pools."""
    pool_mgr = PoolManager(db)
    pools = await pool_mgr.get_all_pools()
    return [
        PoolStatusResponse(
            currency=p.currency,
            tvl=p.tvl,
            order_count=p.order_count,
            match_rate_24h=p.match_rate_24h,
            avg_wait_time=p.avg_wait_time,
        )
        for p in pools
    ]


# ---------------------------------------------------------------------------
# GET /matching/pools/{currency} -- Specific pool
# ---------------------------------------------------------------------------

@router.get(
    "/pools/{currency}",
    response_model=PoolStatusResponse,
    summary="Get specific pool status",
)
async def get_pool(
    currency: str,
    db: AsyncSession = Depends(_get_db),
):
    """Get status of a specific currency pool."""
    pool_mgr = PoolManager(db)
    p = await pool_mgr.get_pool_status(currency.upper())
    return PoolStatusResponse(
        currency=p.currency,
        tvl=p.tvl,
        order_count=p.order_count,
        match_rate_24h=p.match_rate_24h,
        avg_wait_time=p.avg_wait_time,
    )


# ---------------------------------------------------------------------------
# POST /matching/liquidity -- Add liquidity
# ---------------------------------------------------------------------------

@router.post(
    "/liquidity",
    response_model=LiquidityResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add liquidity to a pool",
)
async def add_liquidity(
    body: LiquidityRequest,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(_get_db),
):
    """Deposit liquidity into a currency pool as an LP (KYC + sanctions gated)."""
    await enforce_matching_compliance(db, user_id)
    liq_service = LiquidityService(db)
    try:
        position = await liq_service.add_liquidity(
            user_id=str(user_id),
            currency=body.currency,
            amount=body.amount,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    return LiquidityResponse.model_validate(position)


# ---------------------------------------------------------------------------
# DELETE /matching/liquidity/{id} -- Remove liquidity
# ---------------------------------------------------------------------------

@router.delete(
    "/liquidity/{position_id}",
    summary="Remove liquidity from a position",
)
async def remove_liquidity(
    position_id: str,
    body: Optional[LiquidityWithdrawRequest] = None,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(_get_db),
):
    """Withdraw liquidity from one of the caller's LP positions."""
    position = (await db.execute(
        select(LiquidityPosition).where(LiquidityPosition.id == position_id)
    )).scalar_one_or_none()
    if not position:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Position not found",
        )
    if position.user_id != str(user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not own this position",
        )

    liq_service = LiquidityService(db)
    withdraw_amount = body.amount if body else None
    result = await liq_service.remove_liquidity(position_id, withdraw_amount)

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.error,
        )

    return {
        "position_id": result.position_id,
        "amount_withdrawn": result.amount_withdrawn,
        "remaining": result.remaining,
    }


# ---------------------------------------------------------------------------
# GET /matching/liquidity/positions -- My LP positions
# ---------------------------------------------------------------------------

@router.get(
    "/liquidity/positions",
    response_model=List[LiquidityPositionResponse],
    summary="List my LP positions",
)
async def list_positions(
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(_get_db),
):
    """Get all liquidity positions for the authenticated user."""
    liq_service = LiquidityService(db)
    positions = await liq_service.get_positions(str(user_id))
    return [LiquidityPositionResponse.model_validate(p) for p in positions]


# ---------------------------------------------------------------------------
# GET /matching/live -- Recent matches feed
# ---------------------------------------------------------------------------

@router.get(
    "/live",
    response_model=List[MatchEventResponse],
    summary="Live match feed",
)
async def live_matches(
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(_get_db),
):
    """Get a feed of recent matches for the live dashboard."""
    pool_mgr = PoolManager(db)
    matches = await pool_mgr.get_live_matches(limit=limit)
    return [
        MatchEventResponse(
            match_id=m.match_id,
            match_type=m.match_type,
            source_currency=m.source_currency,
            target_currency=m.target_currency,
            amount=m.amount,
            executed_at=m.executed_at,
        )
        for m in matches
    ]
