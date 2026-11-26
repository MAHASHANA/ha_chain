"""Demo endpoints for testing: faucet, matching trigger, reset."""

from __future__ import annotations

import uuid as _uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.dependencies import get_current_user_id, get_db
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


@demo_router.post("/kyc-verify", summary="Demo-only: auto-approve basic KYC for the caller")
async def demo_kyc_verify(
    user_id: _uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Stand-in for a real KYC provider so the web demo can place orders.

    Requires the caller's JWT and only ever verifies the caller. Disabled
    when ``APP_ENV=production``.
    """
    if get_settings().APP_ENV.lower() == "production":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    from app.models.user import User
    from app.services.kyc_service import KYCService

    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not (user.is_verified and user.kyc_level >= 1):
        kyc = KYCService(db)
        record = await kyc.submit_verification(user_id, level=1, method="id_card")
        await kyc.approve_verification(record.id, verified_by="demo-auto-approve")
    return {"user_id": str(user_id), "kyc_level": user.kyc_level, "is_verified": user.is_verified}


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
            "stellar_tx_hash": m.stellar_tx_hash,
            "stellar_explorer": f"https://stellar.expert/explorer/testnet/tx/{m.stellar_tx_hash}" if m.stellar_tx_hash else None,
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


@demo_router.post("/scenario", summary="Run full investor demo scenario")
async def run_scenario(db: AsyncSession = Depends(get_db)):
    """One-click investor demo: creates 2 users, submits opposite orders,
    runs matching, returns the complete story with fee comparison."""
    import uuid
    import time
    from app.models.user import User, UserWallet
    from app.core.security import hash_password
    from app.services import fx_rates

    start_time = time.time()

    # Get live FX rate
    rate = await fx_rates.get_rate("USD", "INR")
    send_amount_usd = 500.0
    receive_amount_inr = round(send_amount_usd * rate, 2)

    # Create Ali (USA, sends USD -> INR)
    ali_id = str(uuid.uuid4())
    ali = User(
        id=ali_id,
        email=f"ali_{ali_id[:6]}@demo.com",
        phone=f"+1{ali_id[:10].replace('-','')}",
        password_hash=hash_password("demo1234"),
        full_name="Ali Khan",
        country_code="USA",
        default_currency="USD",
        kyc_level=1,
        is_verified=True,
    )
    db.add(ali)
    ali_wallet = UserWallet(user_id=ali_id, currency="USDC", balance=10000, is_primary=True)
    db.add(ali_wallet)

    # Create Raj (India, sends INR -> USD)
    raj_id = str(uuid.uuid4())
    raj = User(
        id=raj_id,
        email=f"raj_{raj_id[:6]}@demo.com",
        phone=f"+91{raj_id[:10].replace('-','')}",
        password_hash=hash_password("demo1234"),
        full_name="Raj Patel",
        country_code="IND",
        default_currency="INR",
        kyc_level=1,
        is_verified=True,
    )
    db.add(raj)
    raj_wallet = UserWallet(user_id=raj_id, currency="USDC", balance=10000, is_primary=True)
    db.add(raj_wallet)
    await db.flush()

    # Submit orders -- through the same KYC + sanctions gate as the public API
    from app.api.v1.matching import enforce_matching_compliance

    ali_recipient = {"name": "Priya Sharma", "account": "priya@upi", "method": "upi"}
    raj_recipient = {"name": "Mike Johnson", "account": "+14155559999", "method": "ach"}
    await enforce_matching_compliance(db, ali_id, ali_recipient)
    await enforce_matching_compliance(db, raj_id, raj_recipient)

    engine = MatchingEngine(db)

    ali_order = await engine.submit_order(
        user_id=ali_id,
        source_currency="USD",
        target_currency="INR",
        amount=send_amount_usd,
        recipient_info=ali_recipient,
    )

    raj_order = await engine.submit_order(
        user_id=raj_id,
        source_currency="INR",
        target_currency="USD",
        amount=receive_amount_inr,
        recipient_info=raj_recipient,
    )

    # Run matching
    stats = await engine.run_matching_cycle()
    elapsed_ms = round((time.time() - start_time) * 1000)

    # Reload orders
    ali_order = (await db.execute(select(MatchOrder).where(MatchOrder.id == ali_order.id))).scalar_one()
    raj_order = (await db.execute(select(MatchOrder).where(MatchOrder.id == raj_order.id))).scalar_one()

    # Get payments
    payments_q = await db.execute(select(LocalPayment).order_by(LocalPayment.created_at.desc()).limit(4))
    payments = [
        {"currency": p.currency, "amount": p.amount, "method": p.payment_method, "tx_ref": p.tx_reference, "status": p.status}
        for p in payments_q.scalars().all()
    ]

    # Fee comparison
    ha_chain_fee = 0.99
    wise_fee = round(send_amount_usd * 0.00643 + 1.50, 2)
    remitly_fee = round(send_amount_usd * 0.018, 2)
    wu_fee = round(send_amount_usd * 0.036, 2)

    wise_receive = round((send_amount_usd - wise_fee) * rate * 0.995, 2)  # 0.5% markup
    remitly_receive = round((send_amount_usd - remitly_fee) * rate * 0.982, 2)  # 1.8% markup
    wu_receive = round((send_amount_usd - wu_fee) * rate * 0.96, 2)  # 4% markup

    return {
        "scenario": "USA to India",
        "sender": {"name": "Ali Khan", "country": "USA", "currency": "USD"},
        "receiver": {"name": "Priya Sharma", "country": "India", "currency": "INR"},
        "amount_sent_usd": send_amount_usd,
        "fx_rate": round(rate, 2),
        "matching": {
            "ali_status": ali_order.status,
            "raj_status": raj_order.status,
            "match_type": stats.get("direct_matches", 0) > 0 and "direct" or "partial",
            "stats": stats,
        },
        "payments": payments,
        "fee_comparison": {
            "ha_chain": {"fee": ha_chain_fee, "recipient_gets": receive_amount_inr, "savings_vs_wu": round(wu_fee - ha_chain_fee, 2)},
            "wise": {"fee": wise_fee, "recipient_gets": wise_receive},
            "remitly": {"fee": remitly_fee, "recipient_gets": remitly_receive},
            "western_union": {"fee": wu_fee, "recipient_gets": wu_receive},
        },
        "elapsed_ms": elapsed_ms,
        "message": f"${send_amount_usd} matched in {elapsed_ms}ms. Recipient gets {receive_amount_inr:,.2f} INR via UPI. Fee: $0.99. Western Union would charge ${wu_fee}."
    }


@demo_router.get("/fee-compare", summary="Compare fees for any amount")
async def fee_compare(amount: float = 500, source: str = "USD", target: str = "INR"):
    """Compare Ha_Chain fees vs competitors for a given transfer."""
    from app.services import fx_rates
    rate = await fx_rates.get_rate(source.upper(), target.upper())

    ha_fee = 0.99
    ha_receive = round((amount - ha_fee) * rate, 2)

    wise_fee = round(amount * 0.00643 + 1.50, 2)
    wise_receive = round((amount - wise_fee) * rate * 0.995, 2)

    remitly_fee = round(amount * 0.018, 2)
    remitly_receive = round((amount - remitly_fee) * rate * 0.982, 2)

    wu_fee = round(amount * 0.036, 2)
    wu_receive = round((amount - wu_fee) * rate * 0.96, 2)

    return {
        "amount": amount,
        "source": source.upper(),
        "target": target.upper(),
        "rate": round(rate, 2),
        "providers": [
            {"name": "Ha_Chain", "fee": ha_fee, "recipient_gets": ha_receive, "fee_pct": round(ha_fee / amount * 100, 2)},
            {"name": "Wise", "fee": wise_fee, "recipient_gets": wise_receive, "fee_pct": round(wise_fee / amount * 100, 2)},
            {"name": "Remitly", "fee": remitly_fee, "recipient_gets": remitly_receive, "fee_pct": round(remitly_fee / amount * 100, 2)},
            {"name": "Western Union", "fee": wu_fee, "recipient_gets": wu_receive, "fee_pct": round(wu_fee / amount * 100, 2)},
        ],
        "savings_vs_wu": round(wu_fee - ha_fee, 2),
    }


@demo_router.get("/fx-rate", summary="Get live exchange rate")
async def get_fx_rate(source: str = "USD", target: str = "INR"):
    """Get live exchange rate between two currencies."""
    from app.services import fx_rates
    rate = await fx_rates.get_rate(source.upper(), target.upper())
    usd_value_of_1_source = await fx_rates.get_usd_value(1.0, source.upper())
    return {
        "source": source.upper(),
        "target": target.upper(),
        "rate": rate,
        "usd_equivalent": usd_value_of_1_source,
    }


@demo_router.get("/fx-rates", summary="Get all exchange rates to USD")
async def get_all_fx_rates():
    """Get exchange rates for all supported currencies."""
    from app.services.fx_rates import FALLBACK_RATES, get_rate
    rates = {}
    for currency in FALLBACK_RATES:
        r = await get_rate(currency, "USD")
        rates[currency] = round(r, 6)
    return rates


@demo_router.get("/blockchain", summary="View on-chain transaction history")
async def blockchain_explorer():
    """Fetch recent Ha_Chain transactions recorded on Stellar testnet."""
    from app.services import stellar_service
    txs = await stellar_service.get_protocol_transactions(limit=30)
    protocol_key = await stellar_service.ensure_protocol_account()
    return {
        "network": "Stellar Testnet",
        "protocol_account": protocol_key,
        "protocol_explorer": f"https://stellar.expert/explorer/testnet/account/{protocol_key}",
        "transactions": txs,
        "total": len(txs),
    }
