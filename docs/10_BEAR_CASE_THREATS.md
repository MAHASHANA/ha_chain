# 10: Bear Case -- 12 Threats That Could Break the Dollar Stablecoin Thesis

## Stress-Testing Ha_Chain's Foundational Assumptions

**Research Date: March 25, 2026**

---

## THREAT RANKING SUMMARY

| # | Threat | Probability (5yr) | Impact | Net Risk |
|---|--------|-------------------|--------|----------|
| 3 | Tether collapse | Low (10-15%) | Catastrophic | **HIGH** |
| 9 | Countries ban stablecoins (capital controls) | High (60-80% for some corridors) | High for affected corridors | **HIGH** |
| 5 | US weaponizes stablecoins too aggressively | Medium (30-40%) | High (trust erosion) | **HIGH** |
| 8 | Interest rates hit zero (stablecoin model breaks) | Low (10-15%) | High (settlement layer risk) | **MODERATE** |
| 7 | Major stablecoin hack/exploit | Medium (30-40%) | Medium (temporary chaos) | **MODERATE** |
| 2 | EU/other blocs favor local stablecoins | Medium (40-50%) | Low-Medium | **MODERATE** |
| 1 | China forces digital yuan, BRICS follows | Low (15-20% for BRICS-wide) | Medium | **MODERATE** |
| 4 | BRICS gold-backed "Unit" succeeds | Low (5-10%) | Medium | **LOW** |
| 10 | CBDCs win (50+ country interop) | Very Low (5%) | High | **LOW** |
| 11 | BRICS payment systems fully converge | Very Low (5%) | High | **LOW** |
| 12 | Dollar loses reserve status | Near Zero (1%) in 5yr | Catastrophic | **NEGLIGIBLE** |
| 6 | Quantum computing breaks encryption | Near Zero (<1%) in 5yr | Catastrophic | **NEGLIGIBLE** |

---

## 1. CHINA BANS STABLECOINS AND FORCES DIGITAL YUAN -- COULD BRICS FOLLOW?

**What has actually happened:**
- China explicitly banned all stablecoins in 2025, including yuan-pegged stablecoins and RWA tokenization. This is not hypothetical -- it is done.
- The digital yuan (e-CNY) became interest-bearing on January 1, 2026, reclassified from "digital cash" to "digital deposit money" at 0.05% annual interest -- the first CBDC in the world to pay interest.
- 225 million personal digital wallets exist across 17 provinces. Cumulative transactions: 3.48 billion for 16.7 trillion yuan ($2.38 trillion).

**Why this is LESS threatening than it appears:**
- Despite all this, e-CNY represents only **0.2% of total Chinese electronic payments**. Alipay and WeChat Pay dominate so thoroughly that even the state cannot displace them.
- Martin Chorzempa at PIIE concludes that China has essentially "given up on state-backed digital cash" as a domestic replacement, shifting focus to international use cases. Consumers refuse to switch from existing apps.
- The interest-bearing pivot is an admission of failure -- they had to bribe people to use it.

**Could BRICS follow China's ban?**
- India: Has not banned stablecoins despite aggressive crypto taxation (30% + 1% TDS). India's digital rupee pilot has even less traction than e-CNY. RBI is cautious but not prohibitionist.
- Russia: Has restricted crypto domestically but actively uses stablecoins for sanctions evasion. Banning them would hurt Russia more than anyone.
- Brazil, UAE, South Africa: All moving toward regulation, not bans. UAE is actively courting crypto companies.

**Threat level: MODERATE for China corridor, LOW for BRICS-wide ban.**

The China corridor was always the hardest. This confirms Ha_Chain should deprioritize it. But a BRICS-wide stablecoin ban is extremely unlikely because most BRICS members benefit from stablecoin access.

---

## 2. EU OR OTHER BLOCS CREATE COMPETING FRAMEWORKS FAVORING LOCAL CURRENCIES

