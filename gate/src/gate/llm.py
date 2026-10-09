"""Context check with an open model served by AkashML.

The model only reads the attachment and reports risk. It can make the gate more
cautious (hold a file for a person) but it can never release a file that the
deterministic checks blocked. If it is unavailable, the gate falls back to the
deterministic checks and holds anything clinical.
"""

import json
import os

from openai import OpenAI

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
    client = OpenAI(
        api_key=os.environ["AKASHML_API_KEY"],
        base_url=os.getenv("AKASHML_BASE_URL", "https://api.akashml.com/v1"),
        timeout=45,
    )
    try:
        resp = client.chat.completions.create(
            model=os.getenv("AKASHML_MODEL", "openai/gpt-oss-120b"),
            messages=[{"role": "user", "content": PROMPT + text[:12000]}],
            temperature=0,
            max_tokens=1500,
            response_format={"type": "json_object"},
        )
        raw = resp.choices[0].message.content or ""
        start, end = raw.find("{"), raw.rfind("}")
        result = json.loads(raw[start : end + 1])
        result["model"] = resp.model
        return result
    except Exception as exc:  # the gate must keep working when the model does not
        return {"error": f"{type(exc).__name__}: {exc}"[:300]}


IMAGE_PROMPT = """This image is one page of an attachment to a public government purchase \
record. Say what it shows. Reply with JSON only:
{"kind": short description, "personal_data": bool, "health_data": bool,
 "medical_image": bool, "safe_for_public": bool}
personal_data: an ID card, a face, a signature, or a named form. health_data or \
medical_image: an x-ray, scan, endoscopy, wound or injury photo, or clinical record."""


def review_image(png: bytes) -> dict | None:
    """Vision check for pages with no usable text, such as photos and x-rays."""
    if not configured():
        return None
    import base64

    client = OpenAI(api_key=os.environ["AKASHML_API_KEY"],
                    base_url=os.getenv("AKASHML_BASE_URL", "https://api.akashml.com/v1"), timeout=45)
    try:
        resp = client.chat.completions.create(
            model=os.getenv("AKASHML_VISION_MODEL", "Qwen/Qwen3.8-27B"),
            messages=[{"role": "user", "content": [
                {"type": "text", "text": IMAGE_PROMPT},
                {"type": "image_url", "image_url": {"url": "data:image/png;base64," + base64.b64encode(png).decode()}},
            ]}],
            temperature=0, max_tokens=600, response_format={"type": "json_object"},
        )
        raw = resp.choices[0].message.content or ""
        result = json.loads(raw[raw.find("{"): raw.rfind("}") + 1])
        result["model"] = resp.model
        return result
    except Exception as exc:
        return {"error": f"{type(exc).__name__}: {exc}"[:300]}
