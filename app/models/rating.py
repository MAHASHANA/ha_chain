"""Rating and agent reputation models."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Rating(Base, UUIDPrimaryKeyMixin):
    """Post-transfer rating submitted by a user about an agent."""

    __tablename__ = "ratings"
    __table_args__ = (
        CheckConstraint("score >= 1 AND score <= 5", name="ck_rating_score_range"),
    )

    transfer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("transfers.id", ondelete="CASCADE"),
        nullable=False, unique=True, index=True,
    )
    rater_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    rated_agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    score: Mapped[int] = mapped_column(
        Integer, nullable=False, comment="1-5 star rating",
    )
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(),
    )

    # --- Relationships -------------------------------------------------------
    transfer: Mapped[Transfer] = relationship(  # type: ignore[name-defined]
        "Transfer", back_populates="rating",
    )
    rater: Mapped[User] = relationship(  # type: ignore[name-defined]
        "User", lazy="noload",
    )
    rated_agent: Mapped[Agent] = relationship(  # type: ignore[name-defined]
        "Agent", back_populates="ratings",
    )

    def __repr__(self) -> str:
        return f"<Rating {self.id} score={self.score} agent={self.rated_agent_id}>"


class AgentReputation(Base, UUIDPrimaryKeyMixin):
    """Denormalized, periodically recomputed reputation snapshot for an agent."""

    __tablename__ = "agent_reputations"

    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False, unique=True, index=True,
    )
    avg_score: Mapped[float] = mapped_column(
        Numeric(3, 2), nullable=False, default=0,
    )
    total_ratings: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0,
    )
    avg_delivery_minutes: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False, default=0,
    )
    success_rate: Mapped[float] = mapped_column(
        Numeric(5, 4), nullable=False, default=1.0,
        comment="Fraction of completed transfers (0.0 - 1.0)",
    )
    tier: Mapped[str] = mapped_column(
        String(20), nullable=False, default="bronze",
        comment="bronze | silver | gold | platinum | master",
    )
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(),
    )

    # --- Relationships -------------------------------------------------------
    agent: Mapped[Agent] = relationship(  # type: ignore[name-defined]
        "Agent", back_populates="reputation",
    )

    def __repr__(self) -> str:
        return f"<AgentReputation {self.id} tier={self.tier!r} avg={self.avg_score}>"