**What has actually happened:**
- MiCA is fully in force. USDT has been delisted across major EU exchanges (Coinbase delisted Dec 2024, Crypto.com by Jan 2025) for non-compliance.
- USDC is the only top-10 stablecoin that is MiCA-compliant. Circle's EURC (euro stablecoin) is also compliant.
- In September 2025, nine major European banks (ING, UniCredit, CaixaBank, Danske Bank, DekaBank, Banca Sella, KBC, SEB, Raiffeisen) formed a consortium to launch a euro stablecoin. Planned launch: H2 2026.

**Why this IS a real threat:**
- If EUR-denominated stablecoins gain traction, European remittance corridors might shift to EUR settlement.
- MiCA could become a template for other regions, each pushing their own currency.
- Singapore developing SGD stablecoins. Brazil authorized BRL-denominated stablecoins. Japan's framework favors JPY stablecoins.

**Why this is LESS threatening than it appears:**
- USD stablecoins currently command **99% market share**. EUR stablecoins have negligible adoption.
- Oxford Law described the European consortium's 2026 launch as "terribly belated."
- Dollar dominance in trade invoicing (especially commodities) means structural demand for USD stablecoins.
- 20% of Nigerians report stablecoins account for more than half their portfolio -- they choose USDT/USDC, not EUR coins.

**Threat level: LOW for next 3-5 years, MODERATE for 5-10 year horizon.**

**Ha_Chain advantage:** A multi-stablecoin world is exactly what a matching protocol is built for. More stablecoins = more matching opportunities. The protocol is currency-agnostic.

---

## 3. TETHER COLLAPSES

**Current state:**
- Market cap: ~$184 billion. Largest stablecoin by far.
- Just hired a Big Four accounting firm for its **first-ever full audit** (announced March 24, 2026 -- literally yesterday).
- S&P Global downgraded USDT to its weakest score, citing Bitcoin exposure (5.6% of reserves) and disclosure gaps.
- $135 billion in US Treasuries (17th largest holder globally).
- $3.3 billion in USDT frozen across 7,268 blacklisted addresses.
- Under DOJ and CFTC investigations.
- Delisted across EU exchanges for MiCA non-compliance.

**What a collapse would look like:**
- Bank run: redemptions exceed liquid reserves. Tether cannot honor 1:1 peg.
- $184B in value needs somewhere to go. Panic conversion to USDC, DAI, or fiat.
- Every DeFi protocol, exchange, remittance service using USDT gets hit.
- Massive crypto contagion. Likely 50-80% crash in BTC, ETH, all tokens within 48 hours.
- Emerging market users holding USDT as savings lose everything.

**Why this is a REAL threat:**
- Tether has never had a full audit until now. The fact they're getting one is both positive and concerning.
- 5.6% Bitcoin exposure means a Bitcoin crash directly threatens the peg.
- DOJ/CFTC investigations not resolved.
- Corporate structure (BVI registered, Hong Kong operated) is deliberately opaque.

**Why this is LESS likely than feared:**
- $135B in US Treasuries is the most liquid asset class on earth. Even in crisis, Tether can sell T-bills within hours.
- Tether survived 2022 crypto winter, UST/Luna collapse, FTX collapse, and multiple bank failures without breaking peg.
- US government has perverse incentive to keep Tether alive -- top-20 holder of US debt. Collapse means forced liquidation of $135B in Treasuries.
- Big Four audit, if clean, removes the largest uncertainty.

**Threat level: LOW probability, CATASTROPHIC impact. Classic tail risk.**

**Ha_Chain mitigation (CRITICAL):**
1. Multi-stablecoin support from day one. USDC should be primary, not USDT.
2. Escrow contracts should support rapid stablecoin swaps.
3. Consider DAI/USDS as decentralized backup.
4. Never hold large treasury balances in USDT.

---

## 4. BRICS GOLD-BACKED DIGITAL CURRENCY ("THE UNIT") SUCCEEDS

