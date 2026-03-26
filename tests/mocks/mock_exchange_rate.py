"""Mock exchange rate provider for testing."""

from typing import Dict, Optional, Tuple


class MockExchangeRateProvider:
    """
    Simulates an exchange rate API (e.g., Open Exchange Rates, CurrencyLayer).

    Maintains a configurable set of currency pair rates for deterministic
    testing. Rates are stored as source->destination mappings.
    """

    # Default rates for common corridors (mid-market rates)
    DEFAULT_RATES = {
        ("USD", "SOS"): 571.50,     # US Dollar to Somali Shilling
        ("USD", "INR"): 83.25,      # US Dollar to Indian Rupee
        ("USD", "MXN"): 17.15,      # US Dollar to Mexican Peso
        ("USD", "PHP"): 56.20,      # US Dollar to Philippine Peso
        ("USD", "KES"): 153.50,     # US Dollar to Kenyan Shilling
        ("USD", "GBP"): 0.79,       # US Dollar to British Pound
        ("USD", "EUR"): 0.92,       # US Dollar to Euro
        ("USD", "AED"): 3.67,       # US Dollar to UAE Dirham
        ("USD", "ETB"): 56.80,      # US Dollar to Ethiopian Birr
    }

    def __init__(self):
        self._rates: Dict[Tuple[str, str], float] = dict(self.DEFAULT_RATES)
        self._call_count: int = 0
        self._should_fail: bool = False
        self._failure_message: str = "Rate provider unavailable"

    def set_rate(self, source: str, destination: str, rate: float):
        """Set a specific exchange rate."""
        self._rates[(source, destination)] = rate

    def set_failure(self, should_fail: bool, message: str = "Rate provider unavailable"):
        """Configure the provider to simulate failures."""
        self._should_fail = should_fail
        self._failure_message = message

    async def get_rate(
        self, source_currency: str, destination_currency: str
    ) -> Optional[float]:
        """
        Get exchange rate for a currency pair.

        Args:
            source_currency: Source currency code (e.g., "USD")
            destination_currency: Destination currency code (e.g., "SOS")

        Returns:
            Exchange rate, or None if pair not found.

        Raises:
            ConnectionError: If provider is configured to fail.
        """
        self._call_count += 1

        if self._should_fail:
            raise ConnectionError(self._failure_message)

        rate = self._rates.get((source_currency, destination_currency))
        if rate is None:
            # Try inverse
            inverse = self._rates.get((destination_currency, source_currency))
            if inverse and inverse > 0:
                return 1.0 / inverse
        return rate

    async def get_rates_batch(
        self, source: str, destinations: list
    ) -> Dict[str, Optional[float]]:
        """Get rates for multiple destination currencies at once."""
        results = {}
        for dest in destinations:
            try:
                results[dest] = await self.get_rate(source, dest)
            except ConnectionError:
                results[dest] = None
        return results

    @property
    def call_count(self) -> int:
        return self._call_count

    def reset(self):
        self._rates = dict(self.DEFAULT_RATES)
        self._call_count = 0
        self._should_fail = False
