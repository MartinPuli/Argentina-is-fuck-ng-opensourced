"""Turn findings into one decision per attachment.

PUBLIC    goes on the public site now.
HOLD      waits for a person. Not public until approved.
WITHHELD  never public. Stays in the internal file only.

Order matters: the model can only add caution. A deterministic block is final.
"""

from dataclasses import asdict

from .detect import Finding, Scan

PUBLIC, HOLD, WITHHELD = "public", "hold", "withheld"


def valid_text_analysis(model: object) -> bool:
    return (
        isinstance(model, dict) and "error" not in model
        and all(type(model.get(key)) is bool for key in ("safe_for_public", "personal_data", "health_data"))
        and model.get("reidentification_risk") in ("none", "low", "medium", "high")
        and isinstance(model.get("reasons"), list)
        and all(isinstance(reason, str) for reason in model["reasons"])
    )


def valid_image_analysis(model: object) -> bool:
    return (
        isinstance(model, dict) and "error" not in model
        and all(type(model.get(key)) is bool for key in
                ("safe_for_public", "personal_data", "health_data", "medical_image"))
        and isinstance(model.get("kind"), str) and bool(model["kind"].strip())
    )


def decide(scan: Scan, model: dict | None, images: list[dict] | None = None) -> tuple[str, list[str], list[dict]]:
    findings: list[Finding] = list(scan.findings)
    reasons: list[str] = []
    image_results = images if isinstance(images, list) else []
    for issue in scan.coverage_issues or ([] if scan.pages else ["empty_document"]):
        findings.append(Finding("incomplete_coverage", "Document analysis is incomplete",
                                issue, 0, "review", "unreadable"))
    for index, page in enumerate(scan.pages):
        for issue in page.coverage_issues:
            findings.append(Finding("incomplete_coverage", "Page analysis is incomplete",
                                    issue, page.number, "review", "unreadable"))
        if not (page.image or page.has_images or page.source in ("ocr", "text+ocr")):
            continue
        img = image_results[index] if index < len(image_results) else None
        if not valid_image_analysis(img):
            findings.append(Finding("unchecked_image", "Image analysis needs review", "",
                                    page.number, "review", "unreadable"))
        elif (img["personal_data"] or img["health_data"] or img["medical_image"]
              or not img["safe_for_public"]):
            findings.append(Finding("model_image", "Image shows personal or medical content",
                                    img["kind"][:120], page.number, "review", "health"))

    if not valid_text_analysis(model):
        findings.append(Finding("unchecked_text", "Text analysis needs review", "",
                                0, "review", "unreadable"))
    elif (not model["safe_for_public"] or model["health_data"] or model["personal_data"]
          or model["reidentification_risk"] in ("medium", "high")):
        findings.append(Finding("model_context", "Model flagged context risk",
                                "; ".join(model["reasons"])[:300] or "unsafe for public",
                                0, "review", "reidentification"))

    if scan.ocr_used and sum(len(p.text) for p in scan.pages) < 40:
        findings.append(Finding("unreadable_scan", "Unreadable scan", "", 0, "review", "unreadable"))

    if any(f.severity == "block" for f in findings):
        reasons.append("Contains personal or health identifiers. Kept in the internal file.")
        return WITHHELD, reasons, [asdict(f) for f in findings]

    decision = PUBLIC
    if any(f.kind == "model_image" for f in findings):
        decision = HOLD
        reasons.append("The vision model sees personal or medical content in an image.")
    if any(f.kind in ("incomplete_coverage", "unchecked_text", "unchecked_image", "unreadable_scan")
           for f in findings):
        decision = HOLD
        reasons.append("Required analysis is missing, failed, or incomplete. A person must review the file.")
    if any(f.severity == "review" and f.rule == "health" and f.kind != "model_image" for f in findings):
        decision = HOLD
        reasons.append("Clinical language without a direct identifier. A person must check re-identification risk.")
    if any(f.kind == "model_context" for f in findings):
        decision = HOLD
        reasons.append("The text model flagged personal, health, or re-identification risk.")
    if decision == PUBLIC and any(f.severity == "review" for f in findings):
        decision = HOLD
        reasons.append("A finding requires human review before publication.")

    if decision == PUBLIC:
        reasons.append("No personal or health data found.")
    return decision, reasons, [asdict(f) for f in findings]
