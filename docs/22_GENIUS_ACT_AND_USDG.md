# 22: GENIUS Act Implementation + USDG -- What Actually Changed and What It Means for Ha_Chain

**Research Date: November 19, 2026**
**Status: Research analysis, not legal advice. Verify every item against primary sources (Federal Register, OCC bulletins) and a payments lawyer before acting.**

> This doc is written in two halves:
> - **Part A-D**: human-readable analysis (what the law is now, USDG, impact on our docs/code).
> - **Part E-F**: a machine-usable rule set and agent specs, so we can turn this into Claude Code agents.

---

## TL;DR (The 8 Things That Matter)

1. **The GENIUS Act is now real law with real rules.** OCC final rule issued Oct 21, 2026 (new 12 CFR Part 15), **effective January 18, 2027**.
2. **It regulates stablecoin ISSUERS, not apps like Ha_Chain.** Our doc 07 "Path 3" is wrong: a PPSI license does **not** replace state money transmitter licenses for an intermediary. Preemption covers issuers only.
3. **Ha_Chain is almost certainly a "Digital Asset Service Provider" (DASP)** under the Act. From **July 18, 2028**, DASPs cannot offer/sell non-permitted payment stablecoins to people in the US.
4. **USDG is issued in Singapore (MAS) and the EU (MiCA), not the US.** Until Treasury declares Singapore/EU "comparable" and Paxos registers with the OCC, USDG's status for US users after July 2028 is unsettled. **No comparability determination exists yet.**
5. **Issuers must be able to freeze, block, and reject on "lawful orders."** USDC and USDG are both freezable. Our "Layer 1 cannot be regulated" claim is weaker than the docs say: the protocol can be immutable, but **the money inside it isn't**.
6. **Issuers can't pay yield. Whether intermediaries can is still unresolved.** The OCC dropped its presumption against affiliate yield arrangements but kept anti-evasion authority, so it will review them case by case. CLARITY Act (which would settle exchange rewards) **failed cloture 49-50 on Sept 15, 2026** and is stalled.
7. **AML for issuers is still in proposal stage** (FinCEN/OFAC proposed rules April & June 2026). Ha_Chain's own AML duties come from being an MSB under the BSA, which GENIUS doesn't change.
8. **Net effect:** GENIUS makes the *settlement asset* (USDC) safer and more legitimate. It does **not** make the *Ha_Chain business* easier to license in the US.

---

## PART A: THE GENIUS ACT -- CURRENT STATE OF THE LAW

### A1. Timeline

| Date | Event | Status |
|---|---|---|
| Jul 18, 2025 | GENIUS Act signed (P.L. 119-27, S.1582) | Law |
| Mar 2026 | OCC proposed rule | Superseded by final |
| Apr 3, 2026 | Treasury: broad-based principles for "substantially similar" state regimes | Proposed |
| Apr 8-10, 2026 | FinCEN + OFAC: AML/CFT + sanctions program rule for PPSIs | **Proposed** (comments closed Jun 9) |
| Jun 18, 2026 | FinCEN + OCC/Fed/FDIC/NCUA: Customer Identification Program rule | **Proposed** |
| Jun 24, 2026 | FinCEN/OFAC: AML/CFT + sanctions risk-management rule | **Proposed** |
| Aug 18, 2026 | Treasury: rules on issuance, offer, and sale of payment stablecoins (Sec. 3) | **Proposed** |
| Sep 2026 | Treasury (SCRC): interim final rule on certifying state regimes | Interim final |
| Sep 15, 2026 | CLARITY Act (market structure) fails Senate cloture 49-50 | Stalled |
| Oct 21, 2026 | **OCC final rule** (12 CFR Part 15; OCC Bulletin 2026-50) | **Final** |
| **Jan 18, 2027** | **GENIUS Act effective date / OCC rule effective** | Upcoming |
| **Jul 18, 2028** | **DASP prohibition on non-permitted stablecoins takes effect** | Upcoming |

Fed, FDIC, and NCUA have proposed rules for issuers they supervise. Status of those is unconfirmed as of this writing.

### A2. Who the Act regulates

