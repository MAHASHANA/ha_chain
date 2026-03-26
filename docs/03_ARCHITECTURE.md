# Ha_Chain Technical Architecture

## System Overview

Ha_Chain is a blockchain-based remittance platform that legalizes informal value transfer (hawala) by combining smart contract escrow, decentralized identity, and tokenized asset investment into a single protocol.

```
                         HA_CHAIN ARCHITECTURE

  ┌──────────────────────────────────────────────────────────┐
  │                      CLIENT LAYER                         │
  │                                                           │
  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │
  │  │ Sender App  │  │ Agent App   │  │ Regulator   │      │
  │  │ (React      │  │ (React      │  │ Dashboard   │      │
  │  │  Native)    │  │  Native)    │  │ (Web)       │      │
  │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘      │
  └─────────┼────────────────┼────────────────┼──────────────┘
            │                │                │
            ▼                ▼                ▼
  ┌──────────────────────────────────────────────────────────┐
  │                      API GATEWAY                          │
  │           FastAPI + JWT Auth + Rate Limiting               │
  │           /api/v1/...                                      │
  └──────────────────────────┬───────────────────────────────┘
                             │
            ┌────────────────┼────────────────┐
            ▼                ▼                ▼
  ┌────────────────┐ ┌──────────────┐ ┌──────────────┐
  │  SERVICE LAYER │ │  ASYNC TASKS │ │  CACHE LAYER │
  │                │ │              │ │              │
  │ TransferSvc    │ │ Celery       │ │ Redis        │
  │ MatchingSvc    │ │ Workers:     │ │              │
  │ EscrowSvc      │ │ - Agent match│ │ - FX rates   │
  │ ComplianceSvc  │ │ - Compliance │ │ - Sessions   │
  │ CorridorSvc    │ │ - Settlement │ │ - Quotes     │
  │ InvestmentSvc  │ │ - Timeout    │ │ - Agent avail│
  │ RatingSvc      │ │ - Notify     │ │              │
  │ KYCSvc         │ │              │ │              │
  └───────┬────────┘ └──────┬───────┘ └──────────────┘
          │                  │
          ▼                  ▼
  ┌──────────────────────────────────────────────────────────┐
  │                    DATA LAYER                              │
  │                                                            │
  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
  │  │ PostgreSQL   │  │ Stellar      │  │ External     │    │
  │  │              │  │ Blockchain   │  │ Services     │    │
  │  │ 23 tables:   │  │              │  │              │    │
  │  │ - Users      │  │ - Escrow     │  │ - KYC: Onfido│    │
  │  │ - Agents     │  │   accounts   │  │ - AML:       │    │
  │  │ - Transfers  │  │ - Staking    │  │   Chainalysis│    │
  │  │ - Corridors  │  │   accounts   │  │ - FX: Open   │    │
  │  │ - Escrow     │  │ - Settlement │  │   Exchange   │    │
  │  │ - KYC        │  │ - USDC asset │  │ - Mobile $:  │    │
  │  │ - Ratings    │  │              │  │   Zaad, MPesa│    │
  │  │ - Investments│  │              │  │   UPI, SPEI  │    │
  │  │ - Compliance │  │              │  │ - Push: FCM  │    │
  │  │ - Notifs     │  │              │  │ - SMS: Twilio│    │
  │  └──────────────┘  └──────────────┘  └──────────────┘    │
  └──────────────────────────────────────────────────────────┘
```

---

## Core Services

### 1. Transfer Service (The Heart)

The transfer service orchestrates the entire remittance lifecycle:

