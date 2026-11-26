# 22: Jurisdiction and Founder Analysis -- Where the Engine Runs vs. Whose Law Applies

## Does moving the matching engine (or the founder) change which laws apply?

**Research Date: November 26, 2026**

> **Not legal advice.** This is issue-spotting to prepare for conversations with qualified US payments/sanctions counsel, Indian FEMA/RBI counsel, and immigration counsel. Items marked *(verify)* are especially in need of confirmation.

---

## THE BOTTOM LINE (Read This First)

| Question | Short answer |
|---|---|
| Does running the matching engine in India avoid US law? | **No.** US law follows US *customers*, US *bank accounts* and US *persons*, not server location. |
| Does running it in India add Indian law? | **Yes, and the P2P matching model is close to what FEMA Section 3 prohibits.** |
| Does an Indian (non-US-person) founder escape US law? | **Only partly.** Personal OFAC obligations largely fall away, but serving US customers still triggers FinCEN/state MTL/18 USC 1960, and non-US founders have been prosecuted for that. |
| Does an Indian-resident founder face more Indian risk? | **Yes, significantly.** FEMA, the Payment and Settlement Systems Act, crypto/VASP rules and Overseas Investment rules all apply personally. Doc 20's "no Indian entity = no Indian exposure" strategy fails if the founder lives in India. |
| What actually reduces US exposure? | Launching corridors with **no US users and no USD through US banks** (e.g. UAE → India). |
| What actually reduces Indian exposure? | Operating as the settlement/matching layer **for a licensed Indian channel** (AD bank, MTSS principal, PA-CB entity), or from **GIFT City (IFSC)**, rather than as a standalone P2P netting scheme. |

---

## 1. THE GOVERNING PRINCIPLE

Regulators assert jurisdiction based on **who you serve, where the money sits, and who you are**, not where the code runs:

1. **Customers**: serving residents of a country/state pulls you into its licensing regime.
2. **Bank accounts and currency**: touching a country's banking system (e.g. ACH, UPI, USD correspondent clearing) creates a nexus there.
3. **Persons**: citizens/residents carry some obligations wherever they operate (US sanctions for US persons, FEMA for Indian residents).

Server location is close to irrelevant on all three tests.

---

## 2. SCENARIO A: US-PERSON FOUNDER, MATCHING ENGINE RUN FROM INDIA

### US law still applies
- **FinCEN MSB status.** Since FinCEN's 2011 MSB rule, a foreign-located MSB doing business "wholly or in substantial part within the United States" is an MSB (31 CFR 1010.100(ff)). It must register, designate a US agent, and run a full BSA/AML program. Collecting USD from US senders and paying US recipients via ACH is doing business in the US.
- **State money transmitter licenses** are triggered by serving residents of a state, wherever the operator sits.
- **18 USC 1960** (unlicensed money transmitting business) reaches businesses affecting interstate or foreign commerce.
- **Offshore was no defense for others.** BitMEX (Seychelles), Binance, KuCoin and OKX were all offshore and all faced US enforcement for serving US customers without registration or licenses.
- **The US leg needs a US bank.** Paying out by ACH means funds sit in a US bank account, and that bank will require US compliance.
- **Personal exposure.** A US person (citizen, green-card holder, or anyone physically in the US) is bound by **OFAC** sanctions wherever they operate, and can face **conspiracy** liability for running an unlicensed transmitter that serves Americans.

### Indian law is added on top
- **FEMA Section 3** prohibits, except through an authorized person:
  - (b) making payment to or for the credit of a person resident outside India;
  - (c) receiving payment **"by order or on behalf of"** a person resident outside India;
  - (d) entering a financial transaction in India in association with acquiring an asset or right outside India.

  In the Ali/Raj example, Ali's mother receives INR from Raj **on Ali's behalf**. That is the pattern 3(c) targets, and it is how Indian law treats hawala. Penalties run up to **3x the amount involved** (FEMA s.13), enforced by the Enforcement Directorate.