- **Permitted Payment Stablecoin Issuers (PPSIs):** subsidiaries of insured banks, federal qualified issuers (OCC-licensed), and state qualified issuers (state regimes certified as "substantially similar"; generally for issuers under $10B).
- **Foreign payment stablecoin issuers:** allowed only if (a) Treasury determines their home regime is **comparable**, (b) they **register with the OCC**, and (c) they hold reserves at US institutions as required and can comply with US lawful orders. **Treasury has not made any comparability determination yet.**
- **Digital Asset Service Providers (DASPs):** anyone who, for compensation, exchanges, transfers, or custodies digital assets for customers. **This is where Ha_Chain lands.** DASPs are restricted in *which* stablecoins they can offer US persons (from July 2028). They don't get a license from GENIUS.

### A3. OCC final rule -- key provisions (12 CFR Part 15)

| Topic | What the final rule says | Ha_Chain relevance |
|---|---|---|
| Reserves | At least 1:1, high-quality liquid assets; monthly disclosure | Makes USDC/USDG safer to hold in escrow/LP pools |
| Redemption | Generally within **2 business days**; the proposed automatic 7-day stress extension was **removed**; >10% of a brand's supply redeemed in 24h triggers notice to OCC within 24h | Faster, more predictable off-ramp for LPs |
| Yield | Restates statutory ban on issuer paying interest/yield to holders. **Dropped** the rebuttable presumption that affiliate/third-party arrangements violate it; **no safe harbors**; anti-evasion reviewed case-by-case | Affects doc 16's "LP pools earn stablecoin yield" plan (see C4) |
| Foreign issuers | Must be under a comparable regime + OCC registration + US reserve requirements; yield ban applies too | Direct impact on USDG (Part B) |
| Preemption | OCC did not write rules; statutory preemption is self-executing and covers **issuer** licensing | Does **not** help Ha_Chain avoid state MTLs |
| Capital, custody, supervision | Detailed capital, PCA, custody, and supervision rules for issuers | Not our burden. We're not an issuer |

### A4. AML/sanctions (FinCEN + OFAC proposals)

- PPSIs would be treated as **financial institutions under the BSA** (and **no longer as MSBs**).
- Must run AML/CFT + **OFAC sanctions compliance programs**, CIP, and Travel Rule transmission.
- **"Lawful order"** is defined broadly: issuers must **freeze, block, reject, or otherwise restrict** stablecoin activity on directives from FinCEN, OFAC, law enforcement, courts, or other competent authorities. Issuers must have the **technical capability** to do this.
- **Status: proposals.** No final FinCEN rule found as of Nov 19, 2026.

**What this means for Ha_Chain:** none of this applies to us *as an issuer*. But (1) Ha_Chain still has its **own** BSA/MSB obligations (registration, AML program, SARs, CTRs, Travel Rule at $3,000), and (2) the issuer's freeze power applies to **every USDC/USDG balance in our contracts**.

### A5. The yield fight and CLARITY

- GENIUS bans **issuers** from paying yield. CRS notes it may not reach the **three-party model** (exchange pays rewards on balances held with it).
- Banks want this "loophole" closed. Crypto firms (e.g., Coinbase) say the ban only binds issuers.
- Compromise drafts in CLARITY would ban passive balance yield but allow **activity-based rewards** (transactions, loyalty).
- CLARITY **failed cloture 49-50 (Sept 15, 2026)**. A motion to reconsider keeps it technically alive. After the Nov 2026 midterms, passage this Congress is widely seen as unlikely. **Treat intermediary yield as legally unsettled.**

---

## PART B: USDG (PAXOS "GLOBAL DOLLAR")

### B1. Facts

| Item | Detail | Confidence |
|---|---|---|
| Issuer | **Paxos Digital Singapore** (MAS-regulated) and **Paxos Issuance Europe** (MiCA) | High |
| US entity | Paxos Trust Co. got **conditional** OCC approval to convert to a national trust bank (Dec 2025). The US entity issues PYUSD/USDP/PAXG, **not USDG** | Medium (final status unconfirmed) |
| Supply | ~$2.7B-$3.1B (Oct-Nov 2026); peak ~$3.4B (May 2026) | Medium (sources vary) |
| Chains | 7-8 chains incl. Ethereum, Solana, X Layer, Robinhood Chain, Mantle. **No evidence of Stellar support** | Medium |
| Network | **Global Dollar Network (GDN)**: launched Nov 2024, 150+ partners (Robinhood, Kraken, Anchorage, Galaxy, Bullish, Nuvei, OKX, ...) | High |
| Economics | Reserve income shared with **partners** (not end holders) based on minting, custody, and acceptance. Reported at ~97-100% of economics | Medium |

