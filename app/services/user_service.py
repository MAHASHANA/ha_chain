"""User registration, profile management, wallet operations."""

from __future__ import annotations

import uuid
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password
from app.exceptions import UserNotFoundError, InsufficientFundsError
from app.models.user import User, UserBeneficiary, UserWallet


class UserService:
    """Stateless service -- all state lives in the database session."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # Registration & lookup
    # ------------------------------------------------------------------

    async def create_user(
        self,
        *,
        email: str,
        phone: str,
        password: str,
        full_name: str,
        country_code: str,
        default_currency: str = "USD",
    ) -> User:
        """Register a new user and provision a default USDC wallet."""
        user = User(
            email=email,
            phone=phone,
            password_hash=hash_password(password),
            full_name=full_name,
            country_code=country_code,
            default_currency=default_currency,
        )
        self.db.add(user)
        await self.db.flush()

        # Create default USDC wallet
        wallet = UserWallet(
            user_id=user.id,
            currency="USDC",
            balance=0,
            is_primary=True,
        )
        self.db.add(wallet)
        await self.db.flush()
        return user

    async def get_by_id(self, user_id: uuid.UUID) -> User:
        result = await self.db.execute(
            select(User).where(User.id == user_id, User.deleted_at.is_(None))
        )
        user = result.scalar_one_or_none()
        if not user:
            raise UserNotFoundError(str(user_id))
        return user

    async def get_by_email(self, email: str) -> User | None:
        result = await self.db.execute(
            select(User).where(User.email == email, User.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    async def get_by_phone(self, phone: str) -> User | None:
        result = await self.db.execute(
            select(User).where(User.phone == phone, User.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    async def authenticate(self, email: str, password: str) -> User | None:
        """Return the user if credentials are valid, otherwise ``None``."""
        user = await self.get_by_email(email)
        if user and verify_password(password, user.password_hash):
            return user
        return None

    # ------------------------------------------------------------------
    # Profile
    # ------------------------------------------------------------------

    async def update_profile(
        self,
        user_id: uuid.UUID,
        *,
        full_name: str | None = None,
        phone: str | None = None,
        country_code: str | None = None,
    ) -> User:
        user = await self.get_by_id(user_id)
        if full_name is not None:
            user.full_name = full_name
        if phone is not None:
            user.phone = phone
        if country_code is not None:
            user.country_code = country_code
        await self.db.flush()
        return user

    # ------------------------------------------------------------------
    # Wallets
    # ------------------------------------------------------------------

    async def get_wallets(self, user_id: uuid.UUID) -> Sequence[UserWallet]:
        result = await self.db.execute(
            select(UserWallet).where(UserWallet.user_id == user_id)
        )
        return result.scalars().all()

    async def get_wallet(self, user_id: uuid.UUID, currency: str = "USDC") -> UserWallet:
        result = await self.db.execute(
            select(UserWallet).where(
                UserWallet.user_id == user_id,
                UserWallet.currency == currency,
            )
        )
        wallet = result.scalar_one_or_none()
        if not wallet:
            raise InsufficientFundsError(f"No {currency} wallet found for user")
        return wallet

    async def debit_wallet(
        self, user_id: uuid.UUID, amount: float, currency: str = "USDC"
    ) -> UserWallet:
        wallet = await self.get_wallet(user_id, currency)
        if float(wallet.balance) < amount:
            raise InsufficientFundsError(
                f"Wallet balance {wallet.balance} {currency} < required {amount}"
            )
        wallet.balance = float(wallet.balance) - amount
        await self.db.flush()
        return wallet

    async def credit_wallet(
        self, user_id: uuid.UUID, amount: float, currency: str = "USDC"
    ) -> UserWallet:
        wallet = await self.get_wallet(user_id, currency)
        wallet.balance = float(wallet.balance) + amount
        await self.db.flush()
        return wallet

    # ------------------------------------------------------------------
    # Beneficiaries
    # ------------------------------------------------------------------

    async def add_beneficiary(
        self,
        user_id: uuid.UUID,
        *,
        beneficiary_name: str,
        phone: str,
        country_code: str,
        default_delivery_method: str = "mobile_money",
    ) -> UserBeneficiary:
        ben = UserBeneficiary(
            user_id=user_id,
            beneficiary_name=beneficiary_name,
            phone=phone,
            country_code=country_code,
            default_delivery_method=default_delivery_method,
        )
        self.db.add(ben)
        await self.db.flush()
        return ben

    async def list_beneficiaries(self, user_id: uuid.UUID) -> Sequence[UserBeneficiary]:
        result = await self.db.execute(
            select(UserBeneficiary).where(UserBeneficiary.user_id == user_id)
        )
        return result.scalars().all()

    async def delete_beneficiary(self, user_id: uuid.UUID, beneficiary_id: uuid.UUID) -> None:
        result = await self.db.execute(
            select(UserBeneficiary).where(
                UserBeneficiary.id == beneficiary_id,
                UserBeneficiary.user_id == user_id,
            )
        )
        ben = result.scalar_one_or_none()
        if ben:
            await self.db.delete(ben)
            await self.db.flush()
