"""Unit tests for the exchange rate service."""

import pytest

from app.services.exchange_rate_service import ExchangeRateService
from tests.mocks.mock_exchange_rate import MockExchangeRateProvider


class TestRateLookup:
    """Tests for exchange rate lookups."""

    @pytest.mark.asyncio
    async def test_get_usd_to_sos_rate(self, mock_rate_provider):
        """Should return correct USD/SOS rate."""
        svc = ExchangeRateService(rate_provider=mock_rate_provider)
        rate = await svc.get_rate("USD", "SOS")
        assert rate == 571.50

    @pytest.mark.asyncio
    async def test_get_usd_to_inr_rate(self, mock_rate_provider):
        """Should return correct USD/INR rate."""
        svc = ExchangeRateService(rate_provider=mock_rate_provider)
        rate = await svc.get_rate("USD", "INR")
        assert rate == 83.25

    @pytest.mark.asyncio
    async def test_get_usd_to_mxn_rate(self, mock_rate_provider):
        """Should return correct USD/MXN rate."""
        svc = ExchangeRateService(rate_provider=mock_rate_provider)
        rate = await svc.get_rate("USD", "MXN")
        assert rate == 17.15

    @pytest.mark.asyncio
    async def test_rate_caching(self, mock_rate_provider):
        """Second call should use cache, not hit provider again."""
        svc = ExchangeRateService(rate_provider=mock_rate_provider)
        await svc.get_rate("USD", "SOS")
        await svc.get_rate("USD", "SOS")

        # Should only have called provider once (second from cache)
        assert mock_rate_provider.call_count == 1

    @pytest.mark.asyncio
    async def test_cache_cleared(self, mock_rate_provider):
        """Clearing cache should cause fresh provider lookup."""
        svc = ExchangeRateService(rate_provider=mock_rate_provider)
        await svc.get_rate("USD", "SOS")
        svc.clear_cache()
        await svc.get_rate("USD", "SOS")

        assert mock_rate_provider.call_count == 2

    @pytest.mark.asyncio
    async def test_set_cached_rate(self, mock_rate_provider):
        """Manually setting a cached rate should override provider."""
        svc = ExchangeRateService(rate_provider=mock_rate_provider)
        svc.set_cached_rate("USD", "SOS", 600.0)
        rate = await svc.get_rate("USD", "SOS")

        assert rate == 600.0
        assert mock_rate_provider.call_count == 0  # Never hit provider

    @pytest.mark.asyncio
    async def test_unknown_pair_raises(self, mock_rate_provider):
        """Unknown currency pair should raise ValueError."""
        svc = ExchangeRateService(rate_provider=mock_rate_provider)
        with pytest.raises(ValueError, match="No rate available"):
            await svc.get_rate("XYZ", "ABC")

    @pytest.mark.asyncio
    async def test_provider_failure_raises(self, mock_rate_provider):
        """Provider failure should propagate as error."""
        mock_rate_provider.set_failure(True, "API down")
        svc = ExchangeRateService(rate_provider=mock_rate_provider)
        with pytest.raises(ConnectionError, match="API down"):
            await svc.get_rate("USD", "SOS")


class TestRateConversion:
    """Tests for currency conversion calculations."""

    @pytest.mark.asyncio
    async def test_convert_usd_to_sos(self, mock_rate_provider):
        """$500 should convert to correct SOS amount."""
        svc = ExchangeRateService(rate_provider=mock_rate_provider)
        result = await svc.convert(500.0, "USD", "SOS")

        assert result["source_amount"] == 500.0
        assert result["source_currency"] == "USD"
        assert result["destination_currency"] == "SOS"
        assert result["mid_rate"] == 571.50
        assert result["destination_amount"] == round(500.0 * 571.50, 2)

    @pytest.mark.asyncio
    async def test_convert_with_markup(self, mock_rate_provider):
        """Conversion with 1% markup should reduce effective rate."""
        svc = ExchangeRateService(rate_provider=mock_rate_provider)
        result = await svc.convert(500.0, "USD", "SOS", markup_percent=1.0)

        effective_rate = 571.50 * (1 - 0.01)
        assert result["effective_rate"] == round(effective_rate, 4)
        assert result["markup_percent"] == 1.0
        assert result["destination_amount"] == round(500.0 * effective_rate, 2)

    @pytest.mark.asyncio
    async def test_convert_zero_amount_raises(self, mock_rate_provider):
        """Zero amount should raise ValueError."""
        svc = ExchangeRateService(rate_provider=mock_rate_provider)
        with pytest.raises(ValueError, match="positive"):
            await svc.convert(0.0, "USD", "SOS")

    @pytest.mark.asyncio
    async def test_convert_negative_amount_raises(self, mock_rate_provider):
        """Negative amount should raise ValueError."""
        svc = ExchangeRateService(rate_provider=mock_rate_provider)
        with pytest.raises(ValueError, match="positive"):
            await svc.convert(-100.0, "USD", "SOS")

    @pytest.mark.asyncio
    async def test_inverse_rate(self, mock_rate_provider):
        """Inverse rate should be 1/rate."""
        svc = ExchangeRateService(rate_provider=mock_rate_provider)
        inverse = await svc.get_inverse_rate("USD", "SOS")
        assert abs(inverse - 1.0 / 571.50) < 0.0001

    @pytest.mark.asyncio
    async def test_convert_multiple_currencies(self, mock_rate_provider):
        """Should handle conversions to different destination currencies."""
        svc = ExchangeRateService(rate_provider=mock_rate_provider)

        sos = await svc.convert(100.0, "USD", "SOS")
        inr = await svc.convert(100.0, "USD", "INR")
        mxn = await svc.convert(100.0, "USD", "MXN")

        assert sos["destination_amount"] == round(100.0 * 571.50, 2)
        assert inr["destination_amount"] == round(100.0 * 83.25, 2)
        assert mxn["destination_amount"] == round(100.0 * 17.15, 2)


class TestMockProvider:
    """Tests for the mock rate provider itself."""

    @pytest.mark.asyncio
    async def test_default_rates_loaded(self, mock_rate_provider):
        """Mock should have default rates for common pairs."""
        rate = await mock_rate_provider.get_rate("USD", "SOS")
        assert rate == 571.50

    @pytest.mark.asyncio
    async def test_set_custom_rate(self, mock_rate_provider):
        """Should allow setting custom rates."""
        mock_rate_provider.set_rate("USD", "BTC", 0.000015)
        rate = await mock_rate_provider.get_rate("USD", "BTC")
        assert rate == 0.000015

    @pytest.mark.asyncio
    async def test_batch_rates(self, mock_rate_provider):
        """Should return multiple rates at once."""
        rates = await mock_rate_provider.get_rates_batch(
            "USD", ["SOS", "INR", "MXN", "XYZ"]
        )
        assert rates["SOS"] == 571.50
        assert rates["INR"] == 83.25
        assert rates["MXN"] == 17.15
        assert rates["XYZ"] is None  # Unknown pair

    @pytest.mark.asyncio
    async def test_reset(self, mock_rate_provider):
        """Reset should restore default rates."""
        mock_rate_provider.set_rate("USD", "SOS", 999.0)
        mock_rate_provider.reset()
        rate = await mock_rate_provider.get_rate("USD", "SOS")
        assert rate == 571.50