**Current state:**
- Pilot launched October 31, 2025, prototype December 8, 2025.
- Structure: 40% gold + 60% BRICS-currency basket (12% each for Real, Yuan, Rupee, Ruble, Rand).
- Daily value adjustment based on gold price and currency basket.
- 2026-2027 is the "infrastructure development" phase.

**Why this IS a real threat:**
- Gold has no counterparty risk. Cannot be sanctioned like stablecoin wallets.
- For countries under/fearing US sanctions, a gold-backed settlement unit is genuinely attractive.
- If oil trades shift to The Unit, petrodollar recycling weakens.
- BRICS+ now represents 45% of world population and ~37% of global GDP.

**Why this is LESS threatening than it appears:**
- Still in pilot with no timeline for production deployment.
- The 60% basket of BRICS currencies is problematic: ruble (volatile/sanctions), rand (volatile/structural), real (volatile/EM).
- Gold-backed settlement requires physical gold custody. Who holds it? Where? Trust problems between BRICS members make governance extremely difficult.
- Fisher Investments argues The Unit is "easily squashed" because it solves a problem that doesn't exist -- BRICS countries can already trade bilaterally in their own currencies.
- BIS exited mBridge in 2024 due to sanctions-evasion concerns.

**Threat level: LOW for next 5 years, UNCERTAIN beyond.**

**Ha_Chain advantage:** If The Unit succeeds, Ha_Chain's "bridge between SWIFT and BRICS" positioning becomes MORE valuable. Building support for gold-backed settlement tokens would be forward-looking.

---

## 5. US WEAPONIZES STABLECOINS TOO AGGRESSIVELY

**What has happened:**
- Tether has frozen $3.3B across 7,268 addresses. Circle has frozen $109M across 372 addresses. 30x gap in enforcement intensity.
- FATF's March 2026 report: stablecoins are the most widely used virtual asset in illicit transactions.
- GENIUS Act mandates OFAC screening, BSA compliance, suspicious activity reporting.
- "Contagion risk" is real: even innocent wallets receiving funds from a blacklisted chain can get flagged and frozen.

**Why this IS a serious threat:**

The trust erosion feedback loop:
1. US freezes wallets for sanctions enforcement.
2. People in ambiguous jurisdictions fear their wallets could be next.
3. Demand shifts to alternatives (gold, local stablecoins, privacy coins).
4. USD stablecoin market share slowly erodes.
5. US responds more aggressively to maintain control.
6. More people flee. Cycle continues.

The core contradiction: the dollar's value as a stablecoin comes from trust, but aggressive weaponization destroys trust.

**Counterargument:**
- People in emerging markets WANT USD exposure despite the risk. The alternative (holding naira, lira, peso) is worse than risk of wallet freeze.
- Most freezes target confirmed criminal activity. False-positive rate is low.
- As long as US doesn't freeze for political reasons (only criminal/sanctions), trust holds.

**Threat level: MODERATE and GROWING. Most underappreciated risk.**

**Ha_Chain advantage:** Money never crosses borders in matched transactions -- less reason for US enforcement to target Ha_Chain transactions. But escrow contracts using freezable USDC/USDT are a vulnerability. Consider fallback mechanisms for frozen funds.

---

## 6. QUANTUM COMPUTING BREAKS BLOCKCHAIN ENCRYPTION

**Current state:**
- Today's quantum computers are "noisy" with high error rates and far fewer logical qubits than needed.
- Breaking ECDSA requires approximately 2,500-4,000 error-corrected logical qubits. Current machines have dozens of noisy physical qubits.
- Vitalik Buterin unveiled Ethereum roadmap for post-quantum resistance (February 2026).
- ARK Invest (March 2026): quantum computing is a "long-term risk, not imminent threat."
- A quantum attack would break ALL public-key cryptography simultaneously -- banking, military, government, everything. Civilization-level event.

