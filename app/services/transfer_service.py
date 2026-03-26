"""Transfer service: handles quotes, initiation, completion, and cancellation."""

import json
import random
import string
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.enums import (
    TransferStatus, DeliveryMethod, EscrowStatus, ComplianceAction, KYCLevel,
)
from app.models.models import Transfer, User, Corridor, Agent


class TransferService:
    def __init__(
        self,
        db: AsyncSession,
        escrow_service=None,
        compliance_service=None,
        matching_service=None,
    ):
        self.db = db
        self.escrow_service = escrow_service
        self.compliance_service = compliance_service
        self.matching_service = matching_service

    async def create_quote(
        self,
        sender_id: str,
        corridor_id: str,
        send_amount_usd: float,
        delivery_method: str,
        receiver_name: str,
        receiver_phone: Optional[str],
        receiver_city: str,
        receiver_country: str,
        mobile_money_provider: Optional[str] = None,
    ) -> Transfer:
        """Create a transfer quote with fee calculation and rate lock."""
        # Validate sender
        sender = await self.db.get(User, sender_id)
        if not sender:
            raise ValueError("Sender not found")

        # Validate corridor
        corridor = await self.db.get(Corridor, corridor_id)
        if not corridor:
            raise ValueError("Corridor not found")
        if corridor.status != "active":
            raise ValueError("Corridor is not active")

        # Check corridor limits
        if send_amount_usd < corridor.min_transfer_usd:
            raise ValueError(
                f"Amount below corridor minimum of ${corridor.min_transfer_usd}"
            )
        if send_amount_usd > corridor.max_transfer_usd:
            raise ValueError(
                f"Amount exceeds corridor maximum of ${corridor.max_transfer_usd}"
            )

        # Check KYC limits
        daily_total = await self._get_daily_transfer_total(sender_id)
        kyc_limit = self._get_kyc_daily_limit(sender.kyc_level)
        if daily_total + send_amount_usd > kyc_limit:
            raise ValueError(
                f"Transfer would exceed daily KYC limit of ${kyc_limit}. "
                f"Already sent ${daily_total} today."
            )

        # Calculate fees
        fee_usd = self._calculate_fee(send_amount_usd, corridor)

        # Calculate receive amount using locked exchange rate
        effective_rate = corridor.exchange_rate * (1 - corridor.exchange_rate_markup)
        receive_amount_local = send_amount_usd * effective_rate

        total_debit = send_amount_usd + fee_usd

        # Generate pickup code for cash pickup
        pickup_code = None
        if delivery_method == DeliveryMethod.CASH_PICKUP.value:
            pickup_code = self._generate_pickup_code()

        quote_expires_at = datetime.now(timezone.utc) + timedelta(
            minutes=settings.QUOTE_EXPIRY_MINUTES
        )

        transfer = Transfer(
            sender_id=sender_id,
            corridor_id=corridor_id,
            status=TransferStatus.QUOTED.value,
            send_amount_usd=send_amount_usd,
            fee_usd=fee_usd,
            total_debit_usd=total_debit,
            exchange_rate=effective_rate,
            receive_amount_local=receive_amount_local,
            receiver_name=receiver_name,
            receiver_phone=receiver_phone,
            receiver_city=receiver_city,
            receiver_country=receiver_country,
            delivery_method=delivery_method,
            mobile_money_provider=mobile_money_provider,
            pickup_code=pickup_code,
            quote_expires_at=quote_expires_at,
        )

        self.db.add(transfer)
        await self.db.flush()
        return transfer

    async def initiate_transfer(self, transfer_id: str) -> Transfer:
        """Initiate a quoted transfer: run compliance, lock escrow."""
        transfer = await self.db.get(Transfer, transfer_id)
        if not transfer:
            raise ValueError("Transfer not found")

        if transfer.status != TransferStatus.QUOTED.value:
            raise ValueError(f"Transfer is in status {transfer.status}, expected QUOTED")

        # Check quote expiry
        if transfer.quote_expires_at and datetime.now(timezone.utc) > transfer.quote_expires_at:
            transfer.status = TransferStatus.EXPIRED.value
            await self.db.flush()
            raise ValueError("Quote has expired")

        # Check sender balance
        sender = await self.db.get(User, transfer.sender_id)
        if sender.wallet_balance_usdc < transfer.total_debit_usd:
            raise ValueError(
                f"Insufficient balance. Required: ${transfer.total_debit_usd}, "
                f"Available: ${sender.wallet_balance_usdc}"
            )

        # Run compliance checks
        if self.compliance_service:
            compliance_result = await self.compliance_service.run_all_checks(transfer)
            if compliance_result.action == ComplianceAction.BLOCKED:
                transfer.status = TransferStatus.COMPLIANCE_BLOCKED.value
                transfer.compliance_status = ComplianceAction.BLOCKED.value
                transfer.compliance_notes = compliance_result.reason
                await self.db.flush()
                raise ValueError(f"Transfer blocked by compliance: {compliance_result.reason}")
            elif compliance_result.action == ComplianceAction.ENHANCED_REVIEW:
                transfer.compliance_status = ComplianceAction.ENHANCED_REVIEW.value
                transfer.compliance_notes = compliance_result.reason
                # Still allow it to proceed but flagged
            transfer.compliance_status = compliance_result.action.value

        # Lock escrow
        if self.escrow_service:
            tx_hash = await self.escrow_service.lock_funds(
                transfer_id=transfer.id,
                amount_usdc=transfer.total_debit_usd,
                sender_address=sender.wallet_address or "",
            )
            transfer.escrow_tx_hash = tx_hash
            transfer.escrow_status = EscrowStatus.LOCKED.value

        # Debit sender
        sender.wallet_balance_usdc -= transfer.total_debit_usd

        transfer.status = TransferStatus.ESCROW_LOCKED.value
        transfer.initiated_at = datetime.now(timezone.utc)
        await self.db.flush()
        return transfer

    async def match_agent(self, transfer_id: str) -> Transfer:
        """Find and assign a matching agent."""
        transfer = await self.db.get(Transfer, transfer_id)
        if not transfer:
            raise ValueError("Transfer not found")

        if self.matching_service:
            agent = await self.matching_service.find_best_agent(transfer)
            if not agent:
                return transfer  # No agent found yet
            transfer.agent_id = agent.id
            transfer.status = TransferStatus.AGENT_MATCHED.value
            transfer.matched_at = datetime.now(timezone.utc)
            await self.db.flush()
        return transfer

    async def agent_accept(self, transfer_id: str, agent_id: str) -> Transfer:
        """Agent accepts the transfer assignment."""
        transfer = await self.db.get(Transfer, transfer_id)
        if not transfer:
            raise ValueError("Transfer not found")
        if transfer.agent_id != agent_id:
            raise ValueError("Agent not assigned to this transfer")
        if transfer.status != TransferStatus.AGENT_MATCHED.value:
            raise ValueError(f"Transfer status {transfer.status}, expected AGENT_MATCHED")

        agent = await self.db.get(Agent, agent_id)
        commission = transfer.send_amount_usd * agent.commission_rate
        transfer.agent_commission_usd = commission

        transfer.status = TransferStatus.AGENT_ACCEPTED.value
        transfer.accepted_at = datetime.now(timezone.utc)
        await self.db.flush()
        return transfer

    async def confirm_delivery(
        self,
        transfer_id: str,
        agent_id: str,
        pickup_code: Optional[str] = None,
    ) -> Transfer:
        """Agent confirms delivery to receiver."""
        transfer = await self.db.get(Transfer, transfer_id)
        if not transfer:
            raise ValueError("Transfer not found")
        if transfer.agent_id != agent_id:
            raise ValueError("Agent not assigned to this transfer")
        if transfer.status != TransferStatus.AGENT_ACCEPTED.value:
            raise ValueError(
                f"Transfer status {transfer.status}, expected AGENT_ACCEPTED"
            )

        # Verify pickup code for cash pickup
        if transfer.delivery_method == DeliveryMethod.CASH_PICKUP.value:
            if not pickup_code or pickup_code != transfer.pickup_code:
                raise ValueError("Invalid pickup code")

        # Release escrow to agent
        agent = await self.db.get(Agent, agent_id)
        if self.escrow_service:
            agent_user = await self.db.get(User, agent.user_id)
            tx_hash = await self.escrow_service.release_funds(
                transfer_id=transfer.id,
                recipient_address=agent_user.wallet_address or "",
            )
            transfer.release_tx_hash = tx_hash
            transfer.escrow_status = EscrowStatus.RELEASED.value

        # Pay agent: send_amount (they delivered local currency equivalent) + commission
        agent_user = await self.db.get(User, agent.user_id)
        agent_user.wallet_balance_usdc += (
            transfer.send_amount_usd + transfer.agent_commission_usd
        )

        # Update agent stats
        agent.total_transactions += 1
        agent.successful_transactions += 1
        agent.success_rate = agent.successful_transactions / agent.total_transactions
        if transfer.accepted_at:
            delivery_time = (
                datetime.now(timezone.utc) - transfer.accepted_at
            ).total_seconds() / 60
            # Running average
            agent.avg_delivery_minutes = (
                (agent.avg_delivery_minutes * (agent.total_transactions - 1) + delivery_time)
                / agent.total_transactions
            )
        agent.daily_volume_usdc += transfer.send_amount_usd

        transfer.status = TransferStatus.DELIVERED.value
        transfer.delivered_at = datetime.now(timezone.utc)
        transfer.completed_at = datetime.now(timezone.utc)
        await self.db.flush()
        return transfer

    async def cancel_transfer(self, transfer_id: str, user_id: str) -> Transfer:
        """Cancel a transfer and refund to sender."""
        transfer = await self.db.get(Transfer, transfer_id)
        if not transfer:
            raise ValueError("Transfer not found")

        cancellable = {
            TransferStatus.QUOTED.value,
            TransferStatus.ESCROW_LOCKED.value,
            TransferStatus.AGENT_MATCHED.value,
        }
        if transfer.status not in cancellable:
            raise ValueError(f"Transfer in status {transfer.status} cannot be cancelled")

        if transfer.sender_id != user_id:
            raise ValueError("Only the sender can cancel")

        # Refund escrow if locked
        if transfer.escrow_status == EscrowStatus.LOCKED.value:
            sender = await self.db.get(User, transfer.sender_id)
            if self.escrow_service:
                await self.escrow_service.refund_funds(
                    transfer_id=transfer.id,
                    sender_address=sender.wallet_address or "",
                )
            sender.wallet_balance_usdc += transfer.total_debit_usd
            transfer.escrow_status = EscrowStatus.REFUNDED.value

        transfer.status = TransferStatus.CANCELLED.value
        transfer.cancelled_at = datetime.now(timezone.utc)
        await self.db.flush()
        return transfer

    async def rate_transfer(
        self, transfer_id: str, user_id: str, rating: int
    ) -> Transfer:
        """Rate a completed transfer (1-5 stars)."""
        if rating < 1 or rating > 5:
            raise ValueError("Rating must be between 1 and 5")

        transfer = await self.db.get(Transfer, transfer_id)
        if not transfer:
            raise ValueError("Transfer not found")
        if transfer.status != TransferStatus.DELIVERED.value:
            raise ValueError("Can only rate delivered transfers")

        if user_id == transfer.sender_id:
            transfer.sender_rating = rating
            # Update agent's average rating
            if transfer.agent_id:
                agent = await self.db.get(Agent, transfer.agent_id)
                if agent:
                    total = agent.total_transactions
                    agent.rating = (
                        (agent.rating * (total - 1) + rating) / total
                    )
        else:
            transfer.agent_rating = rating

        await self.db.flush()
        return transfer

    async def handle_timeout(self, transfer_id: str) -> Transfer:
        """Handle transfer that has timed out waiting for agent match."""
        transfer = await self.db.get(Transfer, transfer_id)
        if not transfer:
            raise ValueError("Transfer not found")

        # Refund
        sender = await self.db.get(User, transfer.sender_id)
        if transfer.escrow_status == EscrowStatus.LOCKED.value:
            if self.escrow_service:
                await self.escrow_service.refund_funds(
                    transfer_id=transfer.id,
                    sender_address=sender.wallet_address or "",
                )
            sender.wallet_balance_usdc += transfer.total_debit_usd
            transfer.escrow_status = EscrowStatus.REFUNDED.value

        transfer.status = TransferStatus.REFUNDED.value
        await self.db.flush()
        return transfer

    def _calculate_fee(self, amount_usd: float, corridor: Corridor) -> float:
        fee = amount_usd * (corridor.base_fee_percent / 100)
        fee += corridor.flat_fee_usd
        return max(fee, corridor.minimum_fee_usd)

    def _get_kyc_daily_limit(self, kyc_level: int) -> float:
        limits = {
            KYCLevel.NONE.value: 0.0,
            KYCLevel.BASIC.value: settings.MAX_DAILY_TRANSFER_KYC1,
            KYCLevel.ENHANCED.value: settings.MAX_DAILY_TRANSFER_KYC2,
            KYCLevel.FULL.value: settings.MAX_DAILY_TRANSFER_KYC3,
        }
        return limits.get(kyc_level, 0.0)

    async def _get_daily_transfer_total(self, sender_id: str) -> float:
        today_start = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        result = await self.db.execute(
            select(func.coalesce(func.sum(Transfer.send_amount_usd), 0.0)).where(
                Transfer.sender_id == sender_id,
                Transfer.created_at >= today_start,
                Transfer.status.notin_([
                    TransferStatus.CANCELLED.value,
                    TransferStatus.REFUNDED.value,
                    TransferStatus.EXPIRED.value,
                ]),
            )
        )
        return float(result.scalar())

    @staticmethod
    def _generate_pickup_code() -> str:
        return "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
