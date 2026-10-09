"""Context check with an open model served by AkashML.

The model only reads the attachment and reports risk. It can make the gate more
cautious (hold a file for a person) but it can never release a file that the
deterministic checks blocked. Missing or incomplete analysis holds the file
for human review rather than treating an unavailable check as approval.
"""

import json
import os

from openai import OpenAI

from .policy import valid_image_analysis, valid_text_analysis

MAX_TEXT_CHARS = 12000

PROMPT = """You review attachments before they are published on a public government \
procurement website in Argentina. Documents are in Spanish.

Public on purpose: what is being bought, quantities, technical specs, prices, supplier \
company names, company CUITs (prefix 30, 33, 34) and business addresses.

Must never be public: anything about a specific patient or private person. That includes \
names, ID numbers, addresses, birth dates, diagnoses, clinical history, disability, and \
combinations of details (age + town + condition + hospital + dates) that could point to \
one person even without a name.

Reply with JSON only, no prose:
{"personal_data": bool, "health_data": bool,
 "reidentification_risk": "none" | "low" | "medium" | "high",
 "safe_for_public": bool,
 "reasons": [short English strings; never copy names, numbers or addresses]}

Attachment text:
"""


def configured() -> bool:
    return bool(os.getenv("AKASHML_API_KEY"))


def review(text: str) -> dict | None:
    if not configured():
        return None
    if not isinstance(text, str) or not text.strip() or len(text) > MAX_TEXT_CHARS:
        return {"error": "text_analysis_incomplete"}
    try:
        client = OpenAI(
            api_key=os.environ["AKASHML_API_KEY"],
            base_url=os.getenv("AKASHML_BASE_URL", "https://api.akashml.com/v1"),
            timeout=45,
        )
        resp = client.chat.completions.create(
            model=os.getenv("AKASHML_MODEL", "openai/gpt-oss-120b"),
            messages=[{"role": "user", "content": PROMPT + text}],
            temperature=0,
            max_tokens=1500,
            response_format={"type": "json_object"},
        )
        raw = resp.choices[0].message.content or ""
        result = json.loads(raw)
        if not valid_text_analysis(result):
            return {"error": "text_analysis_invalid"}
        result["model"] = resp.model
        return result
    except Exception:  # provider errors may include sensitive request contents
        return {"error": "text_analysis_unavailable"}


IMAGE_PROMPT = """This image is one page of an attachment to a public government purchase \
record. Say what it shows. Reply with JSON only:
{"kind": short description, "personal_data": bool, "health_data": bool,
 "medical_image": bool, "safe_for_public": bool}
personal_data: an ID card, a face, a signature, or a named form. health_data or \
medical_image: an x-ray, scan, endoscopy, wound or injury photo, or clinical record."""


def review_image(png: bytes) -> dict | None:
    """Vision check for rendered scans and mixed text/image pages."""
    if not configured():
        return None
    import base64

    try:
        client = OpenAI(api_key=os.environ["AKASHML_API_KEY"],
                        base_url=os.getenv("AKASHML_BASE_URL", "https://api.akashml.com/v1"), timeout=45)
        resp = client.chat.completions.create(
            model=os.getenv("AKASHML_VISION_MODEL", "Qwen/Qwen3.8-27B"),
            messages=[{"role": "user", "content": [
                {"type": "text", "text": IMAGE_PROMPT},
                {"type": "image_url", "image_url": {"url": "data:image/png;base64," + base64.b64encode(png).decode()}},
            ]}],
            temperature=0, max_tokens=600, response_format={"type": "json_object"},
        )
        raw = resp.choices[0].message.content or ""
        result = json.loads(raw)
        if not valid_image_analysis(result):
            return {"error": "image_analysis_invalid"}
        result["model"] = resp.model
        return result
    except Exception:
        return {"error": "image_analysis_unavailable"}
