# Ha_Chain Technical Specification

## For Any Agent Working On The Codebase

---

## CURRENT BUILD STATUS

### What Exists and Works
- **Backend API**: 46 endpoints, FastAPI, running on port 8000
- **Matching Engine**: P2P currency matching (direct, partial, triangular), 30/30 tests passing
- **Smart Contracts**: 9 Solidity files (MatchingPool, Escrow, LiquidityPool, ObligationLedger, ProtocolRegistry)
- **Mobile App**: 26 React Native TypeScript files (all screens, components, services)
- **Test Suite**: 14 test files, matching engine tests all passing
- **Venv**: At `/home/lucid25/ha_chain/venv/` with all Python deps installed

### How to Run
```bash
cd /home/lucid25/ha_chain

# Activate venv
source venv/bin/activate

# Run matching engine tests (30/30 passing)
python -m pytest tests/unit/test_matching_engine.py tests/integration/test_full_matching_flow.py -v

# Start API server
uvicorn app.main:app --host 0.0.0.0 --port 8000

# API docs at http://localhost:8000/docs
```

### Environment
- Python 3.10, venv at `./venv/`
- `.env` file configured for SQLite (dev) -- see `.env`
- ROS is installed on this system -- when running pytest outside venv, use:
  `PYTHONPATH="" PYTHONNOUSERSITE=1 venv/bin/python -m pytest ...`

---

## PROJECT STRUCTURE

