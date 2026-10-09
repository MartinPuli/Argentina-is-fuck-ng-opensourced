"""Read an attachment and find what must not reach the public site.

Two layers. Deterministic checks catch structured identifiers (DNI, CUIL,
affiliate numbers) with no model involved. The model layer (see llm.py) reads
context: a diagnosis without a name, or a page that identifies someone by age,
town and condition.
"""

import io
import os
import re
from dataclasses import dataclass, field

import pymupdf
import pytesseract
from PIL import Image

# The system Tesseract may lack Spanish data; use the per-user copy when it exists.
_USER_TESSDATA = os.path.expanduser("~/.local/share/tessdata")
if os.path.isfile(os.path.join(_USER_TESSDATA, "spa.traineddata")):
    os.environ.setdefault("TESSDATA_PREFIX", _USER_TESSDATA)

MIN_TEXT_CHARS = 25  # sparse text also requires rendered-page analysis
MAX_RENDER_PIXELS = 20_000_000


@dataclass
class Page:
    number: int
    text: str
    source: str  # "text", "ocr", or "text+ocr"
    image: bytes = b""  # rendered page for the vision check
    has_images: bool = False
    coverage_issues: list[str] = field(default_factory=list)


@dataclass
class Finding:
    kind: str  # e.g. "person_cuil", "dni", "health_term"
    label: str  # human description
    evidence: str  # masked snippet, never the raw value
    page: int
    severity: str  # "block" | "review" | "info"
    rule: str  # rule id in rules.py


@dataclass
class Scan:
    pages: list[Page]
    findings: list[Finding] = field(default_factory=list)
    ocr_used: bool = False
    coverage_issues: list[str] = field(default_factory=list)


def extract(pdf: bytes) -> list[Page]:
    pages = []
    with pymupdf.open(stream=pdf, filetype="pdf") as doc:
        for i, page in enumerate(doc, start=1):
            issues: list[str] = []
            try:
                text = page.get_text().strip()
            except Exception:
                text = ""
                issues.append("text_extraction_failed")
            try:
                # Includes inline images actually displayed on the page.
                has_images = bool(page.get_image_info())
            except Exception:
                has_images = True
                issues.append("image_inventory_failed")
            if len(text) >= MIN_TEXT_CHARS and not has_images:
                pages.append(Page(i, text, "text", coverage_issues=issues))
                continue
            source = "text+ocr" if len(text) >= MIN_TEXT_CHARS else "ocr"
            png = b""
            try:
                if page.rect.width * page.rect.height * (150 / 72) ** 2 > MAX_RENDER_PIXELS:
                    issues.append("page_render_limit")
                else:
                    png = page.get_pixmap(dpi=150).tobytes("png")
            except Exception:
                issues.append("page_render_failed")
            if png:
                try:
                    with Image.open(io.BytesIO(png)) as image:
                        ocr = pytesseract.image_to_string(image, lang="spa", timeout=20)
                    if not isinstance(ocr, str):
                        raise ValueError("invalid OCR result")
                    text = (text + "\n" + ocr).strip()
                except Exception:
                    # No exception messages: they may contain document contents.
                    issues.append("ocr_failed")
            pages.append(Page(i, text, source, png, has_images, issues))
    return pages


def mask(value: str) -> str:
    """Keep the shape, hide the middle: 31.846.275 -> 31.***.275"""
    digits = [i for i, c in enumerate(value) if c.isdigit()]
    if len(digits) <= 4:
        return "*" * len(value)
    hide = set(digits[2:-3])
    return "".join("*" if i in hide else c for i, c in enumerate(value))


def cuit_valid(digits: str) -> bool:
    weights = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2]
    check = 11 - sum(int(d) * w for d, w in zip(digits[:10], weights)) % 11
    check = {11: 0, 10: 9}.get(check, check)
    return check == int(digits[10])


PERSON_PREFIXES = {"20", "23", "24", "27"}  # individuals
COMPANY_PREFIXES = {"30", "33", "34"}  # legal entities; not a blanket disclosure authorization

