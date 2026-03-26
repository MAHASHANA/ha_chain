"""Custom exception hierarchy for the ha_chain platform."""

from typing import Any, Dict, Optional


class HaChainError(Exception):
    """Base exception for all application-level errors."""

    def __init__(self, message: str = "An unexpected error occurred", *, detail: Optional[Dict[str, Any]] = None):
        self.message = message
        self.detail = detail or {}
        super().__init__(self.message)


# ---------- Auth / User -----------------------------------------------------

class AuthenticationError(HaChainError):
    """Raised when credentials are invalid or missing."""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message)


class AuthorizationError(HaChainError):
    """Raised when the authenticated user lacks required permissions."""

    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(message)


class UserNotFoundError(HaChainError):
    """Raised when a user lookup yields no result."""

    def __init__(self, identifier: str = ""):
        super().__init__(f"User not found: {identifier}" if identifier else "User not found")


# ---------- KYC -------------------------------------------------------------

class KYCRequiredError(HaChainError):
    """Raised when an operation requires a higher KYC level."""

    def __init__(self, required_level: int, current_level: int):
        super().__init__(
            f"KYC level {required_level} required; current level is {current_level}",
            detail={"required_level": required_level, "current_level": current_level},
        )


# ---------- Transfer --------------------------------------------------------

class TransferError(HaChainError):
    """Base class for transfer-related failures."""


class TransferNotFoundError(TransferError):
    """Raised when a transfer lookup yields no result."""

    def __init__(self, transfer_id: str = ""):
        super().__init__(f"Transfer not found: {transfer_id}" if transfer_id else "Transfer not found")


class InvalidTransferStateError(TransferError):
    """Raised when a state transition is illegal."""

    def __init__(self, current_status: str, attempted_status: str):
        super().__init__(
            f"Cannot transition from '{current_status}' to '{attempted_status}'",
            detail={"current_status": current_status, "attempted_status": attempted_status},
        )


class TransferLimitExceededError(TransferError):
    """Raised when a transfer exceeds corridor or user limits."""

    def __init__(self, message: str = "Transfer limit exceeded"):
        super().__init__(message)


# ---------- Escrow / Blockchain ---------------------------------------------

class EscrowError(HaChainError):
    """Raised when an escrow operation fails on-chain."""

    def __init__(self, message: str = "Escrow operation failed"):
        super().__init__(message)


class BlockchainError(HaChainError):
    """Raised for general blockchain interaction failures."""

    def __init__(self, message: str = "Blockchain operation failed"):
        super().__init__(message)


# ---------- Agent -----------------------------------------------------------

class AgentNotFoundError(HaChainError):
    """Raised when an agent lookup yields no result."""

    def __init__(self, identifier: str = ""):
        super().__init__(f"Agent not found: {identifier}" if identifier else "Agent not found")


class AgentSuspendedError(HaChainError):
    """Raised when an action is attempted on a suspended/revoked agent."""

    def __init__(self, agent_id: str = ""):
        super().__init__(f"Agent is suspended or revoked: {agent_id}")


class InsufficientStakeError(HaChainError):
    """Raised when an agent's stake is below the required threshold."""

    def __init__(self, message: str = "Insufficient stake balance"):
        super().__init__(message)


# ---------- Corridor --------------------------------------------------------

class CorridorNotFoundError(HaChainError):
    """Raised when the requested corridor does not exist or is inactive."""

    def __init__(self, source: str = "", destination: str = ""):
        msg = f"Corridor not found: {source} -> {destination}" if source else "Corridor not found"
        super().__init__(msg)


# ---------- Investment ------------------------------------------------------

class InvestmentError(HaChainError):
    """Base class for investment-related failures."""


class InsufficientFundsError(InvestmentError):
    """Raised when the user wallet lacks required funds."""

    def __init__(self, message: str = "Insufficient funds"):
        super().__init__(message)


# ---------- Compliance ------------------------------------------------------

class ComplianceBlockError(HaChainError):
    """Raised when a compliance rule prevents an operation."""

    def __init__(self, message: str = "Blocked by compliance rules"):
        super().__init__(message)