```
ha_chain/
├── .env                          # SQLite dev config
├── CLAUDE.md                     # Full project context (READ FIRST)
├── TECHNICAL.md                  # This file
├── pyproject.toml                # Python project config
├── venv/                         # Python virtual environment
│
├── contracts/                    # Solidity smart contracts (9 files)
│   ├── MatchingPool.sol          # P2P currency matching (immutable)
│   ├── Escrow.sol                # Trustless fund locking (immutable)
│   ├── LiquidityPool.sol         # Fill unmatched orders (immutable)
│   ├── ObligationLedger.sol      # Permanent match records (immutable)
│   ├── ProtocolRegistry.sol      # Currency pool configs (immutable)
│   └── interfaces/               # IEscrow, IProtocolRegistry, IObligationLedger, IERC20
│
├── mobile/                       # React Native app (26 files)
│   ├── package.json
│   ├── App.tsx                   # Root component
│   ├── index.js                  # Entry point
│   └── src/
│       ├── navigation/AppNavigator.tsx
│       ├── screens/
│       │   ├── auth/             # WelcomeScreen, LoginScreen
│       │   ├── home/HomeScreen.tsx
│       │   ├── send/             # SendScreen, QuoteScreen, ConfirmScreen, SuccessScreen
│       │   ├── pool/PoolStatusScreen.tsx
│       │   └── invest/           # AssetsScreen, PortfolioScreen
│       ├── components/
│       │   ├── common/           # Button, Card, AmountInput, CurrencySelector
│       │   ├── home/             # BalanceCard, QuickActions
│       │   └── send/             # FeeBreakdown, MatchStatus
│       ├── services/             # api.ts, transfer.ts
│       ├── store/AuthContext.tsx
│       ├── types/index.ts
│       ├── theme/index.ts
│       └── utils/                # formatting.ts, constants.ts
│
├── app/                          # FastAPI backend (67 Python files)
│   ├── main.py                   # App factory, /health endpoint
│   ├── config.py                 # Pydantic settings (reads .env)
│   ├── database.py               # Async SQLAlchemy engine + session
│   ├── constants.py              # All enums (25+)
│   ├── enums.py                  # Additional enums
│   ├── exceptions.py             # 17 exception classes
│   ├── dependencies.py           # FastAPI deps (get_db, get_current_user)
│   │
│   ├── models/                   # SQLAlchemy ORM (30+ tables)
│   │   ├── matching.py           # NEW: MatchOrder, Match, LiquidityPosition, LiquidityFill, LocalPayment, PoolSnapshot
│   │   ├── models.py             # OLD: User, Agent, Corridor, Transfer, etc.
│   │   ├── user.py               # User, UserWallet, UserBeneficiary
│   │   ├── agent.py              # Agent, AgentStake, AgentCoverage
│   │   ├── transfer.py           # Transfer, TransferStatusLog
│   │   ├── escrow.py             # EscrowTransaction, SettlementBatch
│   │   ├── corridor.py           # Corridor, CorridorPaymentMethod, ExchangeRate
│   │   ├── kyc.py                # KYCVerification, SanctionsCheck
│   │   ├── rating.py             # Rating, AgentReputation
│   │   ├── investment.py         # TokenizedAsset, InvestmentPosition, InvestmentTransaction
│   │   ├── compliance.py         # ComplianceAlert, SuspiciousActivityReport
│   │   └── notification.py       # Notification
│   │
│   ├── services/                 # Business logic (17 services)
│   │   ├── matching_engine.py    # CORE: P2P matching (direct, partial, triangular)
│   │   ├── pool_manager.py       # Pool stats, match rate estimation
│   │   ├── liquidity_service.py  # LP deposits, fills, earnings (LP_SPREAD=0.002)
│   │   ├── local_settlement.py   # Mock payment rails (UPI, ACH, SEPA, SPEI, mobile money)
│   │   ├── transfer_service.py   # Legacy transfer lifecycle
│   │   ├── matching_service.py   # Legacy agent matching
│   │   ├── compliance_service.py # AML: sanctions, velocity, structuring, auto-SAR
│   │   ├── corridor_service.py   # Corridor fees, rates, limits
│   │   ├── escrow_service.py     # Blockchain escrow wrapper
│   │   ├── investment_service.py # Buy/sell tokenized assets
│   │   ├── exchange_rate_service.py # FX rates with caching
│   │   ├── user_service.py       # Registration, auth, wallets
│   │   ├── agent_service.py      # Agent registration, staking
│   │   ├── kyc_service.py        # KYC verification workflow
│   │   ├── rating_service.py     # Ratings + reputation
│   │   └── notification_service.py # SMS/push/email
│   │
│   ├── api/
│   │   ├── v1/                   # API routes
│   │   │   ├── router.py         # Combines all sub-routers
│   │   │   ├── auth.py           # POST register, login, refresh
│   │   │   ├── users.py          # GET/PATCH profile, wallets, beneficiaries
│   │   │   ├── agents.py         # POST register, stake; GET dashboard
│   │   │   ├── transfers.py      # POST quote, create; GET track
│   │   │   ├── corridors.py      # GET corridors, rates
│   │   │   ├── investments.py    # GET assets; POST buy/sell; GET portfolio
│   │   │   ├── compliance.py     # GET alerts, dashboard, disputes
│   │   │   └── matching.py       # NEW: POST estimate/orders; GET pools/live
│   │   └── schemas/              # Pydantic request/response models
│   │       ├── auth.py, user.py, agent.py, transfer.py
│   │       ├── corridor.py, investment.py, common.py
│   │       └── matching.py       # NEW: OrderEstimate, OrderCreate, PoolStatus, etc.
│   │
│   └── core/
│       ├── security.py           # JWT tokens, bcrypt hashing
│       └── dependencies.py       # Auth dependencies
│
├── tests/                        # Test suite (14 test files)
│   ├── conftest.py               # Fixtures, factories, mock setup
│   ├── factories.py              # Factory-boy model factories
│   ├── mocks/
│   │   ├── mock_blockchain.py    # MockEscrowService, MockStakingService
│   │   ├── mock_kyc_provider.py
│   │   ├── mock_exchange_rate.py # Rates for 9 currency pairs
│   │   └── mock_mobile_money.py  # Zaad, M-Pesa, UPI, SPEI, GCash
│   ├── unit/
│   │   ├── test_matching_engine.py  # 26 tests (NEW, ALL PASSING)
│   │   ├── test_transfer_service.py
│   │   ├── test_matching_service.py
│   │   ├── test_compliance_service.py
│   │   ├── test_corridor_service.py
│   │   ├── test_escrow_service.py
│   │   ├── test_investment_service.py
│   │   └── test_exchange_rate.py
│   └── integration/
│       ├── test_full_matching_flow.py  # 4 tests (NEW, ALL PASSING)
│       ├── test_transfer_flow.py
│       ├── test_agent_lifecycle.py
│       ├── test_multi_corridor.py
│       ├── test_compliance_flow.py
│       └── test_investment_flow.py
│
└── docs/                         # Business documentation (7 files)
    ├── 01_PROBLEM.md
    ├── 02_BUSINESS_MODEL.md
    ├── 03_ARCHITECTURE.md
    ├── 04_GLOBAL_CORRIDORS.md
    ├── 05_USER_PROFIT.md
    ├── 06_MARKET_RESEARCH.md
    └── 07_LEGAL_STRATEGY.md
```

