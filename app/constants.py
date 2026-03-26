"""Enumeration types used across the ha_chain platform."""

from enum import Enum


class TransferStatus(str, Enum):
    """Lifecycle states for a remittance transfer."""

    QUOTE = "quote"
    PENDING = "pending"
    ESCROW_LOCKED = "escrow_locked"
    AGENT_MATCHED = "agent_matched"
    IN_DELIVERY = "in_delivery"
    DELIVERED = "delivered"
    COMPLETED = "completed"
    DISPUTED = "disputed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class DeliveryMethod(str, Enum):
    """Payout delivery channels."""

    MOBILE_MONEY = "mobile_money"
    CASH_PICKUP = "cash_pickup"
    WALLET = "wallet"
    BANK = "bank"


class KYCLevel(int, Enum):
    """Progressive KYC verification tiers."""

    NONE = 0
    BASIC = 1
    ENHANCED = 2
    FULL = 3


class KYCMethod(str, Enum):
    """Identity verification methods."""

    PASSPORT = "passport"
    ID_CARD = "id_card"
    BIOMETRIC_ONLY = "biometric_only"


class KYCDocumentType(str, Enum):
    """Accepted identity documents."""

    PASSPORT = "passport"
    NATIONAL_ID = "national_id"
    DRIVERS_LICENSE = "drivers_license"
    RESIDENCE_PERMIT = "residence_permit"


class KYCStatus(str, Enum):
    """Review status for a KYC submission."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class SanctionsResult(str, Enum):
    """Outcome of a sanctions-list screening."""

    CLEAR = "clear"
    MATCH = "match"
    PENDING_REVIEW = "pending_review"


class SanctionsProvider(str, Enum):
    """Third-party sanctions-screening providers."""

    CHAINALYSIS = "chainalysis"
    ELLIPTIC = "elliptic"


class AgentLicenseStatus(str, Enum):
    """Regulatory licence states for an agent."""

    PENDING = "pending"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    REVOKED = "revoked"


class StakeStatus(str, Enum):
    """Status of an agent's USDC performance stake."""

    LOCKED = "locked"
    RELEASED = "released"
    FORFEITED = "forfeited"


class AgentTier(str, Enum):
    """Reputation tier awarded to agents."""

    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    PLATINUM = "platinum"
    MASTER = "master"


class PaymentMethodType(str, Enum):
    """Corridor-level payment rail categories."""

    MOBILE_MONEY = "mobile_money"
    BANK = "bank"
    CASH = "cash"
    WALLET = "wallet"


class EscrowStatus(str, Enum):
    """On-chain escrow lifecycle."""

    PENDING = "pending"
    LOCKED = "locked"
    RELEASED = "released"
    REFUNDED = "refunded"


class SettlementStatus(str, Enum):
    """Batch settlement processing states."""

    PENDING = "pending"
    PROCESSING = "processing"
    SETTLED = "settled"
    FAILED = "failed"


class BlockchainNetwork(str, Enum):
    """Supported blockchain networks."""

    STELLAR = "stellar"
    ETHEREUM = "ethereum"
    BASE = "base"


class AssetType(str, Enum):
    """Tokenized asset classes available for investment."""

    TREASURY = "treasury"
    EQUITY = "equity"
    COMMODITY = "commodity"
    REAL_ESTATE = "real_estate"


class AssetProvider(str, Enum):
    """Asset tokenization providers."""

    BLACKROCK = "blackrock"
    SECURITIZE = "securitize"
    PAXOS = "paxos"


class RiskLevel(str, Enum):
    """Investment risk classification."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class InvestmentTxType(str, Enum):
    """Investment transaction direction."""

    BUY = "buy"
    SELL = "sell"


class AlertType(str, Enum):
    """AML/compliance alert triggers."""

    LARGE_AMOUNT = "large_amount"
    STRUCTURING = "structuring"
    SANCTIONED_COUNTRY = "sanctioned_country"
    VELOCITY = "velocity"
    PATTERN = "pattern"


class AlertSeverity(str, Enum):
    """Urgency classification for compliance alerts."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SARFiling(str, Enum):
    """Authorities that receive suspicious-activity reports."""

    FINCEN = "fincen"
    LOCAL_AUTHORITY = "local_authority"


class NotificationChannel(str, Enum):
    """User notification delivery channels."""

    SMS = "sms"
    PUSH = "push"
    EMAIL = "email"


class NotificationStatus(str, Enum):
    """Delivery status of a notification."""

    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"


class StatusChangedBy(str, Enum):
    """Actor that triggered a transfer status change."""

    USER = "user"
    AGENT = "agent"
    SYSTEM = "system"
