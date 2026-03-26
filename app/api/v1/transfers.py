"""Transfer endpoints: quote, create, track, confirm delivery, dispute, cancel."""

from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.transfer import (
    CancelRequest,
    ConfirmDeliveryRequest,
    DisputeRequest,
    QuoteRequest,
    QuoteResponse,
    TransferCreateRequest,
    TransferResponse,
)
from app.dependencies import get_current_agent_id, get_current_user_id, get_db
from app.models.models import (
    Agent as ModelsAgent,
    Corridor as ModelsCorridor,
    Transfer as ModelsTransfer,
)
from app.services.transfer_service import TransferService
from app.services.matching_service import MatchingService

router = APIRouter(prefix="/transfers", tags=["transfers"])


# ------------------------------------------------------------------
# Quote
# ------------------------------------------------------------------


@router.post("/quote", status_code=status.HTTP_201_CREATED, summary="Get a transfer quote")
async def create_quote(
    body: QuoteRequest,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Create a quote for sending money to a destination country.

    The quote includes exchange rate, fees, and estimated delivery time.
    Quotes are valid for 15 minutes.
    """
    # Find corridor by sender country + destination country
    from app.models.user import User

    user_q = await db.execute(select(User).where(User.id == user_id))
    user = user_q.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    corridor_q = await db.execute(
        select(ModelsCorridor).where(
            ModelsCorridor.source_country == user.country_code,
            ModelsCorridor.destination_country == body.receiver_country,
            ModelsCorridor.status == "active",
        )
    )
    corridor = corridor_q.scalar_one_or_none()
    if not corridor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No active corridor from {user.country_code} to {body.receiver_country}",
        )

    svc = TransferService(db)
    try:
        transfer = await svc.create_quote(
            sender_id=str(user_id),
            corridor_id=corridor.id,
            send_amount_usd=body.amount,
            delivery_method=body.delivery_method,
            receiver_name="Pending",
            receiver_phone=None,
            receiver_city="Pending",
            receiver_country=body.receiver_country,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    return {
        "id": transfer.id,
        "corridor_id": transfer.corridor_id,
        "source_currency": corridor.source_currency,
        "destination_currency": corridor.destination_currency,
        "send_amount": transfer.send_amount_usd,
        "receive_amount": transfer.receive_amount_local,
        "exchange_rate": transfer.exchange_rate,
        "fee": transfer.fee_usd,
        "total_cost": transfer.total_debit_usd,
        "delivery_method": transfer.delivery_method,
        "expires_at": transfer.quote_expires_at.isoformat() if transfer.quote_expires_at else None,
        "status": transfer.status,
    }


# ------------------------------------------------------------------
# Create transfer (initiate from quote)
# ------------------------------------------------------------------


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Initiate a transfer from a quote",
)
async def create_transfer(
    body: TransferCreateRequest,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Accept a quote and initiate the transfer.

    This will run compliance checks, debit the sender's wallet,
    lock escrow on-chain, and begin agent matching.
    """
    # Fetch the quoted transfer
    transfer_q = await db.execute(
        select(ModelsTransfer).where(ModelsTransfer.id == str(body.quote_id))
    )
    transfer = transfer_q.scalar_one_or_none()
    if not transfer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quote not found")
    if transfer.sender_id != str(user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Quote does not belong to you")

    # Update receiver info
    transfer.receiver_name = body.receiver_name
    transfer.receiver_phone = body.receiver_phone
    if body.receiver_city:
        transfer.receiver_city = body.receiver_city
    if body.delivery_method:
        transfer.delivery_method = body.delivery_method
    await db.flush()

    svc = TransferService(db)
    try:
        transfer = await svc.initiate_transfer(transfer.id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    # Trigger agent matching (non-blocking -- in production this would be a Celery task)
    matching_svc = MatchingService(db)
    svc_with_matching = TransferService(db, matching_service=matching_svc)
    try:
        await svc_with_matching.match_agent(transfer.id)
    except Exception:
        pass  # Agent matching is best-effort at this stage

    return _transfer_to_dict(transfer)


# ------------------------------------------------------------------
# Get transfer by ID
# ------------------------------------------------------------------


@router.get("/{transfer_id}", summary="Get transfer details")
async def get_transfer(
    transfer_id: str,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ModelsTransfer).where(ModelsTransfer.id == transfer_id)
    )
    transfer = result.scalar_one_or_none()
    if not transfer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transfer not found")

    # Verify ownership (sender or assigned agent's user)
    if transfer.sender_id != str(user_id):
        if transfer.agent_id:
            agent_q = await db.execute(
                select(ModelsAgent).where(ModelsAgent.id == transfer.agent_id)
            )
            agent = agent_q.scalar_one_or_none()
            if not agent or agent.user_id != str(user_id):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        else:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return _transfer_to_dict(transfer)


# ------------------------------------------------------------------
# List user's transfers
# ------------------------------------------------------------------


@router.get("", summary="List user's transfers")
async def list_transfers(
    user_id: uuid.UUID = Depends(get_current_user_id),
    status_filter: Optional[str] = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(ModelsTransfer).where(
        ModelsTransfer.sender_id == str(user_id)
    )
    if status_filter:
        stmt = stmt.where(ModelsTransfer.status == status_filter)
    stmt = stmt.order_by(ModelsTransfer.created_at.desc()).limit(limit).offset(offset)

    result = await db.execute(stmt)
    transfers = result.scalars().all()
    return [_transfer_to_dict(t) for t in transfers]


# ------------------------------------------------------------------
# Confirm delivery (agent)
# ------------------------------------------------------------------


@router.post(
    "/{transfer_id}/confirm-delivery",
    summary="Agent confirms delivery to receiver",
)
async def confirm_delivery(
    transfer_id: str,
    body: ConfirmDeliveryRequest,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    # Find agent record
    agent_q = await db.execute(
        select(ModelsAgent).where(ModelsAgent.user_id == str(user_id))
    )
    agent = agent_q.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not registered as an agent")

    svc = TransferService(db)
    try:
        transfer = await svc.confirm_delivery(
            transfer_id=transfer_id,
            agent_id=agent.id,
            pickup_code=body.verification_data,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    return _transfer_to_dict(transfer)


# ------------------------------------------------------------------
# Dispute
# ------------------------------------------------------------------


@router.post("/{transfer_id}/dispute", summary="Open a dispute on a transfer")
async def dispute_transfer(
    transfer_id: str,
    body: DisputeRequest,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ModelsTransfer).where(ModelsTransfer.id == transfer_id)
    )
    transfer = result.scalar_one_or_none()
    if not transfer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transfer not found")
    if transfer.sender_id != str(user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the sender can file a dispute")

    from app.enums import TransferStatus, DisputeStatus
    from app.models.models import Dispute

    if transfer.status in (
        TransferStatus.COMPLETED.value,
        TransferStatus.CANCELLED.value,
        TransferStatus.REFUNDED.value,
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot dispute a transfer in status: {transfer.status}",
        )

    dispute = Dispute(
        transfer_id=transfer.id,
        opened_by=str(user_id),
        reason=body.reason,
        status=DisputeStatus.OPEN.value,
    )
    db.add(dispute)

    old_status = transfer.status
    transfer.status = TransferStatus.DISPUTED.value
    await db.flush()

    return {
        "transfer_id": transfer.id,
        "status": transfer.status,
        "dispute_id": dispute.id,
        "dispute_status": dispute.status,
        "reason": dispute.reason,
    }


# ------------------------------------------------------------------
# Cancel
# ------------------------------------------------------------------


@router.post("/{transfer_id}/cancel", summary="Cancel a transfer and refund")
async def cancel_transfer(
    transfer_id: str,
    body: CancelRequest,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    svc = TransferService(db)
    try:
        transfer = await svc.cancel_transfer(transfer_id, str(user_id))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    return _transfer_to_dict(transfer)


# ------------------------------------------------------------------
# Rate transfer
# ------------------------------------------------------------------


@router.post("/{transfer_id}/rate", summary="Rate a completed transfer")
async def rate_transfer(
    transfer_id: str,
    rating: int = Query(..., ge=1, le=5),
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    svc = TransferService(db)
    try:
        transfer = await svc.rate_transfer(transfer_id, str(user_id), rating)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    return {"transfer_id": transfer.id, "sender_rating": transfer.sender_rating, "agent_rating": transfer.agent_rating}


# ------------------------------------------------------------------
# Helper
# ------------------------------------------------------------------


def _transfer_to_dict(transfer: ModelsTransfer) -> dict:
    """Serialize a Transfer model to a JSON-friendly dict."""
    return {
        "id": transfer.id,
        "sender_id": transfer.sender_id,
        "agent_id": transfer.agent_id,
        "corridor_id": transfer.corridor_id,
        "status": transfer.status,
        "send_amount": transfer.send_amount_usd,
        "fee": transfer.fee_usd,
        "total_cost": transfer.total_debit_usd,
        "exchange_rate": transfer.exchange_rate,
        "receive_amount": transfer.receive_amount_local,
        "receiver_name": transfer.receiver_name,
        "receiver_phone": transfer.receiver_phone,
        "receiver_city": transfer.receiver_city,
        "receiver_country": transfer.receiver_country,
        "delivery_method": transfer.delivery_method,
        "pickup_code": transfer.pickup_code,
        "escrow_tx_hash": transfer.escrow_tx_hash,
        "escrow_status": transfer.escrow_status,
        "compliance_status": transfer.compliance_status,
        "quote_expires_at": transfer.quote_expires_at.isoformat() if transfer.quote_expires_at else None,
        "initiated_at": transfer.initiated_at.isoformat() if transfer.initiated_at else None,
        "matched_at": transfer.matched_at.isoformat() if transfer.matched_at else None,
        "accepted_at": transfer.accepted_at.isoformat() if transfer.accepted_at else None,
        "delivered_at": transfer.delivered_at.isoformat() if transfer.delivered_at else None,
        "completed_at": transfer.completed_at.isoformat() if transfer.completed_at else None,
        "cancelled_at": transfer.cancelled_at.isoformat() if transfer.cancelled_at else None,
        "created_at": transfer.created_at.isoformat() if transfer.created_at else None,
    }
