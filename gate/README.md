# Publication Gate

Private attachments never reach the public procurement portal.

## The problem

In May 2026, Chequeado found that PAMI, Argentina's health insurer for retirees, was publishing patients' medical histories, diagnoses, disability certificates and ID copies on its public purchasing website. Local offices attached the whole clinical file to each purchase record, and the record was published as it was. Files stayed online for days after the story ran, and new ones kept appearing. ([Chequeado](https://chequeado.com/investigaciones/pami-expone-datos-medicos-y-documentos-sensibles-de-sus-afiliados-en-su-sitio-web/), [follow-up](https://chequeado.com/investigaciones/a-una-semana-de-la-revelacion-de-chequeado-el-pami-continua-mostrando-en-su-web-datos-privados-de-sus-afiliados/comment-page-1/))

The team's [problem analysis](../PAMI%20Data%20Exposure%20Problem%20Analysis.md) traces this to one missing control: nobody owned the question "is this exact file safe to publish?"

## What the gate does

It sits between the internal file and the public portal. Every attachment gets one of three decisions:

| Decision | Meaning |
|---|---|
| **public** | No personal or health data. Published now. |
| **hold** | Gray case, such as a diagnosis without a name. Waits for a named reviewer. |
| **withheld** | Contains identifiers or health records. Stays in the internal file. |

The purchase itself (item, office, amount, supplier) is always published. Transparency stays; only the medical evidence stays inside.

How it decides:

1. **Deterministic checks.** DNI, CUIL with check-digit validation, PAMI affiliate numbers, birth dates, home addresses, ICD-10 codes, disability certificates, ID document copies. Company CUITs (prefix 30, 33, 34) are recognized as public business data.
2. **OCR** for scanned pages with no text layer (Tesseract, Spanish).
3. **Context check** by an open model on AkashML. It catches records that identify someone without a name: age, town, condition and hospital together.
4. **Policy.** The model can only add caution. It can hold a file, but it can never release one the deterministic checks blocked.
5. **Human review** for held files, with a brief from an agent hosted on Guild. The agent sees masked findings only, never the document.
6. **Enforcement on every request.** The public file route checks the decision each time, so a guessed URL to a withheld file returns 404.
7. **Audit log.** Every upload, decision and approval is an event in ClickHouse, with a dashboard by office.

Every decision cites the rule behind it (Ley 25.326, Ley 27.275, Ley 26.529, AAIP guidance). See [rules.py](src/gate/rules.py).

## Sponsor tools

| Tool | Role |
|---|---|
| AkashML | Open model (`openai/gpt-oss-120b`) reads each attachment for context risk. Patient files go to an open model, not a closed commercial one. |
| Guild.ai | Hosts the reviewer agent ([guild-agent/PROMPT.md](guild-agent/PROMPT.md)). The app starts a session per held or withheld file and stores the brief. |
| ClickHouse | Audit trail and dashboard: decisions by office, what the gate catches, gate latency, human decisions. |
| Semgrep | Scanned this code, which was written with an AI assistant. See below. |

Each one is optional at runtime. Without keys, the gate runs on deterministic checks and logs to SQLite.

The Guild connector uses the `guild` CLI, logged in on the host, to open a session per case and poll for the brief.

## What Semgrep found in our AI-written code

`semgrep scan --config auto` flagged the HTML forms for missing CSRF protection. That was a real hole in the one place that matters most: the review form. Any web page could make a logged-in reviewer's browser submit "Approve for public" for a held file, and publish a patient's medical record. That is the exact leak this project exists to stop, created by the code meant to stop it.

The fix is a same-origin check on every form post ([app.py](src/gate/app.py), `same_origin_posts`), with a test that a cross-site approval gets 403. Semgrep's rule still matches the templates because it looks for a Django-style token; the protection lives in the middleware.

## Run it

```bash
cd gate
uv sync
uv run python fixtures/make_fixtures.py
cp .env.example .env   # add keys if you have them
uv run uvicorn gate.app:app --port 8765
```

Open http://localhost:8765 and press **Run the PAMI demo case**. Tests: `uv run python -m pytest -q tests`.

OCR needs Tesseract with Spanish data (`spa.traineddata`).

## Fictional data only

Every person, number and diagnosis in [fixtures](fixtures/make_fixtures.py) is invented, and every page is watermarked "DATOS FICTICIOS". No real government system is connected or scanned.

## Limits

- Pattern checks miss identifiers in formats they don't know, and OCR can misread poor scans. Low-confidence scans are held, not published.
- Scanned pages also go to a vision model (Qwen3.8-27B on AkashML). It recognized the scanned DNI. It did not recognize our hand-drawn x-ray, and the gate held that file anyway because unreadable scans never publish. Real medical photos are untested.
- The gate protects what passes through it. It cannot remove copies that were already downloaded, and it cannot stop an office that uploads to the public site by another path.
