"""Unit tests for the escrow service with mocked blockchain."""

import pytest

from app.enums import EscrowStatus
from app.services.escrow_service import EscrowService
from tests.mocks.mock_blockchain import MockEscrowService


class TestEscrowLock:
    """Tests for locking funds in escrow."""

    @pytest.mark.asyncio
    async def test_lock_funds_returns_tx_hash(self, mock_escrow):
        """Locking funds should return a valid transaction hash."""
        svc = EscrowService(mock_escrow)
        tx_hash = await svc.lock_funds(
            transfer_id="transfer-001",
            amount_usdc=500.0,
            sender_address="GSENDER123",
        )
        assert tx_hash is not None
        assert len(tx_hash) == 64  # SHA256 hex

    @pytest.mark.asyncio
    async def test_lock_funds_records_state(self, mock_escrow):
        """Locked escrow should be tracked in mock state."""
        svc = EscrowService(mock_escrow)
        await svc.lock_funds("transfer-001", 500.0, "GSENDER123")

        status = await svc.get_status("transfer-001")
        assert status["status"] == "locked"
        assert status["amount_usdc"] == 500.0

    @pytest.mark.asyncio
    async def test_lock_fails_on_zero_amount(self, mock_escrow):
        """Should reject zero or negative amounts."""
        svc = EscrowService(mock_escrow)
        with pytest.raises(ValueError, match="positive"):
            await svc.lock_funds("transfer-001", 0.0, "GSENDER123")

    @pytest.mark.asyncio
    async def test_lock_fails_on_empty_address(self, mock_escrow):
        """Should reject empty sender address."""
        svc = EscrowService(mock_escrow)
        with pytest.raises(ValueError, match="required"):
            await svc.lock_funds("transfer-001", 500.0, "")


class TestEscrowRelease:
    """Tests for releasing escrowed funds."""

    @pytest.mark.asyncio
    async def test_release_funds_succeeds(self, mock_escrow):
        """Releasing locked escrow should succeed."""
        svc = EscrowService(mock_escrow)
        await svc.lock_funds("transfer-001", 500.0, "GSENDER123")

        tx_hash = await svc.release_funds("transfer-001", "GAGENT456")
        assert tx_hash is not None

        status = await svc.get_status("transfer-001")
        assert status["status"] == "released"

    @pytest.mark.asyncio
    async def test_release_fails_if_not_locked(self, mock_escrow):
        """Cannot release funds that are not in locked state."""
        svc = EscrowService(mock_escrow)

        # No escrow exists - get_escrow_status returns 'pending'
        with pytest.raises(ValueError, match="Cannot release"):
            await svc.release_funds("transfer-001", "GAGENT456")

    @pytest.mark.asyncio
    async def test_double_release_fails(self, mock_escrow):
        """Cannot release the same escrow twice."""
        svc = EscrowService(mock_escrow)
        await svc.lock_funds("transfer-001", 500.0, "GSENDER123")
        await svc.release_funds("transfer-001", "GAGENT456")

        with pytest.raises(ValueError, match="Cannot release"):
            await svc.release_funds("transfer-001", "GAGENT456")


class TestEscrowRefund:
    """Tests for refunding escrowed funds."""

    @pytest.mark.asyncio
    async def test_refund_succeeds(self, mock_escrow):
        """Refunding locked escrow should succeed."""
        svc = EscrowService(mock_escrow)
        await svc.lock_funds("transfer-001", 500.0, "GSENDER123")

        tx_hash = await svc.refund_funds("transfer-001", "GSENDER123")
        assert tx_hash is not None

        status = await svc.get_status("transfer-001")
        assert status["status"] == "refunded"

    @pytest.mark.asyncio
    async def test_refund_fails_if_released(self, mock_escrow):
        """Cannot refund escrow that was already released."""
        svc = EscrowService(mock_escrow)
        await svc.lock_funds("transfer-001", 500.0, "GSENDER123")
        await svc.release_funds("transfer-001", "GAGENT456")

        with pytest.raises(ValueError, match="Cannot refund"):
            await svc.refund_funds("transfer-001", "GSENDER123")

    @pytest.mark.asyncio
    async def test_refund_fails_if_already_refunded(self, mock_escrow):
        """Cannot refund escrow that was already refunded."""
        svc = EscrowService(mock_escrow)
        await svc.lock_funds("transfer-001", 500.0, "GSENDER123")
        await svc.refund_funds("transfer-001", "GSENDER123")

        with pytest.raises(ValueError, match="Cannot refund"):
            await svc.refund_funds("transfer-001", "GSENDER123")


class TestEscrowStatus:
    """Tests for escrow status querying."""

    @pytest.mark.asyncio
    async def test_unknown_transfer_returns_pending(self, mock_escrow):
        """Querying unknown transfer should return pending status."""
        svc = EscrowService(mock_escrow)
        status = await svc.get_status("nonexistent-transfer")
        assert status["status"] == "pending"
        assert status["amount_usdc"] == 0.0

    @pytest.mark.asyncio
    async def test_status_transitions(self, mock_escrow):
        """Verify the full status lifecycle: pending -> locked -> released."""
        svc = EscrowService(mock_escrow)

        # Pending (not yet created)
        status = await svc.get_status("transfer-001")
        assert status["status"] == "pending"

        # Locked
        await svc.lock_funds("transfer-001", 500.0, "GSENDER123")
        status = await svc.get_status("transfer-001")
        assert status["status"] == "locked"

        # Released
        await svc.release_funds("transfer-001", "GAGENT456")
        status = await svc.get_status("transfer-001")
        assert status["status"] == "released"

    @pytest.mark.asyncio
    async def test_multiple_escrows_independent(self, mock_escrow):
        """Multiple escrows should be tracked independently."""
        svc = EscrowService(mock_escrow)
        await svc.lock_funds("transfer-001", 500.0, "GSENDER1")
        await svc.lock_funds("transfer-002", 1000.0, "GSENDER2")

        status1 = await svc.get_status("transfer-001")
        status2 = await svc.get_status("transfer-002")

        assert status1["amount_usdc"] == 500.0
        assert status2["amount_usdc"] == 1000.0

        # Release one, verify other is still locked
        await svc.release_funds("transfer-001", "GAGENT1")
        status1 = await svc.get_status("transfer-001")
        status2 = await svc.get_status("transfer-002")

        assert status1["status"] == "released"
        assert status2["status"] == "locked"
