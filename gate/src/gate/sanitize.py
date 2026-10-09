"""Build a cleaned public copy of an attachment instead of only blocking it.

PAMI's failure was publishing the whole file. Most purchase documents need to be
public; only the patient details inside them must not be. This module removes
those details from the PDF for real (the text is deleted, not covered), lists
every change, and verifies the result with the same detectors.

Wholly clinical or image-based attachments are never cleaned: a disability
certificate or a scanned ID has nothing public left once the person is removed.
"""

import re
from dataclasses import dataclass

import pymupdf

from .detect import AFFILIATE_RE, BIRTH_RE, CUIT_RE, DNI_RE, PERSON_PREFIXES, cuit_valid, mask, scan

# Findings that mean the whole attachment is clinical or identity material.
NOT_CLEANABLE = {"id_document", "disability_cert", "icd10", "model_image", "unreadable_scan",
                 "unchecked_scan", "processing_failed"}
LINE_RE = {"home_address": re.compile(r"domicilio\s*:[^\n]*", re.I),
           "birth_date": BIRTH_RE}


@dataclass
class Candidate:
    pdf: bytes
    manifest: list[dict]  # [{"page", "category", "masked"}] - never raw values
    verified: bool
    problems: list[str]
    text: str  # extracted text of the cleaned copy, safe to share with the verifier


def _spans(text: str) -> list[tuple[str, str]]:
    """Raw strings to remove, with their category. Kept in memory only."""
    spans = []
    for m in CUIT_RE.finditer(text):
        if m.group(1) in PERSON_PREFIXES and cuit_valid("".join(m.groups())):
            spans.append(("CUIL", m.group(0)))
    for m in DNI_RE.finditer(text):
        spans.append(("DNI", m.group(1)))
    for m in AFFILIATE_RE.finditer(text):
        spans.append(("affiliate number", m.group(0)))
    for category, rx in LINE_RE.items():
        for m in rx.finditer(text):
            spans.append((category.replace("_", " "), m.group(0)))
    return spans


def cleanable(findings: list[dict], decision: str) -> bool:
    """A blocked file with health findings is a clinical document: nothing public is left."""
    kinds = {f["kind"] for f in findings}
    clinical = decision == "withheld" and any(f.get("rule") == "health" for f in findings)
    return not clinical and not (kinds & NOT_CLEANABLE)


def build(pdf: bytes, findings: list[dict], phrases: list[dict] | None, decision: str) -> Candidate | None:
    """phrases: [{"text": verbatim, "category": short label}] from the context model."""
    with pymupdf.open(stream=pdf, filetype="pdf") as doc:
        if any(page.get_images() for page in doc) or not cleanable(findings, decision):
            return None
        manifest, removed = [], []
        for page in doc:
            text = page.get_text()
            targets = _spans(text)
            for p in phrases or []:
                value = str(p.get("text", "")).strip()
                if len(value) >= 3 and value in text:
                    targets.append((str(p.get("category", "context"))[:30], value))
            seen = set()
            for category, value in targets:
                if value in seen:
                    continue
                rects = page.search_for(value)
                if not rects:
                    continue
                seen.add(value)
                for rect in rects:
                    page.add_redact_annot(rect, fill=(0, 0, 0))
                manifest.append({"page": page.number + 1, "category": category, "masked": mask(value)
                                 if any(c.isdigit() for c in value) else f"{len(value)} characters"})
                removed.append(value)
            page.apply_redactions(images=pymupdf.PDF_REDACT_IMAGE_NONE)
        if not manifest:
            return None
        doc.set_metadata({})
        doc.del_xml_metadata()
        cleaned = doc.tobytes(garbage=4, deflate=True, clean=True)

    # Verify with the same detectors, on the bytes we would publish.
    check = scan(cleaned)
    text = "\n".join(p.text for p in check.pages)
    problems = [f"{f.label} still present" for f in check.findings if f.severity == "block"]
    problems += ["removed text still extractable" for v in removed if v in text]
    return Candidate(cleaned, manifest, not problems, problems, text)