CUIT_RE = re.compile(r"\b(\d{2})-?(\d{8})-?(\d)\b")
DNI_RE = re.compile(r"(?:\bDNI|D\.N\.I\.?|\bdocumento)[^\d\n]{0,15}(\d{1,2}\.?\d{3}\.?\d{3})\b", re.I)
AFFILIATE_RE = re.compile(r"\b\d{12}/\d{2}\b")
BIRTH_RE = re.compile(r"nacimiento[:\s]+[\w ]{0,4}\d{1,2}[/ ][\w]{2,3}[/ ]\d{4}", re.I)
ICD10_RE = re.compile(r"\b[A-TV-Z]\d{2}\.\d\b")
ADDRESS_RE = re.compile(r"(?<!comercial: )(?<!comercial:)\bdomicilio\s*:", re.I)

ID_DOCUMENT_CUES = ("documento nacional de identidad", "registro nacional de las personas")
DISABILITY_CUES = ("certificado único de discapacidad", "certificado unico de discapacidad", "ley 22.431")
HEALTH_TERMS = (
    "diagnóstico", "diagnostico", "historia clínica", "historia clinica", "epicrisis",
    "antecedentes", "anatomía patológica", "colonoscop", "biopsia", "evolución:",
    "tratamiento", "amputación", "amputacion", "esclerosis", "oncológ",
)


def deterministic(pages: list[Page]) -> list[Finding]:
    out: list[Finding] = []
    for p in pages:
        low = p.text.lower()
        for m in CUIT_RE.finditer(p.text):
            digits = "".join(m.groups())
            if not cuit_valid(digits):
                continue
            if m.group(1) in PERSON_PREFIXES:
                out.append(Finding("person_cuil", "CUIL of a private person", mask(m.group(0)), p.number, "block", "personal_id"))
            elif m.group(1) in COMPANY_PREFIXES:
                out.append(Finding("company_cuit", "Company CUIT (assess procurement context)", m.group(0), p.number, "info", "company_ok"))
        for m in DNI_RE.finditer(p.text):
            out.append(Finding("dni", "National ID (DNI) number", mask(m.group(1)), p.number, "block", "personal_id"))
        for m in AFFILIATE_RE.finditer(p.text):
            out.append(Finding("affiliate_number", "PAMI affiliate number", mask(m.group(0)), p.number, "block", "personal_id"))
        for m in BIRTH_RE.finditer(p.text):
            out.append(Finding("birth_date", "Date of birth", "nacimiento: **/**/****", p.number, "block", "personal_id"))
        if ADDRESS_RE.search(p.text):
            out.append(Finding("home_address", "Home address", "Domicilio: ****", p.number, "block", "personal_id"))
        if any(c in low for c in ID_DOCUMENT_CUES):
            out.append(Finding("id_document", "Image or copy of an identity document", "DOCUMENTO NACIONAL DE IDENTIDAD", p.number, "block", "personal_id"))
        if any(c in low for c in DISABILITY_CUES):
            out.append(Finding("disability_cert", "Disability certificate", "CERTIFICADO ÚNICO DE DISCAPACIDAD", p.number, "block", "health"))
        for m in ICD10_RE.finditer(p.text):
            out.append(Finding("icd10", "Diagnosis code (ICD-10)", m.group(0), p.number, "block", "health"))
        terms = sorted({t for t in HEALTH_TERMS if t in low})
        terms += [w for w in ("vih", "hiv") if re.search(rf"\b{w}\b", low)]
        if terms:
            out.append(Finding("health_terms", "Clinical language", ", ".join(terms[:5]), p.number, "review", "health"))
    return out


def scan(pdf: bytes) -> Scan:
    try:
        pages = extract(pdf)
    except Exception:
        return Scan(pages=[], coverage_issues=["pdf_extraction_failed"])
    return Scan(pages=pages, findings=deterministic(pages),
                ocr_used=any(p.source in ("ocr", "text+ocr") for p in pages),
                coverage_issues=[] if pages else ["empty_document"])
