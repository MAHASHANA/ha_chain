"""Exchange rate service: rate calculation and conversion logic."""

from typing import Optional, Dict


class ExchangeRateService:
    """Manages exchange rate lookups, caching, and conversion calculations."""

    def __init__(self, rate_provider=None):
        self.rate_provider = rate_provider
        self._cache: Dict[str, float] = {}

    async def get_rate(
        self, source_currency: str, destination_currency: str
    ) -> float:
        """Get the current exchange rate from source to destination."""
        pair = f"{source_currency}/{destination_currency}"

        # Check cache first
        if pair in self._cache:
            return self._cache[pair]

        # Fetch from provider
        if self.rate_provider:
            rate = await self.rate_provider.get_rate(source_currency, destination_currency)
            if rate:
                self._cache[pair] = rate
                return rate

        raise ValueError(f"No rate available for {pair}")

    async def convert(
        self,
        amount: float,
        source_currency: str,
        destination_currency: str,
        markup_percent: float = 0.0,
    ) -> dict:
        """Convert an amount from one currency to another."""
        if amount <= 0:
            raise ValueError("Amount must be positive")

        mid_rate = await self.get_rate(source_currency, destination_currency)
        effective_rate = mid_rate * (1 - markup_percent / 100)
        converted = amount * effective_rate

        return {
            "source_amount": amount,
            "source_currency": source_currency,
            "destination_amount": round(converted, 2),
            "destination_currency": destination_currency,
            "mid_rate": mid_rate,
            "effective_rate": round(effective_rate, 4),
            "markup_percent": markup_percent,
        }

    async def get_inverse_rate(
        self, source_currency: str, destination_currency: str
    ) -> float:
        """Get the inverse rate (1/rate)."""
        rate = await self.get_rate(source_currency, destination_currency)
        return 1.0 / rate

    def set_cached_rate(
        self, source_currency: str, destination_currency: str, rate: float
    ):
        """Manually set a cached rate (useful for testing and rate locks)."""
        pair = f"{source_currency}/{destination_currency}"
        self._cache[pair] = rate

    def clear_cache(self):
        """Clear the rate cache."""
        self._cache.clear()