### B2. How GENIUS hits USDG

```
TODAY (Nov 2026)             → USDG usable globally, incl. by US platforms
JAN 18, 2027 (Act effective) → Issuer rules live; USDG's US treatment "not yet settled"
JUL 18, 2028 (DASP ban)      → US DASPs (incl. Ha_Chain) may NOT offer USDG to US persons UNLESS:
                                 (a) Treasury finds Singapore or EU regime "comparable", AND
                                 (b) Paxos registers the issuer with the OCC, AND
                                 (c) it meets US reserve + lawful-order requirements
                               OR Paxos issues a US-permitted version
```

**Open risk:** Treasury's August 2026 proposal has been criticized as effectively **foreclosing foreign-issued stablecoins in all cases** under a strict reading. If that holds, USDG is non-US-only for Ha_Chain after July 2028.

**GDN yield-sharing risk:** sharing reserve income with distribution partners is the kind of arrangement the OCC said it will examine for **anti-evasion** under the yield ban. As a foreign issuer seeking comparability, USDG would face the same ban. The GDN model may have to change for US-facing activity.

### B3. USDC vs USDG for Ha_Chain

| Factor | USDC (Circle) | USDG (Paxos) |
|---|---|---|
| US issuer status under GENIUS | US issuer; expected path to PPSI | Foreign issuer; no comparability determination yet |
| Stellar (our settlement chain) | Native | **Not found** |
| Base (our contract target) | Native | Unverified. Check before building |
| EU (MiCA) | Yes (Circle EU entity) | Yes (Paxos Issuance Europe) |
| Partner economics | Limited | **GDN reserve-income sharing** (if Ha_Chain becomes a partner) |
| Freezable on lawful order | Yes | Yes |

**Recommendation:**
- **USDC = primary settlement asset** for anything touching US persons, and for Stellar.
- **USDG = secondary, non-US legs** (EU, Singapore, Asia corridors), and worth evaluating **GDN partnership** as a revenue line *outside* the US.
- Build a **stablecoin abstraction layer** (allowlist per jurisdiction, per date), not hardcoded USDC. The code currently assumes one token per pool.

---

## PART C: WHAT THIS CHANGES IN OUR DOCS AND CODE

### C1. Claims in our docs that are now wrong or need rewriting

