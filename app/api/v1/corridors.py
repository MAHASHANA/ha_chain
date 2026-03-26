"""Corridor endpoints: list corridors, get rates, payment methods."""

from __future__ import annotations

import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.enums import CorridorStatus
from app.models.models import Corridor as ModelsCorridor
from app.services.corridor_service import CorridorService

router = APIRouter(prefix="/corridors", tags=["corridors"])


@router.get("", summary="List all active corridors")
async def list_corridors(
    source_country: Optional[str] = Query(None, description="Filter by source country (ISO alpha-3)"),
    destination_country: Optional[str] = Query(None, description="Filter by destination country"),
    db: AsyncSession = Depends(get_db),
):
    """Return all active remittance corridors with their fees and delivery methods."""
    svc = CorridorService(db)
    corridors = await svc.get_active_corridors()

    results = []
    for c in corridors:
        if source_country and c.source_country != source_country.upper():
            continue
        if destination_country and c.destination_country != destination_country.upper():
            continue

        try:
            delivery_methods = json.loads(c.supported_delivery_methods) if c.supported_delivery_methods else []
        except (json.JSONDecodeError, TypeError):
            delivery_methods = []

        try:
            providers = json.loads(c.supported_providers) if c.supported_providers else []
        except (json.JSONDecodeError, TypeError):
            providers = []

        results.append({
            "id": c.id,
            "source_country": c.source_country,
            "destination_country": c.destination_country,
            "source_currency": c.source_currency,
            "destination_currency": c.destination_currency,
            "base_fee_percent": c.base_fee_percent,
            "flat_fee_usd": c.flat_fee_usd,
            "minimum_fee_usd": c.minimum_fee_usd,
            "min_transfer": c.min_transfer_usd,
            "max_transfer": c.max_transfer_usd,
            "exchange_rate": c.exchange_rate,
            "exchange_rate_markup": c.exchange_rate_markup,
            "risk_score": c.risk_score,
            "status": c.status,
            "delivery_methods": delivery_methods,
            "providers": providers,
        })

    return {"corridors": results, "total": len(results)}


@router.get("/{corridor_id}", summary="Get corridor details")
async def get_corridor(
    corridor_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ModelsCorridor).where(ModelsCorridor.id == corridor_id)
    )
    corridor = result.scalar_one_or_none()
    if not corridor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Corridor not found",
        )

    try:
        delivery_methods = json.loads(corridor.supported_delivery_methods) if corridor.supported_delivery_methods else []
    except (json.JSONDecodeError, TypeError):
        delivery_methods = []

    try:
        providers = json.loads(corridor.supported_providers) if corridor.supported_providers else []
    except (json.JSONDecodeError, TypeError):
        providers = []

    return {
        "id": corridor.id,
        "source_country": corridor.source_country,
        "destination_country": corridor.destination_country,
        "source_currency": corridor.source_currency,
        "destination_currency": corridor.destination_currency,
        "base_fee_percent": corridor.base_fee_percent,
        "flat_fee_usd": corridor.flat_fee_usd,
        "minimum_fee_usd": corridor.minimum_fee_usd,
        "min_transfer": corridor.min_transfer_usd,
        "max_transfer": corridor.max_transfer_usd,
        "exchange_rate": corridor.exchange_rate,
        "exchange_rate_markup": corridor.exchange_rate_markup,
        "risk_score": corridor.risk_score,
        "status": corridor.status,
        "delivery_methods": delivery_methods,
        "providers": providers,
    }


@router.get("/{corridor_id}/rates", summary="Get corridor rates and fee breakdown")
async def get_corridor_rates(
    corridor_id: str,
    amount: float = Query(100.0, gt=0, description="Amount in source currency to calculate fees for"),
    db: AsyncSession = Depends(get_db),
):
    """Return exchange rate and detailed fee breakdown for a specific corridor and amount."""
    svc = CorridorService(db)
    try:
        breakdown = await svc.calculate_fee(corridor_id, amount)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    return breakdown