**Threat level: NEGLIGIBLE for next 5 years. UNKNOWN for 10-15 year horizon.**

**Ha_Chain implication:** Not a near-term concern. Build on chains moving toward post-quantum resistance (Ethereum, Stellar have signaled this). If Ha_Chain is alive in 10 years, migrate with the ecosystem.

---

## 7. MAJOR STABLECOIN HACK/EXPLOIT DESTROYS CONFIDENCE

**Recent events:**
- Resolv's USR stablecoin exploited March 22, 2026 (three days ago). Attacker minted 50 million USR by depositing only $100,000 USDC. Token crashed 74%.
- $137 million stolen across DeFi in Q1 2026 alone.
- Five largest exploits in 2024-2025 accounted for 62% of total value stolen.

**The real risk scenario:**
- A bridge carrying $2-5B in USDC gets exploited.
- Stolen USDC is real (backed by reserves), but Circle cannot freeze fast enough.
- Market panic. People dump USDC even though underlying reserve is fine.
- Temporary depeg causes cascading DeFi liquidations.

**Why USDT/USDC are safer:**
- NOT algorithmic stablecoins. Backed by real reserves.
- Simpler contracts (mint/burn/blacklist) with years of battle-tested security.
- But bridge exploits could still drain USDC from a specific chain.

**Threat level: MODERATE. Not existential, but could cause temporary chaos.**

**Ha_Chain mitigation:** Use native USDC on deployment chains, not bridged USDC. Avoid cross-chain bridges in escrow design. Stellar-native USDC is issued directly by Circle -- no bridge risk.

---

## 8. US INTEREST RATES DROP TO 0% -- STABLECOIN BUSINESS MODEL COLLAPSES

**The math:**
- Tether: $13B profit in 2024, almost entirely from interest on $135B in Treasuries.
- Circle: $1.68B revenue in 2024, of which $1.67B (99%) was interest income.
- A 50bp rate cut costs Tether ~$600M/year.
- At zero rates, Tether's revenue model produces near-zero income. Circle's model dies.

**Why this IS a threat:**
- Stablecoin issuers must find new revenue models or die.
- If issuers start charging fees or restricting redemptions to survive, trust erodes.
- Industry profitability entirely dependent on a variable it doesn't control (Fed rates).

**Why this is LESS likely currently:**
- Fed is at 4.25-4.50% (March 2026). Iran war, oil >$100, sticky inflation = slow rate cuts.
- Zero-rate environment required a once-in-a-century pandemic.
- Even at 2% rates, Tether earns ~$3.7B/year. Model survives at reduced rates; only zero is existential.

**Threat level: LOW probability in next 3 years, HIGH impact if it happens.**

**Ha_Chain advantage:** Ha_Chain's revenue comes from transaction fees ($0.99 flat + 0.05% protocol fee), NOT interest income. We're not dependent on rate environment. But if stablecoin issuers collapse, the settlement layer becomes unreliable. Mitigation: multi-stablecoin support.

---

## 9. COUNTRIES BAN STABLECOINS TO PROTECT LOCAL CURRENCIES

**Current bans and restrictions:**
- **China**: Complete ban on all stablecoins and crypto.
- **Algeria**: Law 25-10 (July 2025) criminalized all crypto including ownership, trading, mining, promotion.
- **Turkey**: Proposed daily and monthly limits on stablecoin transfers to prevent capital flight.
- **Nigeria**: Shifted from ban to regulation -- launched cNGN (domestic stablecoin) in early 2025.
- **India**: Not banned, but 30% tax + 1% TDS makes stablecoins extremely unattractive.

**The dollarization fear is real:**
- IMF (December 2025): USD stablecoins could spark currency substitution in vulnerable emerging markets.
- In Argentina, Turkey, Nigeria, Lebanon, stablecoins already function as parallel currencies.
- Chatham House: stablecoins enable "digital dollarization" via smartphones.
- This directly threatens central bank monetary policy, tax collection, currency stability.

