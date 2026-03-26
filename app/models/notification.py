"""Notification model for multi-channel user messaging."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDPrimaryKeyMixin


class Notification(Base, UUIDPrimaryKeyMixin):
    """Outbound notification queued for delivery via SMS, push, or email."""

    __tablename__ = "notifications"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    channel: Mapped[str] = mapped_column(
        String(10), nullable=False, index=True,
        comment="sms | push | email",
    )
    template_key: Mapped[str] = mapped_column(
        String(100), nullable=False,
        comment="Identifies the notification template to render",
    )
    payload_json: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True,
        comment="Template variable values",
    )
    status: Mapped[str] = mapped_column(
        String(10), nullable=False, default="pending", index=True,
        comment="pending | sent | failed",
    )
    sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), index=True,
    )

    # --- Relationships -------------------------------------------------------
    user: Mapped[User] = relationship(  # type: ignore[name-defined]
        "User", back_populates="notifications",
    )

    def __repr__(self) -> str:
        return (
            f"<Notification {self.id} channel={self.channel!r} "
            f"template={self.template_key!r} status={self.status!r}>"
        )
