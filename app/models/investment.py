"""Tokenized asset and investment models."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class TokenizedAsset(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A tokenized real-world asset available for investment."""

    __tablename__ = "tokenized_assets"

    symbol: Mapped[str] = mapped_column(
        String(20), unique=True, nullable=False, index=True,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    asset_type: Mapped[str] = mapped_column(
        String(30), nullable=False,
        comment="treasury | equity | commodity | real_estate",
    )
    provider: Mapped[str] = mapped_column(
        String(100), nullable=False,
        comment="blackrock | securitize | paxos",
    )
    blockchain_address: Mapped[str | None] = mapped_column(
        String(128), nullable=True, unique=True,
    )
    current_price: Mapped[float] = mapped_column(
        Numeric(18, 6), nullable=False,
    )
    yield_apy: Mapped[float | None] = mapped_column(
        Numeric(8, 4), nullable=True,
        comment="Annualised percentage yield",
    )
    min_investment: Mapped[float] = mapped_column(
        Numeric(18, 6), nullable=False, default=1.0,
    )
    risk_level: Mapped[str] = mapped_column(
        String(10), nullable=False, default="low",
        comment="low | medium | high",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, index=True,
    )

    # --- Relationships -------------------------------------------------------
    positions: Mapped[list[InvestmentPosition]] = relationship(
        "InvestmentPosition", back_populates="asset", lazy="noload",
    )
    transactions: Mapped[list[InvestmentTransaction]] = relationship(
        "InvestmentTransaction", back_populates="asset", lazy="noload",
    )

    def __repr__(self) -> str:
        return f"<TokenizedAsset {self.id} {self.symbol} type={self.asset_type!r}>"


class InvestmentPosition(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """User's holding of a particular tokenized asset."""

    __tablename__ = "investment_positions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    asset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tokenized_assets.id", ondelete="RESTRICT"),
        nullable=False, index=True,
    )
    quantity: Mapped[float] = mapped_column(
        Numeric(18, 8), nullable=False, default=0,
    )
    avg_purchase_price: Mapped[float] = mapped_column(
        Numeric(18, 6), nullable=False,
    )
    current_value: Mapped[float] = mapped_column(
        Numeric(18, 6), nullable=False, default=0,
    )
    opened_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(),
    )

    # --- Relationships -------------------------------------------------------
    user: Mapped[User] = relationship(  # type: ignore[name-defined]
        "User", back_populates="investment_positions",
    )
    asset: Mapped[TokenizedAsset] = relationship(
        "TokenizedAsset", back_populates="positions", lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<InvestmentPosition {self.id} qty={self.quantity} asset={self.asset_id}>"


class InvestmentTransaction(Base, UUIDPrimaryKeyMixin):
    """Individual buy / sell order against a tokenized asset."""

    __tablename__ = "investment_transactions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    asset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tokenized_assets.id", ondelete="RESTRICT"),
        nullable=False, index=True,
    )
    tx_type: Mapped[str] = mapped_column(
        String(10), nullable=False,
        comment="buy | sell",
    )
    quantity: Mapped[float] = mapped_column(
        Numeric(18, 8), nullable=False,
    )
    price_per_unit: Mapped[float] = mapped_column(
        Numeric(18, 6), nullable=False,
    )
    total_amount: Mapped[float] = mapped_column(
        Numeric(18, 6), nullable=False,
    )
    tx_hash: Mapped[str | None] = mapped_column(
        String(128), nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), index=True,
    )

    # --- Relationships -------------------------------------------------------
    user: Mapped[User] = relationship(  # type: ignore[name-defined]
        "User", lazy="noload",
    )
    asset: Mapped[TokenizedAsset] = relationship(
        "TokenizedAsset", back_populates="transactions", lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<InvestmentTransaction {self.id} {self.tx_type} {self.quantity} @ {self.price_per_unit}>"
