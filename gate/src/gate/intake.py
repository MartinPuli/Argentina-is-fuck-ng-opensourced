"""Private document-label hints; never authority or public purchase metadata."""
import re

import pymupdf

LABELS = {
    "office": r"(?:oficina|office|unidad de gesti[oó]n local|UGL)",
    "procedure": r"(?:expediente|procedimiento|procedure|referencia)",
    "item": r"(?:objeto|[ií]tem|item|bien solicitado)",
    "amount": r"(?:monto(?: total)?|importe(?: total)?|amount)",
}


def details(uploads: list[tuple[str, bytes]]) -> list[dict]:
    hints = []
    for filename, pdf in uploads:
        with pymupdf.open(stream=pdf, filetype="pdf") as document:
            for index in range(min(3, document.page_count)):
                try:
                    text = document[index].get_text()[:12000]
                except Exception:
                    continue  # Full security analysis still runs in the existing worker.
                found = {}
                for name, label in LABELS.items():
                    match = re.search(r"(?im)^\s*" + label + r"\s*:\s*([^\r\n]{1,240})", text)
                    if match:
                        found[name] = match.group(1).strip()
                if found:
                    hints.append({"filename": filename, "page": index + 1, "fields": found})
    return hints
