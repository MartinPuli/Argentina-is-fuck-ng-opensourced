# Additional cybersecurity discovery — October 9, 2026

This expands discovery for **October 9, 2025–October 9, 2026**. It does not complete the request to read every new cybersecurity paper. **986 additional title entries** were parsed across six sources; **175 matched the existing keyword filter**. These are within-source metadata counts, not unique papers, newly published papers or full-text readings. No global DOI deduplication has been completed.

The 18 candidates below were absent from the original 27-record title list. Their metadata and, where marked, abstracts were screened; **this file adds zero targeted full-text reviews and zero reproductions**. Concurrent detailed reviews should record their own evidence status rather than inheriting a status from this queue. See [machine-readable ledger](additional-discovery.json) and [search protocol](SEARCH-PROTOCOL.md).

## Retrieved indexes

| Source | Parsed titles | Keyword matches | Date and retrieval qualification |
|---|---:|---:|---|
| [ACM CCS 2025](https://www.sigsac.org/ccs/CCS2025/accepted-papers/) | 316 | 22 | October 13–17, 2025. Client-rendered HTML was empty; its public JSON yielded 102 + 214 rows. Venue date is not first-preprint date. |
| [RAID 2026](https://raid2026.org/accepted.html) | 59 | 15 | October 11–14, 2026, after cutoff. Public acceptance CSV retrieved; protected paper downloads were not accessed. |
| [ACSAC 2025](https://www.acsac.org/2025/program/papers/) | 84 | 7 | December 8–12, 2025. Nonempty bold paper titles; 84 also reported in organizer slides. |
| [AsiaCCS 2026 cycle 1](https://asiaccs2026.cse.iitkgp.ac.in/cycle-1-papers/) | 74 | 13 | June 1–5, 2026. List announced April 26; 74 nonempty bold titles. |
| [AsiaCCS 2026 cycle 2](https://asiaccs2026.cse.iitkgp.ac.in/cycle-2-papers/) | 48 | 5 | June 1–5, 2026. List announced April 26; 48 nonempty bold titles. |
| [arXiv cs.CR October 2026 snapshot](https://arxiv.org/list/cs.CR/2026-10?skip=0&show=2000) | 405 | 113 | October month-to-cutoff snapshot. 405 titles and unique abstract IDs agree with reported count; not a completed October census. |

Snapshot hashes, byte sizes, exact public data URLs and selectors are in the JSON. HTML/CSV/JSON snapshots stayed in temporary storage and are not redistributed. Deduplicate normalized titles within each source; for arXiv, cross-check unique `/abs/` identifiers. An index can include old work newly deposited: the October arXiv list includes an operating-systems survey citing a 2012 journal publication. Individual publication dates therefore still require checking.

## Priority reading queue

Reasons below are **our triage inferences**, not validated paper findings. No abstract-level performance claim is adopted. “Venue” dates are presentation/publication milestones, not proof of first availability. Unknown dates remain unknown.

| ID | Candidate / primary link | Confirmed date and status | Next review question |
|---|---|---|---|
| AD01 | [From Investigation Failures to Reliable SOC Agents: Understanding and Improving LLM-Based Alert Triage](https://arxiv.org/abs/2610.10608) | First preprint 2026-10-07; `abstract_screened` | Audit evidence sufficiency before dismissing alerts. |
| AD02 | [NOMOS: Compiling Written Policies into Statically Verified Tool-Call Gates for LLM Agents](https://arxiv.org/abs/2610.11030) | First preprint 2026-10-08; `abstract_screened` | Compare deterministic authorization gates against prose-only policy. |
| AD03 | [PyCache Trap: The Inspection-Execution Gap in Agent Skill Scanners](https://arxiv.org/abs/2610.10612) | First preprint 2026-10-07; `abstract_screened` | Check whether admitted artifacts match executed artifacts. |
| AD04 | [Anytime-valid detection of LLM weight exfiltration](https://arxiv.org/abs/2610.11843) | First preprint 2026-10-08; `abstract_screened` | Examine sequential false-alarm control and transfer assumptions. |
| AD05 | [DITTO: A Context-aware Pickle-based Pre-Trained Model Scanner for Effective Security Audits](https://arxiv.org/abs/2610.10735) | First preprint 2026-10-07; `abstract_screened` | Assess model-artifact admission before unsafe deserialization. |
| AD06 | [R+R: From Claims to Crashes: A Systematic Re-evaluation of Graph-Based Network Intrusion Detection Systems](https://www.acsac.org/2025/program/final/s147.html) | First date unresolved; venue 2025-12-10; `abstract_screened` | Audit reproducibility and enterprise generalization of detection metrics. |
| AD07 | [Clouseau: A Hierarchical Multi-Agent Approach For Autonomous Attack Investigation](https://www.doc.ic.ac.uk/~maffeis/papers/acsac25.pdf) | First date unresolved; venue 2025-12-10; `abstract_screened` | Evaluate investigations beginning from a suspicious host event. |
| AD08 | [Revealing the True Indicators: Understanding and Improving IoC Extraction From Threat Reports](https://www.acsac.org/2025/program/final/s253.html) | First date unresolved; venue 2025-12-10; `abstract_screened` | Check labels before converting reports into blocking indicators. |
| AD09 | [SoK: Reshaping Research on Network Intrusion Detection Systems](https://arxiv.org/abs/2604.17556) | First preprint 2026-04-19; venue 2026-06-01; `abstract_screened` | Evaluate analyst reports and realistic traffic rather than sample accuracy. |
| AD10 | [SoK: Systematization, Detection, and Hunting of Windows Malware Persistence Techniques](https://www.eurecom.fr/en/publication/8692) | First date unresolved; venue 2026-06-01; `abstract_screened` | Map host telemetry coverage to persistence and non-persistence. |
| AD11 | [VET Your Agent: Towards Host-Independent Autonomy via Verifiable Execution Traces](https://arxiv.org/abs/2512.15892) | First preprint 2025-12-17; venue 2026-06-01; `abstract_screened` | Separate authentic execution evidence from trusting the host. |
| AD12 | [CRX-ray: Large-Scale Detection of API Key Leakage in Browser Extensions](https://asiaccs2026.cse.iitkgp.ac.in/cycle-1-papers/) | First date unresolved; venue 2026-06-01; `index_only` | Inspect extension packages as another credential-exposure surface. |
| AD13 | [Slot: Provenance-Driven APT Detection through Graph Reinforcement Learning](https://arxiv.org/abs/2410.17910) | First preprint 2024-10-23; revision 2025-07-17; venue 2025-10-13; `abstract_screened` | Compare provenance baselines against emerging detection methods. |
| AD14 | [Dangers Behind Access Control: Understanding and Exploiting Implicit Permissions in Kubernetes](https://dl.acm.org/doi/10.1145/3719027.3765106) | First date unresolved; venue 2025-10-13; `index_only` | Check effective privileges beyond explicitly assigned permissions. |
| AD15 | [Can IOCs impose cost? The effects of publishing threat intelligence on adversary behavior](https://dl.acm.org/doi/10.1145/3719027.3765026) | First date unresolved; venue 2025-10-13; `index_only` | Examine whether shared indicators change adversary behavior. |
| AD16 | [Effective and Efficient Threat Hunting with Small Language Models](https://arxiv.org/abs/2512.06660) | First preprint 2025-12-07; revision 2026-09-17; venue 2026-10-11; `abstract_screened` | Distinguish query syntax/schema validity from successful threat detection. |
| AD17 | [Sometimes Less is More: A Minimalist Approach to Neighborhood-level Provenance-based Intrusion Detection](https://raid2026.org/accepted.html) | First date unresolved; venue 2026-10-11; `index_only` | Compare simpler provenance models before adding agent complexity. |
| AD18 | [Grounded in Knowledge, Guided by Reason: Automated Fake Cyber Threat Intelligence Detection via Knowledge-Augmented LLM Rationales](https://raid2026.org/accepted.html) | First date unresolved; venue 2026-10-11; `index_only` | Examine misinformation defenses for ingested threat intelligence. |

## Date and evidence caveats

- **AD13 is an earlier foundation:** Slot first appeared in October 2024; its July 2025 revision is also before the window. Only its later CCS 2025 milestone falls inside.
- **AD17–AD18 are unresolved publication-date leads:** their public acceptance metadata is confirmed, but RAID starts after the cutoff. Do not count them as newly published in-window works. AD16 qualifies through its December 2025 preprint and September 2026 revision.
- **AD04 is a preprint in-window:** its author-reported workshop acceptance refers to December 2026; that event is after the cutoff. Its model-weight threat model is narrower than general data leakage.
- **AD07 has a title alias:** the official index says “Clouesau” and “Hierarchal”; the author PDF says “Clouseau” and “Hierarchical.” Treat them as one work.
- **AD06 has a version discrepancy to resolve:** the program abstract and an author-PDF search excerpt differ on the number of public datasets. This queue does not adopt either evaluation count.
- **AD12 remains index-only:** the publisher page returned HTTP 403; no full text or earliest public date was verified.

## Work still required

Read the selected methods and limitations, verify exact versions, audit denominators and alert/report units, check artifact availability, and deduplicate against the existing venues. Then continue the other titles, venues, journals, workshops and preprint months. Neither the 986 additional entries nor the earlier 1,378 entries establish exhaustive coverage. No national leak-prevention rate can be inferred from this metadata pass.

## Later review checkpoint — October 9, 2026

The discovery counts above describe the original metadata pass. AD01–AD05 have since advanced to targeted full-text review: [agent reliability](OCTOBER-AGENT-RELIABILITY.md), [artifact security](OCTOBER-ARTIFACT-SECURITY.md), and [exfiltration detection](EARLY-EXFILTRATION-DETECTION.md). Their initial screening status remains recorded in the JSON. AD07, AD08 and AD11 have also advanced: [investigation and execution trust](INVESTIGATION-AND-EXECUTION-TRUST.md) and [threat-report verification](THREAT-REPORT-VERIFICATION.md). Eight of the 18 queued candidates now have targeted full-text reviews; ten remain unread or abstract-screened. AD18 remains index-only; its accessible substitute is a different paper and does not complete AD18. No paper was reproduced.