```
TRANSFER LIFECYCLE:

  QUOTE                    User requests quote
    │                      → Find corridor, get rate, calculate fees
    ▼                      → Return: amount_received, fee, rate, expiry
  INITIATED                User confirms and pays
    │                      → Debit sender wallet
    ▼                      → Run compliance checks
  ESCROW_LOCKED            Funds locked on blockchain
    │                      → Create Stellar escrow transaction
    ▼                      → Trigger agent matching
  AGENT_MATCHED            Best agent selected
    │                      → Notify agent, 5-min acceptance window
    ▼                      → If declined, try next agent
  IN_DELIVERY              Agent is delivering funds
    │                      → Agent pays receiver (cash/mobile money/wallet)
    ▼                      → Receiver verifies (pickup code or biometric)
  COMPLETED                Transfer done
    │                      → Release escrow to agent
    ▼                      → Pay commission, update stats, request ratings

  FAILURE PATHS:
  → No agent found in 30 min → REFUNDED (escrow returns to sender)
  → Compliance block → CANCELLED (funds returned, SAR filed)
  → Dispute raised → DISPUTED (held for investigation)
  → Sender cancels before agent match → CANCELLED (escrow refunded)
```

### 2. Matching Service (The Brain)

Weighted scoring algorithm that matches transfers with the best available agent:

```
SCORE = (rating_avg × 0.35) +      # Quality of service
        (success_rate × 0.25) +     # Reliability
        (speed_score × 0.20) +      # How fast they deliver
        (stake_score × 0.10) +      # Skin in the game
        (price_score × 0.10)        # Commission competitiveness

FILTERS (must pass ALL):
  ✓ Agent is online
  ✓ Agent is in receiver's country/city
  ✓ Agent handles the delivery method (cash/mobile money/wallet)
  ✓ Agent has remaining daily capacity >= transfer amount
  ✓ Agent's license is active
  ✓ Agent has sufficient stake
```

### 3. Escrow Service (The Trust)

Blockchain-based escrow replaces personal trust between hawaladars:

```
STELLAR ESCROW FLOW:

  1. LOCK: Create multi-sig escrow account (2-of-3: sender, agent, platform)
     → Send USDC from sender to escrow account
     → Set 24-hour timeout (auto-refund if not completed)

  2. RELEASE: On delivery confirmation
     → Platform + agent sign release transaction
     → USDC moves from escrow to agent's wallet
     → Commission separated and paid

  3. REFUND: On cancellation or timeout
     → Platform + sender sign refund transaction
     → USDC returns to sender's wallet
```

### 4. Compliance Service (The Shield)

Real-time AML/KYC monitoring on every transaction:

```
COMPLIANCE PIPELINE (runs on every transfer):

  ┌──────────────┐
  │ SANCTIONS     │ Check sender + receiver against OFAC, EU, UN lists
  │ SCREENING     │ → Match = BLOCK transfer immediately
  └──────┬───────┘
         ▼
  ┌──────────────┐
  │ AMOUNT CHECK  │ Transfer > $3,000 = Enhanced KYC required
  │               │ Transfer > $10,000 = Manual review
  └──────┬───────┘
         ▼
  ┌──────────────┐
  │ VELOCITY      │ >$10,000 in 24 hours from same sender = FLAG
  │ CHECK         │ >$50,000 in 30 days = ENHANCED REVIEW
  └──────┬───────┘
         ▼
  ┌──────────────┐
  │ STRUCTURING   │ Multiple transfers just below thresholds
  │ DETECTION     │ e.g., 5 × $990 in one day = FLAG
  └──────┬───────┘
         ▼
  ┌──────────────┐
  │ COUNTRY RISK  │ High-risk corridors have lower thresholds
  │               │ Sanctioned countries = BLOCK
  └──────┬───────┘
         ▼
  ┌──────────────┐
  │ DECISION      │ APPROVE / FLAG / ENHANCED_REVIEW / BLOCK / SAR
  └──────────────┘
```

### 5. Corridor Service (The Map)

Manages every supported country pair with its specific rules:

