# 17: B2B Onboarding Strategy -- Who to Target, How to Capture Reverse Flows

## The Companies That Make 70-85% Netting Possible

**Research Date: March 26, 2026**

---

## THE B2B STABLECOIN MARKET IS EXPLODING

```
B2B stablecoin payment growth:      733% year-over-year
B2B share of stablecoin payments:   60% (~$226B in 2025)
Monthly B2B stablecoin volume:      $6B+ (up from <$100M in early 2023)
Total B2B cross-border market:      $194 TRILLION (2024)

Key moves (March 2026):
  Mastercard acquired BVNK:         $1.8B  (stablecoin B2B infrastructure)
  Stripe Tempo blockchain launched:  $500M  (March 18, 2026)
  Visa stablecoin settlement:        $4.5B  annualized run rate
  Circle CPN live:                   25+ institutional partners
```

---

## HOW B2B CROSS-BORDER PAYMENTS WORK TODAY

### The Pain (What Ha_Chain Replaces)

An Indian IT company receiving $50K from a US client:

```
US client → US bank ($25-50 wire fee)
  → Correspondent bank 1 ($10-100 "lifting fee")
  → Correspondent bank 2 ($10-100 "lifting fee")
  → Indian bank (0.5-2% FX spread)
  → IT company receives INR

Total cost: 1.5-3% ($750-$1,500 on $50K)
Settlement: 2-5 business days
Compliance: FIRC certificate, FEMA purpose codes, EDPMS reporting
Visibility: None until money arrives
```

**59% of corporate clients cite slow processing as key pain point** (Citibank survey). "Like shipping a package without tracking."

### The Fix (Ha_Chain B2B)

```
US client pays into Ha_Chain (domestic ACH, same-day)
  → Ha_Chain's netting solver matches against remittance senders
  → IT company receives INR via UPI/NEFT (instant)

Total cost: 0.1-0.5% ($50-$250 on $50K)
Settlement: minutes
Compliance: Auto-generated FIRC, auto-tagged purpose codes
Visibility: Real-time tracking
```

**Savings: 70-90% on fees. 95%+ faster settlement.**

---

## MAJOR B2B PLATFORMS (Competitive Landscape)

| Company | Revenue/Volume | Blockchain? | Corridors | Fees |
|---|---|---|---|---|
| **Airwallex** | $1B ARR, $130B+ TPV | No | Global, strong APAC | Interbank FX, no markup |
| **Payoneer** | $1.05B revenue | No | India, PH, Pakistan, LatAm | Up to 2% FX markup |
| **Wise Business** | $185B cross-border vol | No | Global, 22+ currencies | Mid-market + transparent |
| **Nium** | Undisclosed | Yes (Visa pilot) | Global, SE Asia | API pricing |
| **Thunes** | Undisclosed | Yes (Yellow Card) | Africa, SE Asia, LatAm | Infrastructure pricing |
| **BVNK** | $30B+ processed | Yes (core) | 130+ countries | Stablecoin rail fees |
| **Stripe/Bridge** | Dominant | Yes (Tempo) | 101 countries | Often < $1 flat |
| **Circle CPN** | Growing | Yes (core) | Global via members | Network fees |
| **Deel** | Undisclosed | Crypto payroll option | 150+ countries | $49/contractor/mo |
| **Papaya Global** | Undisclosed | Yes (stablecoin payroll) | 160+ countries | $3/payment |

**NONE do multilateral netting. ALL route point-to-point. Ha_Chain's netting solver remains unique.**

---

## SPECIFIC COMPANIES TO TARGET (By Corridor)

### Tier 1: Indian IT SMEs (IMMEDIATE -- Highest Impact)

**Why:** 10,000+ companies billing US clients $200K-$5M/year. They CREATE the reverse flow (India→USA) that makes remittance matching possible.

**Pain points:**
- Paying 1.5-3% in SWIFT fees ($30K-$60K/year wasted)
- FEMA compliance is massive burden (FIRC, purpose codes, EDPMS)
- 2-5 day settlement kills cash flow
- Current alternatives: Skydo, Xflow, Payoneer (all charge more than Ha_Chain)

