# Research coverage and unfinished work

**Cutoff:** October 9, 2026. **Primary window:** October 9, 2025–October 9, 2026, following the Argentina report's window. Include earlier foundations separately and distinguish a first preprint from a later venue publication or revision.

The user requested every new cybersecurity paper. This review has **not** achieved that breadth. The search currently has two tracks: broad discovery across major venue lists and prioritized full-text reading of studies that can change our data-leak defense design. Prioritization is an order of work, not a declaration that unread topics have been completed or removed from the objective.

## Observed discovery coverage

Four public venue indexes were retrieved on October 9. A local parser extracted title/link entries, deduplicated within each venue, and applied case-insensitive keyword matching. It produced the following counts:

| Index | Parsed title entries |
|---|---:|
| [USENIX Security 2026 technical sessions](https://www.usenix.org/conference/usenixsecurity26/technical-sessions) | 377 |
| [NDSS 2026 accepted papers](https://www.ndss-symposium.org/ndss2026/accepted-papers/) | 265 |
| [IEEE S&P 2026 accepted papers](https://sp2026.ieee-security.org/accepted-papers.html) | 254 |
| [ACM CCS 2026 accepted list](https://www.sigsac.org/ccs/CCS2026/program/accepted-papers.html) | 482 |
| **Total parsed entries** | **1,378** |

**177 entries matched the initial keyword filter.** Neither count is a full-text reading count or a verified census of new papers. A program can contain retrospective presentations; an accepted list does not establish availability of its papers; versions and titles can change. Exact title strings were unique in this extraction, but no global DOI-based deduplication has been completed.

[search-coverage.json](search-coverage.json) records source URLs, snapshot hashes, sizes, counts and the filter. Public HTML was cached temporarily outside the repository; no full venue pages or paper texts are redistributed here. A hash identifies the retrieved snapshot but cannot reconstruct it, and the live indexes may change.

## Repeating the title pass

1. Download the four linked indexes into separate UTF-8 files and record their SHA-256 hashes and retrieval date.
2. For USENIX, extract title anchors inside `h2` elements whose link contains `/presentation/`. For NDSS, use `h2.pt-cv-title` anchors. For IEEE, use title anchors with `data-toggle="collapse"`. For CCS, use the first `td` in each table row, excluding headings. These selectors reflect the retrieved pages and may need adjustment if their markup changes.
3. Decode HTML entities, remove remaining tags, collapse whitespace and deduplicate `(venue, title)` pairs. Preserve the paper URL when available; otherwise preserve its index URL.
4. Match the explicit keyword list in the JSON. This is title triage, not semantic eligibility judgment. It misses papers that use different language and can admit irrelevant matches such as a non-security meaning of “agent.”
5. Resolve each promising title to primary full text and record status as `index_only`, `abstract_screened`, `fulltext_targeted`, `fulltext_complete`, or `reproduced`. Do not promote a record because an abstract sounds relevant.

## Full-text extraction contract

Each reviewed paper must identify title, canonical primary link, version, dates, publication status, relevant sections, method, what the metric actually measures, important limitations and the resulting implementation decision. Numerical claims need their table/section, denominator, configuration and applicable uncertainty. A paper's claimed mechanism and our design inference must remain distinct.

The current reviews use **targeted full-text reading**: relevant methods, evaluation definitions, results and limitations. They do not claim that all appendices were read or experiments reproduced. Read counts are the number of reviewed paper records in the evidence files, excluding records explicitly marked `counts_as_review: false`; they are not search hits. Those files are:

- [Autonomous defense and repair](AUTONOMOUS-DEFENSE-PAPERS.md) / [records](defense-papers.json).
- [Agent safety](AGENT-SAFETY-PAPERS.md) / [records](agent-safety-papers.json).
- [Learning from incidents](LEAK-LEARNING-PAPERS.md) / [records](leak-learning-papers.json).
- [Threat intelligence and evidence integrity](THREAT-INTELLIGENCE-PAPERS.md) / [records](threat-intelligence-papers.json).
- [Access control and exposure](ACCESS-AND-EXPOSURE-PAPERS.md) / [records](access-exposure-papers.json).
- [October agent reliability](OCTOBER-AGENT-RELIABILITY.md) / [records](october-agent-reliability.json).
- [October artifact security](OCTOBER-ARTIFACT-SECURITY.md) / [records](october-artifact-security.json).
- [Early exfiltration detection](EARLY-EXFILTRATION-DETECTION.md) / [records](early-exfiltration-detection.json).
- [Investigation and execution trust](INVESTIGATION-AND-EXECUTION-TRUST.md) / [records](investigation-execution-trust.json).
- [Threat-report verification](THREAT-REPORT-VERIFICATION.md) / [records](threat-report-verification.json).
- [Detection and response evaluation](DETECTION-AND-RESPONSE-EVALUATION.md) / [records](detection-response-evaluation.json).
- [Permission and credential surfaces](PERMISSION-AND-CREDENTIAL-SURFACES.md) / [records](permission-credential-surfaces.json).
- [Revocation and recovery](REVOCATION-AND-RECOVERY-RESEARCH.md) / [records](revocation-recovery-research.json).

This checkpoint contains **49 selected paper reviews across thirteen evidence files**, counted directly from the files with `counts_as_review: false` excluded. The three excluded metadata-only records are AD18, PCS-01/AD14 and PCS-02/AD12. The five additions after the earlier 44-record checkpoint are AD09, AD15, AD16, the separate TLBAC substitute and RRR-01 on revocation for long-running agents. These reviews include earlier foundations and later revisions/publication milestones; 49 does not mean 49 newly submitted papers inside the window. Reading-depth limitations remain, and these additions were not experimentally reproduced.

## Additional discovery and implementation research

The [additional discovery pass](ADDITIONAL-DISCOVERY.md) records 986 further title entries and 175 keyword matches across CCS 2025, RAID 2026, ACSAC 2025, AsiaCCS 2026 and an October arXiv snapshot. The original discovery pass prioritized 18 candidates without reading their full text. Eleven of those candidates (AD01–AD05, AD07–AD09, AD11, AD15 and AD16) were subsequently reviewed; their current status, initial screening status and evidence links are recorded. AD06, AD10, AD12, AD13, AD14, AD17 and AD18 remain unread or abstract-screened. AD12, AD14 and AD18 are not completed by reviews of different accessible substitutes. The insider-threat, GIDS-Eval and NDSS response-planning studies were also reviewed outside that queue. The two historical index-entry totals are retained as discovery counts and must not be added to paper-reading counts. The reconciliation below supplies a separate, explicitly limited grouping count. RAID's event occurs after the cutoff; public acceptance metadata is distinguished from a paper's first publication.

The [country precedents](COUNTRY-PRECEDENTS.md), [competitor profiles](../../competitor-profiles/_summary.md) and [sandbox documentation review](SANDBOX-ARCHITECTURE.md) are implementation research. Government statements and vendor documentation are not additional academic papers or independent product benchmarks.

## Conservative corpus reconciliation

The [reconciliation report](CORPUS-RECONCILIATION.md), [catalog](corpus-reconciliation.json) and [parser](../../scripts/reconcile_paper_catalog.py) recovered all **2,364 historical entries from ten byte-identical, hash-verified snapshots**. Under exact arXiv-base-ID/DOI and normalized-title rules, they form **2,362 index candidate groups**. Only 721 entries expose an explicit arXiv ID or DOI in the parsed metadata; this is not complete global identity resolution.

At the current saved checkpoint, **49 reviewed records match 29 index groups**; **2,333 index groups have no matched review**, and **20 reviewed groups** are outside these indexes or unmatched under the rules. The catalog records its exact generation time and input-file hashes. One Clouseau spelling alias remains unmerged. These counts describe the saved catalog, not a claim that every unmatched group is a distinct unread paper. Further reviews require regenerated matching counts; do not overwrite the historical snapshot totals.

The two cross-index exact-title matches are SatBleed and Stop My Dancing. Version suffixes, source entries and merge evidence remain available. The arXiv selector now accepts whitespace around `href`, recovering 405 unique abstract IDs from the same original October snapshot; the old zero-ID field was a parser artifact, not an absent-ID count. No paper gained a full-text review merely through reconciliation.

## What remains incomplete

- Full-text review of the remaining venue entries, including the unselected keyword matches and entries missed by the filter.
- Comprehensive discovery of late-2025 publications, journals, workshops, other security venues and preprints. Some additional indexes and an October arXiv snapshot are now recorded, but a complete monthly/category corpus has not been reconciled.
- Resolve remaining preprint/proceedings aliases beyond the conservative grouping, perform retraction/correction checks, and make an exact first-date/version decision for every candidate.
- Full appendices, artifact reproduction, and studies outside the current priority lanes. Cryptography, hardware security, mobile security and other areas remain part of the broad request and have not been exhaustively reviewed.
- Complete backward/forward citation search and independent reproduction of the papers' numerical claims.
- Validation on an actual institution's authorized environment. Neither literature results nor our synthetic experiment establish a national prevention rate.

The coverage ledger should expand as those tasks are completed. Do not replace this list with an “all research reviewed” label merely because the immediate prototype has enough design evidence.
