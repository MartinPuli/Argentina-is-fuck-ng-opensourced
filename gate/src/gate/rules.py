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
    "aaip_public_policy": {
        "title": "AAIP Resolution 40/2018 — Public-body privacy policy",
        "url": "https://www.argentina.gob.ar/normativa/nacional/resoluci%C3%B3n-40-2018-312130/texto",
        "locator": "Articles 1–3; model policy, items 4–10 and 13–14",
        "scope": (
            "Recommended model for public bodies: document collection purposes, retention, "
            "confidentiality, security, transfers and processor responsibilities. Statistical "
            "disclosure requires that identifying a person is not reasonably possible. "
            "Institution-specific legal powers still matter; consent is not the only lawful basis. "
            "Context for policy review, not an additional automatic blocking rule."
        ),
    },
    "aaip_security": {
        "title": "AAIP Resolution 47/2018 — Personal-data security measures",
        "url": "https://www.argentina.gob.ar/normativa/nacional/resoluci%C3%B3n-47-2018-312662/texto",
        "locator": "Articles 2–3; Annex I, sections A–H; Annex II",
        "scope": (
            "Recommended security measures for digital and paper records. Annex I covers "
            "collection, authenticated role-based access, authorized production changes, recovery, "
            "vulnerability management, secure destruction, incident response and development "
            "environments. Use to review storage and workflow safeguards; these recommendations "
            "are not a claim that this gate prevents server compromise or certifies compliance."
        ),
    },
    "aaip_responsible_ai": {
        "title": "AAIP — Responsible AI and personal data, 2025",
        "url": "https://www.argentina.gob.ar/sites/default/files/guia_ai-final-2025.pdf",
        "locator": "PDF pages 20–21 and 33–36, data principles and design recommendations",
        "scope": (
            "Regulator guidance for public and private entities: assess privacy risks early; "
            "minimize personal data; establish legitimate purposes, lawful sources and retention "
            "periods; apply privacy by design and default. Preserve source validity, traceability "
            "and auditability. Guidance for evaluating proposed improvements, not a new statute "
            "or permission to publish an uploaded document."
        ),
    },
    "cert_ar_2024": {
        "title": "CERT-Ar — Annual cybersecurity incident report, 2024",
        "url": "https://www.argentina.gob.ar/sites/default/files/2025/07/informe_cert-ar_2024.pdf",
        "locator": "Annual report: recorded incidents, affected sectors and classifications",
        "scope": (
            "Official incident statistics: 438 incidents recorded in 2024, including 267 in the "
            "State sector. These are reported computer security incidents, not a census of data "
            "leaks, leaked records or affected people. Research context only; statistics cannot "
            "identify the cause of a particular disclosure or authorize a publication rule."
        ),
    },
    "cert_ar_2025": {
        "title": "CERT-Ar — Annual computer security incident report, 2025",
        "url": "https://www.argentina.gob.ar/sites/default/files/2026/09/informe_cert_2025.pdf",
        "locator": "Annual report: recorded incidents, State sector and incident categories",
        "scope": (
            "Official incident statistics: 520 incidents recorded in 2025, including 254 in the "
            "State sector. Account compromise and unauthorized information access are distinct "
            "categories. These counts are not confirmed data-leak or victim totals, and observed "
            "changes do not establish causation. Research context only; not legal authority or "
            "an automatic publication rule."
        ),
    },
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
