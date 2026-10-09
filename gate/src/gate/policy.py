"""Turn findings into one decision per attachment.

PUBLIC    goes on the public site now.
HOLD      waits for a person. Not public until approved.
WITHHELD  never public. Stays in the internal file only.

Order matters: the model can only add caution. A deterministic block is final.
"""

from dataclasses import asdict

from .detect import Finding, Scan

PUBLIC, HOLD, WITHHELD = "public", "hold", "withheld"


def decide(scan: Scan, model: dict | None) -> tuple[str, list[str], list[dict]]:
    findings: list[Finding] = list(scan.findings)
    reasons: list[str] = []

    if any(f.severity == "block" for f in findings):
        reasons.append("Contains personal or health identifiers. Kept in the internal file.")
        return WITHHELD, reasons, [asdict(f) for f in findings]

    decision = PUBLIC
    if any(f.severity == "review" for f in findings):
        decision = HOLD
        reasons.append("Clinical language without a direct identifier. A person must check re-identification risk.")

    if model and "error" not in model:
        risky = (
            not model.get("safe_for_public", False)
            or model.get("health_data")
            or model.get("personal_data")
            or model.get("reidentification_risk") in ("medium", "high")
        )
        if risky:
            decision = HOLD
            findings.append(Finding(
                "model_context", "Model flagged context risk",
                "; ".join(model.get("reasons", []))[:300] or "unsafe for public",
                0, "review", "reidentification",
            ))
            reasons.append(f"Model sees re-identification risk: {model.get('reidentification_risk', '?')}.")
    elif model and "error" in model:
        if decision == PUBLIC and scan.ocr_used:
            decision = HOLD
            reasons.append("Scanned file and the model was unavailable. A person must read it.")
            findings.append(Finding("unchecked_scan", "Scan not checked by model", "", 0, "review", "unreadable"))

    if scan.ocr_used and sum(len(p.text) for p in scan.pages) < 40 and decision == PUBLIC:
        decision = HOLD
        reasons.append("Scan is unreadable. A person must read it.")
        findings.append(Finding("unreadable_scan", "Unreadable scan", "", 0, "review", "unreadable"))

    if decision == PUBLIC:
        reasons.append("No personal or health data found.")
    return decision, reasons, [asdict(f) for f in findings]
