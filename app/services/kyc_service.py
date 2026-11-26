"""KYC verification management."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import KYCRequiredError
from app.models.kyc import KYCVerification
from app.models.user import User


class KYCService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def submit_verification(
        self,
        user_id: uuid.UUID | str,
        *,
        level: int,
        method: str,
        document_type: str | None = None,
        document_hash: str | None = None,
        biometric_hash: str | None = None,
    ) -> KYCVerification:
        """Submit a new KYC verification request (status ``pending``)."""
        record = KYCVerification(
            user_id=user_id,
            level=level,
            method=method,
            document_type=document_type,
            document_hash=document_hash,
            biometric_hash=biometric_hash,
            status="pending",
        )
        self.db.add(record)
        await self.db.flush()
        return record

    async def approve_verification(
        self, kyc_id: uuid.UUID | str, verified_by: uuid.UUID | str
    ) -> KYCVerification:
        """Approve a pending KYC request and upgrade the user's KYC level."""
        record = await self.db.get(KYCVerification, kyc_id)
        if not record:
            raise ValueError(f"KYC record {kyc_id} not found")

        record.status = "approved"
        record.verified_at = datetime.now(timezone.utc)
        record.verified_by = str(verified_by)

        # Upgrade user KYC level. ``db.get`` binds via the column type, which
        # stays correct when SQLite dev mode swaps UUID columns for String(36).
        user = await self.db.get(User, record.user_id)
        if user is None:
            raise ValueError(f"User {record.user_id} not found")
        if record.level > user.kyc_level:
            user.kyc_level = record.level
        user.is_verified = True

        await self.db.flush()
        return record

    async def reject_verification(
        self, kyc_id: uuid.UUID | str, rejected_by: uuid.UUID | str
    ) -> KYCVerification:
        record = await self.db.get(KYCVerification, kyc_id)
        if not record:
            raise ValueError(f"KYC record {kyc_id} not found")

        record.status = "rejected"
        record.verified_at = datetime.now(timezone.utc)
        record.verified_by = str(rejected_by)
        await self.db.flush()
        return record

    async def get_user_verifications(
        self, user_id: uuid.UUID | str
    ) -> Sequence[KYCVerification]:
        result = await self.db.execute(
            select(KYCVerification)
            .where(KYCVerification.user_id == user_id)
            .order_by(KYCVerification.created_at.desc())
        )
        return result.scalars().all()

    async def check_kyc_level(self, user_id: uuid.UUID | str, required_level: int) -> bool:
        """Return ``True`` if the user meets the required KYC level, else raise.

        Raises ``ValueError`` if the user does not exist and
        ``KYCRequiredError`` if the user is inactive, unverified, or below
        ``required_level``.
        """
        user = await self.db.get(User, user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")
        if not user.is_active or user.deleted_at is not None:
            raise KYCRequiredError(required_level=required_level, current_level=0)
        if not user.is_verified or user.kyc_level < required_level:
            raise KYCRequiredError(required_level=required_level, current_level=user.kyc_level)
        return True