---

## THE MATCHING ENGINE (Core Innovation)

### How It Works

```python
# app/services/matching_engine.py

PROTOCOL_FEE = 0.0005  # 0.05% hardcoded

class MatchingEngine:
    # Submit order to pool
    async def submit_order(user_id, source_currency, target_currency, amount, recipient_info, max_wait_hours=4)

    # Direct match: A wants USD→INR, B wants INR→USD
    async def find_direct_match(order) → Optional[Match]

    # Partial match: Split across multiple counterparties (FIFO)
    async def find_partial_matches(order) → List[PartialMatch]

    # Triangular: A→B→C→A cycle detection using directed graph
    async def find_triangular_match(order) → Optional[TriangularMatch]

    # Fill remainder from liquidity pool
    async def fill_from_liquidity(order, remaining) → LiquidityFill

    # Execute match: trigger local payments on both sides
    async def execute_match(match) → ExecutionResult

    # Main loop (runs every few seconds)
    async def run_matching_cycle():
        # 1. Expire old orders past max_wait
        # 2. Find direct matches
        # 3. Find partial matches
        # 4. Find triangular matches
        # 5. Fill remaining from liquidity
        # 6. Execute all matches
```

### Matching Algorithm Scoring
For agent-based delivery (legacy model):
```
score = (rating × 0.35) + (success_rate × 0.25) + (speed × 0.20) + (stake × 0.10) + (price × 0.10)
```

### Key Constants
- `PROTOCOL_FEE = 0.0005` (0.05%)
- `LP_SPREAD = 0.002` (0.2% earned by liquidity providers)
- `INTERFACE_FEE = 0.99` ($0.99 flat per transaction)
- `MAX_WAIT_HOURS = 4` (default wait for matching)
- `ESCROW_TIMEOUT = 24 hours` (auto-refund)

---

## DATABASE MODELS (Key Tables)

### New Matching Models (app/models/matching.py)
```
MatchOrder:      id, user_id, source_currency, target_currency, amount,
                 amount_matched, amount_unmatched, recipient_info(JSON),
                 status, max_wait_until, created_at

Match:           id, order_id_1, order_id_2, order_id_3(nullable),
                 match_type(direct/partial/triangular), amount,
                 exchange_rate, protocol_fee, status, executed_at

LiquidityPosition: id, user_id, currency, amount, earned_fees, created_at

LiquidityFill:   id, order_id, lp_position_id, amount, spread_earned, filled_at

LocalPayment:    id, match_id, order_id, currency, amount, recipient_info(JSON),
                 payment_method, payment_rail, tx_reference, status, executed_at

PoolSnapshot:    id, currency, total_deposits, pending_orders,
                 match_rate_24h, avg_wait_seconds, snapshot_at
```

---

## API ENDPOINTS (46 total)

### Matching (NEW - the core)
```
POST   /api/v1/matching/estimate          # Pre-submission match estimate
POST   /api/v1/matching/orders            # Submit matching order
GET    /api/v1/matching/orders/{id}       # Track order status
DELETE /api/v1/matching/orders/{id}       # Cancel order
GET    /api/v1/matching/pools             # All pool statuses
GET    /api/v1/matching/pools/{currency}  # Specific pool
POST   /api/v1/matching/liquidity         # Add liquidity
DELETE /api/v1/matching/liquidity/{id}    # Remove liquidity
GET    /api/v1/matching/liquidity/positions  # My LP positions
GET    /api/v1/matching/live              # Recent matches feed
```

