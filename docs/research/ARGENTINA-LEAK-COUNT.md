# How many Argentine leaks can we actually substantiate?

**Evidence cutoff: October 9, 2026. Rolling review window: October 9, 2025–October 9, 2026.** This is an auditable sample, not a national census. “More reports found” does not mean “more breaches confirmed.”

## The defensible numbers

The existing timeline contains **15 reviewed entries**, including the separately described Chaco disruption. **Four institution-specific disclosure episodes meet this review's confirmation standard:** IOMA, SCBA, PAMI's public purchasing attachments, and Río Negro payroll information. This is a minimum established within our reviewed sample, not an estimate of Argentina's total. Two organizations affected by one campaign remain two institution-level episodes; they must not be advertised as two independently established intrusion events.

| Classification | Entries in the original reviewed timeline | What the number means |
|---|---:|---|
| Confirmed government disclosure | 4 | An institution acknowledged disclosure or reporting documented exposure with an institutional response. |
| Acknowledged government incident, leak scope unestablished | 1 | Salta Police; system impact does not establish every advertised dataset. |
| Alleged or disputed episode | 6 | WorkManagement/SudamericaData, IBR-CONICET, OSEP, Catamarca, ANSES/SIPA, Mi Argentina. The first concerns a private intermediary. |
| Umbrella claim | 1 | Chronus campaign; its advertised agency count must not be added to individual rows. |
| Enforcement development | 2 | Investigations of illegal data distribution; arrest dates are not extraction dates. |
| Disruption without established confidential-data leak | 1 | Chaco Legislature. |

The [machine-readable ledger](argentina-incident-counts.json) retains each entry's sources, classification and counting flag. The [incident narrative](../INCIDENTS.md) supplies the factual qualifications. Social-media leads and later corroboration appear in separate research ledgers; they enter the confirmed subtotal only after an explicit evidence review.

## What this additional search found

The [social-lead ledger](ARGENTINA-SOCIAL-LEAK-LEADS.md) adds **seven research leads/exclusions**: two government-related unverified claim groups, two nongovernment alerts, two unresolved entities and one nongovernment account-security notice. Five depend on secondary attribution to DailyDarkWeb; the original X posts were inaccessible. None adds a confirmed government disclosure.

The [corroboration pass](ARGENTINA-LEAK-CORROBORATION.md) adds **two named cases and one enforcement update**, alongside checks of existing stories. Córdoba's transport supplier acknowledged a repaired vulnerability according to the municipal response reported by Cadena 3; the exposure magnitude remains researcher-reported. Azul acknowledged defacement while denying the claimed database theft. Neither establishes a verified mass-leak victim total. The Gov.eth arrest is an enforcement development with historical overlap.

These ledger sizes measure research work, not additive incidents. The original confirmed subtotal remains **four**; the new supplier exposure report and disputed cases remain separately labeled. The additional government/education aggregate, CSJN and RENAPER/Health allegations warrant follow-up, but advertising volumes do not establish new independent intrusions.

## Official scale, using a different measurement

CERT.ar's **calendar-2025** report records **520 security incidents**, of which **254** are in its government sector. Within that sector it lists **108 account compromises** and **24 unauthorized-information-access incidents**. These are reported or detected incidents, not 520 leaks, not 254 breached agencies, and not counts of people. Categories and sectors overlap across dimensions; do not sum them. The period differs from our rolling window. [Official report, printed pages 4–5](https://www.argentina.gob.ar/sites/default/files/2026/09/informe_cert_2025.pdf).

Rechecking the official report also confirms the source inconsistency already noted in our main report: its comparison assigns a 2024 phishing percentage to government that the original table assigns to finance. We retain underlying counts and do not repeat that trend claim. [2024 table, printed page 5](https://www.argentina.gob.ar/sites/default/files/2025/07/informe_cert-ar_2024.pdf).

## Rules for expanding the count

1. **Store claims before conclusions.** Record the original post URL when available, publication date, named organization, source-access status, claimed quantity and unit. A repost or an article quoting the same post is another source, not independent confirmation.
2. **Separate dates.** Keep posting, alleged extraction, institutional response and later resale dates distinct. An October advertisement can contain years-old records.
3. **Group cautiously.** Match agency, dataset description, approximate date and cited original source. Mark uncertain overlap explicitly; do not merge solely because two posts say “Argentina.”
4. **Classify the evidence.** An accessible social alert establishes that an allegation was published. A denied claim remains disputed; an inaccessible post stays a retrieval gap. Neither becomes a verified leak automatically.
5. **Keep units intact.** Rows, files, bytes, accounts and distinct people are different measurements. The same person can occur repeatedly within and across collections. Never add advertised totals into “Argentines affected.”
6. **Publish revisions.** If corroboration changes a status, preserve the previous classification, dated reason and source. A correction should decrease the displayed total when necessary.

No raw leaked records, database samples, passwords, victim lists or criminal-market download links belong in this evidence library. They are unnecessary for counting public reports or designing a synthetic defense demonstration.

## What the research should change in the product

A separate scale indicator concerns resale, not new intrusions: Derechos Digitales' March 11, 2026 research announcement identifies **27 groups/channels across Argentina, Brazil and Peru combined**. It describes possible links to state databases. This is neither 27 Argentine breaches nor confirmation of a fresh compromise at each mentioned institution. [Research organization's announcement](https://www.derechosdigitales.org/recursos/identidades-en-venta-el-mercado-ilegal-de-compra-y-venta-de-datos-personales-latinoamericanos-en-telegram/).

Use public reports to decide which defensive checks deserve testing. Use authenticated observations from an enrolled service to decide whether to restrict that service. A claim on X must never, by itself, shut down an agency or revoke its users' accounts.

Our initial product should close a concrete loop: identify an unsafe access path, reproduce it with fictional records, apply a bounded control, then prove both that the unwanted access stopped and that legitimate work still completes. Each reusable lesson should contain its source, confidence, applicable system conditions, synthetic test, proposed control and counterexample. Unknown root causes remain unknown; the agent cannot invent them to make a historical incident fit the demo.

The [sponsor implementation plan](SPONSOR-DEFENSE-PLAN.md) maps this loop to real tool responsibilities. The existing experiments demonstrate narrow controls locally; they do not establish a working autonomous national defense.
