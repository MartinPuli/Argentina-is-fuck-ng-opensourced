# Publication Gate

A publication checkpoint for procurement attachments: check each file, retain uncertain documents for review, and enforce its current decision on every public download.

This local prototype uses fictional documents inspired by [Chequeado's reporting on PAMI attachments](https://chequeado.com/investigaciones/pami-expone-datos-medicos-y-documentos-sensibles-de-sus-afiliados-en-su-sitio-web/). The [incident research](../docs/INCIDENTS.md) and [team problem analysis](../PAMI%20Data%20Exposure%20Problem%20Analysis.md) provide context. No real government system is connected. Detection is fallible; this is not a guarantee that every private document will be identified.

## Run locally

Requires Python 3.11+ and `uv`. From the repository root:

```bash
cd gate
uv sync --frozen
cp .env.example .env
```

Copy the example only for a new setup; preserve an existing `.env`. Edit `.env` before starting:

- Set `GATE_STAFF_PASSWORD` to a private password. An empty or missing password disables staff routes with HTTP 503.
- Keep `GATE_STAFF_USERNAME=reviewer`, or choose a different account name. Both fields are checked.
- Leave optional sponsor settings empty for the offline demo. To start with a fresh case, set `GATE_DB` to a new, unused SQLite filename; existing databases are not reset automatically.

Start the offline demo, explicitly disabling optional sponsor calls even if the surrounding environment contains credentials:

```bash
AKASHML_API_KEY= GUILD_WORKSPACE= GUILD_AGENT= CLICKHOUSE_HOST= uv run --frozen uvicorn gate.app:app --host 127.0.0.1 --port 8765
```

Open [the local overview](http://127.0.0.1:8765), select **Open demo workspace**, and sign in with the configured account. Use the same hostname throughout the session; mutating requests require a matching browser origin. Follow [DEMO.md](DEMO.md) for the complete review and public-download sequence.

The committed fictional PDFs are ready to use. Spanish OCR additionally needs Tesseract and `spa.traineddata`; `TESSDATA_PREFIX` can identify an existing language-data directory. If required OCR is unavailable or fails, the affected file remains nonpublic pending review. The offline demo also works without OCR.

```bash
uv run --frozen python -m pytest -q tests
```

Tests exercise local request, analysis and publication boundaries. They do not establish a live sponsor integration or a public deployment.

## Decisions and enforcement

| Stored decision | Meaning |
|---|---|
| `public` | Required automated analyses completed without a blocking or review finding. Classification can still be wrong. |
| `hold` | Analysis is missing, failed, incomplete, or uncertain. An authenticated reviewer must inspect the original. |
| `withheld` | A deterministic block or reviewer rejection keeps the file internal. The approval endpoint cannot release this state. |
| `approved` | A reviewer approved a held file and recorded a reason. This is a human decision, not an automated safety certificate. |

Without a text model, files that have no deterministic block are **held**, including the harmless technical specification. Missing vision analysis, OCR failure, extraction failure, malformed model output and oversized model text also produce review findings. There is no silent public fallback when a required check is unavailable.

The pipeline combines identifier rules, text extraction, OCR and optional text/image model analysis. Pages containing images receive rendered-page analysis even when they also contain a substantial text layer. Deterministic blocks take precedence over model output. [Policy references](src/gate/rules.py) explain the rationale; they are not a compliance certification.

Staff authentication protects uploads, original PDFs, the review queue and audit dashboard. Reviewer attribution comes from the authenticated account, not the submitted form name; approval and rejection require a reason. Public PDF requests check the current decision, return 404 for held/withheld files, and use `Cache-Control: no-store`. Downloads already received cannot be recalled.

Uploads accept up to eight PDFs, 10 MiB per file, 25 MiB combined and 50 pages per file. Empty, malformed or password-protected PDFs are rejected before purchase creation. These limits do not replace ingress limits at a deployment proxy.

## Sponsor connectors and evidence

| Tool | Implemented connector | Evidence boundary |
|---|---|---|
| AkashML | Sends extracted text and rendered page images to configured text/vision models. Repository defaults are `openai/gpt-oss-120b` and `Qwen/Qwen3.8-27B`. | A configured key is not a successful analysis. Provider/model availability must be checked separately. An open model does not establish private processing or retention guarantees. |
| Guild | Uses an authenticated local `guild` CLI to request reviewer briefs from the selected workspace/agent. | Briefs assist a reviewer and have no publication authority. Settings or a running CLI do not establish a completed session. |
| ClickHouse | Stores decision/review events and supplies audit queries when configured. Otherwise events use SQLite. | Configuration is not evidence that a remote write or query succeeded. Audit charts describe initial decisions, not current publication inventory. |
| Semgrep | Teammate-reported security scan motivated the original CSRF fix. | The original scan output was not independently verified in this iteration. Do not present that report as a fresh scan result. |

The current origin middleware compares scheme, host and effective port and rejects missing, null or mismatched origins on mutating requests, with same-origin Referer fallback only when Origin is absent. Request tests check these boundaries.

For a separately verified sponsor run, configure the intended accounts in `.env` and start without the offline environment overrides. Do not label integrations executed until actual results are observed. The event still requires substantive use of at least three sponsors; the offline walkthrough demonstrates the local control only. See the [event brief](../docs/EVENT-BRIEF.md).

## Limits and data handling

- Use the provided fictional PDFs or other owned synthetic data. No real patient files or leaked records are needed.
- Purchase fields such as item, procedure, office and amount are public immediately. Their plaintext content is not classified. Released filenames are public too; filename sanitization protects header syntax, not privacy. Do not place personal information in these fields.
- Pattern recognition, OCR, model judgments and human review can miss sensitive content. Mixed-image coverage is improved, not exhaustive document-format verification. No clinical-image accuracy claim or broad prevention rate is established.
- Configured model connectors receive document content. Guild receives purchase/file metadata and findings; deterministic identifiers are masked, but filenames and model-generated explanations are not a complete redaction boundary. Audit events include filenames and reviewer identity.
- The single configured staff account is a prototype identity boundary, not a multiuser identity provider. Individual staff accountability, rate limiting, durable job workers and broader authorization remain future work.
- SQLite contains original PDFs; there is no application-level database encryption. Processing remains synchronous. External-service failures and storage availability need operational hardening.
- Alternate publication paths, copies previously downloaded, credential theft and full-host recovery are outside this component's protection. No public deployment or real institutional integration is verified here.

## License

Application code, templates, static assets and fictional fixtures are available under [MIT](LICENSE-MIT). Original documentation remains under the repository's [CC BY 4.0 terms](../LICENSE.md). Dependency licenses and third-party rights remain separate.