**The regulatory escalation pattern:**
1. Government ignores stablecoins.
2. Stablecoins gain 10-20% adoption among financially active population.
3. Local currency weakens. Government panics.
4. Ban or severe restriction imposed.
5. Usage goes underground (VPNs, P2P). Adoption continues but harder.

**Threat level: HIGH for specific corridors, MODERATE overall.**

**Ha_Chain advantage:** In the matching model, money NEVER crosses borders. Stablecoins are only used for the escrow/matching layer -- actual settlement is in local currency via local rails (UPI, M-Pesa, SPEI). If framed as domestic transfers coordinated by a matching protocol (rather than stablecoin remittance), regulatory risk is significantly lower. BUT this framing needs to be bulletproof.

---

## 10. CBDCs ACTUALLY WIN -- DIGITAL YUAN INTEROPERABLE WITH 50+ COUNTRIES

**Current CBDC landscape:**
- 134 countries (98% of global GDP) exploring CBDCs.
- Only 4 have fully launched retail CBDCs (Bahamas, Jamaica, Nigeria, Eastern Caribbean).
- China's e-CNY: 0.2% of domestic electronic payments after 6 years.
- mBridge connects 5 central banks (not 50).

**Why CBDCs are struggling:**
- China, with the most resources and political will, achieved 0.2% penetration.
- No major economy has fully launched retail CBDC (not US, EU, Japan, UK).
- Nigeria's eNaira: <0.5% citizen usage after 2 years.
- Citizens don't want government-surveilled money.
- Interoperability between CBDCs is technically difficult.

**Threat level: LOW for next 5-10 years.**

**Ha_Chain advantage:** If CBDCs succeed, they become just another payment rail. The matching engine doesn't care whether settlement is in USDC, e-CNY, digital rupee, or M-Pesa. CBDCs winning doesn't kill Ha_Chain -- it changes which rails the last mile uses.

---

## 11. BRICS PAYMENT SYSTEMS FULLY CONVERGE INTO ONE SYSTEM

**Current systems:**
- India: UPI (1.7B monthly transactions)
- China: CIPS (yuan-denominated)
- Russia: SPFS (post-sanctions SWIFT alternative)
- Brazil: PIX (300M+ users)
- South Africa: SAMOS

**Why convergence is hard:**
- Five completely different architectures, security protocols, regulatory standards.
- India-China can't agree on borders, let alone financial infrastructure governance.
- No member wants to subordinate its payment system to a collective.
- SWIFT has 11,000+ members across 200+ countries built over 50 years. Can't replicate overnight.
- BRICS Pay itself says it "does not replace SWIFT, Visa, or Mastercard."

**Threat level: LOW for next 5 years, MODERATE for 10+.**

**Ha_Chain advantage:** A fragmented BRICS payment landscape is Ha_Chain's BEST-case scenario. More systems, more currencies, more friction = more need for a matching protocol. Full convergence is the least likely outcome given political dynamics.

---

## 12. HISTORICAL PRECEDENT -- HOW LONG DOES RESERVE CURRENCY TRANSITION TAKE?

**The British Pound Case:**
- 1914: WWI begins sterling's decline
- 1944: Bretton Woods formally subordinates sterling
- 1970s: Sterling Area collapses. Dollar fully dominant.
- **Total transition: ~60 years**

**Key lessons:**
1. Transitions take 50-100 years from beginning to completion.
2. Not smooth -- sterling briefly regained dominance in the 1930s.
3. Required catastrophic events (two world wars, Great Depression).
4. The successor (USD) was already dominant in trade and GDP before becoming reserve currency.
5. There is always a long "zombie" period where the declining currency maintains status through institutional inertia.

**Other examples:**
- Dutch guilder: ~50 years
- Spanish silver real: ~100 years
- Portuguese real: ~80 years

