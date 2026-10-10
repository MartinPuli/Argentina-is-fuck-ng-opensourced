"""Staff-only PDF inspection. No document text leaves these helpers."""

import hashlib
import json
from collections import Counter

import pymupdf

from .rules import RULES, SOURCES


def decoded(value, default):
    try:
        return json.loads(value) if value else default
    except (ValueError, TypeError):
        return default


def page_info(original: bytes, cleaned: bytes | None, number: int) -> dict:
    """Compare actual words at their PDF positions; never return their values.

    This is a text difference overlay, not complete image/annotation analysis.
    The PNG previews remain the actual rendered bytes, without this overlay.
    """
    with pymupdf.open(stream=original, filetype="pdf") as before:
        if number < 1 or number > len(before):
            raise IndexError("Page not found")
        page = before[number - 1]
        info = {"number": number, "total": len(before), "width": page.rect.width,
                "height": page.rect.height, "regions": [], "cleaned_page": False}
        if not cleaned:
            return info
        with pymupdf.open(stream=cleaned, filetype="pdf") as after:
            if number > len(after):
                return info
            info["cleaned_page"] = True
            def key(word):
                return (*[round(c * 2) for c in word[:4]], word[4])
            remaining = Counter(key(w) for w in after[number - 1].get_text("words"))
            lines = {}
            for word in page.get_text("words"):
                identity = key(word)
                if remaining[identity]:
                    remaining[identity] -= 1
                    continue
                # Group removed words on the same line. Only coordinates survive.
                line = word[5:7]
                rect = pymupdf.Rect(word[:4])
                if line in lines:
                    lines[line] |= rect
                else:
                    lines[line] = rect
            for rect in list(lines.values())[:1000]:
                rect = (rect * page.rotation_matrix) & page.rect
                if not rect.is_empty:
                    info["regions"].append([round(rect.x0 / page.rect.width, 5),
                                            round(rect.y0 / page.rect.height, 5),
                                            round(rect.width / page.rect.width, 5),
                                            round(rect.height / page.rect.height, 5)])
        return info


def render_page(pdf: bytes, number: int) -> bytes:
    with pymupdf.open(stream=pdf, filetype="pdf") as document:
        if number < 1 or number > len(document):
            raise IndexError("Page not found")
        page = document[number - 1]
        edge = max(page.rect.width, page.rect.height)
        if edge <= 0:
            raise ValueError("Invalid page dimensions")
        return page.get_pixmap(matrix=pymupdf.Matrix(1400 / edge, 1400 / edge),
                               colorspace=pymupdf.csRGB, alpha=False).tobytes("png")


def evidence(row, current: bool, processing: bool, job: dict | None, citation: dict | None) -> dict:
    findings = decoded(row["findings"], [])
    ids = sorted({f.get("rule") for f in findings if isinstance(f, dict) and f.get("rule") in RULES})
    policies = [{"id": rule_id, **RULES[rule_id]} for rule_id in ids]
    source_ids = {source_id for policy in policies for source_id in policy.get("source_ids", [])}
    clearance = decoded(row["clearance"], {}) or {}
    review = ((clearance.get("levels") or {}).get("public") or {}).get("review")
    verifier = decoded(row["verifier"], {}) or {}
    if review not in {"PASS", "FAIL"}:
        review = verifier.get("verdict") if verifier.get("verdict") in {"PASS", "FAIL"} else None
    visible = current and row["decision"] in {"public", "approved", "cleaned"}
    if row["decision"] == "cleaned" and not row["public_pdf"]:
        visible = False
    return {"id": row["id"], "purchase_id": row["purchase_id"], "filename": row["filename"],
            "decision": row["decision"], "current": current, "processing": processing,
            "published": visible, "original_digest": row["sha256"],
            "cleaned_digest": hashlib.sha256(row["public_pdf"]).hexdigest() if row["public_pdf"] else None,
            "has_cleaned": bool(row["public_pdf"]), "review": review,
            "manifest": [{"page": m.get("page"), "category": str(m.get("category", ""))[:80],
                          "masked": str(m.get("masked", ""))[:120]} for m in decoded(row["manifest"], [])],
            "policies": policies, "sources": [SOURCES[s] for s in sorted(source_ids)],
            "citation": citation, "steps": [{k: s.get(k) for k in ("name", "status", "agent", "duration_ms")}
                                             for s in job["steps"]] if job else [],
            "trace_available": job is not None}
