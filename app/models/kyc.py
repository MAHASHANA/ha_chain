"""KYC verification and sanctions screening models."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class KYCVerification(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A single KYC verification submission and its review outcome."""

    __tablename__ = "kyc_verifications"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    level: Mapped[int] = mapped_column(
        nullable=False, comment="1=basic, 2=enhanced, 3=full",
    )
    method: Mapped[str] = mapped_column(
        String(30), nullable=False,
        comment="passport | id_card | biometric_only",
    )
    document_type: Mapped[str | None] = mapped_column(
        String(30), nullable=True,
        comment="passport | national_id | drivers_license | residence_permit",
    )
    document_hash: Mapped[str | None] = mapped_column(
        String(128), nullable=True,
        comment="SHA-256 hash of the uploaded document",
    )
    biometric_hash: Mapped[str | None] = mapped_column(
        String(128), nullable=True,
        comment="SHA-256 hash of biometric data",
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending", index=True,
        comment="pending | approved | rejected",
    )
    verified_by: Mapped[str | None] = mapped_column(
        String(200), nullable=True,
        comment="Reviewer identifier (user id or system label)",
    )
    verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True,
    )

    # --- Relationships -------------------------------------------------------
    user: Mapped[User] = relationship(  # type: ignore[name-defined]
        "User", back_populates="kyc_verifications",
    )

    def __repr__(self) -> str:
        return f"<KYCVerification {self.id} level={self.level} status={self.status!r}>"


class SanctionsCheck(Base, UUIDPrimaryKeyMixin):
    """Result of a sanctions / watchlist screening for a user."""

    __tablename__ = "sanctions_checks"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    provider: Mapped[str] = mapped_column(
        String(30), nullable=False,
        comment="chainalysis | elliptic",
    )
    result: Mapped[str] = mapped_column(
        String(20), nullable=False,
        comment="clear | match | pending_review",
    )
    checked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), index=True,
    )
    details_json: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True,
    )

    # --- Relationships -------------------------------------------------------
    user: Mapped[User] = relationship(  # type: ignore[name-defined]
        "User", back_populates="sanctions_checks",
    )

    def __repr__(self) -> str:
        return f"<SanctionsCheck {self.id} provider={self.provider!r} result={self.result!r}>"