**Killer features for them:**
- Automatic FIRC generation (huge pain point solved)
- 70-90% fee savings
- Minutes instead of days
- API integration (they're tech companies -- they can self-integrate)

**Go-to-market:**
1. Free trial: "First $10,000 at zero fee"
2. API docs and SDKs (self-service for tech companies)
3. Content: "How Indian IT companies save 70% on cross-border payments"
4. Partner with India's NASSCOM or STPI for distribution

**Target list:**
- Tier 3 (immediate): SMEs billing $200K-$5M/year (10,000+ companies)
- Tier 2 (medium-term): Mphasis, LTIMindtree, Zensar, Hexaware ($500M-$5B revenue)
- Tier 1 (aspirational): TCS, Infosys, Wipro, HCLTech (use negotiated bank rates)

### Tier 2: Philippine BPO Mid-Market

**Why:** $28B in BPO exports to USA. Creates massive reverse flow against $38B remittance.

**Target:**
- Mid-market agencies ($10M-$100M revenue): SuperStaff, Unity Connect, NeoWork
- VA agencies and freelancer collectives (thousands)
- Currently using Payoneer at 2% FX markup

**Value prop:** "Save vs Payoneer's 2%. Get mid-market rates. GCash/Maya payout."

### Tier 3: Mexican Manufacturers (Nearshoring Wave)

**Why:** $935B bilateral trade, nearly perfectly balanced. Ideal for netting.

**Target:**
- 6,500 IMMEX-registered maquiladora companies
- Electronics manufacturing ($53.2B, growing to $97.4B by 2031)
- Auto parts, aerospace components

### Tier 4: Nigerian Importers

**Why:** $15.5B+ imports from China annually. Lose up to 20% in FX/bank fees.

**Target:**
- Consumer electronics importers
- Textile importers
- Already using informal channels (stablecoins, hawala)

### Tier 5: Somaliland Import Businesses

**Why:** Import economy creates the REVERSE FLOW against diaspora remittance.

**How it works:**
```
Somaliland businessman imports goods from Dubai → needs to send USD/AED to Dubai
Somali diaspora in UAE → needs to send money to Somaliland

These net PERFECTLY. The import payment IS the reverse flow.
```

Currently using Dahabshiil (hawala) for international payments. Ha_Chain formalizes this.

---

## WHAT HA_CHAIN MUST BUILD FOR B2B (MVP)

### Business API (4-8 weeks development)

1. **Business account type** with KYB verification
2. **Invoice API** -- create, track, settle invoices programmatically
3. **Batch payment endpoint** -- multiple payments in one API call
4. **Webhook/callback system** -- notify business systems on settlement
5. **Compliance documentation export** -- auto-FIRC for India, tax receipts
6. **Reconciliation dashboard** -- web UI for finance teams
7. **Rate locking** -- lock FX rate for 15-60 minutes
8. **Recurring payments** -- scheduled transfers for regular billing

### KYB Onboarding (Partner with Sumsub/Onfido)

- Company registration verification
- UBO (Ultimate Beneficial Owner) identification (25%+ ownership)
- Director/officer KYC screening
- Sanctions and PEP screening
- Business activity verification
- Source of funds documentation
- Cost: $5-15 per business verification

---

## REVENUE MODEL FOR B2B

| Service | Pricing | Rationale |
|---|---|---|
| Business API access | $49.99/month | Infrastructure cost coverage |
| Transaction fee (matched) | 0.1-0.3% | Much cheaper than 1.5% SWIFT |
| Transaction fee (LP pool) | 0.3-0.5% | Still cheaper than alternatives |
| FX conversion | Mid-market + 0.1% | Transparent |
| Rate lock premium | 0.05% | Optional convenience |
| Batch processing | $0.50/payment | Volume discount |
| Priority settlement (<5 min) | +0.05% | Premium speed |

**Critical insight:** B2B pricing should attract MAXIMUM VOLUME, not maximize per-transaction revenue. Every B2B reverse flow captured enables better matching for remittance, reducing LP costs network-wide. A B2B payment that creates reverse flow is worth more to the network than its fee.

---

## THE REVENUE MATH (Year 3 Projections)

| Flow Type | Monthly Volume | Match Rate | Monthly Revenue |
|---|---|---|---|
| B2C Remittance | $500M | 60% matched | ~$2M |
| B2B IT/BPO Services | $100M | 70% matched | ~$260K |
| B2B Trade Payments | $50M | 50% matched | ~$200K |
| LP Pool Provision | $250M unmatched | -- | ~$250K |
| Business API Subscriptions | 500 businesses | -- | ~$25K |
| **Total** | **$650M** | | **~$2.7M/month = $33M/year** |

B2B revenue alone is modest (~$6M/year). But B2B flows increase remittance matching from ~15% to ~60%, reducing LP capital requirements by ~75%.

---

## STRATEGIC POSITIONING

Ha_Chain should be **built ON TOP of** existing stablecoin infrastructure:
- Use **Stripe/Bridge** for fiat↔stablecoin conversion
- Use **Circle CPN** or **Stellar** for inter-institution settlement
- Use **Thunes/Yellow Card** for emerging market payouts
- **Ha_Chain's unique value = the netting solver** that sits on top of commodity rails

```
EXISTING RAILS (commodity):     Stripe, Circle, Stellar, SWIFT
                                    ↑
HA_CHAIN'S UNIQUE LAYER:        Multilateral netting solver
                                    ↑
VALUE CREATED:                  60-80% of flows net out
                                (vs 0% on existing rails)
```

---

## PHASED B2B ROLLOUT

### Phase 1 (Immediate): B2C Remittance Only
- LP pools handle everything. Business works at 0% match rate.
- Launch in Somaliland (zero competition)

### Phase 2 (3-6 months): B2B Business API + Indian IT SMEs
- Onboard 50-100 Indian IT companies
- Automatic FIRC generation (killer feature)
- These create reverse flows → remittance match rate jumps to 40-60%

### Phase 3 (6-12 months): Philippine BPO + Mexican Trade
- 20-50 Philippine BPO agencies
- Mexican manufacturer payments
- Multilateral netting across all corridors activated

### Phase 4 (12-18 months): Full B2B Trade Invoicing
- Open account trade settlement
- Partner with trade finance platforms
- Target: 60-80% netting efficiency across 20+ corridors

---

## SOURCES

### B2B Payment Platforms
- [Airwallex $1B ARR - Sacra](https://sacra.com/c/airwallex/)
- [B2B Payments Market - Fortune Business Insights](https://www.fortunebusinessinsights.com/b2b-payments-market-108853)
- [Cross-Border B2B Market - Global Growth Insights](https://www.globalgrowthinsights.com/market-reports/cross-border-b2b-payments-market-123059)
- [Mastercard Acquires BVNK $1.8B](https://www.mastercard.com/us/en/news-and-trends/press/2026/march/Mastercard-to-acquire-BVNK.html)

### Stablecoin B2B
- [B2B Stablecoin 733% Growth - FXC Intelligence](https://www.fxcintel.com/research/reports/ct-b2b-payments-2025-roundup)
- [Stripe Tempo Mainnet - CoinDesk](https://www.coindesk.com/tech/2026/03/18/stripe-led-payments-blockchain-tempo/)
- [Circle CPN Whitepaper (PDF)](https://6778953.fs1.hubspotusercontent-na1.net/hubfs/6778953/PDFs/Whitepapers/CPN_Whitepaper.pdf)
- [How B2B Stablecoin Payments Work - Stripe](https://stripe.com/resources/more/b2b-stablecoin-payments)

### India IT Services
- [India IT Industry - IBEF](https://www.ibef.org/industry/information-technology-india)
- [India IT Export Market - Mordor Intelligence](https://www.mordorintelligence.com/industry-reports/india-software-services-export-industry-market)
- [India PA-CB Framework - The Week](https://www.theweek.in/theweek/business/2026/03/21/pa-cb-framework-explained.html)
- [International Payments for IT Exporters - Xflow](https://www.xflowpay.com/blog/international-payments-for-it-ites)

### Philippines BPO
- [Philippine BPO Outlook 2025 - Creathink](https://creathink-solutions.com/articles/philippine-bpo-industry-2025/)
- [Philippines Outsourcing Report - MicroSourcing](https://www.microsourcing.com/2025-philippines-outsourcing-trend-report)

### Mexico Trade
- [Mexico Nearshoring 2026 - EAW Logistics](https://www.eawlogistics.com/mexico-in-focus-trade-nearshoring-and-the-2026-outlook/)
- [Mexico 81% Exports to US - Supply Chain Intelligence](https://news.yrules.com/en/archives/6562)

### KYB
- [KYB Guide 2026 - Sumsub](https://sumsub.com/blog/kyb-guide/)
- [AML KYC KYB in Cross-Border - Yogupay](https://yogupay.com/aml-kyc-kyc-navigating/)