```
CORRIDOR CONFIGURATION:

  USA → India:
    source_currency: USD
    dest_currency: INR
    base_fee: 1.0%
    min_transfer: $10
    max_transfer: $25,000
    delivery_methods: [UPI, IMPS, NEFT, bank_transfer]
    estimated_delivery: 15 minutes (UPI) / 2 hours (bank)
    kyc_required: Level 1 (up to $1,000/day)
                  Level 2 (up to $5,000/day)
                  Level 3 (up to $25,000/day)
    regulatory_notes: "RBI regulations apply on receiver side"

  USA → Mexico:
    source_currency: USD
    dest_currency: MXN
    base_fee: 0.8%
    delivery_methods: [SPEI, CoDi, cash_pickup]
    estimated_delivery: 10 minutes (SPEI) / 1 hour (cash)

  ... (9+ corridors configured)
```

### 6. Investment Service (The Growth Engine)

Tokenized asset access integrated directly into the remittance flow:

```
SUPPORTED ASSETS:

  US Treasury Bonds (BlackRock BUIDL)
    → Yield: ~4.2% APY
    → Min: $1
    → Risk: Very Low
    → Settlement: Ethereum/Base

  S&P 500 Index (Securitize)
    → Historical return: ~10% annual
    → Min: $5
    → Risk: Medium

  Gold (Paxos PAXG)
    → Backed by physical gold in London vaults
    → Min: $1
    → Risk: Low-Medium

  Real Estate (RealT)
    → Yield: 6-8% from rental income
    → Min: $10
    → Risk: Medium
```

---

## Database Schema (23 Tables)

### Core Entities:
- **User** (sender/receiver identity, KYC level, country)
- **UserWallet** (balances in multiple currencies/USDC)
- **UserBeneficiary** (saved recipients)

### Agent Network:
- **Agent** (licensed hawaladars/payout agents)
- **AgentStake** (blockchain collateral records)
- **AgentCoverage** (cities/countries served, payment methods)
- **AgentReputation** (computed scores and tiers)

### Transfer Engine:
- **Transfer** (the core transaction record, 24 columns)
- **TransferStatusLog** (immutable audit trail of every status change)

### Financial Infrastructure:
- **EscrowTransaction** (blockchain escrow records)
- **SettlementBatch** (agent settlement batches)
- **Corridor** (country pair configurations)
- **CorridorPaymentMethod** (delivery methods per corridor)
- **ExchangeRate** (cached FX rates)

### Compliance:
- **KYCVerification** (identity verification records)
- **SanctionsCheck** (OFAC/EU/UN screening results)
- **ComplianceAlert** (flagged transactions)
- **SuspiciousActivityReport** (auto-filed SARs)

### User Features:
- **Rating** (transfer ratings by users)
- **TokenizedAsset** (available investment assets)
- **InvestmentPosition** (user holdings)
- **InvestmentTransaction** (buy/sell records)
- **Notification** (SMS/push/email records)

---

## Technology Stack

| Layer | Technology | Why |
|---|---|---|
| **API Framework** | FastAPI (Python) | Async, fast, auto-docs, type-safe |
| **Database** | PostgreSQL + SQLAlchemy async | Reliable, JSONB support, proven at scale |
| **Cache** | Redis | FX rates, sessions, agent availability |
| **Task Queue** | Celery + Redis | Agent matching, settlement, notifications |
| **Blockchain** | Stellar Network | Designed for payments, USDC native, <1 second finality, $0.00001 per tx |
| **Backup Chain** | Base (Coinbase L2) or Arbitrum | For tokenized asset settlement |
| **KYC Provider** | Onfido / Jumio | Document + biometric verification |
| **AML Provider** | Chainalysis / Elliptic | Sanctions screening, transaction monitoring |
| **FX Rates** | Open Exchange Rates / CurrencyLayer | Real-time rates for 170+ currencies |
| **SMS** | Twilio | Global SMS for OTP and notifications |
| **Push** | Firebase Cloud Messaging | Mobile push notifications |
| **Mobile Apps** | React Native | Cross-platform iOS + Android |
| **Hosting** | AWS / GCP | Auto-scaling, multi-region |
| **Monitoring** | Datadog / Sentry | APM, error tracking, alerting |

---

## Security Architecture

### Authentication:
- JWT access tokens (15 min expiry) + refresh tokens (7 day)
- bcrypt password hashing
- Rate limiting on auth endpoints (5 attempts/minute)