- **Payment and Settlement Systems Act 2007.** Operating a payment system requires RBI authorization, and operating without it is a criminal offense *(verify current penalty provisions)*.
- **Remittance channels are narrow.** Inward remittances flow through RBI's **Money Transfer Service Scheme (MTSS)** or **Authorised Dealer (AD) banks**. Outward remittances flow through the **Liberalised Remittance Scheme (LRS)** with TCS. P2P netting fits neither channel.
- **Crypto.** VASPs serving Indians must register with **FIU-IND** under PMLA (since 2023). Gains are taxed at 30% (s.115BBH) with 1% TDS on transfers (s.194S). India blocked unregistered offshore exchanges in 2024.

**Conclusion A:** moving servers to India does not reduce US exposure and adds Indian exposure.

---

## 3. SCENARIO B: INDIAN FOUNDER RESIDENT IN INDIA

### What gets better (US side)
- **Personal OFAC obligations largely fall away.** A non-US person outside the US isn't directly bound by US primary sanctions. However:
  - Causing a US person or US bank to violate sanctions (e.g. routing USD through US correspondents) is still chargeable under IEEPA.
  - Secondary sanctions can target non-US persons.
  - USD clearing creates a nexus by itself.
- **No US tax/reporting burden on the founder personally** (no FBAR/CFC rules, unless US-resident).

### What does NOT change (US side)
- **Serving US customers still makes the business a US MSB** and triggers state MTLs and 18 USC 1960, whoever the founder is.
- **Non-US founders have been charged personally.** The BitMEX founders were charged with BSA violations and CZ (Canadian) pleaded guilty. The **US-India extradition treaty (1997)** exists.

### What gets worse (India side)
- **FEMA now applies to the founder personally**, and the founder would be the organizer of the matching scheme. Doc 20's strategy (sec. 10: "DO NOT establish an Indian entity... no Indian presence") depends on the operator being outside India. A founder living in India *is* an Indian presence, and Indian authorities can act against individuals directly. FEMA s.37A also allows seizure of Indian assets equivalent to foreign-held value in certain cases.
- **Overseas Investment Rules, 2022.** Under the 2022 framework, a **resident individual generally cannot make Overseas Direct Investment in a foreign entity engaged in financial services activity** *(verify)*. An India-resident founder therefore may not be able to simply own a Delaware, Dubai or El Salvador remittance company. Further constraints:
  - LRS caps personal outward remittance at USD 250,000 per year.
  - The rules restrict "round-tripping" structures (a foreign company owning an Indian subsidiary).
- **Tax residence of the company.** A foreign company **effectively managed from India** can be treated as Indian tax resident under the **Place of Effective Management (POEM)** rules.
- **Payment and Settlement Systems Act, FIU-IND/VASP registration and crypto tax** all apply directly.

### What becomes possible (India side)
An Indian founder is well placed to take *legitimate* Indian routes that a foreign operator can't easily take:
- **Partner with an AD bank, an MTSS principal or a PA-CB (Payment Aggregator -- Cross Border) entity.** Ha_Chain's matching logic would become their netting/settlement engine rather than a standalone scheme.
- **RBI Regulatory Sandbox.** Earlier cohorts covered cross-border payments.
- **GIFT City (IFSC).** Units there are treated as non-resident for FEMA purposes and are regulated by IFSCA, which has a payment-services framework *(verify current IFSCA payment services regulations and whether remittance activity is permitted)*. This is plausibly the cleanest home for an India-founded cross-border payments company.

**Conclusion B:** being Indian reduces *personal* US sanctions exposure. It does not remove US exposure if you serve US users, and it substantially increases personal Indian exposure for the current P2P design.

---

## 4. SCENARIO C: INDIAN CITIZEN LIVING IN THE US (e.g. on a visa)

This is the most complex position, because both regimes bite:
- **US.** Anyone physically in the US is a **US person** for OFAC purposes, and US tax residents carry US reporting duties. Everything in Scenario A applies.
- **India.** Someone who left India for work or study for an indefinite period is generally **non-resident** under FEMA, so the personal FEMA burden is lighter while abroad. It returns on moving back, and the *scheme* still violates FEMA on the India leg regardless.
- **Immigration.** Most US work visas (e.g. F-1, H-1B) restrict working on your own startup without specific authorization. **Get immigration counsel before doing operational work on the company.**

