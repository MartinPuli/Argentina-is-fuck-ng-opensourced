# PDF browser verification

Uses [tester-army/e2e](https://github.com/tester-army/e2e), following its `skills/e2e` setup, writing-tests and running guides. Inspected upstream commit: `da790a1250d9164064a7ddde17a931f61e161f31`. Published dependencies are pinned independently: `e2e@0.19.0`, `@e2e-dev/web@0.14.0`.

## Run

Install the Python app first, using the instructions in [the gate README](../README.md). It must have `gate/.venv/bin/python` and the app installed there. Node 24.8+ or 22.22.3+ is required.

From this directory:

```bash
npm ci
npm test
```

Chromium downloads on first use if missing. The runner starts and stops a loopback server on a free port. Its SQLite database is temporary, staff authentication stays enabled, the credential is generated per run, deployment `.env` files are not loaded, and sponsor calls are disabled. No shared workspace is reset. No AI subscription is required: these exact browser interactions use the framework's deterministic API.

Eleven tests exercise all nine committed fictional PDFs through the upload form, confirm a private publication decision, check public HTTP 404 and unauthenticated original HTTP 401, and exercise human approval through both Review and Live. The two publication tests compare the downloaded public PDF with the original benign fixture byte for byte. Only the inspected equipment specification is approved.

Results, screenshots, JUnit and step traces appear under `.e2e/` and are ignored by Git. [The verification report](../verification/PDF-VERIFICATION-2026-10-09.md) records the executed results and limitations. These local tests establish publication boundaries; they do not establish live sponsor integration or a breach-prevention rate.

## Additional checks

From the repository root:

```bash
gate/.venv/bin/python gate/scripts/check_pdfs.py
gate/.venv/bin/python gate/scripts/check_live_pdfs.py \
  --origin https://your-enrolled-app.example \
  --purchases 4 5 --procedure-prefix QA-PDF-UNIQUE-RUN- \
  --expected-count 9 --output /tmp/live-pdfs.json
```

The second command is read-only and intended for a fictional run that you previously uploaded to your own app. It uses durable workspace metadata and a unique procedure prefix so reused purchase IDs cannot silently select unrelated records. Missing job receipts are reported separately from publication-access checks. It checks only the most recent 100 workspace files exposed by the app API and must run before the test workspace is reset. It cannot prove scanned-image redaction or complete provider processing from metadata alone.
