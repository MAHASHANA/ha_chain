"""SQLAlchemy ORM models for ha_chain."""

import uuid
from datetime import datetime, timezone
from typing import Optional, List

from sqlalchemy import (
    Column, String, Float, Integer, Boolean, DateTime, ForeignKey,
    Text, Enum as SAEnum, JSON, UniqueConstraint, Index
)
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.database import Base
from app.enums import (
    TransferStatus, DeliveryMethod, MobileMoneyProvider, KYCLevel,
    AgentStatus, EscrowStatus, ComplianceAction, ComplianceCheckType,
    CorridorStatus, InvestmentStatus, DisputeStatus,
)


def generate_uuid() -> str:
    return str(uuid.uuid4())


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    phone: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    country: Mapped[str] = mapped_column(String(3), nullable=False)  # ISO 3166-1 alpha-3
    kyc_level: Mapped[int] = mapped_column(Integer, default=KYCLevel.NONE.value)
    wallet_address: Mapped[Optional[str]] = mapped_column(String(56), nullable=True)
    wallet_balance_usdc: Mapped[float] = mapped_column(Float, default=0.0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_sanctioned: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    sent_transfers: Mapped[List["Transfer"]] = relationship(
        "Transfer", back_populates="sender", foreign_keys="Transfer.sender_id"
    )
    agent_profile: Mapped[Optional["Agent"]] = relationship("Agent", back_populates="user", uselist=False)
    investments: Mapped[List["Investment"]] = relationship("Investment", back_populates="user")


class Agent(Base):
    __tablename__ = "agents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), unique=True, nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    country: Mapped[str] = mapped_column(String(3), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), default=AgentStatus.PENDING.value)
    is_online: Mapped[bool] = mapped_column(Boolean, default=False)
    delivery_methods: Mapped[str] = mapped_column(Text, default="[]")  # JSON array
    supported_providers: Mapped[str] = mapped_column(Text, default="[]")  # JSON array
    rating: Mapped[float] = mapped_column(Float, default=5.0)
    total_transactions: Mapped[int] = mapped_column(Integer, default=0)
    successful_transactions: Mapped[int] = mapped_column(Integer, default=0)
    success_rate: Mapped[float] = mapped_column(Float, default=1.0)
    avg_delivery_minutes: Mapped[float] = mapped_column(Float, default=30.0)
    stake_amount_usdc: Mapped[float] = mapped_column(Float, default=0.0)
    daily_volume_usdc: Mapped[float] = mapped_column(Float, default=0.0)
    daily_limit_usdc: Mapped[float] = mapped_column(Float, default=10000.0)
    commission_rate: Mapped[float] = mapped_column(Float, default=0.005)  # 0.5%
    staking_tx_hash: Mapped[Optional[str]] = mapped_column(String(66), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    user: Mapped["User"] = relationship("User", back_populates="agent_profile")
    transfers: Mapped[List["Transfer"]] = relationship("Transfer", back_populates="agent")


class Corridor(Base):
    __tablename__ = "corridors"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    source_country: Mapped[str] = mapped_column(String(3), nullable=False)
    destination_country: Mapped[str] = mapped_column(String(3), nullable=False)
    source_currency: Mapped[str] = mapped_column(String(3), nullable=False)
    destination_currency: Mapped[str] = mapped_column(String(3), nullable=False)
    base_fee_percent: Mapped[float] = mapped_column(Float, nullable=False)
    flat_fee_usd: Mapped[float] = mapped_column(Float, default=0.0)
    minimum_fee_usd: Mapped[float] = mapped_column(Float, default=1.0)
    min_transfer_usd: Mapped[float] = mapped_column(Float, default=5.0)
    max_transfer_usd: Mapped[float] = mapped_column(Float, default=10000.0)
    exchange_rate: Mapped[float] = mapped_column(Float, nullable=False)
    exchange_rate_markup: Mapped[float] = mapped_column(Float, default=0.01)  # 1% markup
    risk_score: Mapped[int] = mapped_column(Integer, default=5)  # 1-10
    status: Mapped[str] = mapped_column(String(20), default=CorridorStatus.ACTIVE.value)
    supported_delivery_methods: Mapped[str] = mapped_column(Text, default="[]")
    supported_providers: Mapped[str] = mapped_column(Text, default="[]")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    __table_args__ = (
        UniqueConstraint("source_country", "destination_country", name="uq_corridor"),
        Index("ix_corridor_countries", "source_country", "destination_country"),
    )


class Transfer(Base):
    __tablename__ = "transfers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    sender_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    agent_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("agents.id"), nullable=True)
    corridor_id: Mapped[str] = mapped_column(String(36), ForeignKey("corridors.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default=TransferStatus.QUOTED.value, index=True)

    # Amounts
    send_amount_usd: Mapped[float] = mapped_column(Float, nullable=False)
    fee_usd: Mapped[float] = mapped_column(Float, nullable=False)
    total_debit_usd: Mapped[float] = mapped_column(Float, nullable=False)
    exchange_rate: Mapped[float] = mapped_column(Float, nullable=False)
    receive_amount_local: Mapped[float] = mapped_column(Float, nullable=False)
    agent_commission_usd: Mapped[float] = mapped_column(Float, default=0.0)

    # Receiver details
    receiver_name: Mapped[str] = mapped_column(String(255), nullable=False)
    receiver_phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    receiver_city: Mapped[str] = mapped_column(String(100), nullable=False)
    receiver_country: Mapped[str] = mapped_column(String(3), nullable=False)

    # Delivery
    delivery_method: Mapped[str] = mapped_column(String(20), nullable=False)
    mobile_money_provider: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    pickup_code: Mapped[Optional[str]] = mapped_column(String(6), nullable=True)

    # Escrow
    escrow_tx_hash: Mapped[Optional[str]] = mapped_column(String(66), nullable=True)
    escrow_status: Mapped[str] = mapped_column(String(20), default=EscrowStatus.PENDING.value)
    release_tx_hash: Mapped[Optional[str]] = mapped_column(String(66), nullable=True)

    # Compliance
    compliance_status: Mapped[str] = mapped_column(
        String(20), default=ComplianceAction.APPROVED.value
    )
    compliance_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Ratings
    sender_rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 1-5
    agent_rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 1-5

    # Timestamps
    quote_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    initiated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    matched_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    accepted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    delivered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    sender: Mapped["User"] = relationship("User", back_populates="sent_transfers", foreign_keys=[sender_id])
    agent: Mapped[Optional["Agent"]] = relationship("Agent", back_populates="transfers")
    corridor: Mapped["Corridor"] = relationship("Corridor")
    compliance_checks: Mapped[List["ComplianceCheck"]] = relationship("ComplianceCheck", back_populates="transfer")
    dispute: Mapped[Optional["Dispute"]] = relationship("Dispute", back_populates="transfer", uselist=False)


class ComplianceCheck(Base):
    __tablename__ = "compliance_checks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    transfer_id: Mapped[str] = mapped_column(String(36), ForeignKey("transfers.id"), nullable=False)
    check_type: Mapped[str] = mapped_column(String(30), nullable=False)
    result: Mapped[str] = mapped_column(String(20), nullable=False)
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    risk_score: Mapped[int] = mapped_column(Integer, default=0)  # 0-100
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    transfer: Mapped["Transfer"] = relationship("Transfer", back_populates="compliance_checks")


class Dispute(Base):
    __tablename__ = "disputes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    transfer_id: Mapped[str] = mapped_column(String(36), ForeignKey("transfers.id"), unique=True, nullable=False)
    opened_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default=DisputeStatus.OPEN.value)
    resolution_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    transfer: Mapped["Transfer"] = relationship("Transfer", back_populates="dispute")


class TokenizedAsset(Base):
    __tablename__ = "tokenized_assets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    symbol: Mapped[str] = mapped_column(String(10), nullable=False, unique=True)
    asset_type: Mapped[str] = mapped_column(String(50), nullable=False)  # sukuk, real_estate, equity
    total_supply: Mapped[float] = mapped_column(Float, nullable=False)
    price_per_token_usd: Mapped[float] = mapped_column(Float, nullable=False)
    annual_yield_percent: Mapped[float] = mapped_column(Float, default=0.0)
    issuer: Mapped[str] = mapped_column(String(255), nullable=False)
    stellar_asset_code: Mapped[Optional[str]] = mapped_column(String(12), nullable=True)
    stellar_issuer: Mapped[Optional[str]] = mapped_column(String(56), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Investment(Base):
    __tablename__ = "investments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    asset_id: Mapped[str] = mapped_column(String(36), ForeignKey("tokenized_assets.id"), nullable=False)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    purchase_price_usd: Mapped[float] = mapped_column(Float, nullable=False)
    current_value_usd: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default=InvestmentStatus.ACTIVE.value)
    purchase_tx_hash: Mapped[Optional[str]] = mapped_column(String(66), nullable=True)
    sale_tx_hash: Mapped[Optional[str]] = mapped_column(String(66), nullable=True)
    sold_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    user: Mapped["User"] = relationship("User", back_populates="investments")
    asset: Mapped["TokenizedAsset"] = relationship("TokenizedAsset")


class SanctionsList(Base):
    """Cached sanctions list entries for OFAC screening."""
    __tablename__ = "sanctions_list"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    aliases: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    country: Mapped[Optional[str]] = mapped_column(String(3), nullable=True)
    source: Mapped[str] = mapped_column(String(50), nullable=False)  # OFAC, UN, EU
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
