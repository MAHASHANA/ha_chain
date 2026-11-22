// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Test.sol";
import "../Escrow.sol";
import "../MatchingPool.sol";
import "../ObligationLedger.sol";
import "../ProtocolRegistry.sol";
import "./MockERC20.sol";

/// @notice Tests for escrow accounting in MatchingPool.
/// NOTE: amounts are matched 1:1 across pools (exchange rate hardcoded 1e18).
/// FX conversion is a separate, known gap; these tests use same-scale tokens.
contract MatchingPoolTest is Test {
    bytes32 constant USD = keccak256("USD");
    bytes32 constant INR = keccak256("INR");
    bytes32 constant MXN = keccak256("MXN");

    MockERC20 usd;
    MockERC20 inr;
    MockERC20 mxn;
    ProtocolRegistry registry;
    Escrow escrow;
    ObligationLedger ledger;
    MatchingPool pool;

    address treasury = makeAddr("treasury");
    address ali = makeAddr("ali");         // has USD, wants INR
    address raj = makeAddr("raj");         // has INR, wants USD
    address maria = makeAddr("maria");     // has MXN, wants USD (triangular)
    address aliRecipient = makeAddr("aliRecipient");
    address rajRecipient = makeAddr("rajRecipient");
    address mariaRecipient = makeAddr("mariaRecipient");

    uint256 constant FEE_BPS = 5;

    function setUp() public {
        usd = new MockERC20("USD");
        inr = new MockERC20("INR");
        mxn = new MockERC20("MXN");

        bytes32[] memory ids = new bytes32[](3);
        ids[0] = USD; ids[1] = INR; ids[2] = MXN;
        address[] memory toks = new address[](3);
        toks[0] = address(usd); toks[1] = address(inr); toks[2] = address(mxn);
        uint256[] memory mins = new uint256[](3);
        uint256[] memory maxs = new uint256[](3);
        for (uint256 i; i < 3; i++) { mins[i] = 1; maxs[i] = 1_000_000e6; }
        registry = new ProtocolRegistry(ids, toks, mins, maxs);

        // Escrow and Ledger need the MatchingPool address, and MatchingPool
        // needs theirs: predict the MatchingPool address (deployed 3rd).
        uint64 nonce = vm.getNonce(address(this));
        address predictedPool = vm.computeCreateAddress(address(this), nonce + 2);
        escrow = new Escrow(predictedPool, treasury);
        ledger = new ObligationLedger(predictedPool);
        pool = new MatchingPool(address(escrow), address(ledger), address(registry), treasury);
        assertEq(address(pool), predictedPool, "address prediction");

        _fund(ali, usd, 1_000e6);
        _fund(raj, inr, 1_000e6);
        _fund(maria, mxn, 1_000e6);
    }

    // ── helpers ──────────────────────────────────

    function _fund(address who, MockERC20 tok, uint256 amt) internal {
        tok.mint(who, amt);
        vm.prank(who);
        tok.approve(address(pool), type(uint256).max);
    }

    function _deposit(address who, bytes32 from, bytes32 to, uint256 amt, address recipient)
        internal returns (bytes32)
    {
        vm.prank(who);
        return pool.deposit(from, to, amt, recipient, block.timestamp + 12 hours);
    }

    function _fee(uint256 amt) internal pure returns (uint256) {
        return (amt * FEE_BPS) / 10_000;
    }

    // ── direct match ─────────────────────────────

    function test_fullMatch_paysBothSidesNetOfFee() public {
        bytes32 a = _deposit(ali, USD, INR, 100e6, aliRecipient);
        bytes32 r = _deposit(raj, INR, USD, 100e6, rajRecipient);

        pool.matchDirect(a, r);

        // Ali's USD goes to Raj's recipient; Raj's INR goes to Ali's recipient.
        assertEq(usd.balanceOf(rajRecipient), 100e6 - _fee(100e6));
        assertEq(inr.balanceOf(aliRecipient), 100e6 - _fee(100e6));
        assertTrue(pool.getOrder(a).filled);
        assertTrue(pool.getOrder(r).filled);
    }

    /// The original bug: a partial match released the larger order's ENTIRE escrow.
    function test_partialMatch_paysOnlyMatchedAmount() public {
        bytes32 a = _deposit(ali, USD, INR, 100e6, aliRecipient);
        bytes32 r = _deposit(raj, INR, USD, 40e6, rajRecipient);

        pool.matchDirect(a, r);

        // Only 40 matched: Raj's recipient gets 40 USD (net), not 100.
        assertEq(usd.balanceOf(rajRecipient), 40e6 - _fee(40e6), "overpaid larger side");
        assertEq(inr.balanceOf(aliRecipient), 40e6 - _fee(40e6));

        MatchingPool.DepositOrder memory oa = pool.getOrder(a);
        assertEq(oa.remainingAmount, 60e6);
        assertFalse(oa.filled);
        assertTrue(pool.getOrder(r).filled);
        // The 60 USD remainder is still in escrow, backing the open order.
        assertEq(escrow.getEscrowAmount(oa.escrowId), 60e6);
    }

    /// The remainder of a partially-filled order must still be matchable.
    function test_partialRemainder_canMatchAgain() public {
        bytes32 a = _deposit(ali, USD, INR, 100e6, aliRecipient);
        bytes32 r1 = _deposit(raj, INR, USD, 40e6, rajRecipient);
        pool.matchDirect(a, r1);

        bytes32 r2 = _deposit(raj, INR, USD, 60e6, rajRecipient);
        pool.matchDirect(a, r2);

        assertTrue(pool.getOrder(a).filled);
        assertEq(usd.balanceOf(rajRecipient), (40e6 - _fee(40e6)) + (60e6 - _fee(60e6)));
    }

    /// The remainder must be refundable on cancel, in full, with no fee.
    function test_cancelAfterPartial_refundsRemainderWithoutFee() public {
        bytes32 a = _deposit(ali, USD, INR, 100e6, aliRecipient);
        bytes32 r = _deposit(raj, INR, USD, 40e6, rajRecipient);
        pool.matchDirect(a, r);

        uint256 before = usd.balanceOf(ali);
        vm.prank(ali);
        pool.cancelOrder(a);
        assertEq(usd.balanceOf(ali) - before, 60e6);
    }

    function test_cancelUnmatched_refundsFullAmountWithoutFee() public {
        bytes32 a = _deposit(ali, USD, INR, 100e6, aliRecipient);
        vm.prank(ali);
        pool.cancelOrder(a);
        assertEq(usd.balanceOf(ali), 1_000e6, "cancel should not charge a fee");
        assertEq(escrow.accumulatedFees(address(usd)), 0);
    }

    function test_claimRefundAfterDeadline_returnsRemainder() public {
        bytes32 a = _deposit(ali, USD, INR, 100e6, aliRecipient);
        bytes32 r = _deposit(raj, INR, USD, 40e6, rajRecipient);
        pool.matchDirect(a, r);

        vm.warp(block.timestamp + 13 hours);
        pool.claimRefund(a);
        assertEq(usd.balanceOf(ali), 1_000e6 - 100e6 + 60e6);
    }

    function test_feesOnlyOnMatchedVolume_andWithdrawable() public {
        bytes32 a = _deposit(ali, USD, INR, 100e6, aliRecipient);
        bytes32 r = _deposit(raj, INR, USD, 40e6, rajRecipient);
        pool.matchDirect(a, r);

        assertEq(escrow.accumulatedFees(address(usd)), _fee(40e6));
        escrow.withdrawFees(address(usd));
        assertEq(usd.balanceOf(treasury), _fee(40e6));
    }

    // ── triangular ───────────────────────────────

    function test_triangularPartial_paysOnlyMatchedAmount() public {
        // Ali USD->INR, Raj INR->MXN, Maria MXN->USD
        bytes32 o1 = _deposit(ali, USD, INR, 100e6, aliRecipient);
        bytes32 o2 = _deposit(raj, INR, MXN, 50e6, rajRecipient);
        bytes32 o3 = _deposit(maria, MXN, USD, 80e6, mariaRecipient);

        pool.matchTriangular(o1, o2, o3);

        uint256 net = 50e6 - _fee(50e6);
        assertEq(usd.balanceOf(mariaRecipient), net);
        assertEq(inr.balanceOf(aliRecipient), net);
        assertEq(mxn.balanceOf(rajRecipient), net);
        assertEq(pool.getOrder(o1).remainingAmount, 50e6);
        assertEq(pool.getOrder(o3).remainingAmount, 30e6);
        assertTrue(pool.getOrder(o2).filled);
    }

    // ── solvency invariant (fuzz) ────────────────

    /// For any pair of amounts: escrow balance == sum of open remainders + unwithdrawn fees,
    /// and nobody receives more than was matched.
    function testFuzz_escrowStaysSolvent(uint96 amtA, uint96 amtR) public {
        uint256 a_ = bound(uint256(amtA), 1, 1_000e6);
        uint256 r_ = bound(uint256(amtR), 1, 1_000e6);
        bytes32 a = _deposit(ali, USD, INR, a_, aliRecipient);
        bytes32 r = _deposit(raj, INR, USD, r_, rajRecipient);

        pool.matchDirect(a, r);

        uint256 matched = a_ < r_ ? a_ : r_;
        assertEq(usd.balanceOf(rajRecipient), matched - _fee(matched));
        assertEq(
            usd.balanceOf(address(escrow)),
            pool.getOrder(a).remainingAmount + escrow.accumulatedFees(address(usd))
        );
        assertEq(
            inr.balanceOf(address(escrow)),
            pool.getOrder(r).remainingAmount + escrow.accumulatedFees(address(inr))
        );
    }

    // ── safety edges ─────────────────────────────

    function test_onlyMatchingPoolCanRelease() public {
        bytes32 a = _deposit(ali, USD, INR, 100e6, aliRecipient);
        bytes32 eid = pool.getOrder(a).escrowId;
        vm.expectRevert(Escrow.OnlyMatchingPool.selector);
        escrow.releasePartial(eid, address(this), 1e6);
        vm.expectRevert(Escrow.OnlyMatchingPool.selector);
        escrow.refundRemaining(eid);
    }

    function test_deadlineBeyondEscrowWindowRejected() public {
        vm.prank(ali);
        vm.expectRevert(MatchingPool.InvalidDeadline.selector);
        pool.deposit(USD, INR, 100e6, aliRecipient, block.timestamp + 25 hours);
    }

    function test_cannotMatchExpiredOrder() public {
        bytes32 a = _deposit(ali, USD, INR, 100e6, aliRecipient);
        bytes32 r = _deposit(raj, INR, USD, 100e6, rajRecipient);
        vm.warp(block.timestamp + 13 hours);
        vm.expectRevert(MatchingPool.OrderExpired.selector);
        pool.matchDirect(a, r);
    }

    function test_cannotMatchCancelledOrder() public {
        bytes32 a = _deposit(ali, USD, INR, 100e6, aliRecipient);
        bytes32 r = _deposit(raj, INR, USD, 100e6, rajRecipient);
        vm.prank(ali);
        pool.cancelOrder(a);
        vm.expectRevert(MatchingPool.OrderAlreadyCancelled.selector);
        pool.matchDirect(a, r);
    }

    function test_publicEscrowRefundAfterExpiry_isSafetyValve() public {
        bytes32 a = _deposit(ali, USD, INR, 100e6, aliRecipient);
        bytes32 eid = pool.getOrder(a).escrowId;
        vm.expectRevert(Escrow.EscrowNotExpired.selector);
        escrow.refund(eid);
        vm.warp(block.timestamp + 12 hours);
        escrow.refund(eid);
        assertEq(usd.balanceOf(ali), 1_000e6);
    }

    function test_cannotDoubleRefund() public {
        bytes32 a = _deposit(ali, USD, INR, 100e6, aliRecipient);
        vm.prank(ali);
        pool.cancelOrder(a);
        vm.warp(block.timestamp + 13 hours);
        vm.expectRevert(MatchingPool.OrderAlreadyCancelled.selector);
        pool.claimRefund(a);
    }
}
