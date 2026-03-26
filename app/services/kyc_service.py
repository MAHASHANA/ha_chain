"""KYC verification management."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import KYCRequiredError
from app.models.kyc import KYCRecord
from app.models.user import User


class KYCService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def submit_verification(
        self,
        user_id: uuid.UUID,
        *,
        level_requested: int,
        document_type: str,
        document_number: str | None = None,
        document_country: str,
        extra_data: dict | None = None,
    ) -> KYCRecord:
        """Submit a new KYC verification request."""
        record = KYCRecord(
            user_id=user_id,
            level_requested=level_requested,
            document_type=document_type,
            document_number=document_number,
            document_country=document_country,
            extra_data=extra_data,
        )
        self.db.add(record)
        await self.db.flush()
        return record

    async def approve_verification(
        self, kyc_id: uuid.UUID, verified_by: uuid.UUID
    ) -> KYCRecord:
        """Approve a pending KYC request and upgrade the user's KYC level."""
        result = await self.db.execute(select(KYCRecord).where(KYCRecord.id == kyc_id))
        record = result.scalar_one_or_none()
        if not record:
            raise ValueError(f"KYC record {kyc_id} not found")

        record.status = "approved"
        record.verified_at = datetime.now(timezone.utc)
        record.verified_by = verified_by

        # Upgrade user KYC level
        user_q = await self.db.execute(select(User).where(User.id == record.user_id))
        user = user_q.scalar_one()
        if record.level_requested > user.kyc_level:
            user.kyc_level = record.level_requested
            user.is_verified = True

        await self.db.flush()
        return record

    async def reject_verification(
        self, kyc_id: uuid.UUID, reason: str, rejected_by: uuid.UUID
    ) -> KYCRecord:
        result = await self.db.execute(select(KYCRecord).where(KYCRecord.id == kyc_id))
        record = result.scalar_one_or_none()
        if not record:
            raise ValueError(f"KYC record {kyc_id} not found")

        record.status = "rejected"
        record.rejection_reason = reason
        record.verified_at = datetime.now(timezone.utc)
        record.verified_by = rejected_by
        await self.db.flush()
        return record

    async def get_user_verifications(self, user_id: uuid.UUID) -> Sequence[KYCRecord]:
        result = await self.db.execute(
            select(KYCRecord)
            .where(KYCRecord.user_id == user_id)
            .order_by(KYCRecord.created_at.desc())
        )
        return result.scalars().all()

    async def check_kyc_level(self, user_id: uuid.UUID, required_level: int) -> bool:
        """Return ``True`` if the user meets the required KYC level, else raise."""
        user_q = await self.db.execute(select(User).where(User.id == user_id))
        user = user_q.scalar_one_or_none()
        if not user:
            raise ValueError(f"User {user_id} not found")
        if user.kyc_level < required_level:
            raise KYCRequiredError(required_level=required_level, current_level=user.kyc_level)
        return True
