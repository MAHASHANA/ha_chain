"""SQLAlchemy ORM models for the peer-to-peer currency matching pool.

These models replace the traditional remittance-agent pipeline with a
matching-engine architecture where money never crosses borders.  Users
with opposite currency needs are matched and each pays locally.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional, List

from sqlalchemy import (
    Column, String, Float, Integer, Boolean, DateTime, ForeignKey,
    Text, Index, UniqueConstraint, Numeric, CheckConstraint, JSON,
)
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.database import Base


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _generate_uuid() -> str:
    return str(uuid.uuid4())


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# MatchOrder -- pending orders in the pool
# ---------------------------------------------------------------------------

class MatchOrder(Base):
    """An order submitted by a user who wants currency A delivered as
    currency B to a recipient in another country.

    Orders sit in the pool until the matching engine pairs them with
    counter-orders (direct, partial, or triangular) or fills them from
    the liquidity reserve.
    """

    __tablename__ = "match_orders"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_generate_uuid)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)

    # Currency pair -- what the user has and what they need delivered
    source_currency: Mapped[str] = mapped_column(String(3), nullable=False)
    target_currency: Mapped[str] = mapped_column(String(3), nullable=False)

    # Amounts (source currency)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    amount_matched: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    amount_unmatched: Mapped[float] = mapped_column(Float, nullable=False)

    # Recipient details stored as JSON for flexibility
    recipient_info: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Status lifecycle
    status: Mapped[str] = mapped_column(String(30), default="pending", nullable=False, index=True)
    # pending -> partially_matched -> fully_matched -> filled -> expired -> cancelled

    # Matching preferences
    max_wait_until: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Exchange rate at submission time (informational)
    indicative_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)
    matched_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    matches_as_order1: Mapped[List["Match"]] = relationship(
        "Match", back_populates="order1", foreign_keys="Match.order_id_1",
    )
    matches_as_order2: Mapped[List["Match"]] = relationship(
        "Match", back_populates="order2", foreign_keys="Match.order_id_2",
    )
    matches_as_order3: Mapped[List["Match"]] = relationship(
        "Match", back_populates="order3", foreign_keys="Match.order_id_3",
    )
    liquidity_fills: Mapped[List["LiquidityFill"]] = relationship(
        "LiquidityFill", back_populates="order",
    )
    local_payments: Mapped[List["LocalPayment"]] = relationship(
        "LocalPayment", back_populates="order",
    )

    __table_args__ = (
        Index("ix_match_orders_pair_status", "source_currency", "target_currency", "status"),
        Index("ix_match_orders_status_expires", "status", "max_wait_until"),
        Index("ix_match_orders_unmatched", "status", "amount_unmatched"),
        CheckConstraint("amount > 0", name="ck_match_orders_amount_positive"),
        CheckConstraint("amount_unmatched >= 0", name="ck_match_orders_unmatched_nonneg"),
        CheckConstraint("amount_matched >= 0", name="ck_match_orders_matched_nonneg"),
    )


# ---------------------------------------------------------------------------
# Match -- executed matches (direct, partial, triangular)
# ---------------------------------------------------------------------------

class Match(Base):
    """Record of a match between two or three orders.

    Match types:
    - ``direct``: order_1 and order_2 are perfect counterparties
    - ``partial``: order_1 and order_2 overlap partially
    - ``triangular``: A->B->C->A circular match, order_id_3 is set
    """

    __tablename__ = "matches"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_generate_uuid)

    order_id_1: Mapped[str] = mapped_column(
        String(36), ForeignKey("match_orders.id"), nullable=False, index=True,
    )
    order_id_2: Mapped[str] = mapped_column(
        String(36), ForeignKey("match_orders.id"), nullable=False, index=True,
    )
    order_id_3: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("match_orders.id"), nullable=True, index=True,
    )

    match_type: Mapped[str] = mapped_column(String(20), nullable=False)  # direct, partial, triangular
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    exchange_rate: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    protocol_fee: Mapped[float] = mapped_column(Float, default=0.0)

    # Status: pending_execution -> executing -> settled -> failed
    status: Mapped[str] = mapped_column(String(30), default="pending_execution", nullable=False, index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    executed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    order1: Mapped["MatchOrder"] = relationship(
        "MatchOrder", back_populates="matches_as_order1", foreign_keys=[order_id_1],
    )
    order2: Mapped["MatchOrder"] = relationship(
        "MatchOrder", back_populates="matches_as_order2", foreign_keys=[order_id_2],
    )
    order3: Mapped[Optional["MatchOrder"]] = relationship(
        "MatchOrder", back_populates="matches_as_order3", foreign_keys=[order_id_3],
    )
    local_payments: Mapped[List["LocalPayment"]] = relationship(
        "LocalPayment", back_populates="match",
    )

    __table_args__ = (
        Index("ix_matches_type_status", "match_type", "status"),
        CheckConstraint("amount > 0", name="ck_matches_amount_positive"),
    )


# ---------------------------------------------------------------------------
# LiquidityPosition -- LP deposits
# ---------------------------------------------------------------------------

class LiquidityPosition(Base):
    """A liquidity provider's deposit in a specific currency pool.

    LPs earn a spread (0.2%) when their liquidity is used to fill
    unmatched portions of user orders.
    """

    __tablename__ = "liquidity_positions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_generate_uuid)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, index=True)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    earned_fees: Mapped[float] = mapped_column(Float, default=0.0)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    # Relationships
    fills: Mapped[List["LiquidityFill"]] = relationship(
        "LiquidityFill", back_populates="position",
    )

    __table_args__ = (
        Index("ix_lp_positions_currency_active", "currency", "is_active"),
        CheckConstraint("amount >= 0", name="ck_lp_amount_nonneg"),
    )


# ---------------------------------------------------------------------------
# LiquidityFill -- when LP fills an unmatched order
# ---------------------------------------------------------------------------

class LiquidityFill(Base):
    """Record of LP liquidity being used to fill an unmatched order.

    The LP earns a spread on each fill.
    """

    __tablename__ = "liquidity_fills"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_generate_uuid)
    order_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("match_orders.id"), nullable=False, index=True,
    )
    lp_position_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("liquidity_positions.id"), nullable=False, index=True,
    )

    amount: Mapped[float] = mapped_column(Float, nullable=False)
    spread_earned: Mapped[float] = mapped_column(Float, nullable=False)

    # Status: pending -> settled -> failed -> reversed
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)

    filled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    # Relationships
    order: Mapped["MatchOrder"] = relationship("MatchOrder", back_populates="liquidity_fills")
    position: Mapped["LiquidityPosition"] = relationship("LiquidityPosition", back_populates="fills")

    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_lp_fill_amount_positive"),
        CheckConstraint("spread_earned >= 0", name="ck_lp_fill_spread_nonneg"),
    )


# ---------------------------------------------------------------------------
# PoolSnapshot -- periodic snapshots of pool state
# ---------------------------------------------------------------------------

class PoolSnapshot(Base):
    """Point-in-time snapshot of a currency pool.

    Captured periodically for analytics and the real-time dashboard.
    """

    __tablename__ = "pool_snapshots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_generate_uuid)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, index=True)

    total_deposits: Mapped[float] = mapped_column(Float, default=0.0)
    pending_orders: Mapped[int] = mapped_column(Integer, default=0)
    match_rate_24h: Mapped[float] = mapped_column(Float, default=0.0)
    avg_wait_seconds: Mapped[float] = mapped_column(Float, default=0.0)

    snapshot_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, index=True)

    __table_args__ = (
        Index("ix_pool_snapshots_currency_time", "currency", "snapshot_at"),
    )


# ---------------------------------------------------------------------------
# LocalPayment -- record of each local settlement
# ---------------------------------------------------------------------------

class LocalPayment(Base):
    """Record of a domestic payment executed as part of a match settlement.

    When Ali (USA, USD->INR) matches with Raj (India, INR->USD):
    - Payment 1: Ali's USD -> Raj's US recipient (ACH)
    - Payment 2: Raj's INR -> Ali's India recipient (UPI)
    Both are local, no FX.
    """

    __tablename__ = "local_payments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_generate_uuid)
    match_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("matches.id"), nullable=True, index=True,
    )
    order_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("match_orders.id"), nullable=True, index=True,
    )

    # Payment details
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    recipient_info: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    payment_method: Mapped[str] = mapped_column(String(30), nullable=False)
    payment_rail: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    tx_reference: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Status: initiated -> processing -> completed -> failed -> reversed
    status: Mapped[str] = mapped_column(String(20), default="initiated", nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    executed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    match: Mapped[Optional["Match"]] = relationship("Match", back_populates="local_payments")
    order: Mapped[Optional["MatchOrder"]] = relationship("MatchOrder", back_populates="local_payments")

    __table_args__ = (
        Index("ix_local_payments_status", "status"),
        CheckConstraint("amount > 0", name="ck_local_payment_amount_positive"),
    )
