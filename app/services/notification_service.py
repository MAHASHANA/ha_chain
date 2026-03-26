"""Notification service -- sends SMS, push, and email alerts.

In production these would integrate with Twilio, FCM, SendGrid, etc.
For now we log notifications and store them for retrieval.
"""

from __future__ import annotations

import logging
import uuid

logger = logging.getLogger(__name__)


class NotificationService:
    """Fire-and-forget notification dispatcher."""

    async def send_transfer_initiated(self, user_id: uuid.UUID, transfer_id: uuid.UUID, amount: float, currency: str) -> None:
        logger.info(
            "NOTIFY user=%s: Transfer %s initiated for %s %s",
            user_id, transfer_id, amount, currency,
        )

    async def send_agent_matched(self, user_id: uuid.UUID, transfer_id: uuid.UUID, agent_name: str) -> None:
        logger.info(
            "NOTIFY user=%s: Agent '%s' matched for transfer %s",
            user_id, agent_name, transfer_id,
        )

    async def send_transfer_offer(self, agent_user_id: uuid.UUID, transfer_id: uuid.UUID, amount: float) -> None:
        logger.info(
            "NOTIFY agent_user=%s: New transfer offer %s amount=%s",
            agent_user_id, transfer_id, amount,
        )

    async def send_delivery_confirmed(self, user_id: uuid.UUID, transfer_id: uuid.UUID) -> None:
        logger.info(
            "NOTIFY user=%s: Transfer %s delivered successfully",
            user_id, transfer_id,
        )

    async def send_transfer_completed(self, user_id: uuid.UUID, transfer_id: uuid.UUID) -> None:
        logger.info(
            "NOTIFY user=%s: Transfer %s completed -- please rate your experience",
            user_id, transfer_id,
        )

    async def send_transfer_cancelled(self, user_id: uuid.UUID, transfer_id: uuid.UUID, reason: str) -> None:
        logger.info(
            "NOTIFY user=%s: Transfer %s cancelled -- reason: %s",
            user_id, transfer_id, reason,
        )

    async def send_pickup_code(self, user_id: uuid.UUID, transfer_id: uuid.UUID, pickup_code: str) -> None:
        logger.info(
            "NOTIFY user=%s: Pickup code for transfer %s is %s",
            user_id, transfer_id, pickup_code,
        )

    async def send_compliance_hold(self, user_id: uuid.UUID, transfer_id: uuid.UUID) -> None:
        logger.info(
            "NOTIFY user=%s: Transfer %s is on hold for compliance review",
            user_id, transfer_id,
        )
