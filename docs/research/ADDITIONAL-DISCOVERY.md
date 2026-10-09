# Additional cybersecurity discovery — October 9, 2026

This expands discovery for **October 9, 2025–October 9, 2026**. It does not complete the request to read every new cybersecurity paper. **986 additional title entries** were parsed across six sources; **175 matched the existing keyword filter**. These are within-source metadata counts, not unique papers, newly published papers or full-text readings. No global DOI deduplication has been completed.

The 18 candidates below were absent from the original 27-record title list. The original pass screened metadata and, where marked, abstracts, adding zero full-text reviews. **Eleven of the 18 candidates have since received targeted full-text review; seven remain unread or abstract-screened.** This queue links those evidence records and adds no separate paper reads or reproductions. See [machine-readable ledger](additional-discovery.json) and [search protocol](SEARCH-PROTOCOL.md).

## Retrieved indexes

| Source | Parsed titles | Keyword matches | Date and retrieval qualification |
|---|---:|---:|---|
| [ACM CCS 2025](https://www.sigsac.org/ccs/CCS2025/accepted-papers/) | 316 | 22 | October 13–17, 2025. Client-rendered HTML was empty; its public JSON yielded 102 + 214 rows. Venue date is not first-preprint date. |
| [RAID 2026](https://raid2026.org/accepted.html) | 59 | 15 | October 11–14, 2026, after cutoff. Public acceptance CSV retrieved; protected paper downloads were not accessed. |
| [ACSAC 2025](https://www.acsac.org/2025/program/papers/) | 84 | 7 | December 8–12, 2025. Nonempty bold paper titles; 84 also reported in organizer slides. |
| [AsiaCCS 2026 cycle 1](https://asiaccs2026.cse.iitkgp.ac.in/cycle-1-papers/) | 74 | 13 | June 1–5, 2026. List announced April 26; 74 nonempty bold titles. |
| [AsiaCCS 2026 cycle 2](https://asiaccs2026.cse.iitkgp.ac.in/cycle-2-papers/) | 48 | 5 | June 1–5, 2026. List announced April 26; 48 nonempty bold titles. |
| [arXiv cs.CR October 2026 snapshot](https://arxiv.org/list/cs.CR/2026-10?skip=0&show=2000) | 405 | 113 | October month-to-cutoff snapshot. 405 titles; later reconciliation recovered 405 unique abstract IDs from the same snapshot. Not a completed October census. |

Snapshot hashes, byte sizes, exact public data URLs and selectors are in the JSON. HTML/CSV/JSON snapshots stayed in temporary storage and are not redistributed. The original pass deduplicated normalized titles within each source. The later [reconciliation](CORPUS-RECONCILIATION.md) recovered 405 `/abs/` identifiers after correcting whitespace handling in links; the JSON preserves the initial zero-ID parser result with a linked correction. Title counts and snapshot hashes are unchanged. An index can include old work newly deposited: the October arXiv list includes an operating-systems survey citing a 2012 journal publication. Individual publication dates therefore still require checking.

## Priority reading queue and current status

Reasons below are **our triage inferences**, not validated paper findings. The table shows current reading status; initial screening status is preserved in the JSON. No abstract-level performance claim is adopted. “Venue” dates are presentation/publication milestones, not proof of first availability. Unknown dates remain unknown.

| ID | Candidate / primary link | Confirmed date and status | Next review question |
|---|---|---|---|
| AD01 | [From Investigation Failures to Reliable SOC Agents: Understanding and Improving LLM-Based Alert Triage](https://arxiv.org/abs/2610.10608) | First preprint 2026-10-07; [`fulltext_targeted`](october-agent-reliability.json) | Audit evidence sufficiency before dismissing alerts. |
| AD02 | [NOMOS: Compiling Written Policies into Statically Verified Tool-Call Gates for LLM Agents](https://arxiv.org/abs/2610.11030) | First preprint 2026-10-08; [`fulltext_targeted`](october-agent-reliability.json) | Compare deterministic authorization gates against prose-only policy. |
| AD03 | [PyCache Trap: The Inspection-Execution Gap in Agent Skill Scanners](https://arxiv.org/abs/2610.10612) | First preprint 2026-10-07; [`fulltext_targeted`](october-artifact-security.json) | Check whether admitted artifacts match executed artifacts. |
| AD04 | [Anytime-valid detection of LLM weight exfiltration](https://arxiv.org/abs/2610.11843) | First preprint 2026-10-08; [`fulltext_targeted`](early-exfiltration-detection.json) | Examine sequential false-alarm control and transfer assumptions. |
| AD05 | [DITTO: A Context-aware Pickle-based Pre-Trained Model Scanner for Effective Security Audits](https://arxiv.org/abs/2610.10735) | First preprint 2026-10-07; [`fulltext_targeted`](october-artifact-security.json) | Assess model-artifact admission before unsafe deserialization. |
| AD06 | [R+R: From Claims to Crashes: A Systematic Re-evaluation of Graph-Based Network Intrusion Detection Systems](https://www.acsac.org/2025/program/final/s147.html) | First date unresolved; venue 2025-12-10; `abstract_screened` | Audit reproducibility and enterprise generalization of detection metrics. |
| AD07 | [Clouseau: A Hierarchical Multi-Agent Approach For Autonomous Attack Investigation](https://www.doc.ic.ac.uk/~maffeis/papers/acsac25.pdf) | First date unresolved; venue 2025-12-10; [`fulltext_targeted`](investigation-execution-trust.json) | Evaluate investigations beginning from a suspicious host event. |
| AD08 | [Revealing the True Indicators: Understanding and Improving IoC Extraction From Threat Reports](https://www.acsac.org/2025/program/final/s253.html) | First date unresolved; venue 2025-12-10; [`fulltext_targeted`](threat-report-verification.json) | Check labels before converting reports into blocking indicators. |
| AD09 | [SoK: Reshaping Research on Network Intrusion Detection Systems](https://arxiv.org/abs/2604.17556) | First preprint 2026-04-19; venue 2026-06-01; [`fulltext_targeted`](detection-response-evaluation.json) | Evaluate analyst reports and realistic traffic rather than sample accuracy. |
| AD10 | [SoK: Systematization, Detection, and Hunting of Windows Malware Persistence Techniques](https://www.eurecom.fr/en/publication/8692) | First date unresolved; venue 2026-06-01; `abstract_screened` | Map host telemetry coverage to persistence and non-persistence. |
| AD11 | [VET Your Agent: Towards Host-Independent Autonomy via Verifiable Execution Traces](https://arxiv.org/abs/2512.15892) | First preprint 2025-12-17; venue 2026-06-01; [`fulltext_targeted`](investigation-execution-trust.json) | Separate authentic execution evidence from trusting the host. |
| AD12 | [CRX-ray: Large-Scale Detection of API Key Leakage in Browser Extensions](https://asiaccs2026.cse.iitkgp.ac.in/cycle-1-papers/) | First date unresolved; venue 2026-06-01; `index_only` | Inspect extension packages as another credential-exposure surface. |
| AD13 | [Slot: Provenance-Driven APT Detection through Graph Reinforcement Learning](https://arxiv.org/abs/2410.17910) | First preprint 2024-10-23; revision 2025-07-17; venue 2025-10-13; `abstract_screened` | Compare provenance baselines against emerging detection methods. |
| AD14 | [Dangers Behind Access Control: Understanding and Exploiting Implicit Permissions in Kubernetes](https://dl.acm.org/doi/10.1145/3719027.3765106) | First date unresolved; venue 2025-10-13; `index_only` | Check effective privileges beyond explicitly assigned permissions. |
| AD15 | [Can IOCs impose cost? The effects of publishing threat intelligence on adversary behavior](https://dl.acm.org/doi/10.1145/3719027.3765026) | First date unresolved; venue 2025-10-13; [`fulltext_targeted`](threat-report-verification.json) | Examine whether shared indicators change adversary behavior. |
| AD16 | [Effective and Efficient Threat Hunting with Small Language Models](https://arxiv.org/abs/2512.06660) | First preprint 2025-12-07; revision 2026-09-17; venue 2026-10-11; [`fulltext_targeted`](permission-credential-surfaces.json) | Distinguish query syntax/schema validity from successful threat detection. |
| AD17 | [Sometimes Less is More: A Minimalist Approach to Neighborhood-level Provenance-based Intrusion Detection](https://raid2026.org/accepted.html) | First date unresolved; venue 2026-10-11; `index_only` | Compare simpler provenance models before adding agent complexity. |
| AD18 | [Grounded in Knowledge, Guided by Reason: Automated Fake Cyber Threat Intelligence Detection via Knowledge-Augmented LLM Rationales](https://raid2026.org/accepted.html) | First date unresolved; venue 2026-10-11; `index_only` | Examine misinformation defenses for ingested threat intelligence. |

## Date and evidence caveats

- **AD13 is an earlier foundation:** Slot first appeared in October 2024; its July 2025 revision is also before the window. Only its later CCS 2025 milestone falls inside.
- **AD17–AD18 are unresolved publication-date leads:** their public acceptance metadata is confirmed, but RAID starts after the cutoff. Do not count them as newly published in-window works. AD16 qualifies through its December 2025 preprint and September 2026 revision.
- **AD04 is a preprint in-window:** its author-reported workshop acceptance refers to December 2026; that event is after the cutoff. Its model-weight threat model is narrower than general data leakage.
- **AD07 has a title alias:** the official index says “Clouesau” and “Hierarchal”; the author PDF says “Clouseau” and “Hierarchical.” The review associates the author manuscript with the program entry. The conservative automated catalog leaves this spelling match unmerged and flags it for identity resolution; its group count is therefore not a verified paper count.
- **AD06 has a version discrepancy to resolve:** the program abstract and an author-PDF search excerpt differ on the number of public datasets. This queue does not adopt either evaluation count.
- **AD12 and AD14 remain index-only:** primary metadata was checked, but full text was not retrieved. See the [access record](PERMISSION-AND-CREDENTIAL-SURFACES.md). The accessible TLBAC substitute is a different paper and does not complete either queue item.
- **AD09, AD15 and AD16 now have targeted reviews:** AD09 uses arXiv v1, AD15 an unnumbered accepted author manuscript, and AD16 arXiv v3. A venue date is not substituted for an unknown first-public date, and preprint/proceedings equivalence is not assumed.

## Work still required

Read the seven remaining candidates, continue unread sections and appendices of the targeted reviews, verify versions, audit denominators and alert/report units, and check artifact availability. The [corpus reconciliation](CORPUS-RECONCILIATION.md) joins exact identifiers and normalized titles across the ten indexes; global DOI resolution remains unfinished. Then continue the other titles, venues, journals, workshops and preprint months. Neither the 986 additional entries nor the earlier 1,378 entries establish exhaustive coverage. No national leak-prevention rate can be inferred from this metadata pass.

## Later review checkpoint — October 9, 2026

The discovery counts above describe the original metadata pass. **Eleven candidates now have targeted full-text reviews:** AD01–AD05, AD07–AD09, AD11, AD15 and AD16. Their evidence is in [agent reliability](OCTOBER-AGENT-RELIABILITY.md), [artifact security](OCTOBER-ARTIFACT-SECURITY.md), [exfiltration detection](EARLY-EXFILTRATION-DETECTION.md), [investigation and execution trust](INVESTIGATION-AND-EXECUTION-TRUST.md), [threat-report verification](THREAT-REPORT-VERIFICATION.md), [detection/response evaluation](DETECTION-AND-RESPONSE-EVALUATION.md) and [permission/credential surfaces](PERMISSION-AND-CREDENTIAL-SURFACES.md).

**Seven remain:** AD06, AD10, AD12, AD13, AD14, AD17 and AD18. AD12, AD14 and AD18 have access/metadata records but remain unread; substitute reviews are separate works. No paper was reproduced.

Across the original and additional index snapshots, the [reconciliation checkpoint](CORPUS-RECONCILIATION.md) recovers 2,364 entries and groups them into 2,362 candidates under explicit rules. That is metadata grouping, not a first-publication census or a reading count. Current overall review totals are maintained in the [search protocol](SEARCH-PROTOCOL.md), separately from this 18-item queue.
