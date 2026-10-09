"""The rules every decision cites. Plain text, versioned with the code.

These are reviewed operational summaries, not the full legal texts or a compliance
certification. Source links and article locators let reviewers inspect the basis.
"""

import hashlib
import json

REVIEWED_ON = "2026-10-09"
SOURCES = {
    "access": {"title": "Ley 27.275 — Access to public information",
               "url": "https://www.argentina.gob.ar/normativa/nacional/ley-27275-265949/texto",
               "locator": "Articles 1, 8(c–d, h–i), 12 and 32(g)",
               "scope": "National framework; confirm institution-specific applicability."},
    "privacy": {"title": "Ley 25.326 — Personal data protection",
                "url": "https://www.argentina.gob.ar/normativa/nacional/64790/actualizacion",
                "locator": "Articles 1–2, 4–5, 7–11",
                "scope": "Personal data, including legal persons where applicable; health data is sensitive."},
    "patient": {"title": "Ley 26.529 — Patient rights",
                "url": "https://www.argentina.gob.ar/normativa/nacional/160432/actualizacion",
                "locator": "Articles 2(c–d) and 4",
                "scope": "Patient privacy, clinical confidentiality and disclosure authorization."},
    "aaip": {"title": "AAIP — Caja de herramientas: acceso a la información pública",
             "url": "https://www.argentina.gob.ar/sites/default/files/aaip_caja_de_herramientas_archivos.pdf",
             "locator": "PDF page 31 and Annex II, anonymization recommendations",
             "scope": "Regulator guidance on dissociation and preventing reidentification; not a statute."},
}

RULES = {
    "personal_id": {
        "title": "Personal identifiers require a publication basis",
        "text": (
            "The law permits withholding personal information that cannot be dissociated, "
            "subject to lawful-disclosure conditions. This gate uses a stricter default: "
            "keep private-person DNI, CUIL, affiliate numbers, birth dates and home addresses "
            "out of public attachments unless an authorized review establishes a publication basis."
        ),
        "source": "Ley 27.275, arts. 1, 8(i), 12; Ley 25.326, arts. 4–5, 9–11",
        "url": "https://www.argentina.gob.ar/normativa/nacional/ley-27275-265949/texto",
    },
    "health": {
        "title": "Health data is sensitive data",
        "text": (
            "Health information is sensitive personal data. Patient-linked diagnoses, clinical "
            "histories and disability certificates stay internal under this gate's default. "
            "Anonymous clinical or product terminology is not automatically prohibited: assess "
            "whether a person remains identifiable and whether disclosure is authorized."
        ),
        "source": "Ley 25.326, arts. 2, 7–10; Ley 26.529, arts. 2(c–d), 4",
        "url": "https://www.argentina.gob.ar/normativa/nacional/64790/actualizacion",
    },
    "reidentification": {
        "title": "Removing the name is not enough",
        "text": (
            "A record without a name can still point to one person when it combines age, "
            "town, condition, provider or dates. The privacy regulator's guidance asks for "
            "dissociation and measures against reidentification, not just deleting the name. "
            "The gate restricts uncertain cases; its checks do not certify anonymity."
        ),
        "source": "AAIP, Caja de herramientas, anonymization section and Annex II",
        "url": "https://www.argentina.gob.ar/sites/default/files/aaip_caja_de_herramientas_archivos.pdf",
    },
    "company_ok": {
        "title": "Preserve legitimate procurement information",
        "text": (
            "Procurement transparency includes objectives, amounts and suppliers. A company CUIT "
            "alone is not a private-person CUIL finding. This is not blanket permission to publish "
            "corporate records: confidential commercial information, personal data, sole-trader "
            "details and other exceptions still require assessment."
        ),
        "source": "Ley 27.275, arts. 8(c–d), 32(g); Ley 25.326, arts. 1–2",
        "url": "https://www.argentina.gob.ar/normativa/nacional/ley-27275-265949/texto",
    },
    "unreadable": {
        "title": "Incomplete analysis cannot clear a file",
        "text": (
            "Missing or failed analysis never counts as approval. Keep the attachment private; "
            "the configured workflow may require review or conservatively block it. "
            "This is an application safeguard, not a quoted legal requirement."
        ),
        "source": "Gate policy",
        "url": "",
    },
}


RULES["learned"] = {
    "title": "Incident-derived publication check",
    "text": "A reviewed source led to a tested, approved phrase-group check. Its finding can restrict publication; it cannot release another rule's restriction.",
    "source": "Learning library: approved incident-derived rule",
    "url": "/learning",
}

for _key, _ids in {"personal_id": ["access", "privacy"], "health": ["privacy", "patient"],
                   "reidentification": ["aaip", "privacy"], "company_ok": ["access", "privacy"],
                   "unreadable": [], "learned": []}.items():
    RULES[_key]["source_ids"] = _ids
    RULES[_key]["kind"] = ("Operational policy based on official sources" if _ids
                           else "Application safeguard; not legislation")


def guideline_pack() -> dict:
    """Only public authored summaries and citations, never uploaded document data."""
    data = {"reviewed_on": REVIEWED_ON, "sources": SOURCES, "policies": RULES,
            "notice": "Reviewed operational summaries, not the full legal texts or a compliance certification. Official sources prevail. Incident claims and retrieved context are not legal authority."}
    text = json.dumps(data, sort_keys=True, ensure_ascii=False, indent=2)
    return {"digest": hashlib.sha256(text.encode()).hexdigest(), "text": text, **data}


def model_guidelines() -> dict:
    pack = guideline_pack()
    return {key: pack[key] for key in ("digest", "reviewed_on", "sources", "policies", "notice")}
