"""The rules every decision cites. Plain text, versioned with the code.

These are summaries for the demo, not legal advice. Each one names the law it
paraphrases so a reviewer can check the source.
"""

RULES = {
    "personal_id": {
        "title": "Personal identifiers stay out of public records",
        "text": (
            "Access-to-information law lets an agency withhold personal data that cannot be "
            "separated from a record. The public version of a purchase must not carry a "
            "person's DNI, CUIL, affiliate number, birth date or home address."
        ),
        "source": "Ley 27.275, art. 8; Ley 25.326, arts. 4 and 9",
        "url": "https://www.argentina.gob.ar/normativa/nacional/ley-27275-265949/texto",
    },
    "health": {
        "title": "Health data is sensitive data",
        "text": (
            "Health information is sensitive data under the personal data law and is covered "
            "by medical confidentiality. Diagnoses, clinical histories and disability "
            "certificates may support a purchase internally but must not be published."
        ),
        "source": "Ley 25.326, arts. 2, 7 and 8; Ley 26.529, art. 2",
        "url": "https://www.argentina.gob.ar/normativa/nacional/64790/actualizacion",
    },
    "reidentification": {
        "title": "Removing the name is not enough",
        "text": (
            "A record without a name can still point to one person when it combines age, "
            "town, condition, provider or dates. The privacy regulator's guidance asks for "
            "dissociation, not just deleting the name. A person decides these cases."
        ),
        "source": "AAIP, guía de anonimización y disociación",
        "url": "https://www.argentina.gob.ar/sites/default/files/aaip_caja_de_herramientas_archivos.pdf",
    },
    "company_ok": {
        "title": "Supplier business data is public",
        "text": (
            "A company's CUIT, business address and quoted prices are part of procurement "
            "transparency and stay public."
        ),
        "source": "Ley 27.275, art. 1 (máxima divulgación)",
        "url": "https://www.argentina.gob.ar/normativa/nacional/ley-27275-265949/texto",
    },
    "unreadable": {
        "title": "If the gate cannot read it, a person must",
        "text": (
            "A scan the gate cannot read with confidence is held for human review. Silence "
            "from the checker is not approval."
        ),
        "source": "Gate policy",
        "url": "",
    },
}
