"""Agent, stake, and coverage area models."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Agent(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Licensed hawala agent who facilitates local cash-in / cash-out."""

    __tablename__ = "agents"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
        unique=True, nullable=False, index=True,
    )
    license_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending", index=True,
        comment="pending | active | suspended | revoked",
    )
    stake_amount_usdc: Mapped[float] = mapped_column(
        Numeric(18, 6), nullable=False, default=0,
    )
    rating_avg: Mapped[float] = mapped_column(
        Numeric(3, 2), nullable=False, default=0,
    )
    total_transactions: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0,
    )
    coverage_city: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True,
    )
    coverage_country: Mapped[str] = mapped_column(
        String(3), nullable=False, index=True, comment="ISO 3166-1 alpha-3",
    )
    daily_limit: Mapped[float] = mapped_column(
        Numeric(18, 2), nullable=False, default=50_000,
    )
    operating_currency: Mapped[str] = mapped_column(
        String(10), nullable=False, default="USD",
    )
    commission_rate: Mapped[float] = mapped_column(
        Numeric(5, 4), nullable=False, default=0.005, comment="Decimal fraction, e.g. 0.005 = 0.5%",
    )
    is_online: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, index=True,
    )

    # --- Relationships -------------------------------------------------------
    user: Mapped[User] = relationship(  # type: ignore[name-defined]
        "User", back_populates="agent", lazy="selectin",
    )
    stakes: Mapped[list[AgentStake]] = relationship(
        "AgentStake", back_populates="agent", lazy="selectin",
        cascade="all, delete-orphan",
    )
    coverage_areas: Mapped[list[AgentCoverage]] = relationship(
        "AgentCoverage", back_populates="agent", lazy="selectin",
        cascade="all, delete-orphan",
    )
    ratings: Mapped[list[Rating]] = relationship(  # type: ignore[name-defined]
        "Rating", back_populates="rated_agent", lazy="noload",
    )
    reputation: Mapped[AgentReputation | None] = relationship(  # type: ignore[name-defined]
        "AgentReputation", back_populates="agent", uselist=False, lazy="noload",
    )
    settlement_batches: Mapped[list[SettlementBatch]] = relationship(  # type: ignore[name-defined]
        "SettlementBatch", back_populates="agent", lazy="noload",
    )

    def __repr__(self) -> str:
        return f"<Agent {self.id} city={self.coverage_city!r} status={self.license_status!r}>"


class AgentStake(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """On-chain USDC performance bond deposited by an agent."""

    __tablename__ = "agent_stakes"

    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    amount: Mapped[float] = mapped_column(
        Numeric(18, 6), nullable=False,
    )
    tx_hash: Mapped[str | None] = mapped_column(
        String(128), nullable=True, unique=True, comment="Blockchain transaction hash",
    )
    staked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(),
    )
    released_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="locked", index=True,
        comment="locked | released | forfeited",
    )

    # --- Relationships -------------------------------------------------------
    agent: Mapped[Agent] = relationship("Agent", back_populates="stakes")

    def __repr__(self) -> str:
        return f"<AgentStake {self.id} amount={self.amount} status={self.status!r}>"


class AgentCoverage(Base, UUIDPrimaryKeyMixin):
    """Geographic service area and accepted payment methods for an agent."""

    __tablename__ = "agent_coverage"

    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    country_code: Mapped[str] = mapped_column(
        String(3), nullable=False, index=True, comment="ISO 3166-1 alpha-3",
    )
    city: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    lat: Mapped[float] = mapped_column(Float, nullable=False)
    lng: Mapped[float] = mapped_column(Float, nullable=False)
    radius_km: Mapped[float] = mapped_column(Float, nullable=False, default=10.0)
    payment_methods: Mapped[list | None] = mapped_column(
        JSONB, nullable=True, comment="JSON array of accepted payment method codes",
    )

    # --- Relationships -------------------------------------------------------
    agent: Mapped[Agent] = relationship("Agent", back_populates="coverage_areas")

    def __repr__(self) -> str:
        return f"<AgentCoverage {self.id} {self.city} ({self.country_code})>"
