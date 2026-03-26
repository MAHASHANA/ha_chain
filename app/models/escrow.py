"""Escrow and settlement batch models for blockchain-backed fund locking."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class EscrowTransaction(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """On-chain escrow record that locks funds for a transfer."""

    __tablename__ = "escrow_transactions"

    transfer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("transfers.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    blockchain: Mapped[str] = mapped_column(
        String(20), nullable=False,
        comment="stellar | ethereum | base",
    )
    tx_hash: Mapped[str | None] = mapped_column(
        String(128), nullable=True, unique=True,
    )
    amount_usdc: Mapped[float] = mapped_column(
        Numeric(18, 6), nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending", index=True,
        comment="pending | locked | released | refunded",
    )
    locked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    released_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    smart_contract_address: Mapped[str | None] = mapped_column(
        String(128), nullable=True,
    )

    # --- Relationships -------------------------------------------------------
    transfer: Mapped[Transfer] = relationship(  # type: ignore[name-defined]
        "Transfer", back_populates="escrow_transactions",
    )

    def __repr__(self) -> str:
        return (
            f"<EscrowTransaction {self.id} {self.amount_usdc} USDC "
            f"chain={self.blockchain!r} status={self.status!r}>"
        )


class SettlementBatch(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Aggregated settlement payout to an agent."""

    __tablename__ = "settlement_batches"

    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    total_amount: Mapped[float] = mapped_column(
        Numeric(18, 6), nullable=False,
    )
    currency: Mapped[str] = mapped_column(
        String(10), nullable=False, default="USDC",
    )
    batch_tx_hash: Mapped[str | None] = mapped_column(
        String(128), nullable=True, unique=True,
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending", index=True,
        comment="pending | processing | settled | failed",
    )
    settled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )

    # --- Relationships -------------------------------------------------------
    agent: Mapped[Agent] = relationship(  # type: ignore[name-defined]
        "Agent", back_populates="settlement_batches",
    )

    def __repr__(self) -> str:
        return f"<SettlementBatch {self.id} {self.total_amount} {self.currency} status={self.status!r}>"
