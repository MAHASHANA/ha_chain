"""Corridor, payment method, and exchange rate models."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Corridor(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A supported money-transfer route between two countries / currencies."""

    __tablename__ = "corridors"
    __table_args__ = (
        UniqueConstraint(
            "source_country", "destination_country",
            "source_currency", "destination_currency",
            name="uq_corridor_route",
        ),
    )

    source_country: Mapped[str] = mapped_column(
        String(3), nullable=False, index=True, comment="ISO 3166-1 alpha-3",
    )
    destination_country: Mapped[str] = mapped_column(
        String(3), nullable=False, index=True, comment="ISO 3166-1 alpha-3",
    )
    source_currency: Mapped[str] = mapped_column(String(10), nullable=False)
    destination_currency: Mapped[str] = mapped_column(String(10), nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, index=True,
    )
    base_fee_percent: Mapped[float] = mapped_column(
        Numeric(5, 4), nullable=False, default=0.005,
        comment="Decimal fraction, e.g. 0.005 = 0.5%",
    )
    min_fee: Mapped[float] = mapped_column(
        Numeric(18, 6), nullable=False, default=0.99,
    )
    max_fee: Mapped[float] = mapped_column(
        Numeric(18, 6), nullable=False, default=50.00,
    )
    min_transfer: Mapped[float] = mapped_column(
        Numeric(18, 2), nullable=False, default=10,
    )
    max_transfer: Mapped[float] = mapped_column(
        Numeric(18, 2), nullable=False, default=10_000,
    )
    estimated_delivery_minutes: Mapped[int] = mapped_column(
        Integer, nullable=False, default=60,
    )
    regulatory_notes: Mapped[str | None] = mapped_column(
        Text, nullable=True,
    )

    # --- Relationships -------------------------------------------------------
    payment_methods: Mapped[list[CorridorPaymentMethod]] = relationship(
        "CorridorPaymentMethod", back_populates="corridor", lazy="selectin",
        cascade="all, delete-orphan",
    )
    exchange_rates: Mapped[list[ExchangeRate]] = relationship(
        "ExchangeRate", back_populates="corridor", lazy="noload",
        cascade="all, delete-orphan",
        order_by="ExchangeRate.fetched_at.desc()",
    )

    def __repr__(self) -> str:
        return (
            f"<Corridor {self.id} {self.source_country}/{self.source_currency} "
            f"-> {self.destination_country}/{self.destination_currency}>"
        )


class CorridorPaymentMethod(Base, UUIDPrimaryKeyMixin):
    """Available payout method within a corridor (e.g. M-Pesa in KEN)."""

    __tablename__ = "corridor_payment_methods"

    corridor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("corridors.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    method_type: Mapped[str] = mapped_column(
        String(30), nullable=False,
        comment="mobile_money | bank | cash | wallet",
    )
    provider_name: Mapped[str] = mapped_column(
        String(100), nullable=False,
        comment="e.g. Zaad, M-Pesa, UPI, SPEI, GCash",
    )
    provider_code: Mapped[str] = mapped_column(
        String(50), nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True,
    )
    additional_fee: Mapped[float] = mapped_column(
        Numeric(18, 6), nullable=False, default=0,
    )

    # --- Relationships -------------------------------------------------------
    corridor: Mapped[Corridor] = relationship(
        "Corridor", back_populates="payment_methods",
    )

    def __repr__(self) -> str:
        return f"<CorridorPaymentMethod {self.id} {self.provider_name} ({self.method_type})>"


class ExchangeRate(Base, UUIDPrimaryKeyMixin):
    """Cached FX rate snapshot for a corridor."""

    __tablename__ = "exchange_rates"

    corridor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("corridors.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    rate: Mapped[float] = mapped_column(
        Numeric(18, 8), nullable=False,
    )
    source: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="Data provider or API that supplied this rate",
    )
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), index=True,
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True,
    )

    # --- Relationships -------------------------------------------------------
    corridor: Mapped[Corridor] = relationship(
        "Corridor", back_populates="exchange_rates",
    )

    def __repr__(self) -> str:
        return f"<ExchangeRate {self.id} rate={self.rate} source={self.source!r}>"