### Data Protection:
- All PII encrypted at rest (AES-256)
- KYC documents stored as hashes, not raw images
- Biometric data stored as encrypted hashes only
- TLS 1.3 for all API communication
- Database encryption at rest

### Blockchain Security:
- Multi-sig escrow (2-of-3) prevents single-party theft
- Time-locked transactions (24hr auto-refund)
- Agent stakes provide financial collateral against fraud
- All blockchain transactions immutable and auditable

### Compliance Security:
- Real-time sanctions screening on every transaction
- Automated SAR filing for suspicious activity
- Regulator read-only API access (audit trail)
- Geographic restrictions enforced at API level

---

## API Endpoints Summary

### Authentication
| Method | Endpoint | Description |
|---|---|---|
| POST | /api/v1/auth/register | Create account |
| POST | /api/v1/auth/login | Get JWT tokens |
| POST | /api/v1/auth/refresh | Refresh access token |

### Users
| Method | Endpoint | Description |
|---|---|---|
| GET | /api/v1/users/me | Get profile |
| PATCH | /api/v1/users/me | Update profile |
| GET | /api/v1/users/me/wallets | List wallets |
| POST | /api/v1/users/me/beneficiaries | Add beneficiary |

### Transfers (Core)
| Method | Endpoint | Description |
|---|---|---|
| POST | /api/v1/transfers/quote | Get a quote |
| POST | /api/v1/transfers | Initiate transfer |
| GET | /api/v1/transfers/{id} | Track transfer |
| POST | /api/v1/transfers/{id}/confirm-delivery | Agent confirms payout |
| POST | /api/v1/transfers/{id}/dispute | Raise dispute |
| POST | /api/v1/transfers/{id}/cancel | Cancel transfer |
| POST | /api/v1/transfers/{id}/rate | Rate the transfer |

### Agents
| Method | Endpoint | Description |
|---|---|---|
| POST | /api/v1/agents/register | Become an agent |
| POST | /api/v1/agents/stake | Stake collateral |
| GET | /api/v1/agents/dashboard | Agent stats |
| POST | /api/v1/agents/transfers/{id}/accept | Accept a transfer |

### Corridors
| Method | Endpoint | Description |
|---|---|---|
| GET | /api/v1/corridors | List all corridors |
| GET | /api/v1/corridors/{id}/rates | Get current rates |

### Investments
| Method | Endpoint | Description |
|---|---|---|
| GET | /api/v1/investments/assets | Browse tokenized assets |
| POST | /api/v1/investments/buy | Buy asset |
| POST | /api/v1/investments/sell | Sell asset |
| GET | /api/v1/investments/portfolio | View portfolio |

### Compliance (Regulator Access)
| Method | Endpoint | Description |
|---|---|---|
| GET | /api/v1/compliance/alerts | View compliance alerts |
| GET | /api/v1/compliance/dashboard | Aggregate statistics |

---

## Testing Strategy

### Unit Tests (81 tests)
Test each service in isolation with mocked dependencies:
- Transfer fee calculations across all corridors
- Agent matching scoring algorithm
- Compliance rule engine (sanctions, velocity, structuring)
- Escrow state machine transitions
- Investment buy/sell accounting
- Exchange rate caching and conversion

### Integration Tests (41 tests)
Test full flows end-to-end with test database:
- Complete transfer: USA→Somalia, USA→India, USA→Mexico, USA→Philippines
- Agent lifecycle: register → stake → accept → deliver → rate
- Multi-corridor simultaneous transfers
- Compliance blocking and SAR filing
- Investment buy → hold → sell lifecycle

### Mock Services
- MockBlockchain: Simulates Stellar escrow without network calls
- MockKYCProvider: Configurable verification results
- MockExchangeRate: Realistic rates for 9 currency pairs
- MockMobileMoney: Simulates Zaad, M-Pesa, UPI, SPEI, GCash

**Total: 122 tests, all passing.**
