"""User, wallet, and beneficiary models."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, SoftDeleteMixin, UUIDPrimaryKeyMixin


class User(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    """Platform user -- senders, receivers, and agents share this identity."""

    __tablename__ = "users"

    phone: Mapped[str] = mapped_column(
        String(20), unique=True, nullable=False, index=True,
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True,
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    country_code: Mapped[str] = mapped_column(
        String(3), nullable=False, index=True, comment="ISO 3166-1 alpha-3",
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    kyc_level: Mapped[int] = mapped_column(
        default=0, nullable=False, comment="0=none, 1=basic, 2=enhanced, 3=full",
    )
    default_currency: Mapped[str] = mapped_column(
        String(10), default="USD", nullable=False,
    )

    # --- Relationships -------------------------------------------------------
    wallets: Mapped[list[UserWallet]] = relationship(
        "UserWallet", back_populates="user", lazy="selectin",
        cascade="all, delete-orphan",
    )
    beneficiaries: Mapped[list[UserBeneficiary]] = relationship(
        "UserBeneficiary", back_populates="user", lazy="selectin",
        cascade="all, delete-orphan",
    )
    agent: Mapped[Agent | None] = relationship(  # type: ignore[name-defined]
        "Agent", back_populates="user", uselist=False, lazy="noload",
    )
    kyc_verifications: Mapped[list[KYCVerification]] = relationship(  # type: ignore[name-defined]
        "KYCVerification", back_populates="user", lazy="noload",
    )
    sanctions_checks: Mapped[list[SanctionsCheck]] = relationship(  # type: ignore[name-defined]
        "SanctionsCheck", back_populates="user", lazy="noload",
    )
    notifications: Mapped[list[Notification]] = relationship(  # type: ignore[name-defined]
        "Notification", back_populates="user", lazy="noload",
    )
    investment_positions: Mapped[list[InvestmentPosition]] = relationship(  # type: ignore[name-defined]
        "InvestmentPosition", back_populates="user", lazy="noload",
    )

    def __repr__(self) -> str:
        return f"<User {self.id} phone={self.phone!r}>"


class UserWallet(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Per-currency wallet for a user (on-platform balance + optional chain address)."""

    __tablename__ = "user_wallets"
    __table_args__ = (
        UniqueConstraint("user_id", "currency", name="uq_user_wallet_currency"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    currency: Mapped[str] = mapped_column(
        String(10), nullable=False, default="USDC",
    )
    balance: Mapped[float] = mapped_column(
        Numeric(18, 6), nullable=False, default=0,
    )
    wallet_address: Mapped[str | None] = mapped_column(
        String(128), nullable=True, comment="On-chain wallet address",
    )
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # --- Relationships -------------------------------------------------------
    user: Mapped[User] = relationship("User", back_populates="wallets")

    def __repr__(self) -> str:
        return f"<UserWallet {self.id} {self.currency} user={self.user_id}>"


class UserBeneficiary(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Saved beneficiary for repeat transfers."""

    __tablename__ = "user_beneficiaries"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    beneficiary_name: Mapped[str] = mapped_column(String(200), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    country_code: Mapped[str] = mapped_column(
        String(3), nullable=False, comment="ISO 3166-1 alpha-3",
    )
    default_delivery_method: Mapped[str] = mapped_column(
        String(30), nullable=False, default="mobile_money",
        comment="mobile_money | cash_pickup | wallet",
    )

    # --- Relationships -------------------------------------------------------
    user: Mapped[User] = relationship("User", back_populates="beneficiaries")

    def __repr__(self) -> str:
        return f"<UserBeneficiary {self.id} {self.beneficiary_name!r}>"
