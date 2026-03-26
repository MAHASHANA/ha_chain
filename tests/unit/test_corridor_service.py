"""Unit tests for the corridor service -- fees, limits, and exchange rates."""

import pytest

from app.enums import CorridorStatus
from app.services.corridor_service import CorridorService
from tests.mocks.mock_exchange_rate import MockExchangeRateProvider


class TestCorridorFees:
    """Tests for corridor fee calculations."""

    @pytest.mark.asyncio
    async def test_usa_to_somalia_fee_calculation(
        self, db_session, corridor_usa_somalia,
    ):
        """USA->Somalia: 1.5% base + $0.50 mobile money fee."""
        svc = CorridorService(db=db_session)
        result = await svc.calculate_fee(corridor_usa_somalia.id, 500.0)

        # 1.5% of 500 = $7.50, + $0.50 flat = $8.00
        expected_fee = 500.0 * 0.015 + 0.50
        assert result["fee_usd"] == expected_fee
        assert result["total_debit_usd"] == 500.0 + expected_fee
        assert result["receive_currency"] == "SOS"
        assert result["send_amount_usd"] == 500.0

    @pytest.mark.asyncio
    async def test_usa_to_india_fee_calculation(
        self, db_session, corridor_usa_india,
    ):
        """USA->India: 1.0% base (high volume corridor = lower fee)."""
        svc = CorridorService(db=db_session)
        result = await svc.calculate_fee(corridor_usa_india.id, 1000.0)

        # 1.0% of 1000 = $10.00, no flat fee
        expected_fee = 1000.0 * 0.01
        assert result["fee_usd"] == expected_fee
        assert result["receive_currency"] == "INR"

    @pytest.mark.asyncio
    async def test_usa_to_mexico_fee_calculation(
        self, db_session, corridor_usa_mexico,
    ):
        """USA->Mexico: 0.8% base (highest volume = lowest fee)."""
        svc = CorridorService(db=db_session)
        result = await svc.calculate_fee(corridor_usa_mexico.id, 300.0)

        # 0.8% of 300 = $2.40, no flat fee
        expected_fee = 300.0 * 0.008
        assert result["fee_usd"] == expected_fee
        assert result["receive_currency"] == "MXN"

    @pytest.mark.asyncio
    async def test_minimum_fee_applied(
        self, db_session, corridor_usa_somalia,
    ):
        """Small transfers should pay at least minimum fee."""
        svc = CorridorService(db=db_session)
        result = await svc.calculate_fee(corridor_usa_somalia.id, 10.0)

        # 1.5% of 10 = $0.15, + $0.50 flat = $0.65
        # But minimum fee is $2.00
        assert result["fee_usd"] == 2.0

    @pytest.mark.asyncio
    async def test_inactive_corridor_rejected(
        self, db_session, corridor_usa_somalia,
    ):
        """Transfer to inactive corridor should fail."""
        corridor_usa_somalia.status = CorridorStatus.INACTIVE.value
        await db_session.flush()

        svc = CorridorService(db=db_session)
        with pytest.raises(ValueError, match="inactive"):
            await svc.calculate_fee(corridor_usa_somalia.id, 500.0)

    @pytest.mark.asyncio
    async def test_below_minimum_amount_rejected(
        self, db_session, corridor_usa_somalia,
    ):
        """Amount below corridor minimum should be rejected."""
        svc = CorridorService(db=db_session)
        with pytest.raises(ValueError, match="below minimum"):
            await svc.calculate_fee(corridor_usa_somalia.id, 1.0)

    @pytest.mark.asyncio
    async def test_above_maximum_amount_rejected(
        self, db_session, corridor_usa_somalia,
    ):
        """Amount above corridor maximum should be rejected."""
        svc = CorridorService(db=db_session)
        with pytest.raises(ValueError, match="exceeds maximum"):
            await svc.calculate_fee(corridor_usa_somalia.id, 20000.0)

    @pytest.mark.asyncio
    async def test_exchange_rate_with_markup(
        self, db_session, corridor_usa_somalia,
    ):
        """Effective rate should include markup."""
        svc = CorridorService(db=db_session)
        result = await svc.calculate_fee(corridor_usa_somalia.id, 500.0)

        # Mid rate: 571.50, markup: 1%, effective: 571.50 * 0.99 = 565.785
        expected_rate = round(571.50 * 0.99, 4)
        assert result["exchange_rate"] == expected_rate

    @pytest.mark.asyncio
    async def test_receive_amount_calculation(
        self, db_session, corridor_usa_india,
    ):
        """Receive amount should be send_amount * effective_rate."""
        svc = CorridorService(db=db_session)
        result = await svc.calculate_fee(corridor_usa_india.id, 1000.0)

        expected_rate = 83.25 * 0.99
        expected_receive = round(1000.0 * expected_rate, 2)
        assert result["receive_amount"] == expected_receive

    @pytest.mark.asyncio
    async def test_get_active_corridors(
        self, db_session, corridor_usa_somalia, corridor_usa_india,
        corridor_usa_mexico,
    ):
        """Should return only active corridors."""
        # Deactivate one
        corridor_usa_mexico.status = CorridorStatus.INACTIVE.value
        await db_session.flush()

        svc = CorridorService(db=db_session)
        active = await svc.get_active_corridors()

        assert len(active) == 2
        ids = [c.id for c in active]
        assert corridor_usa_mexico.id not in ids

    @pytest.mark.asyncio
    async def test_update_exchange_rate(
        self, db_session, corridor_usa_somalia,
    ):
        """Should update the corridor's exchange rate."""
        svc = CorridorService(db=db_session)
        updated = await svc.update_exchange_rate(corridor_usa_somalia.id, 580.0)
        assert updated.exchange_rate == 580.0

    @pytest.mark.asyncio
    async def test_refresh_rates_from_provider(
        self, db_session, corridor_usa_somalia, corridor_usa_india,
        mock_rate_provider,
    ):
        """Should update rates from external provider."""
        mock_rate_provider.set_rate("USD", "SOS", 575.00)
        mock_rate_provider.set_rate("USD", "INR", 84.00)

        svc = CorridorService(db=db_session, rate_provider=mock_rate_provider)
        count = await svc.refresh_rates_from_provider()

        assert count == 2
        refreshed_som = await db_session.get(
            type(corridor_usa_somalia), corridor_usa_somalia.id
        )
        assert refreshed_som.exchange_rate == 575.00