### Auth, Users, Agents, Transfers, Corridors, Investments, Compliance
(36 additional endpoints -- see full list by running server and visiting /docs)

---

## SMART CONTRACTS (Solidity)

All contracts are designed to be IMMUTABLE (no proxy pattern, no admin keys, no upgrade mechanism):

```
MatchingPool.sol       -- On-chain matching, deposit/match/cancel/refund
Escrow.sol             -- Lock/release/refund with timeout, multi-sig (2-of-3)
LiquidityPool.sol      -- LP deposits, order filling, fee distribution
ObligationLedger.sol   -- Permanent match records, pool obligations
ProtocolRegistry.sol   -- Currency pool configs (set at deployment)
```

Target deployment: Base Sepolia testnet (Ethereum L2)
Protocol fee: 0.05% hardcoded → treasury address (set at deployment, immutable)

---

## MOBILE APP (React Native)

### Key Screens
- **SendScreen** -- Currency pair selector, amount input, LIVE match estimate, fee breakdown, competitor comparison
- **QuoteScreen** -- Transparent fee display: matched portion (FREE), unmatched (0.2%), platform ($0.99)
- **PoolStatusScreen** -- Live pool visualization, match feed, order book
- **HomeScreen** -- Balance, quick actions, pool stats, recent transfers
- **AssetsScreen** -- Browse tokenized assets (treasuries, gold, real estate)

### Theme
- Primary: #2563EB (blue)
- Secondary: #10B981 (green)
- Accent: #F59E0B (amber)
- Background: #F8FAFC

### Build for Android
```bash
cd mobile
npm install
npx react-native run-android
```

---

## WHAT NEEDS TO BE BUILT NEXT

### Priority 1: Deploy Smart Contracts to Testnet
- [ ] Set up Hardhat/Foundry config for Base Sepolia
- [ ] Write deployment scripts
- [ ] Deploy all 5 contracts
- [ ] Verify on block explorer
- [ ] Write contract tests (Hardhat)

### Priority 2: Connect Backend to Smart Contracts
- [ ] Web3 integration in escrow_service.py (replace mock with real Stellar/Base calls)
- [ ] Listen for on-chain events (match executed, escrow released)
- [ ] Sync on-chain state with database

### Priority 3: Mobile App Build
- [ ] `npm install` in mobile/
- [ ] Configure Android build (android/ directory setup)
- [ ] Connect to backend API (update API_URL in constants.ts)
- [ ] Test full flow on Android emulator

### Priority 4: Database Migration
- [ ] Set up Alembic for schema migrations
- [ ] Create initial migration from all models
- [ ] Support both SQLite (dev) and PostgreSQL (prod)

### Priority 5: Real Payment Rail Integration
- [ ] UPI integration (India) -- sandbox API
- [ ] SPEI integration (Mexico) -- sandbox API
- [ ] Mobile money integration (Zaad, M-Pesa) -- sandbox APIs
- [ ] ACH integration (USA) -- sandbox API

### Priority 6: Authentication & Security
- [ ] OTP-based phone auth (Twilio)
- [ ] JWT token refresh flow
- [ ] Rate limiting on all endpoints
- [ ] Input validation hardening

---

## IMPORTANT NOTES FOR AGENTS

1. **The matching engine is the CORE** -- everything else supports it. `matching_engine.py` is the most important file.

2. **Two model systems exist** -- `app/models/models.py` (old, agent-based) and `app/models/matching.py` (new, P2P matching). The new matching models are the future. The old ones will eventually be deprecated.

3. **ROS is installed on this machine** -- when running Python outside venv, ROS plugins interfere with pytest. Always use the venv: `source venv/bin/activate` or `PYTHONPATH="" PYTHONNOUSERSITE=1 venv/bin/python`

4. **Smart contracts must be IMMUTABLE** -- no admin keys, no proxy pattern, no upgrade mechanism. This is a legal requirement (Tornado Cash precedent protects immutable code from regulation).

5. **The protocol is NOT a money transmitter** -- this is by design. The interfaces (apps) are licensed. The protocol is autonomous code. Keep this separation clear in all code and documentation.

6. **Test everything** -- 30/30 matching tests pass. Don't break them. Add tests for new features.