---

## 5. SCENARIO D: A CORRIDOR THAT NEVER TOUCHES THE US

Example: **UAE → India**, operated from **ADGM** (doc 19's recommended launch) or GIFT City.

- **No US customers and no USD through US banks** means FinCEN registration and state MTLs largely drop out.
- **What still applies:**
  - OFAC for any US-person founder or staff, and for any USD leg;
  - FCPA (if a US person or US issuer);
  - US tax reporting for US-person owners (FBAR, CFC/GILTI).
- **The licensing burden moves to the UAE** (an ADGM/CBUAE license) **and India** (an RBI-approved inbound channel). Pure P2P netting on the India leg still conflicts with FEMA. The design needs to route the India payout through, or on behalf of, a licensed inbound remittance channel.

This is the scenario that genuinely reduces regulatory surface. It's achieved by choosing **customers and currencies**, not by choosing **server location**.

---

## 6. CORRECTIONS TO EARLIER DOCS

| Doc | Claim | Correction |
|---|---|---|
| 21, "How Ha_Chain Fixes It" (hawala section) | "No forex = FEMA doesn't apply" | Wrong. FEMA s.3(b)-(d) covers payments made or received on behalf of non-residents even when no currency is exchanged. Doc 20 sec. 8-9 already identifies this. *(Fixed in doc 21.)* |
| 20, sec. 10 | "DO NOT establish an Indian entity -- no Indian presence" avoids Indian licensing | Holds only if no founder, staff or control is in India. It fails for an India-resident founder, and RBI/ED can still act against Indian participants and the scheme. *(Note added in doc 20.)* |
| 07 / 10 / 21 | Offshore licensing (El Salvador, MiCA, ADGM) as a way to serve US users | An offshore license doesn't authorize serving US customers. US law applies to US-facing activity. |

---

## 7. QUESTIONS TO TAKE TO COUNSEL

**US payments counsel**
1. If we exclude US users entirely (geo-blocking, KYC residency checks, no US bank accounts), what residual US exposure remains for a US-person or non-US-person founder?
2. Can an MTL partner be the transmitter of record for the US leg, with Ha_Chain as a technology provider?

**Indian FEMA/RBI counsel**
3. Can the matching model be restructured as a netting/settlement service for an AD bank, MTSS principal or PA-CB entity so the India payout is "through an authorised person"?
4. Is GIFT City/IFSCA a viable base, and under which payment-services regulation?
5. For an India-resident founder: can we lawfully hold equity in a foreign payments entity under the Overseas Investment Rules 2022, and how should we structure to avoid POEM and round-tripping issues?

**Immigration counsel** (if living in the US on a visa)
6. What work on our own startup is permitted under my current status?

---

## SOURCES / REFERENCES (to verify with counsel)

- 31 CFR 1010.100(ff): MSB definition, including foreign-located MSBs (FinCEN final rule, July 2011)
- 31 CFR 1022.380: MSB registration
- 18 USC 1960: unlicensed money transmitting businesses
- United States v. Storm (SDNY, verdict Aug 2025); Samourai Wallet pleas (2025); BitMEX, Binance, KuCoin, OKX enforcement actions
- Foreign Exchange Management Act, 1999: s.3, s.13, s.37A
- Payment and Settlement Systems Act, 2007: s.4 and penalty provisions
- RBI Master Direction: Money Transfer Service Scheme; Liberalised Remittance Scheme
- RBI Payment Aggregator -- Cross Border (PA-CB) framework
- Foreign Exchange Management (Overseas Investment) Rules and Regulations, 2022
- PMLA notification bringing VASPs under FIU-IND (March 2023); Income Tax Act s.115BBH, s.194S
- Income Tax Act s.6(3): Place of Effective Management
- IFSCA framework for payment services in GIFT City
- US-India Extradition Treaty (1997)
