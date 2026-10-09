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

The current reviews use **targeted full-text reading**: relevant methods, evaluation definitions, results and limitations. They do not claim that all appendices were read or experiments reproduced. Read counts are the number of records in the individual evidence files, not search hits. Those files are:

- [Autonomous defense and repair](AUTONOMOUS-DEFENSE-PAPERS.md) / [records](defense-papers.json).
- [Agent safety](AGENT-SAFETY-PAPERS.md) / [records](agent-safety-papers.json).
- [Learning from incidents](LEAK-LEARNING-PAPERS.md) / [records](leak-learning-papers.json).
- [Threat intelligence and evidence integrity](THREAT-INTELLIGENCE-PAPERS.md) / [records](threat-intelligence-papers.json).
- [Access control and exposure](ACCESS-AND-EXPOSURE-PAPERS.md) / [records](access-exposure-papers.json).
- [October agent reliability](OCTOBER-AGENT-RELIABILITY.md) / [records](october-agent-reliability.json).
- [October artifact security](OCTOBER-ARTIFACT-SECURITY.md) / [records](october-artifact-security.json).
- [Early exfiltration detection](EARLY-EXFILTRATION-DETECTION.md) / [records](early-exfiltration-detection.json).

This checkpoint contains **38 selected paper records** across eight files: the previous 32 plus two October agent-reliability, two artifact-security and two exfiltration-detection reviews. They include explicitly labeled earlier foundations and later publication milestones, so 38 does not mean 38 newly submitted papers inside the window. Reading-depth limitations appear in each file; none of these six additions was experimentally reproduced.

## Additional discovery and implementation research

The [additional discovery pass](ADDITIONAL-DISCOVERY.md) records 986 further title entries and 175 keyword matches across CCS 2025, RAID 2026, ACSAC 2025, AsiaCCS 2026 and an October arXiv snapshot. The original discovery pass prioritized 18 candidates without reading their full text. Five of those candidates (AD01–AD05) were subsequently reviewed; their current status and review links are now recorded. The separate insider-threat paper adds the sixth new review. These counts are not globally deduplicated and must not be added to paper-reading counts. RAID's event occurs after the cutoff; public acceptance metadata is distinguished from a paper's first publication.

The [country precedents](COUNTRY-PRECEDENTS.md), [competitor profiles](../../competitor-profiles/_summary.md) and [sandbox documentation review](SANDBOX-ARCHITECTURE.md) are implementation research. Government statements and vendor documentation are not additional academic papers or independent product benchmarks.

## What remains incomplete

- Full-text review of the remaining venue entries, including the unselected keyword matches and entries missed by the filter.
- Comprehensive discovery of late-2025 publications, journals, workshops, other security venues and preprints. Some additional indexes and an October arXiv snapshot are now recorded, but a complete monthly/category corpus has not been reconciled.
- Global deduplication across preprints and proceedings, retraction/correction checks, and an exact date decision for every candidate.
- Full appendices, artifact reproduction, and studies outside the current priority lanes. Cryptography, hardware security, mobile security and other areas remain part of the broad request and have not been exhaustively reviewed.
- Complete backward/forward citation search and independent reproduction of the papers' numerical claims.
- Validation on an actual institution's authorized environment. Neither literature results nor our synthetic experiment establish a national prevention rate.

The coverage ledger should expand as those tasks are completed. Do not replace this list with an “all research reviewed” label merely because the immediate prototype has enough design evidence.