| Doc / location | Current claim | Reality | Severity |
|---|---|---|---|
| `07_LEGAL_STRATEGY.md` Path 3 (~L69-90) | GENIUS "created a brand new type of license that could replace 40+ state MTLs"; Ha_Chain can be a "payment stablecoin service" under one license | PPSI license is for **issuing** stablecoins. Preemption covers issuers only. A company moving stablecoins for customers is still a money transmitter in nearly every state | **Critical** |
| `07_LEGAL_STRATEGY.md` Path 3 | "Ha_Chain never 'transmits money' -- it facilitates stablecoin transfers" | FinCEN has treated transmitting convertible virtual currency for others as money transmission since 2013/2019 guidance. Stablecoins don't change that | **Critical** |
| `CLAUDE.md` Layer 2 | "US: GENIUS Act FQPSI or partner with licensed MTL" | FQPSI is not realistic or relevant (you'd have to *become an issuer*). **Partner with licensed MTL** is the actual path | High |
| `CLAUDE.md` Layer 1 | "Immutable Protocol (Cannot be regulated)" | Protocol code may be immutable, but USDC/USDG inside it are **freezable by issuers on lawful order** | High |
| `16_MATHEMATICAL_BREAKTHROUGH.md` (~L214-218, L307) | LP pools earn yield via sDAI/USDY/USDe | sDAI/USDe are not GENIUS payment stablecoins; USDY is a tokenized note (securities analysis). After Jul 2028 a US DASP can't offer non-permitted stablecoins to US persons. Yield-sharing to users is legally unsettled | High |
| `14_FUTURE_PREDICTIONS.md` L119 | "GENIUS Act implementation (Jan 2027) unlocks institutional adoption" | Date is correct (Jan 18, 2027) | OK |
| `18_B2B_LEGAL_FRAMEWORK.md` "GENIUS Act and B2B" (~L73) | Review against this doc | B2B may use payment-processor/integral-transaction exemptions, but GENIUS doesn't add a new exemption | Review |

### C2. The "immutable escrow + freezable stablecoin" problem

This is the most important technical finding:

```
contracts/Escrow.sol      → no admin, no pause, no upgrade (by design)
USDC / USDG               → issuer can BLACKLIST ANY ADDRESS on lawful order

Scenario:
  1. A sanctioned person deposits into MatchingPool via a fresh wallet
  2. OFAC / law enforcement issues a lawful order
  3. Circle blacklists... the ESCROW CONTRACT ADDRESS (the funds are there)
  4. Every user's escrowed USDC in that contract is frozen
  5. Contract has no admin → no way to segregate, refund, or comply
```

Implications:
- **Per-order escrow (or per-user vault) isolation** is safer than one pooled escrow address.
- **Pre-deposit sanctions screening at the interface layer** is required. The immutable contract can't screen, so the licensed interface must.
- The "immutable = unregulatable" framing should be replaced with "**immutable logic, compliant perimeter**."

### C3. Licensing reality for the US leg

```
OPTION                          FEASIBLE?   NOTES
Become a PPSI (issuer)          No          Bank-level capital, reserves, supervision. Not our business.
GENIUS replaces MTLs            No          Preemption = issuers only.
Own state MTLs (~49 states)     Later       $1M-$3M+, 12-24 months. NC requires license too.
Partner with licensed MTL/PPSI  YES (now)   e.g. Bridge/Stripe, BVNK, Circle partners, Zero Hash-type providers
Agent-of-payee exemption        Narrow      State-by-state; needs counsel; poor fit for P2P matching
B2B payment-processor exemption Possible    Doc 18; B2B-only flows; still BSA/OFAC
```

### C4. Yield and LP economics (doc 16 rework)

- **Don't promise yield to retail LPs or users in the US.** Treat as unsettled until CLARITY (or regulators) resolve the three-party question.
- **Activity-based rewards** (fee rebates per matched transfer) are the most defensible model in current drafts.
- **Institutional LPs** (non-US, or qualified) can hold yield-bearing instruments directly; Ha_Chain shouldn't be the one paying the yield.
- **GDN partnership (USDG)** is a potential *company* revenue line from reserve income, outside the US perimeter. Get counsel review given OCC anti-evasion language.

### C5. Code impact

| Area | File(s) | Change implied by this analysis |
|---|---|---|
| Stablecoin allowlist | new `app/services/stablecoin_registry.py` (proposed) | Per-jurisdiction, per-date allowlist (USDC for US; USDG non-US; block non-permitted for US persons from 2028-07-18) |
| Sanctions screening | `app/services/compliance_service.py` | Screen **before** deposit/escrow, both sender and recipient, both legs |
| Escrow isolation | `contracts/Escrow.sol`, `contracts/MatchingPool.sol` | Per-order vaults, and fix the partial-release bug (`MatchingPool.sol:318-322`) |
| Freeze handling | `app/services/escrow_service.py`, `stellar_service.py` | Detect blacklisted/frozen state on tokens; surface to users; ops runbook |
| Travel Rule | `app/services/transfer_service.py` | Originator/beneficiary info for transfers >= $3,000 |
| Remittance disclosures (B2C US) | mobile `QuoteScreen.tsx`, `ConfirmScreen.tsx` | CFPB Remittance Rule (Reg E Subpart B): prepayment disclosure, receipt, 30-min cancellation, error resolution |
| Config | `app/config.py` | Default `JWT_SECRET` should fail closed in production |

---

## PART D: STRATEGIC READ

**What GENIUS gives Ha_Chain:**
- A **legitimate, supervised settlement asset** (USDC) with 2-business-day redemption and 1:1 reserves. That's better LP collateral and easier to explain to banks and B2B clients.
- A **clear rulebook** for partners (Circle, Bridge, BVNK) that we can build on top of.
- Tailwind for **B2B stablecoin adoption** (doc 17), which is our reverse-flow source.

**What GENIUS takes away:**
- The idea that a single federal license avoids state MTLs.
- The idea that the money layer is ungovernable.
- Easy access to foreign stablecoins (USDG) for US users after mid-2028.
- Easy yield marketing.

**Recommended US posture (2027-2028):**
1. **Partner, don't license.** US leg runs through a licensed MTL/stablecoin partner. Ha_Chain = technology + matching/netting engine.
2. **USDC-first, multi-stablecoin abstraction** in code.
3. **Compliance perimeter at the interface**: KYC, OFAC screening, Travel Rule, and Reg E disclosures before anything touches a contract.
4. **USDG + GDN** evaluated for EU/Singapore corridors only.
5. **Watch list** (Part F, Agent 3): FinCEN final AML rule, Treasury Sec. 3 final rule, first foreign comparability determination, CLARITY revival, OCC actions on yield arrangements.

---

## PART E: MACHINE-USABLE RULE SET

Each rule has an ID so agents and code reviews can cite it. `Effective` is when it bites. `Source` points to Part A/B.

| ID | Rule | Applies to | Effective | Check | Source |
|---|---|---|---|---|---|
| G-01 | Ha_Chain is a DASP/MSB, not a PPSI. Never claim a GENIUS license replaces MTLs | Docs, pitch, legal | Now | Flag text claiming FQPSI/PPSI/GENIUS "replaces" state MTLs | A2, A3 |
| G-02 | US-person flows must use a licensed MTL/stablecoin partner (or own licenses) | Architecture, onboarding | Now | Any US fiat on/off-ramp code path must route via a partner adapter | C3 |
| G-03 | Only **permitted** payment stablecoins may be offered to US persons | Stablecoin registry, UI | **2028-07-18** | Token allowlist keyed by user jurisdiction + date | A2, B2 |
| G-04 | USDG is foreign-issued; treat as non-US unless comparability + OCC registration confirmed | Registry | Now → 2028 | USDG disabled for `jurisdiction == US` after 2028-07-18 unless flag `usdg_us_permitted` | B2 |
| G-05 | Assume any stablecoin balance can be frozen on lawful order | Contracts, ops | Now | Escrow must not pool all users behind one address; frozen-state handling exists | A4, C2 |
| G-06 | Sanctions screening must happen **before** funds enter an immutable contract | Interface, compliance service | Now | Deposit/escrow endpoints call screening for sender + recipient on both legs | A4, C2 |
| G-07 | No issuer-style yield promised to US users/LPs; rewards must be activity-based | Docs, LP product, UI copy | Now (unsettled) | Flag "APY", "yield", "interest" in US-facing copy or LP marketing | A3, A5, C4 |
| G-08 | Don't hold or offer sDAI/USDe/USDY as "stablecoins" to US persons | LP pools | 2028-07-18 (sooner for securities issues) | Pool token list review | C1, C4 |
| G-09 | Travel Rule: originator/beneficiary data for transfers >= $3,000 | Transfer service | Now | Field presence + transmission to counterparty VASP/partner | A4, C5 |
| G-10 | B2C US remittances need CFPB Reg E Subpart B disclosures, 30-min cancel, error resolution | Mobile app, transfer service | Now | Quote/confirm/receipt screens show required fields | C5 |
| G-11 | Redemption assumptions: issuer redemption ~2 business days; no auto 7-day stress extension | LP liquidity model | 2027-01-18 | LP stress model uses T+2 off-ramp | A3 |
| G-12 | Rule-status awareness: FinCEN AML, CIP, Treasury Sec. 3 are **proposals**; re-check before relying | All | Ongoing | Agent 3 watch list | A1 |

---

## PART F: AGENT SPECS (to build next)

These are designs, not created yet. Each maps to rules in Part E.

### Agent 1: `compliance-reviewer`
- **Purpose:** Review code diffs and PRs against G-02, G-03, G-05, G-06, G-09, G-10.
- **Inputs:** git diff, `app/services/*`, `contracts/*.sol`, mobile screens.
- **Output:** findings with rule ID, file:line, severity, suggested fix.
- **Tools:** Read, Grep, Bash (git diff). No write.
- **Trigger:** before merging anything under `app/services/`, `contracts/`, `mobile/src/screens/send/`.

### Agent 2: `doc-claims-auditor`
- **Purpose:** Scan `docs/*.md`, `CLAUDE.md`, pitch materials for claims that contradict this doc (G-01, G-07, G-08, the "cannot be regulated" framing).
- **Output:** table of claim → why it's wrong → corrected wording, with doc and line.
- **Tools:** Read, Grep. Edits only with approval.
- **Seed list:** Part C1.

### Agent 3: `regulatory-watch`
- **Purpose:** Periodically check for status changes on the watch list and update Part A1 of this doc.
- **Watch list:**
  1. FinCEN/OFAC PPSI AML + sanctions rules: final?
  2. FinCEN CIP rule: final?
  3. Treasury Sec. 3 issuance/offer/sale rule: final? Foreign-issuer reading?
  4. Treasury comparability determinations (Singapore? EU?)
  5. Paxos: OCC registration of USDG issuer / US-issued USDG?
  6. CLARITY Act revival / yield compromise
  7. Fed/FDIC/NCUA final GENIUS rules
  8. OCC enforcement/guidance on yield arrangements
- **Tools:** WebSearch, web-fetch, Edit (this doc only).
- **Cadence:** monthly (via `/schedule`), plus ad-hoc.

### Agent 4: `stablecoin-selector`
- **Purpose:** For a given corridor + user jurisdiction + date, return the allowed settlement tokens and chain, with reasoning (G-03, G-04, G-08).
- **Becomes code:** the logic should end up in `stablecoin_registry.py`, with the agent used to keep the table current.

### (Product, not Claude Code) Sanctions/lawful-order service
- A backend service implementing G-05/G-06/G-09 at runtime: OFAC/UN/EU screening, freeze-state detection on tokens, case management. This belongs in `app/services/compliance_service.py`, not an AI agent.

---

## SOURCES

### GENIUS Act and implementing rules
- [S.1582 GENIUS Act - Congress.gov](https://www.congress.gov/bill/119th-congress/senate-bill/1582) / [Text](https://www.congress.gov/bill/119th-congress/senate-bill/1582/text)
- [CRS R49351: GENIUS Act (P.L. 119-27)](https://www.congress.gov/crs_external_products/R/PDF/R49351/R49351.2.pdf)
- [OCC Bulletin 2026-50: GENIUS Act Final Rule](https://www.occ.treas.gov/news-issuances/bulletins/2026/bulletin-2026-50.html)
- [OCC Bulletin 2026-3: Proposed Rule](https://www.occ.treas.gov/news-issuances/bulletins/2026/bulletin-2026-3.html)
- [Mayer Brown: OCC Finalizes GENIUS Act Rulemaking](https://www.mayerbrown.com/en/insights/publications/2026/11/occ-finalizes-genius-act-rulemaking)
- [Gibson Dunn: OCC Finalizes Its Payment Stablecoin Framework](https://www.gibsondunn.com/the-genius-act-occ-finalizes-its-payment-stablecoin-framework/)
- [Arnold & Porter: OCC's Final Rule](https://www.arnoldporter.com/en/perspectives/advisories/2026/10/implementing-the-genius-act-the-occs-final-rule)
- [Sidley: OCC Finalizes Regulatory Framework](https://www.sidley.com/en/insights/newsupdates/2026/10/occ-finalizes-regulatory-framework-for-payment-stablecoins-under-genius-act)
- [Davis Wright Tremaine: Impact of OCC Final Rule](https://www.dwt.com/blogs/financial-services-law-advisor/2026/11/occ-final-rule-genius-act-stablecoin-issuers)
- [Consumer Finance Monitor: OCC Final GENIUS Rule](https://www.consumerfinancemonitor.com/2026/11/18/occ-issues-final-genius-act-rule-establishing-a-federal-framework-for-payment-stablecoin-issuers/)
- [Stablecoin Insider: Yield, Reserves and Redemptions](https://stablecoininsider.org/occ-genius-act-final-rule/)
- [Federal Register: Treasury Sec. 3 Issuance, Offer, Sale (Aug 18, 2026)](https://www.federalregister.gov/documents/2026/08/18/2026-16796/genius-act-regulations-on-payment-stablecoin-issuance-offer-and-sale)
- [Sullivan & Cromwell: Treasury Proposes Rules Clarifying Prohibitions](https://www.sullcrom.com/insights/memo/2026/August/Treasury-Department-Proposes-Rules-Clarifying-GENIUS-Act-Prohibitions)
- [KPMG: Treasury Proposal for Issuance, Offer, and Sale](https://kpmg.com/us/en/articles/2026/genius-act-treasury-proposal-payment-stablecoins-reg-alert.html)
- [Federal Register: State Regime Broad-Based Principles (Apr 3, 2026)](https://www.federalregister.gov/documents/2026/04/03/2026-06489/genius-act-broad-based-principles-for-determining-whether-a-state-level-regulatory-regime-is)

### AML / sanctions
- [Federal Register: PPSI AML/CFT + Sanctions Program (Apr 10, 2026)](https://www.federalregister.gov/documents/2026/04/10/2026-06963/permitted-payment-stablecoin-issuer-anti-money-launderingcountering-the-financing-of-terrorism)
- [Federal Register: PPSI AML/CFT + Sanctions Risk Management (Jun 24, 2026)](https://www.federalregister.gov/documents/2026/06/24/2026-12692/permitted-payment-stablecoin-issuer-anti-money-launderingcountering-the-financing-of-terrorism-and)
- [FinCEN: CIP Proposed Rule](https://www.fincen.gov/news/news-releases/fincen-agencies-propose-rule-implement-genius-act-customer-identification)
- [Holland & Knight: FinCEN and OFAC Propose Rules](https://www.hklaw.com/en/insights/publications/2026/04/fincen-and-ofac-propose-aml-sanctions-rules-for-stablecoin-issuers)
- [Alston & Bird: Proposed AML/CFT/Sanctions Rules](https://www.alston.com/en/insights/publications/2026/07/proposed-aml-cft-sanctions-rules-genius-act)
- [ABA Business Law Today: From Money Transmitters to PPSIs](https://www.americanbar.org/groups/business_law/resources/business-law-today/2026-june/treasurys-proposed-stablecoin-compliance-framework/)

### State licensing / MTLs
- [Bitcoin.com: Do You Still Need MTLs After GENIUS?](https://news.bitcoin.com/regulation-and-legal/stablecoins-after-the-genius-act-part-3-do-you-still-need-money-transmitter-licenses/)
- [Regulatory Counsel: Unlicensed Money Transmission](https://regulatory-counsel.com/insights/unlicensed-money-transmission-crypto-state-licences)

### Yield / CLARITY
- [CRS IF13174: The Stablecoin Yield Debate](https://www.everycrsreport.com/reports/IF13174.html)
- [DLA Piper: Senate Fails to Advance CLARITY](https://www.dlapiper.com/en/insights/publications/2026/09/senate-fails-to-advance-the-clarity-act)
- [Orrick: CLARITY Act Stalls](https://www.orrick.com/en/Insights/2026/10/The-CLARITY-Act-Stalls-in-the-Senate-Whats-Next-for-Digital-Asset-Regulation)
- [American Banker: Banks Push Back on Stablecoin Yield](https://www.americanbanker.com/news/banks-consumer-groups-push-back-against-stablecoin-yield)

### USDG / Paxos
- [Global Dollar: About USDG](https://globaldollar.com/about-usdg)
- [Paxos (company) - Wikipedia](https://en.wikipedia.org/wiki/Paxos_(company))
- [DefiLlama: Global Dollar](https://defillama.com/stablecoin/global-dollar)
- [Crypto Briefing: USDG hits $3.2B](https://cryptobriefing.com/paxos-usdg-market-cap-3-billion/)
- [The Block: GDN New Members, Solana](https://www.theblock.co/post/353947/global-dollar-network-new-members-solana-usdg-stablecoin)
- [The Block: OKX Joins GDN](https://www.theblock.co/post/362514/okx-global-dollar-network-paxos-usdg-stablecoin)
- [Crowdfund Insider: GDN 100+ Partners, USDG $1B](https://www.crowdfundinsider.com/2025/12/256468-global-dollar-network-grows-to-100-partners-and-usdg-stablecoin-tops-1b-in-market-cap/)
- [Stablecoin Insider: What Is USDG](https://stablecoininsider.org/usdg-stablecoin/)

*Lower-confidence items (aggregator/AI-generated pages) were used only where noted as "Medium" confidence and should be re-verified.*
