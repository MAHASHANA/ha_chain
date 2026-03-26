"""Enumerations used across the application."""

import enum


class TransferStatus(str, enum.Enum):
    QUOTED = "quoted"
    INITIATED = "initiated"
    ESCROW_LOCKED = "escrow_locked"
    AGENT_MATCHED = "agent_matched"
    AGENT_ACCEPTED = "agent_accepted"
    IN_PROGRESS = "in_progress"
    DELIVERED = "delivered"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    DISPUTED = "disputed"
    EXPIRED = "expired"
    COMPLIANCE_HOLD = "compliance_hold"
    COMPLIANCE_BLOCKED = "compliance_blocked"


class DeliveryMethod(str, enum.Enum):
    CASH_PICKUP = "cash_pickup"
    MOBILE_MONEY = "mobile_money"
    BANK_TRANSFER = "bank_transfer"
    WALLET = "wallet"


class MobileMoneyProvider(str, enum.Enum):
    ZAAD = "zaad"           # Somalia
    EDAHAB = "edahab"       # Somalia
    MPESA = "mpesa"         # Kenya/East Africa
    UPI = "upi"             # India
    SPEI = "spei"           # Mexico
    GCASH = "gcash"         # Philippines


class KYCLevel(int, enum.Enum):
    NONE = 0
    BASIC = 1       # Phone + ID = $1000/day
    ENHANCED = 2    # Address + selfie = $5000/day
    FULL = 3        # Full verification = $50000/day


class AgentStatus(str, enum.Enum):
    PENDING = "pending"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DEACTIVATED = "deactivated"


class EscrowStatus(str, enum.Enum):
    PENDING = "pending"
    LOCKED = "locked"
    RELEASED = "released"
    REFUNDED = "refunded"
    DISPUTED = "disputed"


class ComplianceAction(str, enum.Enum):
    APPROVED = "approved"
    FLAGGED = "flagged"
    ENHANCED_REVIEW = "enhanced_review"
    BLOCKED = "blocked"
    SAR_FILED = "sar_filed"


class ComplianceCheckType(str, enum.Enum):
    SANCTIONS = "sanctions"
    VELOCITY = "velocity"
    STRUCTURING = "structuring"
    COUNTRY_RISK = "country_risk"
    AMOUNT_THRESHOLD = "amount_threshold"
    PATTERN = "pattern"


class CorridorStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


class InvestmentStatus(str, enum.Enum):
    PENDING = "pending"
    ACTIVE = "active"
    SOLD = "sold"
    CANCELLED = "cancelled"


class DisputeStatus(str, enum.Enum):
    OPEN = "open"
    INVESTIGATING = "investigating"
    RESOLVED_SENDER = "resolved_sender"
    RESOLVED_AGENT = "resolved_agent"
    CLOSED = "closed"
