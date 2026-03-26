"""SQLAlchemy ORM models for the ha_chain platform.

Importing this module ensures every model is registered with the shared
``Base.metadata`` so that Alembic auto-generation and ``create_all`` work
correctly.
"""

from app.db.base import Base  # noqa: F401 -- keep metadata populated

from app.models.user import User, UserWallet, UserBeneficiary
from app.models.agent import Agent, AgentStake, AgentCoverage
from app.models.transfer import Transfer, TransferStatusLog
from app.models.escrow import EscrowTransaction, SettlementBatch
from app.models.corridor import Corridor, CorridorPaymentMethod, ExchangeRate
from app.models.kyc import KYCVerification, SanctionsCheck
from app.models.rating import Rating, AgentReputation
from app.models.investment import TokenizedAsset, InvestmentPosition, InvestmentTransaction
from app.models.compliance import ComplianceAlert, SuspiciousActivityReport
from app.models.notification import Notification
from app.models.matching import (
    MatchOrder, Match, LiquidityPosition, LiquidityFill,
    LocalPayment, PoolSnapshot,
)

__all__ = [
    "Base",
    # user
    "User",
    "UserWallet",
    "UserBeneficiary",
    # agent
    "Agent",
    "AgentStake",
    "AgentCoverage",
    # transfer
    "Transfer",
    "TransferStatusLog",
    # escrow
    "EscrowTransaction",
    "SettlementBatch",
    # corridor
    "Corridor",
    "CorridorPaymentMethod",
    "ExchangeRate",
    # kyc
    "KYCVerification",
    "SanctionsCheck",
    # rating
    "Rating",
    "AgentReputation",
    # investment
    "TokenizedAsset",
    "InvestmentPosition",
    "InvestmentTransaction",
    # compliance
    "ComplianceAlert",
    "SuspiciousActivityReport",
    # notification
    "Notification",
    # matching (P2P)
    "MatchOrder",
    "Match",
    "LiquidityPosition",
    "LiquidityFill",
    "LocalPayment",
    "PoolSnapshot",
]
