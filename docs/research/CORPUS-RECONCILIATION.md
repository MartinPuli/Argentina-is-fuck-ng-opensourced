# Corpus reconciliation and remaining reading queue

**Cutoff: 2026-10-09.** This is a metadata reconciliation, not additional paper reading or an exhaustive literature census.

The ten hash-verified historical snapshots contain **2,364 index entries**. The stated rules produce **2,362 candidate groups**, including title-only matches whose bibliographic identity is not independently established. There are **55 reviewed evidence records** in the files present at generation; **35 index groups match a reviewed record**, leaving **2,327 index groups without a matched review**. A further **20 reviewed groups** do not match these indexes under the stated rules. These are not all unread: the last category contains earlier/outside-index work and unresolved aliases.

Counts are a generated checkpoint. The JSON records its exact generation time and hashes of all review files. Concurrent later reviews require rerunning the script; they are not silently included.

## Source coverage

| Public index | Entries | Groups with matched review | Groups without matched review |
|---|---:|---:|---:|
| [USENIX Security 2026](https://www.usenix.org/conference/usenixsecurity26/technical-sessions) | 377 | 8 | 369 |
| [NDSS 2026](https://www.ndss-symposium.org/ndss2026/accepted-papers/) | 265 | 6 | 259 |
| [IEEE S&P 2026](https://sp2026.ieee-security.org/accepted-papers.html) | 254 | 2 | 252 |
| [ACM CCS 2026 accepted list](https://www.sigsac.org/ccs/CCS2026/program/accepted-papers.html) | 482 | 3 | 479 |
| [ACM CCS 2025](https://www.sigsac.org/ccs/CCS2025/assets/accepted-papers.json) | 316 | 3 | 313 |
| [RAID 2026](https://raid2026.org/data/accepted_papers.csv) | 59 | 1 | 58 |
| [ACSAC 2025](https://www.acsac.org/2025/program/papers/) | 84 | 2 | 82 |
| [AsiaCCS 2026 cycle 1](https://asiaccs2026.cse.iitkgp.ac.in/cycle-1-papers/) | 74 | 1 | 73 |
| [AsiaCCS 2026 cycle 2](https://asiaccs2026.cse.iitkgp.ac.in/cycle-2-papers/) | 48 | 2 | 46 |
| [arXiv cs.CR October 2026 snapshot](https://arxiv.org/list/cs.CR/2026-10?skip=0&show=2000) | 405 | 7 | 398 |

Per-source group counts overlap across indexes; do not sum them as globally unique papers. No publication-date eligibility is inferred from a venue label. RAID 2026 acceptance metadata precedes its October 11–14 conference, and the October arXiv snapshot is an incomplete month. First preprints, revisions, venue appearances and earlier foundations need separate date decisions.

## Reproducible rules

1. Reuse the original cached HTML/JSON/CSV only when its SHA-256 matches the discovery ledger. All ten matched. Parsing also must reproduce each historical entry count; otherwise generation stops. No live index refresh was needed.
2. Parse the selectors documented below. Keep every entry's source, title, link and row locator. Do not redistribute abstracts, author lists, papers or original index pages.
3. Group identical arXiv base IDs (retaining observed version suffixes), then explicit DOIs. Group exact normalized titles only when both components lack conflicting same-type identifiers. Normalization is Unicode NFKC, case-folding, non-alphanumeric characters to spaces, and collapsed whitespace. It does not remove subtitles, stems or version words.
4. Read only the academic evidence files linked as records in SEARCH-PROTOCOL.md, plus the concurrently assigned permission-credential-surfaces.json when present. Exclude counts_as_review:false. Vendor documentation and curated queue status never add paper reads. The 18 curated queue records can supply identity metadata bridges only.
5. Preserve every merge edge and its exact basis. Similarity suggestions for otherwise unmatched reviews remain separate and never promote reading status. No DOI lookup service, complete version search or global identity resolution was performed.

Selectors: USENIX presentation anchors inside h2; NDSS h2.pt-cv-title anchors; IEEE a[data-toggle=collapse]; CCS 2026 first td per tr; CCS 2025 firstCycle/secondCycle arrays with submission prefixes removed; RAID nonempty CSV title rows; ACSAC/AsiaCCS nonempty b titles; arXiv paired dt/dd blocks containing a list-title and /abs/ identifier. The parser accepts whitespace around href assignments. This recovers 405 arXiv identifiers: the older additional ledger's zero unique_abs_ids was a parsing artifact, not evidence that IDs were unavailable.

## Cross-index matches and unresolved aliases

- **SatBleed: Security of Commoditized Communication Modules in Satellites**: arxiv_oct26, ieeesp26. Grouped by the exact normalized title; the sources retain their own entries.
- **Stop My Dancing! Understanding, Detecting and Attributing Motion-Aware Deepfake Videos**: arxiv_oct26, ccs26. Grouped by the exact normalized title; the sources retain their own entries.
- **Unmerged:** Clouseau: A Hierarchical Multi-Agent Approach For Autonomous Attack Investigation ↔ Clouesau: A Hierarchal Multi Agent Approach For Autonomous Attack Investigation. Reason: title_similarity_only_not_merged; inspect primary identity evidence before counting them together.

## What remains unfinished

Candidate groups are a conservative catalog unit, not verified unique scientific works. Different titles can conceal the same paper; same titles can conceal different papers. Most venue entries lack arXiv/DOI identifiers in the index. A title-only match cannot establish that the reviewed preprint is textually identical to its proceedings version. An unmatched review does not mean its venue was omitted, and an index group without a match is not proof nobody reviewed a differently named version.

This pass does not read the unreviewed titles or classify their relevance. Cryptography, hardware, mobile security and other broad topics remain in the queue. All months/categories, journal coverage, correction/retraction checks, first-publication dates, complete appendices and independent reproduction remain incomplete. No national leak-prevention rate follows from these counts.

## Re-run and artifacts

[Catalog and provenance](corpus-reconciliation.json) contains entry-level metadata, groups, source hashes, review references and merge evidence. [The standard-library script](../../scripts/reconcile_paper_catalog.py) performs no network requests and executes no author code.

```sh
python3 scripts/reconcile_paper_catalog.py
```

Defaults read /tmp/breachstop-paper-review and /tmp/argentina-additional-discovery. Override with --original-cache and --additional-cache. Those temporary caches are not shipped in the repository. If missing, retrieve the public URLs in the catalog into those filenames and require matching hashes; a changed live page needs a new explicitly dated manifest rather than reuse of old counts. Saved metadata can still be regrouped and inspected without original page redistribution.
