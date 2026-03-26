"""Corridor service: manages remittance corridors, fees, and exchange rates."""

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.enums import CorridorStatus
from app.models.models import Corridor


class CorridorService:
    def __init__(self, db: AsyncSession, rate_provider=None):
        self.db = db
        self.rate_provider = rate_provider

    async def get_corridor(
        self, source_country: str, destination_country: str
    ) -> Optional[Corridor]:
        """Get a corridor by source and destination country."""
        result = await self.db.execute(
            select(Corridor).where(
                Corridor.source_country == source_country,
                Corridor.destination_country == destination_country,
            )
        )
        return result.scalar_one_or_none()

    async def get_active_corridors(self) -> List[Corridor]:
        """Get all active corridors."""
        result = await self.db.execute(
            select(Corridor).where(Corridor.status == CorridorStatus.ACTIVE.value)
        )
        return list(result.scalars().all())

    async def calculate_fee(
        self, corridor_id: str, amount_usd: float
    ) -> dict:
        """Calculate transfer fee for a given corridor and amount."""
        corridor = await self.db.get(Corridor, corridor_id)
        if not corridor:
            raise ValueError("Corridor not found")

        if corridor.status != CorridorStatus.ACTIVE.value:
            raise ValueError(f"Corridor is {corridor.status}")

        if amount_usd < corridor.min_transfer_usd:
            raise ValueError(
                f"Amount ${amount_usd} below minimum ${corridor.min_transfer_usd}"
            )
        if amount_usd > corridor.max_transfer_usd:
            raise ValueError(
                f"Amount ${amount_usd} exceeds maximum ${corridor.max_transfer_usd}"
            )

        # Calculate percentage-based fee
        percentage_fee = amount_usd * (corridor.base_fee_percent / 100)

        # Add flat fee
        total_fee = percentage_fee + corridor.flat_fee_usd

        # Apply minimum fee
        total_fee = max(total_fee, corridor.minimum_fee_usd)

        # Calculate receive amount
        effective_rate = corridor.exchange_rate * (1 - corridor.exchange_rate_markup)
        receive_amount = amount_usd * effective_rate

        return {
            "send_amount_usd": amount_usd,
            "fee_usd": round(total_fee, 2),
            "total_debit_usd": round(amount_usd + total_fee, 2),
            "exchange_rate": round(effective_rate, 4),
            "receive_amount": round(receive_amount, 2),
            "receive_currency": corridor.destination_currency,
        }

    async def update_exchange_rate(
        self, corridor_id: str, new_rate: float
    ) -> Corridor:
        """Update the exchange rate for a corridor."""
        corridor = await self.db.get(Corridor, corridor_id)
        if not corridor:
            raise ValueError("Corridor not found")

        corridor.exchange_rate = new_rate
        await self.db.flush()
        return corridor

    async def refresh_rates_from_provider(self) -> int:
        """Refresh all corridor rates from the rate provider. Returns count updated."""
        if not self.rate_provider:
            raise ValueError("No rate provider configured")

        corridors = await self.get_active_corridors()
        updated = 0
        for corridor in corridors:
            rate = await self.rate_provider.get_rate(
                corridor.source_currency, corridor.destination_currency
            )
            if rate and rate != corridor.exchange_rate:
                corridor.exchange_rate = rate
                updated += 1

        await self.db.flush()
        return updated
