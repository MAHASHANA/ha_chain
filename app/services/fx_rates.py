"""Live FX rate provider using free exchangerate.host API.

Fetches real exchange rates and caches them for 5 minutes.
Falls back to hardcoded rates if the API is unreachable.
"""

from __future__ import annotations

import time
from typing import Dict, Optional

import httpx

# Cache: { "USD/INR": (rate, timestamp) }
_cache: Dict[str, tuple[float, float]] = {}
CACHE_TTL = 300  # 5 minutes

# Fallback rates (approximate, March 2026)
FALLBACK_RATES: Dict[str, float] = {
    "USD": 1.0,
    "INR": 83.5,
    "MXN": 17.2,
    "PHP": 56.5,
    "GBP": 0.79,
    "NGN": 1550.0,
    "EUR": 0.92,
    "SOS": 571.0,
    "PKR": 280.0,
    "ETB": 57.0,
    "KES": 153.0,
    "GHS": 15.5,
    "CNY": 7.25,
}


async def get_rate(source: str, target: str) -> float:
    """Get exchange rate from source to target currency.

    Returns how many units of target you get for 1 unit of source.
    Example: get_rate("USD", "INR") -> 83.5 (1 USD = 83.5 INR)
    """
    source = source.upper()
    target = target.upper()

    if source == target:
        return 1.0

    cache_key = f"{source}/{target}"
    now = time.time()

    # Check cache
    if cache_key in _cache:
        rate, ts = _cache[cache_key]
        if now - ts < CACHE_TTL:
            return rate

    # Try live API
    rate = await _fetch_live_rate(source, target)
    if rate:
        _cache[cache_key] = (rate, now)
        return rate

    # Fallback: compute via USD cross rate
    return _fallback_rate(source, target)


async def get_usd_value(amount: float, currency: str) -> float:
    """Convert any amount to its USD equivalent."""
    if currency.upper() == "USD":
        return amount
    rate = await get_rate(currency, "USD")
    return round(amount * rate, 2)


async def convert(amount: float, source: str, target: str) -> float:
    """Convert amount from source currency to target currency."""
    rate = await get_rate(source, target)
    return round(amount * rate, 2)


async def _fetch_live_rate(source: str, target: str) -> Optional[float]:
    """Fetch rate from free API."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            # Try open.er-api.com (free, no key needed)
            resp = await client.get(
                f"https://open.er-api.com/v6/latest/{source}"
            )
            if resp.status_code == 200:
                data = resp.json()
                if data.get("result") == "success":
                    rates = data.get("rates", {})
                    if target in rates:
                        return float(rates[target])
    except Exception:
        pass

    return None


def _fallback_rate(source: str, target: str) -> float:
    """Compute rate via USD cross using hardcoded fallback rates."""
    source_to_usd = 1.0 / FALLBACK_RATES.get(source, 1.0)
    usd_to_target = FALLBACK_RATES.get(target, 1.0)
    return round(source_to_usd * usd_to_target, 6)


async def get_all_rates_to_usd() -> Dict[str, float]:
    """Get all supported currencies' rates to USD. For display."""
    result = {}
    for currency in FALLBACK_RATES:
        rate = await get_rate(currency, "USD")
        result[currency] = rate
    return result