**Current dollar situation:**
- No clear successor. Yuan has capital controls. Euro has no fiscal union. Gold can't scale. Bitcoin too volatile.
- Most likely: not replacement but fragmentation -- multipolar system where dollar is largest but not only player.

**Threat level: NEGLIGIBLE for 5 years, LOW for 10, UNCERTAIN for 25+.**

**Ha_Chain advantage:** The dollar will remain dominant long enough for Ha_Chain to build, scale, and profit. But design currency-agnostic from day one for the multipolar future.

---

## THE HONEST BOTTOM LINE

The USD stablecoin dominance thesis is **robust for the next 5-7 years** but not invulnerable. The most likely failure mode is not dramatic collapse but slow erosion through:
- Regulatory fragmentation (different stablecoin regimes per region)
- Capital controls in receiving countries
- Trust erosion from aggressive US enforcement
- Gradual rise of local and regional alternatives

**Ha_Chain's matching model is actually better positioned for a fragmented future than for total USD dominance.** A messier, more multipolar financial world creates MORE demand for a protocol that bridges across systems, not less.

The existential risk is not that the dollar stablecoin thesis fails. It is that Ha_Chain builds a brittle system dependent on a single stablecoin (USDT) on a single chain and gets caught when disruption hits.

---

## ARCHITECTURAL COUNTERMEASURES FOR HA_CHAIN

### The Three HIGH-Risk Threats Share a Common Theme: Centralized Stablecoin Dependency

Every major risk comes back to USDT/USDC being centrally controlled, freezable, collapsible, and bannable.

### Countermeasures:

1. **Primary settlement on USDC (not USDT)**
   - USDC is regulated, audited, MiCA-compliant, gaining market share (64% of volume, 86% institutional preference)
   - Tether is a liability

2. **Multi-stablecoin escrow design**
   - Support USDC, USDT, DAI/USDS, EURC, PYUSD
   - Automatic fallback if one stablecoin is frozen or depegged

3. **The matching model is the shield**
   - Money never crosses borders in matched transactions = genuine legal protection against capital controls
   - Double down on this framing. Ensure technical implementation truly delivers.

4. **Minimize on-chain stablecoin exposure time**
   - Funds in escrow for minutes, not hours or days
   - Longer exposure = higher freeze risk

5. **Native chain USDC only**
   - Use Stellar-native USDC (issued by Circle directly on Stellar) and Base-native USDC
   - Avoid bridged USDC -- bridge exploits are the most realistic hack vector

6. **Build for the multipolar future**
   - Currency-agnostic protocol design
   - Support for CBDC settlement rails
   - Support for gold-backed tokens
   - Support for local stablecoins (cNGN, EURC, etc.)

7. **Corridor diversification**
   - Don't concentrate on any single corridor
   - If Turkey bans stablecoins, India corridor keeps running
   - If India restricts, Philippines keeps running
   - Geographic diversification is risk management

---

## SOURCES

