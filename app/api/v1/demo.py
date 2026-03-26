"""Demo endpoints for testing: faucet, matching trigger, reset."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.matching import MatchOrder, Match, LocalPayment
from app.services.matching_engine import MatchingEngine

demo_router = APIRouter(prefix="/api/v1/demo", tags=["demo"])


@demo_router.post("/faucet", summary="Give demo balance to a user wallet")
async def faucet(
    user_id: str,
    amount: float = 1000.0,
    currency: str = "USDC",
    db: AsyncSession = Depends(get_db),
):
    """Credit demo funds to a user's wallet. For testing only."""
    from app.models.user import User, UserWallet

    # Find user
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Find or create wallet
    wallet_q = await db.execute(
        select(UserWallet).where(
            UserWallet.user_id == user_id,
            UserWallet.currency == currency.upper(),
        )
    )
    wallet = wallet_q.scalar_one_or_none()
    if not wallet:
        wallet = UserWallet(
            user_id=user_id,
            currency=currency.upper(),
            balance=0,
            is_primary=(currency.upper() == "USDC"),
        )
        db.add(wallet)
        await db.flush()

    wallet.balance += amount
    await db.flush()

    return {
        "user_id": user_id,
        "currency": wallet.currency,
        "new_balance": wallet.balance,
        "credited": amount,
    }


@demo_router.post("/match-now", summary="Trigger matching cycle manually")
async def trigger_matching(db: AsyncSession = Depends(get_db)):
    """Run one full matching cycle immediately. Returns match stats."""
    engine = MatchingEngine(db)
    stats = await engine.run_matching_cycle()
    return stats


@demo_router.get("/orders", summary="List all orders in the system (admin view)")
async def list_all_orders(
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    """List all matching orders across all users."""
    result = await db.execute(
        select(MatchOrder)
        .order_by(MatchOrder.created_at.desc())
        .limit(limit)
    )
    orders = result.scalars().all()
    return [
        {
            "id": o.id,
            "user_id": o.user_id,
            "source_currency": o.source_currency,
            "target_currency": o.target_currency,
            "amount": o.amount,
            "amount_matched": o.amount_matched,
            "amount_unmatched": o.amount_unmatched,
            "status": o.status,
            "created_at": o.created_at.isoformat() if o.created_at else None,
            "matched_at": o.matched_at.isoformat() if o.matched_at else None,
        }
        for o in orders
    ]


@demo_router.get("/matches", summary="List all matches in the system")
async def list_all_matches(
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    """List all matches across the system."""
    result = await db.execute(
        select(Match)
        .order_by(Match.created_at.desc())
        .limit(limit)
    )
    matches = result.scalars().all()
    return [
        {
            "id": m.id,
            "match_type": m.match_type,
            "order_id_1": m.order_id_1,
            "order_id_2": m.order_id_2,
            "order_id_3": m.order_id_3,
            "amount": m.amount,
            "protocol_fee": m.protocol_fee,
            "status": m.status,
            "created_at": m.created_at.isoformat() if m.created_at else None,
            "executed_at": m.executed_at.isoformat() if m.executed_at else None,
        }
        for m in matches
    ]


@demo_router.get("/payments", summary="List all local payments")
async def list_all_payments(
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    """List all local payments that were executed."""
    result = await db.execute(
        select(LocalPayment)
        .order_by(LocalPayment.created_at.desc())
        .limit(limit)
    )
    payments = result.scalars().all()
    return [
        {
            "id": p.id,
            "match_id": p.match_id,
            "order_id": p.order_id,
            "currency": p.currency,
            "amount": p.amount,
            "payment_method": p.payment_method,
            "tx_reference": p.tx_reference,
            "status": p.status,
            "executed_at": p.executed_at.isoformat() if p.executed_at else None,
        }
        for p in payments
    ]


@demo_router.get("/stats", summary="Get system-wide demo stats")
async def demo_stats(db: AsyncSession = Depends(get_db)):
    """Get overall system statistics for the demo dashboard."""
    from app.models.user import User

    user_count = (await db.execute(select(func.count(User.id)))).scalar() or 0
    order_count = (await db.execute(select(func.count(MatchOrder.id)))).scalar() or 0
    match_count = (await db.execute(select(func.count(Match.id)))).scalar() or 0
    payment_count = (await db.execute(select(func.count(LocalPayment.id)))).scalar() or 0

    pending_orders = (await db.execute(
        select(func.count(MatchOrder.id)).where(MatchOrder.status.in_(["pending", "partially_matched"]))
    )).scalar() or 0

    matched_orders = (await db.execute(
        select(func.count(MatchOrder.id)).where(MatchOrder.status.in_(["fully_matched", "filled"]))
    )).scalar() or 0

    total_volume = (await db.execute(
        select(func.coalesce(func.sum(Match.amount), 0))
    )).scalar() or 0

    return {
        "users": user_count,
        "total_orders": order_count,
        "pending_orders": pending_orders,
        "matched_orders": matched_orders,
        "total_matches": match_count,
        "total_payments": payment_count,
        "total_volume_matched": round(float(total_volume), 2),
    }
