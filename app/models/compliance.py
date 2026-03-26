"""Compliance alert and suspicious activity report models."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ComplianceAlert(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """AML/CFT alert raised by automated rules or manual review."""

    __tablename__ = "compliance_alerts"

    transfer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("transfers.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    alert_type: Mapped[str] = mapped_column(
        String(30), nullable=False, index=True,
        comment="large_amount | structuring | sanctioned_country | velocity | pattern",
    )
    severity: Mapped[str] = mapped_column(
        String(10), nullable=False, index=True,
        comment="low | medium | high | critical",
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    auto_resolved: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False,
    )
    resolved_by: Mapped[str | None] = mapped_column(
        String(200), nullable=True, comment="Reviewer identifier",
    )
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )

    # --- Relationships -------------------------------------------------------
    transfer: Mapped[Transfer] = relationship(  # type: ignore[name-defined]
        "Transfer", back_populates="compliance_alerts",
    )
    suspicious_activity_reports: Mapped[list[SuspiciousActivityReport]] = relationship(
        "SuspiciousActivityReport", back_populates="alert", lazy="noload",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"<ComplianceAlert {self.id} type={self.alert_type!r} "
            f"severity={self.severity!r}>"
        )


class SuspiciousActivityReport(Base, UUIDPrimaryKeyMixin):
    """SAR filed with a regulatory authority in response to an alert."""

    __tablename__ = "suspicious_activity_reports"

    transfer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("transfers.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    alert_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("compliance_alerts.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    filed_with: Mapped[str] = mapped_column(
        String(30), nullable=False,
        comment="fincen | local_authority",
    )
    report_json: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True,
    )
    filed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), index=True,
    )

    # --- Relationships -------------------------------------------------------
    transfer: Mapped[Transfer] = relationship(  # type: ignore[name-defined]
        "Transfer", lazy="noload",
    )
    alert: Mapped[ComplianceAlert] = relationship(
        "ComplianceAlert", back_populates="suspicious_activity_reports",
    )

    def __repr__(self) -> str:
        return f"<SuspiciousActivityReport {self.id} filed_with={self.filed_with!r}>"
