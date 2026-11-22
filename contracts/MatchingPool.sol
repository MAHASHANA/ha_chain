// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "./interfaces/IERC20.sol";
import "./interfaces/IEscrow.sol";
import "./interfaces/IObligationLedger.sol";
import "./interfaces/IProtocolRegistry.sol";

/// @title MatchingPool - Immutable peer-to-peer currency matching engine
/// @author Ha_Chain Protocol
/// @notice Core matching engine for the Ha_Chain remittance protocol. Users
///         deposit into currency pools and the algorithm finds counterparties
///         (direct, partial, or triangular). Matched pairs are settled atomically
///         through the Escrow contract.
/// @dev Fully immutable: no proxy pattern, no admin keys, no upgrade mechanism.
///      Protocol fee of 0.05% is hardcoded and sent to the treasury address
///      set at construction.
contract MatchingPool {
    // ──────────────────────────────────────────────
    //  Types
    // ──────────────────────────────────────────────

    struct DepositOrder {
        address depositor;
        bytes32 poolId;          // currency pool (keccak256("USD"), etc.)
        uint256 amount;          // original deposit amount
        uint256 remainingAmount; // unfilled portion
        bytes32 targetPoolId;    // what currency they want
        address recipient;       // who receives on the other side
        uint256 deadline;        // expiry timestamp
        bytes32 escrowId;        // linked escrow deposit
        bool filled;             // fully filled
        bool cancelled;          // cancelled by depositor or expired
    }

    // ──────────────────────────────────────────────
    //  Constants
    // ──────────────────────────────────────────────

    /// @notice Protocol fee: 0.05% (5 basis points)
    uint256 public constant FEE_BPS = 5;
    uint256 public constant FEE_DENOMINATOR = 10_000;

    /// @notice Default escrow expiry: 24 hours
    uint256 public constant DEFAULT_ESCROW_DURATION = 24 hours;

    /// @notice Match type identifiers
    bytes32 public constant MATCH_DIRECT = keccak256("direct");
    bytes32 public constant MATCH_PARTIAL = keccak256("partial");
    bytes32 public constant MATCH_TRIANGULAR = keccak256("triangular");

    // ──────────────────────────────────────────────
    //  Immutable State
    // ──────────────────────────────────────────────

    /// @notice Escrow contract for fund custody
    IEscrow public immutable escrow;

    /// @notice Obligation ledger for audit trail
    IObligationLedger public immutable ledger;

    /// @notice Protocol registry for pool configs
    IProtocolRegistry public immutable registry;

    /// @notice Treasury address for protocol fees
    address public immutable treasury;

    // ──────────────────────────────────────────────
    //  State
    // ──────────────────────────────────────────────

    /// @notice All deposit orders by ID
    mapping(bytes32 => DepositOrder) private _orders;

    /// @notice Order nonce for unique IDs
    uint256 private _orderNonce;

    /// @notice Active order IDs per pool pair (poolId => targetPoolId => orderIds[])
    mapping(bytes32 => mapping(bytes32 => bytes32[])) private _poolOrders;

    /// @notice Index of an order in its pool pair array (for O(1) removal)
    mapping(bytes32 => uint256) private _orderIndex;

    /// @notice Whether an order ID is in the active pool
    mapping(bytes32 => bool) private _orderActive;

    /// @notice User's order IDs for enumeration
    mapping(address => bytes32[]) private _userOrders;

    /// @notice Total number of orders created
    uint256 public orderCount;

    /// @notice Total number of successful matches
    uint256 public matchCount;

    /// @notice Reentrancy guard
    uint256 private _guardStatus;

    // ──────────────────────────────────────────────
    //  Events
    // ──────────────────────────────────────────────

    /// @dev Emitted when a new deposit order is created
    event OrderCreated(
        bytes32 indexed orderId,
        address indexed depositor,
        bytes32 indexed poolId,
        bytes32 targetPoolId,
        uint256 amount,
        address recipient,
        uint256 deadline
    );

    /// @dev Emitted when two orders are directly matched
    event DirectMatch(
        bytes32 indexed orderId1,
        bytes32 indexed orderId2,
        uint256 amount
    );

    /// @dev Emitted when orders are partially matched
    event PartialMatch(
        bytes32 indexed orderId1,
        bytes32 indexed orderId2,
        uint256 matchedAmount,
        uint256 remainingAmount1,
        uint256 remainingAmount2
    );

    /// @dev Emitted for a triangular match (A->B->C->A)
    event TriangularMatch(
        bytes32 indexed orderId1,
        bytes32 indexed orderId2,
        bytes32 indexed orderId3,
        uint256 amount
    );

    /// @dev Emitted when an order is cancelled
    event OrderCancelled(
        bytes32 indexed orderId,
        address indexed depositor,
        uint256 refundAmount
    );

    /// @dev Emitted when an expired order is refunded
    event OrderRefunded(
        bytes32 indexed orderId,
        address indexed depositor,
        uint256 refundAmount
    );

    // ──────────────────────────────────────────────
    //  Errors
    // ──────────────────────────────────────────────

    error ZeroAmount();
    error ZeroAddress();
    error InvalidPool();
    error SamePool();
    error InvalidDeadline();
    error AmountBelowMinimum();
    error AmountAboveMaximum();
    error OrderNotFound();
    error OrderAlreadyFilled();
    error OrderAlreadyCancelled();
    error NotOrderOwner();
    error OrderNotExpired();
    error OrderExpired();
    error PoolMismatch();
    error InsufficientAmount();
    error TransferFailed();
    error Reentrancy();
    error OrdersNotCompatible();

    // ──────────────────────────────────────────────
    //  Modifiers
    // ──────────────────────────────────────────────

    modifier nonReentrant() {
        if (_guardStatus == 1) revert Reentrancy();
        _guardStatus = 1;
        _;
        _guardStatus = 0;
    }

    // ──────────────────────────────────────────────
    //  Constructor
    // ──────────────────────────────────────────────

    /// @notice Deploy the matching pool
    /// @param _escrow Address of the Escrow contract
    /// @param _ledger Address of the ObligationLedger contract
    /// @param _registry Address of the ProtocolRegistry contract
    /// @param _treasury Address that receives protocol fees
    constructor(
        address _escrow,
        address _ledger,
        address _registry,
        address _treasury
    ) {
        if (_escrow == address(0)) revert ZeroAddress();
        if (_ledger == address(0)) revert ZeroAddress();
        if (_registry == address(0)) revert ZeroAddress();
        if (_treasury == address(0)) revert ZeroAddress();

        escrow = IEscrow(_escrow);
        ledger = IObligationLedger(_ledger);
        registry = IProtocolRegistry(_registry);
        treasury = _treasury;
    }

    // ──────────────────────────────────────────────
    //  Core Functions
    // ──────────────────────────────────────────────

    /// @notice Create a deposit order and lock funds in escrow
    /// @param poolId The currency pool to deposit into (e.g., keccak256("USD"))
    /// @param targetPoolId The currency pool desired (e.g., keccak256("INR"))
    /// @param amount The amount of tokens to deposit
    /// @param recipient The address that receives matched funds on the other side
    /// @param deadline Expiry timestamp for this order
    /// @return orderId The unique identifier for this order
    function deposit(
        bytes32 poolId,
        bytes32 targetPoolId,
        uint256 amount,
        address recipient,
        uint256 deadline
    ) external nonReentrant returns (bytes32 orderId) {
        // Validate inputs
        if (amount == 0) revert ZeroAmount();
        if (recipient == address(0)) revert ZeroAddress();
        if (poolId == targetPoolId) revert SamePool();
        if (deadline <= block.timestamp) revert InvalidDeadline();
        // Escrow expiry equals the order deadline, so the escrow can never be
        // refunded out from under a still-open order.
        if (deadline > block.timestamp + DEFAULT_ESCROW_DURATION) revert InvalidDeadline();
        if (!registry.isPoolActive(poolId)) revert InvalidPool();
        if (!registry.isPoolActive(targetPoolId)) revert InvalidPool();

        // Check deposit limits
        uint256 minDep = registry.getMinDeposit(poolId);
        uint256 maxDep = registry.getMaxDeposit(poolId);
        if (amount < minDep) revert AmountBelowMinimum();
        if (amount > maxDep) revert AmountAboveMaximum();

        // Get pool token and transfer from depositor to escrow
        address token = registry.getPoolToken(poolId);
        bool success = IERC20(token).transferFrom(msg.sender, address(escrow), amount);
        if (!success) revert TransferFailed();

        // Lock funds in escrow
        bytes32 escrowId = escrow.lockFunds(token, msg.sender, amount, deadline);

        // Create order
        unchecked { ++_orderNonce; }
        orderId = keccak256(
            abi.encodePacked(msg.sender, poolId, targetPoolId, amount, _orderNonce, block.timestamp)
        );

        _orders[orderId] = DepositOrder({
            depositor: msg.sender,
            poolId: poolId,
            amount: amount,
            remainingAmount: amount,
            targetPoolId: targetPoolId,
            recipient: recipient,
            deadline: deadline,
            escrowId: escrowId,
            filled: false,
            cancelled: false
        });

        // Add to active orders pool
        _addToPool(orderId, poolId, targetPoolId);
        _userOrders[msg.sender].push(orderId);

        unchecked { ++orderCount; }

        emit OrderCreated(orderId, msg.sender, poolId, targetPoolId, amount, recipient, deadline);
    }

    /// @notice Match two orders directly (A wants B, B wants A)
    /// @param orderId1 First order
    /// @param orderId2 Second order
    /// @dev Anyone can call this to trigger a match. The caller receives no
    ///      reward -- matching is incentivized by off-chain relayers or bots.
    function matchDirect(bytes32 orderId1, bytes32 orderId2) external nonReentrant {
        DepositOrder storage order1 = _orders[orderId1];
        DepositOrder storage order2 = _orders[orderId2];

        // Validate both orders exist and are active
        _validateOrderActive(order1, orderId1);
        _validateOrderActive(order2, orderId2);

        // Verify compatibility: order1.poolId == order2.targetPoolId AND vice versa
        if (order1.poolId != order2.targetPoolId) revert OrdersNotCompatible();
        if (order2.poolId != order1.targetPoolId) revert OrdersNotCompatible();

        // Determine match amount (minimum of both remaining amounts)
        uint256 matchAmount = order1.remainingAmount < order2.remainingAmount
            ? order1.remainingAmount
            : order2.remainingAmount;

        bool isPartial = (order1.remainingAmount != order2.remainingAmount);

        // Release ONLY the matched amount from each escrow:
        // Order1's funds go to Order2's recipient (Order2's depositor wanted Order1's currency)
        // Order2's funds go to Order1's recipient (Order1's depositor wanted Order2's currency)
        // Any unmatched remainder stays in escrow, backing the still-open order.
        // NOTE: amounts are matched 1:1 across pools; FX conversion is not yet implemented.
        escrow.releasePartial(order1.escrowId, order2.recipient, matchAmount);
        escrow.releasePartial(order2.escrowId, order1.recipient, matchAmount);
        _fill(order1, orderId1, matchAmount);
        _fill(order2, orderId2, matchAmount);

        // Record on the obligation ledger
        bytes32 matchType = isPartial ? MATCH_PARTIAL : MATCH_DIRECT;
        ledger.recordMatch(orderId1, orderId2, matchAmount, 1e18, matchType);

        // Update pool volumes
        IObligationLedger(address(ledger)).addPoolVolume(order1.poolId, matchAmount);
        IObligationLedger(address(ledger)).addPoolVolume(order2.poolId, matchAmount);

        // Update obligations
        IObligationLedger(address(ledger)).updateObligation(
            order1.poolId,
            order2.poolId,
            matchAmount
        );

        // Record user match history
        IObligationLedger(address(ledger)).addUserMatch(order1.depositor, orderId1);
        IObligationLedger(address(ledger)).addUserMatch(order2.depositor, orderId2);

        unchecked { ++matchCount; }

        if (isPartial) {
            emit PartialMatch(
                orderId1,
                orderId2,
                matchAmount,
                order1.remainingAmount,
                order2.remainingAmount
            );
        } else {
            emit DirectMatch(orderId1, orderId2, matchAmount);
        }
    }

    /// @notice Match three orders in a triangular pattern (A->B->C->A)
    /// @param orderId1 Order wanting B (has A)
    /// @param orderId2 Order wanting C (has B)
    /// @param orderId3 Order wanting A (has C)
    /// @dev The triangular cycle: Order1 has poolA wants poolB,
    ///      Order2 has poolB wants poolC, Order3 has poolC wants poolA.
    ///      Settlement: Order1's funds -> Order3's recipient,
    ///      Order2's funds -> Order1's recipient, Order3's funds -> Order2's recipient.
    function matchTriangular(
        bytes32 orderId1,
        bytes32 orderId2,
        bytes32 orderId3
    ) external nonReentrant {
        DepositOrder storage order1 = _orders[orderId1];
        DepositOrder storage order2 = _orders[orderId2];
        DepositOrder storage order3 = _orders[orderId3];

        // Validate all orders
        _validateOrderActive(order1, orderId1);
        _validateOrderActive(order2, orderId2);
        _validateOrderActive(order3, orderId3);

        // Verify triangular compatibility:
        // Order1 has poolA, wants poolB -> Order2 has poolB
        // Order2 has poolB, wants poolC -> Order3 has poolC
        // Order3 has poolC, wants poolA -> Order1 has poolA
        if (order1.targetPoolId != order2.poolId) revert OrdersNotCompatible();
        if (order2.targetPoolId != order3.poolId) revert OrdersNotCompatible();
        if (order3.targetPoolId != order1.poolId) revert OrdersNotCompatible();

        // Match amount is the minimum of all three remaining amounts
        uint256 matchAmount = order1.remainingAmount;
        if (order2.remainingAmount < matchAmount) matchAmount = order2.remainingAmount;
        if (order3.remainingAmount < matchAmount) matchAmount = order3.remainingAmount;

        // Release funds in the triangular pattern:
        // Order1's escrow (poolA tokens) -> Order3's recipient (Order3 wanted poolA)
        // Order2's escrow (poolB tokens) -> Order1's recipient (Order1 wanted poolB)
        // Order3's escrow (poolC tokens) -> Order2's recipient (Order2 wanted poolC)

        escrow.releasePartial(order1.escrowId, order3.recipient, matchAmount);
        escrow.releasePartial(order2.escrowId, order1.recipient, matchAmount);
        escrow.releasePartial(order3.escrowId, order2.recipient, matchAmount);
        _fill(order1, orderId1, matchAmount);
        _fill(order2, orderId2, matchAmount);
        _fill(order3, orderId3, matchAmount);

        // Record on ledger
        ledger.recordTriangularMatch(orderId1, orderId2, orderId3, matchAmount, 1e18);

        // Update pool volumes
        IObligationLedger(address(ledger)).addPoolVolume(order1.poolId, matchAmount);
        IObligationLedger(address(ledger)).addPoolVolume(order2.poolId, matchAmount);
        IObligationLedger(address(ledger)).addPoolVolume(order3.poolId, matchAmount);

        // Record user match history
        IObligationLedger(address(ledger)).addUserMatch(order1.depositor, orderId1);
        IObligationLedger(address(ledger)).addUserMatch(order2.depositor, orderId2);
        IObligationLedger(address(ledger)).addUserMatch(order3.depositor, orderId3);

        // Update obligations in the triangular cycle
        IObligationLedger(address(ledger)).updateObligation(order1.poolId, order2.poolId, matchAmount);
        IObligationLedger(address(ledger)).updateObligation(order2.poolId, order3.poolId, matchAmount);
        IObligationLedger(address(ledger)).updateObligation(order3.poolId, order1.poolId, matchAmount);

        unchecked { ++matchCount; }

        emit TriangularMatch(orderId1, orderId2, orderId3, matchAmount);
    }

    /// @notice Cancel an active order and trigger escrow refund
    /// @param orderId The order to cancel
    /// @dev Only the original depositor can cancel. Refund goes through escrow.
    function cancelOrder(bytes32 orderId) external nonReentrant {
        DepositOrder storage order = _orders[orderId];
        if (order.depositor == address(0)) revert OrderNotFound();
        if (order.depositor != msg.sender) revert NotOrderOwner();
        if (order.filled) revert OrderAlreadyFilled();
        if (order.cancelled) revert OrderAlreadyCancelled();

        order.cancelled = true;
        _removeFromPool(orderId, order.poolId, order.targetPoolId);

        // Return the unmatched remainder to the depositor, fee-free.
        escrow.refundRemaining(order.escrowId);

        emit OrderCancelled(orderId, order.depositor, order.remainingAmount);
    }

    /// @notice Claim refund for an expired order
    /// @param orderId The expired order
    /// @dev Anyone can call this after the order's deadline has passed.
    ///      The refund is processed through the escrow contract.
    function claimRefund(bytes32 orderId) external nonReentrant {
        DepositOrder storage order = _orders[orderId];
        if (order.depositor == address(0)) revert OrderNotFound();
        if (order.filled) revert OrderAlreadyFilled();
        if (order.cancelled) revert OrderAlreadyCancelled();
        if (block.timestamp <= order.deadline) revert OrderNotExpired();

        order.cancelled = true;
        _removeFromPool(orderId, order.poolId, order.targetPoolId);

        // Return the unmatched remainder to the depositor, fee-free.
        escrow.refundRemaining(order.escrowId);

        emit OrderRefunded(orderId, order.depositor, order.remainingAmount);
    }

    // ──────────────────────────────────────────────
    //  View Functions
    // ──────────────────────────────────────────────

    /// @notice Get an order by ID
    /// @param orderId The order identifier
    /// @return The DepositOrder struct
    function getOrder(bytes32 orderId) external view returns (DepositOrder memory) {
        return _orders[orderId];
    }

    /// @notice Get active orders for a pool pair
    /// @param poolId The source pool
    /// @param targetPoolId The target pool
    /// @return Array of active order IDs
    function getPoolOrders(
        bytes32 poolId,
        bytes32 targetPoolId
    ) external view returns (bytes32[] memory) {
        return _poolOrders[poolId][targetPoolId];
    }

    /// @notice Get all order IDs for a user
    /// @param user The user address
    /// @return Array of order IDs
    function getUserOrders(address user) external view returns (bytes32[] memory) {
        return _userOrders[user];
    }

    /// @notice Get the number of active orders in a pool pair
    /// @param poolId The source pool
    /// @param targetPoolId The target pool
    /// @return The count of active orders
    function getPoolOrderCount(
        bytes32 poolId,
        bytes32 targetPoolId
    ) external view returns (uint256) {
        return _poolOrders[poolId][targetPoolId].length;
    }

    /// @notice Calculate protocol fee for an amount
    /// @param amount The gross amount
    /// @return The fee (0.05%)
    function calculateFee(uint256 amount) external pure returns (uint256) {
        return (amount * FEE_BPS) / FEE_DENOMINATOR;
    }

    // ──────────────────────────────────────────────
    //  Internal Functions
    // ──────────────────────────────────────────────

    /// @dev Validate that an order exists and is active
    function _validateOrderActive(
        DepositOrder storage order,
        bytes32 orderId
    ) internal view {
        if (order.depositor == address(0)) revert OrderNotFound();
        if (order.filled) revert OrderAlreadyFilled();
        if (order.cancelled) revert OrderAlreadyCancelled();
        if (block.timestamp > order.deadline) revert OrderExpired();
        // suppress unused variable warning
        orderId;
    }

    /// @dev Reduce an order's remaining amount; close it out when fully filled
    function _fill(DepositOrder storage order, bytes32 orderId, uint256 amount) internal {
        order.remainingAmount -= amount;
        if (order.remainingAmount == 0) {
            order.filled = true;
            _removeFromPool(orderId, order.poolId, order.targetPoolId);
        }
    }

    /// @dev Add an order to the active pool pair index
    function _addToPool(bytes32 orderId, bytes32 poolId, bytes32 targetPoolId) internal {
        bytes32[] storage orders = _poolOrders[poolId][targetPoolId];
        _orderIndex[orderId] = orders.length;
        orders.push(orderId);
        _orderActive[orderId] = true;
    }

    /// @dev Remove an order from the active pool pair index (swap-and-pop)
    function _removeFromPool(bytes32 orderId, bytes32 poolId, bytes32 targetPoolId) internal {
        if (!_orderActive[orderId]) return;

        bytes32[] storage orders = _poolOrders[poolId][targetPoolId];
        uint256 index = _orderIndex[orderId];
        uint256 lastIndex = orders.length - 1;

        if (index != lastIndex) {
            bytes32 lastOrderId = orders[lastIndex];
            orders[index] = lastOrderId;
            _orderIndex[lastOrderId] = index;
        }

        orders.pop();
        delete _orderIndex[orderId];
        _orderActive[orderId] = false;
    }
}