### China & Digital Yuan
- [China Gives Up on State-Backed Digital Cash (PIIE)](https://www.piie.com/blogs/realtime-economics/2026/china-gives-state-backed-digital-cash)
- [China Interest-Bearing Digital Yuan (BeinCrypto)](https://beincrypto.com/china-digital-yuan-interest-ban-crypto-2026/)
- [China Bans Yuan Stablecoins (Crypto Valley Journal)](https://cryptovalleyjournal.com/focus/legal-and-compliance/china-bans-yuan-stablecoins-and-rwa-tokenization/)
- [China Digital Yuan Cross-Border (IDEAS-BRICS)](https://ideas-brics.org/chinas-digital-rmb-cross-border-integration/)

### EU & MiCA
- [Europe's MiCA Moment -- Racing Against Time (Oxford Law)](https://blogs.law.ox.ac.uk/oblb/blog-post/2025/11/europes-mica-moment-racing-against-time-stablecoin-wars)
- [5 MiCA-Compliant Stablecoins (Yellow)](https://yellow.com/learn/5-stablecoins-that-meet-mica-regulations-unlike-usdt)

### Tether Risk
- [Tether Hires Big Four for Full Audit (CoinDesk)](https://www.coindesk.com/business/2026/03/24/tether-hires-a-big-four-firm-for-a-full-audit/)
- [S&P Downgrades Tether (CoinDesk)](https://www.coindesk.com/policy/2025/11/26/s-and-p-downgrades-tether-s-usdt/)

### BRICS Gold-Backed Currency
- [BRICS Gold-Backed "Unit" Explained (CCN)](https://www.ccn.com/education/crypto/dollar-debasement-fears-brics-gold-backed-unit-currency-explained/)
- [Squashing BRICS Unit Fears (Fisher Investments)](https://www.fisherinvestments.com/en-us/insights/market-commentary/squashing-fears-of-the-brics-launching-a-unit-of-account)
- [BRICS New Payment System (Asia Times)](https://asiatimes.com/2026/01/brics-laying-first-tracks-for-new-global-payment-system/)

### Stablecoin Weaponization
- [Stablecoin Freezes Data Analysis (AMLBot)](https://blog.amlbot.com/stablecoin-freezes-2023-2025/)
- [Tether Freezes $3.3B (Yahoo Finance)](https://finance.yahoo.com/news/tether-freezes-3-3b-usdt-134406781.html)
- [FATF Warns Stablecoins in Sanctions Evasion (CoinDesk)](https://www.coindesk.com/policy/2026/03/03/stablecoins-sanctions-evasion-money-laundering)
- [Unstable Coins -- US Security Risks (CSIS)](https://www.csis.org/analysis/unstable-coins-stablecoin-regulation)

### Quantum Computing
- [Vitalik Post-Quantum Roadmap (CoinDesk)](https://www.coindesk.com/tech/2026/02/26/vitalik-buterin-ethereum-quantum-computing/)
- [ARK: Quantum Long-Term Risk (CoinDesk)](https://www.coindesk.com/tech/2026/03/12/quantum-computing-long-term-risk-bitcoin/)

### Hacks & Exploits
- [Resolv USR Exploit (CoinAlertNews)](https://coinalertnews.com/news/2026/03/22/resolv-stablecoin-exploit-depeg-2026)

### Interest Rate Risk
- [How Stablecoins Profit From US Debt (Three Sigma)](https://threesigma.xyz/blog/stablecoin/stablecoin-revenue-models-interest-rate-impact)

### Capital Controls & Bans
- [IMF Flags Stablecoins Risk to Emerging Markets (CoinDesk)](https://www.coindesk.com/markets/2025/12/10/imf-flags-stablecoins-emerging-markets/)
- [Stablecoins and Digital Dollarization (Chatham House)](https://www.chathamhouse.org/2025/08/will-stablecoins-help-developing-countries/)
- [2026 Digital Dollarization Wave (MrsCoins)](https://mrscoins.com/stablecoins-global-finance-2026/)

### CBDCs
- [BRICS Pay (Wikipedia)](https://en.wikipedia.org/wiki/BRICS_Pay)

### Historical Precedent
- [Zombie International Currency: Sterling 1945-1971 (Cambridge)](https://www.cambridge.org/core/journals/journal-of-economic-history/article/zombie-international-currency/)
- [Retirement of Sterling as Reserve Currency (CIRJE)](https://www.cirje.e.u-tokyo.ac.jp/research/workshops/history/history_paper2009/history1109.pdf)

### USDC Momentum
- [USDC Volume Surge (SmallWorldFS)](https://www.smallworldfs.com/blog/2026/03/21/usdc-volume-surge/)
- [USDC Leads 2026 Stablecoin Growth (CoinGenius)](https://coingenius.news/usdc-leads-stablecoin-growth-2026-supply-increase/)
