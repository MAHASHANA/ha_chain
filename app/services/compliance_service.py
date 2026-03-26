"""Compliance service: AML/KYC checks, sanctions screening, pattern detection."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.enums import ComplianceAction, ComplianceCheckType
from app.models.models import Transfer, User, Corridor, ComplianceCheck, SanctionsList


@dataclass
class ComplianceResult:
    action: ComplianceAction
    reason: str
    checks: List[dict] = field(default_factory=list)
    risk_score: int = 0  # 0-100


class ComplianceService:
    # Countries on major sanctions lists
    SANCTIONED_COUNTRIES = {"PRK", "IRN", "SYR", "CUB"}

    # High-risk countries (higher scrutiny, not blocked)
    HIGH_RISK_COUNTRIES = {"SOM", "AFG", "YEM", "IRQ", "LBY", "SDN", "MMR"}

    def __init__(self, db: AsyncSession, kyc_provider=None):
        self.db = db
        self.kyc_provider = kyc_provider

    async def run_all_checks(self, transfer: Transfer) -> ComplianceResult:
        """Run the full compliance check suite on a transfer."""
        checks = []
        total_risk = 0
        max_action = ComplianceAction.APPROVED

        # 1. Sanctions screening
        sanctions_result = await self._check_sanctions(transfer)
        checks.append(sanctions_result)
        total_risk += sanctions_result["risk_score"]
        if sanctions_result["action"] == ComplianceAction.BLOCKED:
            return ComplianceResult(
                action=ComplianceAction.BLOCKED,
                reason=sanctions_result["details"],
                checks=checks,
                risk_score=100,
            )

        # 2. Country risk
        country_result = await self._check_country_risk(transfer)
        checks.append(country_result)
        total_risk += country_result["risk_score"]

        # 3. Amount threshold
        amount_result = self._check_amount_threshold(transfer)
        checks.append(amount_result)
        total_risk += amount_result["risk_score"]
        if amount_result["action"].value > max_action.value if hasattr(max_action, 'value') else False:
            max_action = amount_result["action"]

        # 4. Velocity check
        velocity_result = await self._check_velocity(transfer)
        checks.append(velocity_result)
        total_risk += velocity_result["risk_score"]

        # 5. Structuring detection
        structuring_result = await self._check_structuring(transfer)
        checks.append(structuring_result)
        total_risk += structuring_result["risk_score"]

        # Persist checks
        for check in checks:
            cc = ComplianceCheck(
                transfer_id=transfer.id,
                check_type=check["type"],
                result=check["action"].value,
                details=check.get("details", ""),
                risk_score=check["risk_score"],
            )
            self.db.add(cc)

        # Determine overall action
        action = self._determine_action(checks, total_risk)
        reason_parts = [c["details"] for c in checks if c["action"] != ComplianceAction.APPROVED]
        reason = "; ".join(reason_parts) if reason_parts else "All checks passed"

        # Auto SAR filing for critical risk
        if total_risk >= 80:
            action = ComplianceAction.SAR_FILED

        await self.db.flush()

        return ComplianceResult(
            action=action,
            reason=reason,
            checks=checks,
            risk_score=min(total_risk, 100),
        )

    async def _check_sanctions(self, transfer: Transfer) -> dict:
        """Screen receiver name against sanctions lists."""
        # Check sanctioned countries
        if transfer.receiver_country in self.SANCTIONED_COUNTRIES:
            return {
                "type": ComplianceCheckType.SANCTIONS.value,
                "action": ComplianceAction.BLOCKED,
                "details": f"Destination country {transfer.receiver_country} is sanctioned",
                "risk_score": 100,
            }

        # Screen name against OFAC list
        result = await self.db.execute(
            select(SanctionsList).where(
                SanctionsList.full_name == transfer.receiver_name
            )
        )
        match = result.scalar_one_or_none()
        if match:
            return {
                "type": ComplianceCheckType.SANCTIONS.value,
                "action": ComplianceAction.BLOCKED,
                "details": f"Receiver {transfer.receiver_name} matches {match.source} sanctions list",
                "risk_score": 100,
            }

        # Check sender sanctions status
        sender = await self.db.get(User, transfer.sender_id)
        if sender and sender.is_sanctioned:
            return {
                "type": ComplianceCheckType.SANCTIONS.value,
                "action": ComplianceAction.BLOCKED,
                "details": "Sender is flagged as sanctioned",
                "risk_score": 100,
            }

        return {
            "type": ComplianceCheckType.SANCTIONS.value,
            "action": ComplianceAction.APPROVED,
            "details": "No sanctions matches",
            "risk_score": 0,
        }

    async def _check_country_risk(self, transfer: Transfer) -> dict:
        """Assess country risk level."""
        corridor = await self.db.get(Corridor, transfer.corridor_id)
        risk_score = 0
        if corridor:
            risk_score = corridor.risk_score * 5  # Scale to 0-50

        if transfer.receiver_country in self.HIGH_RISK_COUNTRIES:
            risk_score = max(risk_score, 30)

        action = ComplianceAction.APPROVED
        if risk_score >= 40:
            action = ComplianceAction.ENHANCED_REVIEW

        return {
            "type": ComplianceCheckType.COUNTRY_RISK.value,
            "action": action,
            "details": f"Country risk score: {risk_score}",
            "risk_score": risk_score,
        }

    def _check_amount_threshold(self, transfer: Transfer) -> dict:
        """Check if amount triggers enhanced review."""
        if transfer.send_amount_usd >= settings.ENHANCED_REVIEW_THRESHOLD:
            return {
                "type": ComplianceCheckType.AMOUNT_THRESHOLD.value,
                "action": ComplianceAction.ENHANCED_REVIEW,
                "details": f"Amount ${transfer.send_amount_usd} exceeds ${settings.ENHANCED_REVIEW_THRESHOLD} threshold",
                "risk_score": 25,
            }
        return {
            "type": ComplianceCheckType.AMOUNT_THRESHOLD.value,
            "action": ComplianceAction.APPROVED,
            "details": "Amount within normal range",
            "risk_score": 0,
        }

    async def _check_velocity(self, transfer: Transfer) -> dict:
        """Check 24-hour transfer velocity."""
        since = datetime.now(timezone.utc) - timedelta(hours=24)
        result = await self.db.execute(
            select(func.coalesce(func.sum(Transfer.send_amount_usd), 0.0)).where(
                Transfer.sender_id == transfer.sender_id,
                Transfer.created_at >= since,
                Transfer.status.notin_(["cancelled", "refunded", "expired"]),
            )
        )
        total_24h = float(result.scalar()) + transfer.send_amount_usd

        if total_24h > settings.VELOCITY_24H_THRESHOLD:
            return {
                "type": ComplianceCheckType.VELOCITY.value,
                "action": ComplianceAction.FLAGGED,
                "details": f"24h velocity ${total_24h} exceeds ${settings.VELOCITY_24H_THRESHOLD}",
                "risk_score": 40,
            }
        return {
            "type": ComplianceCheckType.VELOCITY.value,
            "action": ComplianceAction.APPROVED,
            "details": f"24h velocity ${total_24h} within limits",
            "risk_score": 0,
        }

    async def _check_structuring(self, transfer: Transfer) -> dict:
        """Detect structuring (smurfing) patterns."""
        since = datetime.now(timezone.utc) - timedelta(
            hours=settings.STRUCTURING_WINDOW_HOURS
        )
        result = await self.db.execute(
            select(Transfer).where(
                Transfer.sender_id == transfer.sender_id,
                Transfer.created_at >= since,
                Transfer.send_amount_usd < settings.STRUCTURING_AMOUNT_THRESHOLD,
                Transfer.status.notin_(["cancelled", "refunded", "expired"]),
            )
        )
        recent_sub_threshold = list(result.scalars().all())

        # Count including the current transfer if it's sub-threshold
        count = len(recent_sub_threshold)
        if transfer.send_amount_usd < settings.STRUCTURING_AMOUNT_THRESHOLD:
            count += 1

        if count >= settings.STRUCTURING_COUNT_THRESHOLD:
            return {
                "type": ComplianceCheckType.STRUCTURING.value,
                "action": ComplianceAction.FLAGGED,
                "details": (
                    f"Potential structuring detected: {count} sub-${settings.STRUCTURING_AMOUNT_THRESHOLD} "
                    f"transfers in {settings.STRUCTURING_WINDOW_HOURS}h"
                ),
                "risk_score": 50,
            }
        return {
            "type": ComplianceCheckType.STRUCTURING.value,
            "action": ComplianceAction.APPROVED,
            "details": f"{count} sub-threshold transfers in window",
            "risk_score": 0,
        }

    def _determine_action(self, checks: List[dict], total_risk: int) -> ComplianceAction:
        """Determine overall compliance action from individual check results."""
        actions = [c["action"] for c in checks]

        if ComplianceAction.BLOCKED in actions:
            return ComplianceAction.BLOCKED
        if total_risk >= 80:
            return ComplianceAction.SAR_FILED
        if ComplianceAction.FLAGGED in actions or total_risk >= 50:
            return ComplianceAction.FLAGGED
        if ComplianceAction.ENHANCED_REVIEW in actions or total_risk >= 25:
            return ComplianceAction.ENHANCED_REVIEW
        return ComplianceAction.APPROVED
