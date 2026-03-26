"""Mock mobile money providers for testing (Zaad, M-Pesa, UPI, GCash, SPEI)."""

import hashlib
import time
from typing import Dict, Optional


class MockMobileMoneyProvider:
    """
    Simulates mobile money API interactions for multiple providers.

    Supports Zaad (Somalia), M-Pesa (Kenya), UPI (India),
    SPEI (Mexico), and GCash (Philippines).
    """

    SUPPORTED_PROVIDERS = {"zaad", "mpesa", "upi", "spei", "gcash", "edahab"}

    # Provider-specific config
    PROVIDER_CONFIG = {
        "zaad": {
            "country": "SOM",
            "currency": "USD",  # Zaad operates in USD
            "phone_prefix": "+252",
            "min_amount": 1.0,
            "max_amount": 5000.0,
        },
        "edahab": {
            "country": "SOM",
            "currency": "USD",
            "phone_prefix": "+252",
            "min_amount": 1.0,
            "max_amount": 3000.0,
        },
        "mpesa": {
            "country": "KEN",
            "currency": "KES",
            "phone_prefix": "+254",
            "min_amount": 10.0,
            "max_amount": 150000.0,
        },
        "upi": {
            "country": "IND",
            "currency": "INR",
            "phone_prefix": "+91",
            "min_amount": 1.0,
            "max_amount": 500000.0,
        },
        "spei": {
            "country": "MEX",
            "currency": "MXN",
            "phone_prefix": "+52",
            "min_amount": 1.0,
            "max_amount": 200000.0,
        },
        "gcash": {
            "country": "PHL",
            "currency": "PHP",
            "phone_prefix": "+63",
            "min_amount": 1.0,
            "max_amount": 100000.0,
        },
    }

    def __init__(self):
        self._transactions: Dict[str, dict] = {}
        self._tx_counter: int = 0
        self._should_fail: Dict[str, bool] = {}
        self._failure_messages: Dict[str, str] = {}
        self._balances: Dict[str, float] = {}  # phone -> balance

    def set_failure(
        self, provider: str, should_fail: bool, message: str = "Provider unavailable"
    ):
        """Configure a provider to simulate failures."""
        self._should_fail[provider] = should_fail
        self._failure_messages[provider] = message

    def set_balance(self, phone: str, balance: float):
        """Set a test balance for a phone number."""
        self._balances[phone] = balance

    async def send_money(
        self,
        provider: str,
        recipient_phone: str,
        amount: float,
        currency: str,
        reference: str,
    ) -> dict:
        """
        Send money via mobile money provider.

        Args:
            provider: Provider name (zaad, mpesa, upi, spei, gcash).
            recipient_phone: Recipient's phone number.
            amount: Amount in local currency.
            currency: Currency code.
            reference: Transfer reference ID.

        Returns:
            Transaction result dict.
        """
        if provider not in self.SUPPORTED_PROVIDERS:
            raise ValueError(f"Unsupported provider: {provider}")

        if self._should_fail.get(provider, False):
            return {
                "success": False,
                "provider": provider,
                "error": self._failure_messages.get(provider, "Provider error"),
                "reference": reference,
            }

        config = self.PROVIDER_CONFIG[provider]
        if amount < config["min_amount"]:
            return {
                "success": False,
                "provider": provider,
                "error": f"Amount below minimum {config['min_amount']} {config['currency']}",
                "reference": reference,
            }
        if amount > config["max_amount"]:
            return {
                "success": False,
                "provider": provider,
                "error": f"Amount exceeds maximum {config['max_amount']} {config['currency']}",
                "reference": reference,
            }

        self._tx_counter += 1
        tx_id = hashlib.sha256(
            f"{provider}-{reference}-{self._tx_counter}".encode()
        ).hexdigest()[:16].upper()

        # Credit recipient
        self._balances[recipient_phone] = (
            self._balances.get(recipient_phone, 0.0) + amount
        )

        result = {
            "success": True,
            "provider": provider,
            "transaction_id": tx_id,
            "recipient_phone": recipient_phone,
            "amount": amount,
            "currency": currency,
            "reference": reference,
            "timestamp": time.time(),
        }

        self._transactions[tx_id] = result
        return result

    async def check_transaction(self, provider: str, transaction_id: str) -> dict:
        """Check the status of a mobile money transaction."""
        tx = self._transactions.get(transaction_id)
        if not tx:
            return {"found": False, "transaction_id": transaction_id}
        return {"found": True, **tx}

    async def get_balance(self, provider: str, phone: str) -> float:
        """Get the balance for a phone number on a provider."""
        return self._balances.get(phone, 0.0)

    def reset(self):
        self._transactions.clear()
        self._tx_counter = 0
        self._should_fail.clear()
        self._failure_messages.clear()
        self._balances.clear()
