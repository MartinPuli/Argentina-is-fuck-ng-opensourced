"""Fetch pinned, unmodified official PDFs, or verify previously downloaded copies."""

import argparse
import hashlib
import json
from pathlib import Path
from urllib.parse import urlsplit

import httpx
import pymupdf

MANIFEST = Path(__file__).resolve().parents[1] / "fixtures/public-documents.json"
MAX_BYTES = 10 * 1024 * 1024


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--offline", action="store_true", help="Verify local copies without network access")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    rows = []
    manifest = json.loads(MANIFEST.read_text())
    with httpx.Client(timeout=60, follow_redirects=False, trust_env=False) as client:
        for source in manifest["documents"]:
            name, url = source["filename"], source["url"]
            address = urlsplit(url)
            if Path(name).name != name or address.scheme != "https" or address.netloc != "www.argentina.gob.ar":
                raise ValueError("Manifest must contain simple filenames and official HTTPS URLs.")
            target = args.output / name
            if target.exists():
                if target.stat().st_size > MAX_BYTES:
                    raise ValueError(f"Local PDF exceeds size limit: {name}")
                raw = target.read_bytes()
            elif args.offline:
                raise ValueError(f"Missing local PDF: {name}")
            else:
                with client.stream("GET", url) as response:
                    response.raise_for_status()
                    chunks, size = [], 0
                    for chunk in response.iter_bytes():
                        size += len(chunk)
                        if size > MAX_BYTES:
                            raise ValueError(f"Official PDF exceeds size limit: {name}")
                        chunks.append(chunk)
                raw = b"".join(chunks)
            if len(raw) != source["bytes"] or hashlib.sha256(raw).hexdigest() != source["sha256"]:
                raise ValueError(f"PDF changed; review the source before updating the manifest: {name}")
            with pymupdf.open(stream=raw, filetype="pdf") as document:
                if document.needs_pass or len(document) != source["pages"]:
                    raise ValueError(f"PDF structure differs from the reviewed copy: {name}")
            if not target.exists():
                target.write_bytes(raw)
            rows.append({"filename": name, "sha256": source["sha256"], "pages": source["pages"],
                         "within_upload_size_and_page_limits": source["within_upload_size_and_page_limits"]})
    print(json.dumps({"status": "verified", "documents": rows}, indent=2))


if __name__ == "__main__":
    main()
