"""Compliance / regulator dashboard endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, require_admin
from app.models.models import (
    ComplianceCheck as ModelsCheck,
    Transfer as ModelsTransfer,
    User as ModelsUser,
    Dispute as ModelsDispute,
)

router = APIRouter(prefix="/compliance", tags=["compliance"])


# ------------------------------------------------------------------
# Alerts / Checks
# ------------------------------------------------------------------


@router.get("/alerts", summary="List compliance alerts and flagged transfers")
async def list_alerts(
    severity: Optional[str] = Query(None, description="Filter: flagged, enhanced_review, blocked, sar_filed"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    admin_id: uuid.UUID = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """List compliance checks that were flagged or required action."""
    stmt = select(ModelsCheck).where(
        ModelsCheck.result.notin_(["approved"]),
    )
    if severity:
        stmt = stmt.where(ModelsCheck.result == severity)
    stmt = stmt.order_by(ModelsCheck.created_at.desc()).limit(limit).offset(offset)

    result = await db.execute(stmt)
    checks = result.scalars().all()

    return {
        "alerts": [
            {
                "id": c.id,
                "transfer_id": c.transfer_id,
                "check_type": c.check_type,
                "result": c.result,
                "details": c.details,
                "risk_score": c.risk_score,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            }
            for c in checks
        ],
        "total": len(checks),
    }


@router.get("/transfers/{transfer_id}/checks", summary="Get compliance checks for a transfer")
async def get_transfer_checks(
    transfer_id: str,
    admin_id: uuid.UUID = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ModelsCheck)
        .where(ModelsCheck.transfer_id == transfer_id)
        .order_by(ModelsCheck.created_at)
    )
    checks = result.scalars().all()

    return {
        "transfer_id": transfer_id,
        "checks": [
            {
                "id": c.id,
                "check_type": c.check_type,
                "result": c.result,
                "details": c.details,
                "risk_score": c.risk_score,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            }
            for c in checks
        ],
    }


# ------------------------------------------------------------------
# Dashboard stats
# ------------------------------------------------------------------


@router.get("/dashboard", summary="Compliance dashboard overview")
async def compliance_dashboard(
    admin_id: uuid.UUID = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Aggregate compliance metrics for the regulator dashboard."""
    # Total flagged transfers
    flagged_q = await db.execute(
        select(sa_func.count(ModelsCheck.id)).where(
            ModelsCheck.result.in_(["flagged", "enhanced_review", "sar_filed"])
        )
    )
    flagged_count = flagged_q.scalar() or 0

    # Blocked transfers
    blocked_q = await db.execute(
        select(sa_func.count(ModelsCheck.id)).where(ModelsCheck.result == "blocked")
    )
    blocked_count = blocked_q.scalar() or 0

    # Open disputes
    disputes_q = await db.execute(
        select(sa_func.count(ModelsDispute.id)).where(
            ModelsDispute.status.in_(["open", "investigating"])
        )
    )
    open_disputes = disputes_q.scalar() or 0

    # Total transfers today
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    today_q = await db.execute(
        select(sa_func.count(ModelsTransfer.id)).where(
            ModelsTransfer.created_at >= today_start
        )
    )
    today_transfers = today_q.scalar() or 0

    # Total volume today
    vol_q = await db.execute(
        select(sa_func.coalesce(sa_func.sum(ModelsTransfer.send_amount_usd), 0)).where(
            ModelsTransfer.created_at >= today_start,
            ModelsTransfer.status.notin_(["cancelled", "refunded", "expired"]),
        )
    )
    today_volume = float(vol_q.scalar() or 0)

    # High-risk transfers (risk_score >= 50)
    high_risk_q = await db.execute(
        select(sa_func.count(ModelsCheck.id)).where(ModelsCheck.risk_score >= 50)
    )
    high_risk_count = high_risk_q.scalar() or 0

    return {
        "flagged_transfers": flagged_count,
        "blocked_transfers": blocked_count,
        "open_disputes": open_disputes,
        "today_transfers": today_transfers,
        "today_volume_usd": today_volume,
        "high_risk_checks": high_risk_count,
    }


# ------------------------------------------------------------------
# Dispute management
# ------------------------------------------------------------------


@router.get("/disputes", summary="List open disputes")
async def list_disputes(
    status_filter: Optional[str] = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    admin_id: uuid.UUID = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(ModelsDispute)
    if status_filter:
        stmt = stmt.where(ModelsDispute.status == status_filter)
    stmt = stmt.order_by(ModelsDispute.created_at.desc()).limit(limit).offset(offset)

    result = await db.execute(stmt)
    disputes = result.scalars().all()

    return {
        "disputes": [
            {
                "id": d.id,
                "transfer_id": d.transfer_id,
                "opened_by": d.opened_by,
                "reason": d.reason,
                "status": d.status,
                "resolution_notes": d.resolution_notes,
                "created_at": d.created_at.isoformat() if d.created_at else None,
                "resolved_at": d.resolved_at.isoformat() if d.resolved_at else None,
            }
            for d in disputes
        ],
        "total": len(disputes),
    }


@router.post("/disputes/{dispute_id}/resolve", summary="Resolve a dispute")
async def resolve_dispute(
    dispute_id: str,
    resolution: str = Query(..., description="resolved_sender | resolved_agent | closed"),
    notes: str = Query("", description="Resolution notes"),
    admin_id: uuid.UUID = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ModelsDispute).where(ModelsDispute.id == dispute_id)
    )
    dispute = result.scalar_one_or_none()
    if not dispute:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dispute not found")

    dispute.status = resolution
    dispute.resolution_notes = notes
    dispute.resolved_at = datetime.now(timezone.utc)

    # Update the transfer status back from disputed
    transfer_q = await db.execute(
        select(ModelsTransfer).where(ModelsTransfer.id == dispute.transfer_id)
    )
    transfer = transfer_q.scalar_one_or_none()
    if transfer:
        if resolution == "resolved_sender":
            # Refund the sender
            from app.services.transfer_service import TransferService
            svc = TransferService(db)
            try:
                await svc.cancel_transfer(transfer.id, transfer.sender_id)
            except ValueError:
                pass  # May already be cancelled
        elif resolution in ("resolved_agent", "closed"):
            transfer.status = "completed"

    await db.flush()

    return {
        "dispute_id": dispute.id,
        "status": dispute.status,
        "resolution_notes": dispute.resolution_notes,
        "resolved_at": dispute.resolved_at.isoformat(),
    }
