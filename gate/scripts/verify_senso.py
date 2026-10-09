"""Verify real public-guideline ingestion/retrieval without printing credentials."""

import argparse
import json
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

from gate import senso_context  # noqa: E402

parser = argparse.ArgumentParser()
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()
try:
    senso_context.sync()
    receipt = senso_context.refresh()
    if not receipt["ready"]:
        raise ValueError("Guideline ingestion is still processing. Run this check again later.")
    context = senso_context.retrieve("Patient identifiers and reidentification in public procurement PDFs")
except ValueError as exc:
    print(str(exc))
    raise SystemExit(1) from None
args.output.write_text(json.dumps(context, indent=2, ensure_ascii=False) + "\n")
print(json.dumps({"status": "retrieved", "passages": len(context["passages"]),
                  "guideline_digest": context["guideline_digest"], "output": str(args.output)}))
