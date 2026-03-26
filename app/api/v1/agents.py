"""Agent registration, staking, dashboard, and transfer management endpoints."""

from __future__ import annotations

import json
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.agent import (
    AgentDashboardResponse,
    AgentRegisterRequest,
    AgentResponse,
    SetOnlineRequest,
    StakeRequest,
    StakeResponse,
)
from app.api.schemas.transfer import TransferResponse
from app.dependencies import get_current_agent_id, get_current_user_id, get_db
from app.enums import AgentStatus
from app.models.models import Agent as ModelsAgent, Transfer as ModelsTransfer, User as ModelsUser

router = APIRouter(prefix="/agents", tags=["agents"])


@router.post(
    "/register",
    response_model=AgentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register as an agent",
)
async def register_agent(
    body: AgentRegisterRequest,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    # Check if already registered
    existing = await db.execute(
        select(ModelsAgent).where(ModelsAgent.user_id == str(user_id))
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User is already registered as an agent",
        )

    agent = ModelsAgent(
        user_id=str(user_id),
        city=body.city,
        country=body.country,
        status=AgentStatus.PENDING.value,
        delivery_methods=json.dumps(body.supported_delivery_methods),
        supported_providers=json.dumps(body.supported_currencies),
        commission_rate=body.commission_rate,
    )
    db.add(agent)
    await db.flush()

    return AgentResponse(
        id=uuid.UUID(agent.id),
        user_id=uuid.UUID(agent.user_id),
        business_name=body.business_name,
        country=agent.country,
        city=agent.city,
        license_status=agent.status,
        is_online=agent.is_online,
        commission_rate=agent.commission_rate,
        staked_amount=agent.stake_amount_usdc,
        rating_avg=agent.rating,
        rating_count=0,
        total_transactions=agent.total_transactions,
        created_at=agent.created_at,
    )


@router.post("/stake", response_model=StakeResponse, summary="Stake USDC as an agent")
async def stake_usdc(
    body: StakeRequest,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    # Find agent record for this user
    result = await db.execute(
        select(ModelsAgent).where(ModelsAgent.user_id == str(user_id))
    )
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent profile not found")

    # Check user has enough USDC balance
    user_q = await db.execute(select(ModelsUser).where(ModelsUser.id == str(user_id)))
    user = user_q.scalar_one_or_none()
    if not user or user.wallet_balance_usdc < body.amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient USDC balance for staking",
        )

    # Debit user wallet and add to stake
    user.wallet_balance_usdc -= body.amount
    agent.stake_amount_usdc += body.amount
    if body.tx_hash:
        agent.staking_tx_hash = body.tx_hash

    # Auto-activate when minimum stake met (500 USDC)
    if agent.stake_amount_usdc >= 500 and agent.status == AgentStatus.PENDING.value:
        agent.status = AgentStatus.ACTIVE.value

    await db.flush()

    return StakeResponse(
        id=uuid.UUID(agent.id),
        agent_id=uuid.UUID(agent.id),
        amount=body.amount,
        currency="USDC",
        status="locked",
        tx_hash=body.tx_hash,
        staked_at=agent.created_at,
    )


@router.get("/dashboard", response_model=AgentDashboardResponse, summary="Agent dashboard stats")
async def agent_dashboard(
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ModelsAgent).where(ModelsAgent.user_id == str(user_id))
    )
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent profile not found")

    # Count active transfers
    active_q = await db.execute(
        select(ModelsTransfer).where(
            ModelsTransfer.agent_id == agent.id,
            ModelsTransfer.status.in_(["agent_matched", "agent_accepted", "in_progress"]),
        )
    )
    active_transfers = len(active_q.scalars().all())

    return AgentDashboardResponse(
        agent_id=agent.id,
        business_name=f"Agent-{agent.id[:8]}",
        license_status=agent.status,
        is_online=agent.is_online,
        staked_amount=agent.stake_amount_usdc,
        total_transactions=agent.total_transactions,
        total_volume=agent.daily_volume_usdc,
        rating_avg=agent.rating,
        rating_count=agent.total_transactions,
        success_rate=agent.success_rate,
        avg_delivery_minutes=int(agent.avg_delivery_minutes),
        active_transfers=active_transfers,
        today_volume=agent.daily_volume_usdc,
        daily_limit=agent.daily_limit_usdc,
        remaining_capacity=max(0, agent.daily_limit_usdc - agent.daily_volume_usdc),
    )


@router.put("/status", summary="Set agent online/offline status")
async def set_online_status(
    body: SetOnlineRequest,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ModelsAgent).where(ModelsAgent.user_id == str(user_id))
    )
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent profile not found")
    if agent.status != AgentStatus.ACTIVE.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Agent is not active")

    agent.is_online = body.is_online
    await db.flush()

    return {"is_online": agent.is_online}


@router.post(
    "/transfers/{transfer_id}/accept",
    summary="Agent accepts a transfer assignment",
)
async def accept_transfer(
    transfer_id: str,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    # Find agent for this user
    agent_q = await db.execute(
        select(ModelsAgent).where(ModelsAgent.user_id == str(user_id))
    )
    agent = agent_q.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent profile not found")

    from app.services.transfer_service import TransferService

    svc = TransferService(db)
    try:
        transfer = await svc.agent_accept(transfer_id, agent.id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    return {
        "transfer_id": transfer.id,
        "status": transfer.status,
        "accepted_at": transfer.accepted_at.isoformat() if transfer.accepted_at else None,
    }
