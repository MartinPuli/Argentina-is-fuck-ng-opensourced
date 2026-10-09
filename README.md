# Argentina-is-fuck-ng-opensourced

## Argentina government data leaks

Plain-English research on prominent Argentine government and government-linked data exposures, their causes, and their consequences for people, the economy and public institutions.

**Research window:** October 9, 2025–October 9, 2026  
**Evidence cutoff:** October 9, 2026  
**Language:** English  
**License:** [CC BY 4.0](LICENSE.md) for the original research text.

The repository also contains a research-backed defense proposal and a small runnable experiment. The proposed autonomous product is **not deployed**; the local experiment tests ordinary authorization and revocation with fictional data.

## Start here

Read the **[complete report](REPORT.md)** for the connected explanation, or choose a topic below.

| Document | What it covers |
|---|---|
| [Methodology and limitations](docs/METHODOLOGY.md) | Scope, evidence labels, what was verified, and what remains unknown. |
| [Argentine context and glossary](docs/GLOSSARY.md) | DNI, ANSES, PAMI, IOMA, ARCA, courts, and essential security terminology. |
| [Incident timeline](docs/INCIDENTS.md) | Confirmed disclosures, acknowledged incidents, disputed claims, enforcement developments, and older cases excluded from the window. |
| [Targets, origins and causes](docs/CAUSES.md) | Recurring government functions, account compromise, publication failures, intermediaries, and reporting rules. |
| [Consequences](docs/CONSEQUENCES.md) | Documented harm and plausible risks to citizens, the economy and government. |
| [Patterns and priorities](docs/PATTERNS-AND-PRIORITIES.md) | What happens after disclosure and practical ways to reduce harm. |
| [Source index](docs/SOURCES.md) | Deduplicated links to the report's source material. |
| [PAMI contribution review](docs/research/PAMI-CONTRIBUTION-REVIEW.md) | Review of the newly contributed PAMI analysis, citation corrections and implications for the defense. |

## From research to a defense

| Document | What it establishes |
|---|---|
| [What to build](docs/research/WHAT-TO-BUILD.md) | Plain-English architecture, how past incidents become reusable tests, development order and remaining work. |
| [Measured effects](docs/research/MEASURED-EFFECTS.md) | Actual local HTTP results, the records exposed before containment, and the cost to legitimate use. |
| [Search coverage](docs/research/SEARCH-PROTOCOL.md) | 32 selected paper records; separate discovery ledgers contain 1,378 initial and 986 additional title entries, not globally deduplicated. |
| [Autonomous defense and repair](docs/research/AUTONOMOUS-DEFENSE-PAPERS.md) | Eight selected papers, with versions, evaluation definitions and limitations. |
| [Agent safety](docs/research/AGENT-SAFETY-PAPERS.md) | Nine selected papers on untrusted evidence, permissions and trustworthy evaluation. |
| [Learning from incidents](docs/research/LEAK-LEARNING-PAPERS.md) | Five studies on incident context, feedback, shared learning and the gap between scores and enforcement. |
| [Threat intelligence and evidence integrity](docs/research/THREAT-INTELLIGENCE-PAPERS.md) | Five studies on behavior, log integrity, stolen-data circulation and credential remediation. |
| [Access control and exposure](docs/research/ACCESS-AND-EXPOSURE-PAPERS.md) | Five further studies on permission chains, effective access and confidentiality limits. |
| [Other countries](docs/research/COUNTRY-PRECEDENTS.md) | Government-confirmed programs, historical deployments and lessons for Argentina. |
| [Competitive comparison](competitor-profiles/_summary.md) | Existing commercial capabilities, open-source response building blocks and honest positioning. |
| [Sandbox architecture](docs/research/SANDBOX-ARCHITECTURE.md) | Firecracker, gVisor, Kata and E2B; separate repair, rehearsal and verification jobs. |
| [Additional paper discovery](docs/research/ADDITIONAL-DISCOVERY.md) | Broader metadata coverage and 18 unread or abstract-screened candidates. |
| [Hackathon fit](docs/HACKATHON-FIT.md) and [event brief](docs/EVENT-BRIEF.md) | Planned challenge fit, required integrations and evidence still needed. |
| [Runnable reference experiment](experiments/reference-defense/README.md) | Standard-library Python, four control modes, response transcripts and additional independently specified cases. |
| [Publication regression experiment](experiments/publication-regression/README.md) | Real local HTTP checks of stale artifacts, approved releases and a deliberate misclassification failure. |

The paper reviews read relevant full-text methods, results and limitations; they are neither an exhaustive literature review nor independent reproductions of those studies. The experiment contains no AI agent or sponsor calls, and does not test government infrastructure.

## How to interpret the research

The report distinguishes a confirmed disclosure from a criminal claim, an institutional denial, and an investigation that has not reached a public conclusion. It also separates the date of an intrusion from the date of publicity or an arrest.

“Front-page” is interpreted as substantive national or provincial coverage. This is not an exhaustive incident census or a verified collection of historical newspaper front pages. Record counts are not necessarily counts of distinct people; the incidents and developments in the timeline must not be added together as independent confirmed breaches.

The findings and their citations are in the linked documents. This repository preserves a research snapshot; it does not imply ongoing monitoring or that every external page remains unchanged.

## Repository contents

This repository contains original analysis, source references and an isolated synthetic experiment. It contains no leaked databases, victim records, live credentials, copied news articles or redistributed paper texts. The full report and topic chapters intentionally contain the same research so readers can use either format.

## Corrections and contributions

See [CONTRIBUTING.md](CONTRIBUTING.md) for how to propose a sourced correction or add later evidence. Keep the full report and relevant chapter consistent, preserve uncertainty, and record changes in [CHANGELOG.md](CHANGELOG.md).

## Reuse

You may share and adapt the original text under [CC BY 4.0](LICENSE.md), with attribution and an indication of changes. Linked articles, official documents and other third-party works retain their own rights and terms.

The reference experiment's Python source and executable JSON fixtures are separately [MIT licensed](experiments/reference-defense/LICENSE-MIT). Its documentation and generated results remain CC BY 4.0.

Suggested attribution: **MartinPuli, _Argentina Government Data Leaks_, research snapshot dated October 9, 2026.** Include a link to this repository and the license.
