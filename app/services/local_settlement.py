"""Local settlement service: executes domestic payments via local rails.

Each payment rail (UPI, ACH, SEPA, SPEI, Mobile Money) is mocked here.
In production these would integrate with real payment processors.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class PaymentResult:
    """Result of a local payment attempt."""
    tx_id: str
    status: str  # completed, pending, failed
    timestamp: datetime
    payment_method: str
    amount: float
    currency: str
    error: Optional[str] = None


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _tx_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:16]}"


# ---------------------------------------------------------------------------
# Mock payment rail implementations
# ---------------------------------------------------------------------------

async def pay_via_upi(
    amount: float,
    currency: str,
    recipient: dict,
) -> PaymentResult:
    """Simulate a UPI payment (India)."""
    return PaymentResult(
        tx_id=_tx_id("UPI"),
        status="completed",
        timestamp=_now(),
        payment_method="upi",
        amount=amount,
        currency=currency,
    )


async def pay_via_ach(
    amount: float,
    currency: str,
    recipient: dict,
) -> PaymentResult:
    """Simulate an ACH transfer (USA)."""
    return PaymentResult(
        tx_id=_tx_id("ACH"),
        status="completed",
        timestamp=_now(),
        payment_method="ach",
        amount=amount,
        currency=currency,
    )


async def pay_via_sepa(
    amount: float,
    currency: str,
    recipient: dict,
) -> PaymentResult:
    """Simulate a SEPA transfer (Europe)."""
    return PaymentResult(
        tx_id=_tx_id("SEPA"),
        status="completed",
        timestamp=_now(),
        payment_method="sepa",
        amount=amount,
        currency=currency,
    )


async def pay_via_spei(
    amount: float,
    currency: str,
    recipient: dict,
) -> PaymentResult:
    """Simulate a SPEI transfer (Mexico)."""
    return PaymentResult(
        tx_id=_tx_id("SPEI"),
        status="completed",
        timestamp=_now(),
        payment_method="spei",
        amount=amount,
        currency=currency,
    )


async def pay_via_mobile_money(
    amount: float,
    currency: str,
    recipient: dict,
) -> PaymentResult:
    """Simulate a mobile money transfer (Africa/emerging markets)."""
    return PaymentResult(
        tx_id=_tx_id("MOMO"),
        status="completed",
        timestamp=_now(),
        payment_method="mobile_money",
        amount=amount,
        currency=currency,
    )


# ---------------------------------------------------------------------------
# Payment method routing
# ---------------------------------------------------------------------------

RAIL_MAP = {
    "upi": pay_via_upi,
    "ach": pay_via_ach,
    "sepa": pay_via_sepa,
    "spei": pay_via_spei,
    "mobile_money": pay_via_mobile_money,
}

# Currency -> default payment method mapping
CURRENCY_METHOD_MAP = {
    "USD": "ach",
    "INR": "upi",
    "EUR": "sepa",
    "GBP": "sepa",
    "MXN": "spei",
    "KES": "mobile_money",
    "NGN": "mobile_money",
    "GHS": "mobile_money",
    "SOS": "mobile_money",
    "PHP": "mobile_money",
}


async def execute_local_payment(
    currency: str,
    amount: float,
    recipient: dict,
    method: Optional[str] = None,
) -> PaymentResult:
    """Execute a local payment using the appropriate rail.

    Args:
        currency: ISO 4217 currency code.
        amount: Payment amount in the local currency.
        recipient: Dict with recipient details (account, name, etc.).
        method: Optional override of payment method. If not provided,
                inferred from currency.

    Returns:
        PaymentResult with transaction details.
    """
    if method is None:
        method = CURRENCY_METHOD_MAP.get(currency, "ach")

    rail_fn = RAIL_MAP.get(method)
    if rail_fn is None:
        return PaymentResult(
            tx_id=_tx_id("ERR"),
            status="failed",
            timestamp=_now(),
            payment_method=method,
            amount=amount,
            currency=currency,
            error=f"Unknown payment method: {method}",
        )

    return await rail_fn(amount=amount, currency=currency, recipient=recipient)
