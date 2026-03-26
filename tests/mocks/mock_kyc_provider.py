"""Mock KYC verification provider for testing."""

from typing import Dict, Optional


class MockKYCProvider:
    """
    Simulates a KYC verification provider (e.g., Jumio, Onfido).

    Maintains a configurable set of verification results for testing
    different KYC scenarios.
    """

    def __init__(self):
        self._verifications: Dict[str, dict] = {}
        self._default_result = "approved"

    def set_verification_result(
        self,
        user_id: str,
        result: str,
        level: int = 1,
        reason: Optional[str] = None,
    ):
        """Pre-configure a verification result for a user."""
        self._verifications[user_id] = {
            "user_id": user_id,
            "result": result,  # approved, rejected, pending, manual_review
            "level": level,
            "reason": reason,
        }

    def set_default_result(self, result: str):
        """Set the default result for users not explicitly configured."""
        self._default_result = result

    async def verify_identity(self, user_id: str, documents: dict) -> dict:
        """
        Simulate identity verification.

        Args:
            user_id: User to verify.
            documents: Dict with document data (id_front, id_back, selfie, etc.)

        Returns:
            Verification result dict.
        """
        if user_id in self._verifications:
            return self._verifications[user_id]

        return {
            "user_id": user_id,
            "result": self._default_result,
            "level": 1,
            "reason": None,
        }

    async def check_sanctions(self, full_name: str, country: str) -> dict:
        """
        Simulate sanctions screening.

        Returns:
            Dict with match status and details.
        """
        # Pre-configured sanctioned names for testing
        sanctioned = {
            "BLOCKED PERSON": {"match": True, "source": "OFAC", "score": 100},
            "SANCTIONED ENTITY": {"match": True, "source": "UN", "score": 95},
        }

        normalized = full_name.upper().strip()
        if normalized in sanctioned:
            return {
                "screened_name": full_name,
                "match": True,
                "details": sanctioned[normalized],
            }

        return {
            "screened_name": full_name,
            "match": False,
            "details": None,
        }

    async def get_verification_status(self, user_id: str) -> dict:
        """Get the current verification status for a user."""
        if user_id in self._verifications:
            return self._verifications[user_id]
        return {
            "user_id": user_id,
            "result": "not_started",
            "level": 0,
            "reason": None,
        }

    def reset(self):
        self._verifications.clear()
        self._default_result = "approved"
