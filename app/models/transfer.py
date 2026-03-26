"""Transfer and status-log models."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Transfer(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A single remittance transaction from sender to receiver."""

    __tablename__ = "transfers"

    # --- Participants --------------------------------------------------------
    sender_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False, index=True,
    )
    receiver_phone: Mapped[str] = mapped_column(String(20), nullable=False)
    receiver_name: Mapped[str] = mapped_column(String(200), nullable=False)
    receiver_country: Mapped[str] = mapped_column(
        String(3), nullable=False, index=True, comment="ISO 3166-1 alpha-3",
    )

    # --- Agents (nullable -- matched later in lifecycle) ---------------------
    sending_agent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.id", ondelete="SET NULL"),
        nullable=True, index=True,
    )
    payout_agent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.id", ondelete="SET NULL"),
        nullable=True, index=True,
    )

    # --- Corridor ------------------------------------------------------------
    corridor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("corridors.id", ondelete="RESTRICT"),
        nullable=False, index=True,
    )

    # --- Amounts & FX --------------------------------------------------------
    amount_sent: Mapped[float] = mapped_column(Numeric(18, 6), nullable=False)
    amount_sent_currency: Mapped[str] = mapped_column(String(10), nullable=False)
    amount_received: Mapped[float] = mapped_column(Numeric(18, 6), nullable=False)
    amount_received_currency: Mapped[str] = mapped_column(String(10), nullable=False)
    exchange_rate: Mapped[float] = mapped_column(Numeric(18, 8), nullable=False)
    fee_amount: Mapped[float] = mapped_column(Numeric(18, 6), nullable=False, default=0)
    fee_currency: Mapped[str] = mapped_column(String(10), nullable=False)

    # --- Delivery ------------------------------------------------------------
    delivery_method: Mapped[str] = mapped_column(
        String(30), nullable=False,
        comment="mobile_money | cash_pickup | wallet | bank",
    )
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="quote", index=True,
        comment="quote | pending | escrow_locked | agent_matched | in_delivery | delivered | completed | disputed | cancelled | refunded",
    )
    pickup_code: Mapped[str | None] = mapped_column(
        String(6), nullable=True, index=True,
        comment="6-character code for cash-pickup",
    )

    # --- Blockchain references -----------------------------------------------
    escrow_tx_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    settlement_tx_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)

    # --- Timestamps ----------------------------------------------------------
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True,
    )

    # --- Relationships -------------------------------------------------------
    sender: Mapped[User] = relationship(  # type: ignore[name-defined]
        "User", foreign_keys=[sender_id], lazy="selectin",
    )
    sending_agent: Mapped[Agent | None] = relationship(  # type: ignore[name-defined]
        "Agent", foreign_keys=[sending_agent_id], lazy="noload",
    )
    payout_agent: Mapped[Agent | None] = relationship(  # type: ignore[name-defined]
        "Agent", foreign_keys=[payout_agent_id], lazy="noload",
    )
    corridor: Mapped[Corridor] = relationship(  # type: ignore[name-defined]
        "Corridor", lazy="selectin",
    )
    status_logs: Mapped[list[TransferStatusLog]] = relationship(
        "TransferStatusLog", back_populates="transfer", lazy="noload",
        cascade="all, delete-orphan",
        order_by="TransferStatusLog.created_at",
    )
    escrow_transactions: Mapped[list[EscrowTransaction]] = relationship(  # type: ignore[name-defined]
        "EscrowTransaction", back_populates="transfer", lazy="noload",
    )
    compliance_alerts: Mapped[list[ComplianceAlert]] = relationship(  # type: ignore[name-defined]
        "ComplianceAlert", back_populates="transfer", lazy="noload",
    )
    rating: Mapped[Rating | None] = relationship(  # type: ignore[name-defined]
        "Rating", back_populates="transfer", uselist=False, lazy="noload",
    )

    def __repr__(self) -> str:
        return (
            f"<Transfer {self.id} {self.amount_sent} {self.amount_sent_currency} "
            f"-> {self.amount_received} {self.amount_received_currency} "
            f"status={self.status!r}>"
        )


class TransferStatusLog(Base, UUIDPrimaryKeyMixin):
    """Immutable audit trail for every transfer state change."""

    __tablename__ = "transfer_status_logs"

    transfer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("transfers.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    old_status: Mapped[str | None] = mapped_column(String(30), nullable=True)
    new_status: Mapped[str] = mapped_column(String(30), nullable=False)
    changed_by: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="user | agent | system",
    )
    reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), index=True,
    )

    # --- Relationships -------------------------------------------------------
    transfer: Mapped[Transfer] = relationship("Transfer", back_populates="status_logs")

    def __repr__(self) -> str:
        return f"<TransferStatusLog {self.id} {self.old_status}->{self.new_status}>"
