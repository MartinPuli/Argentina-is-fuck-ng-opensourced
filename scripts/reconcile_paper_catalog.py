#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Offline, standard-library reconciliation of hash-verified public index caches.

Run from any directory. This script reads metadata only and never executes paper
artifacts. Re-downloads are deliberately not automatic: replacement snapshots
require a new manifest and must not silently inherit historical counts.
"""
import argparse
import csv
import difflib
import hashlib
import html
import io
import json
import re
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin

REPO = Path(__file__).resolve().parents[1]
RESEARCH = REPO / "docs/research"
TAG = re.compile(r"<[^>]+>")


def clean(value):
    return " ".join(html.unescape(TAG.sub(" ", value)).split())


def normalized(value):
    value = unicodedata.normalize("NFKC", value).casefold()
    return " ".join("".join(c if c.isalnum() else " " for c in value).split())


def identifiers(values):
    parts = [str(x).strip() for x in values if x]
    text = " ".join(parts)
    modern_id = r"(\d{4}\.\d{4,5}(?:v\d+)?)"
    matches = re.findall(r"(?:arxiv\.org/(?:abs|html|pdf)/|\barxiv:\s*)" + modern_id + r"(?!\d)", text, re.I)
    matches += [x for x in parts if re.fullmatch(modern_id, x, re.I)]
    matches = [x.casefold() for x in matches if 1 <= int(x[2:4]) <= 12]
    arxiv = sorted({re.sub(r"v\d+$", "", x) for x in matches})
    versions = sorted({x for x in matches if re.search(r"v\d+$", x)})
    dois = sorted(set(x.rstrip(".,;)").casefold() for x in re.findall(r"10\.\d{4,9}/[^\s\"<>?#]+", text)))
    return {"arxiv": arxiv, "doi": dois, "arxiv_versions": versions}


def conflicting_identifiers(left, right):
    conflicts = []
    for kind in ("arxiv", "doi"):
        a = {v for e in left for v in e["ids"][kind]}
        b = {v for e in right for v in e["ids"][kind]}
        if a and b and a.isdisjoint(b):
            conflicts.append(kind)
    return conflicts


def self_check():
    assert identifiers(["https://doi.org/10.1109/ACSAC67867.2025.00051"])["arxiv"] == []
    assert identifiers(["10.1109/TEST.2026.12345"])["arxiv"] == []
    x = identifiers(["https://arxiv.org/abs/2507.06252v1", "2507.06252v2"])
    assert x["arxiv"] == ["2507.06252"]
    assert x["arxiv_versions"] == ["2507.06252v1", "2507.06252v2"]
    assert identifiers(["arXiv:2610.10612v1"])["arxiv"] == ["2610.10612"]
    assert identifiers(["arXiv:2625.10612v1"])["arxiv"] == []
    assert identifiers(["https://example.org/papers/2610.10612v1"])["arxiv"] == []
    a = {"ids": identifiers(["arXiv:2610.10612v1"])}
    b = {"ids": identifiers(["arXiv:2610.10613v1"])}
    c = {"ids": identifiers(["arXiv:2610.10612v2"])}
    assert conflicting_identifiers([a], [b]) == ["arxiv"]
    assert conflicting_identifiers([a], [c]) == []
    assert conflicting_identifiers([a], [{"ids": identifiers([])}]) == []
    assert normalized("Paper—Title: A") == normalized("paper-title: a")
    assert normalized("Paper: A") != normalized("Paper: B")


def anchor(fragment, base):
    m = re.search(r'<a\b[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', fragment, re.S | re.I)
    return (clean(m[2]), urljoin(base, html.unescape(m[1]))) if m else (clean(fragment), base)


def extract(source_id, data, url):
    text = data.decode("utf-8-sig")
    rows = []
    if source_id == "ccs25data":
        obj = json.loads(text)
        for cycle in ("firstCycle", "secondCycle"):
            for item in obj[cycle]:
                rows.append((re.sub(r"^\(#\d+\)\s*", "", item["title"]), item.get("url", url), cycle))
    elif source_id == "raid26csv":
        rows = [(r["title"], url, "csv-id:" + r["id"]) for r in csv.DictReader(io.StringIO(text)) if r.get("title", "").strip()]
    elif source_id == "arxiv_oct26":
        for block in re.findall(r"<dt\b[^>]*>.*?</dd>", text, re.S | re.I):
            title = re.search(r'<div\b[^>]*class=["\'][^"\']*list-title[^"\']*["\'][^>]*>(.*?)</div>', block, re.S)
            aid = re.search(r'href\s*=\s*["\'](?:https://arxiv.org)?/abs/(\d{4}\.\d{4,5}(?:v\d+)?)["\']', block)
            if title and aid:
                rows.append((re.sub(r"^Title:\s*", "", clean(title[1])), "https://arxiv.org/abs/" + aid[1], aid[1]))
    elif source_id in ("acsac25", "asiaccs26c1", "asiaccs26c2"):
        rows = [(clean(b), url, "b:" + str(i)) for i, b in enumerate(re.findall(r"<b\b[^>]*>(.*?)</b>", text, re.S | re.I)) if clean(b)]
    elif source_id == "ccs26":
        for i, row in enumerate(re.findall(r"<tr\b[^>]*>(.*?)</tr>", text, re.S | re.I)):
            td = re.search(r"<td\b[^>]*>(.*?)</td>", row, re.S | re.I)
            if td:
                title, link = anchor(td[1], url)
                rows.append((title, link, "tr:" + str(i)))
    elif source_id == "ieeesp26":
        for i, a in enumerate(re.findall(r"<a\b[^>]*>.*?</a>", text, re.S | re.I)):
            if re.search(r'data-toggle=["\']collapse["\']', a):
                title, link = anchor(a, url)
                rows.append((title, link, "collapse-anchor:" + str(i)))
    else:
        for i, h in enumerate(re.findall(r"<h2\b[^>]*>.*?</h2>", text, re.S | re.I)):
            if source_id == "usenix26" and "/presentation/" not in h:
                continue
            if source_id == "ndss26" and "pt-cv-title" not in h:
                continue
            title, link = anchor(h, url)
            rows.append((title, link, "h2:" + str(i)))
    return [{"title": clean(t), "url": u, "locator": l} for t, u, l in rows if clean(t)]


def main():
    self_check()
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--original-cache", type=Path, default=Path("/tmp/breachstop-paper-review"))
    ap.add_argument("--additional-cache", type=Path, default=Path("/tmp/argentina-additional-discovery"))
    ap.add_argument("--output", type=Path, default=RESEARCH / "corpus-reconciliation.json")
    ap.add_argument("--markdown-output", type=Path, default=RESEARCH / "CORPUS-RECONCILIATION.md")
    args = ap.parse_args()
    old_bytes = (RESEARCH / "search-coverage.json").read_bytes()
    additional_bytes = (RESEARCH / "additional-discovery.json").read_bytes()
    old = json.loads(old_bytes)
    additional = json.loads(additional_bytes)
    manifests = []
    for sid, s in zip(("usenix26", "ndss26", "ieeesp26", "ccs26"), old["sources"]):
        manifests.append({"id": sid, "name": s["venue"], "url": s["url"], "expected_sha256": s["sha256_html_snapshot"], "old_count": s["parsed_entries"], "cache": args.original_cache / (sid + ".html"), "snapshot_date": old["review_date"], "ledger": "search-coverage.json"})
    for s in additional["sources"]:
        ext = ".json" if s["id"] == "ccs25data" else ".txt" if s["id"] == "raid26csv" else ".html"
        manifests.append({"id": s["id"], "name": s["name"], "url": s["snapshot"]["url"], "expected_sha256": s["snapshot"]["sha256"], "old_count": s["parsed_title_entries"], "cache": args.additional_cache / (s["id"] + ext), "snapshot_date": s["retrieved_on"], "ledger": "additional-discovery.json"})
    entries, snapshots = [], []
    for m in manifests:
        data = m["cache"].read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        if digest != m["expected_sha256"]:
            raise SystemExit("Snapshot mismatch; refusing historical-count substitution: " + m["id"])
        rows = extract(m["id"], data, m["url"])
        if len(rows) != m["old_count"]:
            raise SystemExit("Selector/count mismatch in verified snapshot: " + m["id"])
        snaps = {k: v for k, v in m.items() if k not in ("cache", "expected_sha256")}
        snaps.update(sha256=digest, bytes=len(data), historical_hash_verified=True, parsed_raw_rows=len(rows), parsed_exact_titles=len(set(r["title"] for r in rows)), parsed_normalized_titles=len(set(normalized(r["title"]) for r in rows)))
        snapshots.append(snaps)
        for i, r in enumerate(rows):
            entries.append({"entry_id": m["id"] + ":" + str(i), "kind": "index", "source": m["id"], **r, "ids": identifiers([r["url"]])})

    review_files, excluded = [], []
    protocol = (RESEARCH / "SEARCH-PROTOCOL.md").read_text()
    review_names = set(re.findall(r"\[records\]\(([^)]+\.json)\)", protocol))
    # A concurrent, explicitly assigned paper-review lane may precede its protocol link.
    review_names.add("permission-credential-surfaces.json")
    for path in sorted(RESEARCH.glob("*.json")):
        if path.name not in review_names:
            continue
        review_bytes = path.read_bytes()
        obj = json.loads(review_bytes)
        if not isinstance(obj, dict):
            continue
        row_key = "records" if "records" in obj else "papers"
        rows = obj.get(row_key, [])
        if not isinstance(rows, list) or not any(isinstance(r, dict) and "title" in r for r in rows):
            continue
        included = 0
        for i, r in enumerate(rows):
            if r.get("counts_as_review") is False:
                excluded.append({"file": path.name, "record": r.get("id", i), "title": r.get("title"), "reason": "counts_as_review:false"})
                continue
            if "title" not in r:
                continue
            # Identity fields only: never harvest identifiers cited inside findings.
            fields = [v for k, v in r.items() if k == "doi" or "url" in k or "version" in k or k in ("preprint", "arxiv_id")]
            ids = identifiers([json.dumps(x) if isinstance(x, (dict, list)) else x for x in fields])
            urls = [v for k, v in r.items() if "url" in k and isinstance(v, str) and v.startswith("http")]
            entries.append({"entry_id": path.name + ":" + str(i), "kind": "review", "source": path.name, "record_id": r.get("id", i), "title": r["title"], "url": urls[0] if urls else None, "locator": "/" + row_key + "/" + str(i), "ids": ids, "reading_depth": r.get("reading_status", r.get("reading_depth", r.get("readingdepth", "targeted_fulltext_per_review_ledger")))})
            included += 1
        review_files.append({"file": path.name, "sha256": hashlib.sha256(review_bytes).hexdigest(), "included_records": included})

    # The curated discovery queue provides metadata bridges, not new paper reads.
    for i, r in enumerate(additional["candidates"]):
        values = [v for k, v in r.items() if "url" in k or "link" in k or k == "version"]
        entries.append({"entry_id": "queue:" + r["id"], "kind": "queue_metadata", "source": "additional-discovery.json", "record_id": r["id"], "title": r["title"], "url": r.get("canonical_primary_url"), "locator": "/candidates/" + str(i), "ids": identifiers(values)})

    parent = list(range(len(entries)))
    def root(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    evidence, uncertain = [], []
    for kind in ("arxiv", "doi", "title"):
        seen = {}
        for i, entry in enumerate(entries):
            keys = [normalized(entry["title"])] if kind == "title" else entry["ids"][kind]
            for key in keys:
                if key not in seen:
                    seen[key] = i
                    continue
                a, b = root(i), root(seen[key])
                if a == b:
                    continue
                if kind == "title":
                    members_a = [e for j, e in enumerate(entries) if root(j) == a]
                    members_b = [e for j, e in enumerate(entries) if root(j) == b]
                    conflicts = conflicting_identifiers(members_a, members_b)
                    if conflicts:
                        uncertain.append({"entries": [entry["entry_id"], entries[seen[key]]["entry_id"]], "reason": "same_normalized_title_conflicting_identifiers", "conflicts": conflicts})
                        continue
                parent[a] = b
                evidence.append({"entries": [entry["entry_id"], entries[seen[key]]["entry_id"]], "basis": kind, "key": key})

    components = defaultdict(list)
    for i in range(len(entries)):
        components[root(i)].append(i)
    groups = []
    index_to_group = {}
    for indices in components.values():
        members = [entries[i] for i in indices]
        gid = "C-" + hashlib.sha256("\n".join(sorted(e["entry_id"] for e in members)).encode()).hexdigest()[:12]
        for i in indices:
            index_to_group[i] = gid
        groups.append({"group_id": gid, "title": members[0]["title"], "index_sources": sorted({e["source"] for e in members if e["kind"] == "index"}), "review_refs": [e["entry_id"] for e in members if e["kind"] == "review"], "entry_refs": [e["entry_id"] for e in members], "arxiv_ids": sorted({v for e in members for v in e["ids"]["arxiv"]}), "dois": sorted({v for e in members for v in e["ids"]["doi"]}), "title_variants": sorted({e["title"] for e in members})})

    # Similar names are suggestions only. They never merge or promote read status.
    index_rows = [(i, e, normalized(e["title"])) for i, e in enumerate(entries) if e["kind"] == "index"]
    for i, e in enumerate(entries):
        if e["kind"] != "review" or any(g["group_id"] == index_to_group[i] and g["index_sources"] for g in groups):
            continue
        title = normalized(e["title"])
        matches = []
        for j, candidate, other in index_rows:
            overlap = len(set(title.split()) & set(other.split())) / max(1, min(len(set(title.split())), len(set(other.split()))))
            if overlap < 0.55:
                continue
            score = difflib.SequenceMatcher(None, title, other).ratio()
            if score >= 0.80:
                matches.append((score, candidate["entry_id"]))
        for score, ref in sorted(matches, reverse=True)[:3]:
            uncertain.append({"entries": [e["entry_id"], ref], "reason": "title_similarity_only_not_merged", "similarity": round(score, 4)})

    index_groups = [g for g in groups if g["index_sources"]]
    reviewed_groups = [g for g in groups if g["review_refs"]]
    matched = [g for g in index_groups if g["review_refs"]]
    summary = {"index_raw_entries": sum(e["kind"] == "index" for e in entries), "historical_ledger_entries": old["entries"] + additional["parsed_additional_title_entries"], "index_candidate_groups": len(index_groups), "review_records": sum(e["kind"] == "review" for e in entries), "reviewed_groups": len(reviewed_groups), "index_groups_with_review": len(matched), "index_groups_without_review": len(index_groups) - len(matched), "reviewed_groups_not_matched_to_indexes": len(reviewed_groups) - len(matched), "all_groups_including_queue_and_review_only": len(groups), "uncertain_aliases": len(uncertain), "merge_basis_counts": dict(Counter(e["basis"] for e in evidence))}
    summary["index_entries_with_explicit_arxiv_or_doi"] = sum(e["kind"] == "index" and bool(e["ids"]["arxiv"] or e["ids"]["doi"]) for e in entries)
    summary["index_unique_arxiv_ids"] = len({v for e in entries if e["kind"] == "index" for v in e["ids"]["arxiv"]})
    summary["index_unique_dois"] = len({v for e in entries if e["kind"] == "index" for v in e["ids"]["doi"]})
    per_source = []
    for s in snapshots:
        sg = [g for g in index_groups if s["id"] in g["index_sources"]]
        per_source.append({"id": s["id"], "raw_entries": s["parsed_raw_rows"], "candidate_groups": len(sg), "groups_with_review": sum(bool(g["review_refs"]) for g in sg), "groups_without_review": sum(not g["review_refs"] for g in sg)})
    output = {"schema_version": 1, "generated_at_utc": datetime.now(timezone.utc).isoformat(), "cutoff": "2026-10-09", "exhaustive": False, "global_doi_resolution_completed": False, "summary": summary, "rules": {"strong": "Same arXiv base ID or explicit DOI; version suffix retained separately.", "weak": "NFKC/casefold/alphanumeric normalized exact title, unless both groups carry conflicting same-type identifiers.", "not_merged": "Fuzzy title matches; different IDs without a shared identity key.", "review_status": "Only records in review evidence files count; curated queue metadata never adds reads.", "date_scope": "Index inclusion does not establish first publication inside window; venue dates, preprints and revisions remain distinct.", "snapshot_policy": "Original byte-identical hash-verified caches; no network refresh."}, "snapshots": snapshots, "review_file_snapshots": review_files, "excluded_review_records": excluded, "per_source": per_source, "merge_evidence": evidence, "uncertain_aliases": uncertain, "groups": groups, "entries": entries}
    output["input_manifest_hashes"] = {"search-coverage.json": hashlib.sha256(old_bytes).hexdigest(), "additional-discovery.json": hashlib.sha256(additional_bytes).hexdigest(), "SEARCH-PROTOCOL.md": hashlib.sha256(protocol.encode()).hexdigest()}
    output["parser_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n")
    lines = [
        "# Corpus reconciliation and remaining reading queue",
        "",
        "**Cutoff: 2026-10-09.** This is a metadata reconciliation, not additional paper reading or an exhaustive literature census.",
        "",
        f"The ten hash-verified historical snapshots contain **{summary['index_raw_entries']:,} index entries**. The stated rules produce **{summary['index_candidate_groups']:,} candidate groups**, including title-only matches whose bibliographic identity is not independently established. There are **{summary['review_records']} reviewed evidence records** in the files present at generation; **{summary['index_groups_with_review']} index groups match a reviewed record**, leaving **{summary['index_groups_without_review']:,} index groups without a matched review**. A further **{summary['reviewed_groups_not_matched_to_indexes']} reviewed groups** do not match these indexes under the stated rules. These are not all unread: the last category contains earlier/outside-index work and unresolved aliases.",
        "",
        "Counts are a generated checkpoint. The JSON records its exact generation time and hashes of all review files. Concurrent later reviews require rerunning the script; they are not silently included.",
        "",
        "## Source coverage",
        "",
        "| Public index | Entries | Groups with matched review | Groups without matched review |",
        "|---|---:|---:|---:|",
    ]
    for s, counts in zip(snapshots, per_source):
        lines.append(f"| [{s['name']}]({s['url']}) | {counts['raw_entries']} | {counts['groups_with_review']} | {counts['groups_without_review']} |")
    lines += [
        "",
        "Per-source group counts overlap across indexes; do not sum them as globally unique papers. No publication-date eligibility is inferred from a venue label. RAID 2026 acceptance metadata precedes its October 11–14 conference, and the October arXiv snapshot is an incomplete month. First preprints, revisions, venue appearances and earlier foundations need separate date decisions.",
        "",
        "## Reproducible rules",
        "",
        "1. Reuse the original cached HTML/JSON/CSV only when its SHA-256 matches the discovery ledger. All ten matched. Parsing also must reproduce each historical entry count; otherwise generation stops. No live index refresh was needed.",
        "2. Parse the selectors documented below. Keep every entry's source, title, link and row locator. Do not redistribute abstracts, author lists, papers or original index pages.",
        "3. Group identical arXiv base IDs (retaining observed version suffixes), then explicit DOIs. Group exact normalized titles only when both components lack conflicting same-type identifiers. Normalization is Unicode NFKC, case-folding, non-alphanumeric characters to spaces, and collapsed whitespace. It does not remove subtitles, stems or version words.",
        "4. Read only the academic evidence files linked as records in SEARCH-PROTOCOL.md, plus the concurrently assigned permission-credential-surfaces.json when present. Exclude counts_as_review:false. Vendor documentation and curated queue status never add paper reads. The 18 curated queue records can supply identity metadata bridges only.",
        "5. Preserve every merge edge and its exact basis. Similarity suggestions for otherwise unmatched reviews remain separate and never promote reading status. No DOI lookup service, complete version search or global identity resolution was performed.",
        "",
        "Selectors: USENIX presentation anchors inside h2; NDSS h2.pt-cv-title anchors; IEEE a[data-toggle=collapse]; CCS 2026 first td per tr; CCS 2025 firstCycle/secondCycle arrays with submission prefixes removed; RAID nonempty CSV title rows; ACSAC/AsiaCCS nonempty b titles; arXiv paired dt/dd blocks containing a list-title and /abs/ identifier. The parser accepts whitespace around href assignments. This recovers 405 arXiv identifiers: the older additional ledger's zero unique_abs_ids was a parsing artifact, not evidence that IDs were unavailable.",
        "",
        "## Cross-index matches and unresolved aliases",
        "",
    ]
    for g in index_groups:
        if len(g["index_sources"]) > 1:
            lines.append(f"- **{g['title']}**: {', '.join(g['index_sources'])}. Grouped by the exact normalized title; the sources retain their own entries.")
    by_ref = {e["entry_id"]: e for e in entries}
    for a in uncertain:
        left, right = (by_ref[ref] for ref in a["entries"])
        lines.append(f"- **Unmerged:** {left['title']} ↔ {right['title']}. Reason: {a['reason']}; inspect primary identity evidence before counting them together.")
    lines += [
        "",
        "## What remains unfinished",
        "",
        "Candidate groups are a conservative catalog unit, not verified unique scientific works. Different titles can conceal the same paper; same titles can conceal different papers. Most venue entries lack arXiv/DOI identifiers in the index. A title-only match cannot establish that the reviewed preprint is textually identical to its proceedings version. An unmatched review does not mean its venue was omitted, and an index group without a match is not proof nobody reviewed a differently named version.",
        "",
        "This pass does not read the unreviewed titles or classify their relevance. Cryptography, hardware, mobile security and other broad topics remain in the queue. All months/categories, journal coverage, correction/retraction checks, first-publication dates, complete appendices and independent reproduction remain incomplete. No national leak-prevention rate follows from these counts.",
        "",
        "## Re-run and artifacts",
        "",
        "[Catalog and provenance](corpus-reconciliation.json) contains entry-level metadata, groups, source hashes, review references and merge evidence. [The standard-library script](../../scripts/reconcile_paper_catalog.py) performs no network requests and executes no author code.",
        "",
        "```sh",
        "python3 scripts/reconcile_paper_catalog.py",
        "```",
        "",
        "Defaults read /tmp/breachstop-paper-review and /tmp/argentina-additional-discovery. Override with --original-cache and --additional-cache. Those temporary caches are not shipped in the repository. If missing, retrieve the public URLs in the catalog into those filenames and require matching hashes; a changed live page needs a new explicitly dated manifest rather than reuse of old counts. Saved metadata can still be regrouped and inspected without original page redistribution.",
        "",
    ]
    args.markdown_output.write_text("\n".join(lines))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
