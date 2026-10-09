# ArgenSec Gate (Publication Gate)

ArgenSec Gate checks every PDF before PAMI, Argentina's health insurer for retirees, publishes it on its public purchase site. In May 2026, [Chequeado found](https://chequeado.com/investigaciones/pami-expone-datos-medicos-y-documentos-sensibles-de-sus-afiliados-en-su-sitio-web/) medical histories, disability certificates and ID card copies on that site. Nothing checked the files first. This is that check.

Live demo: [argensec.pujia.ar](https://argensec.pujia.ar). Video script: [DEMO.md](DEMO.md). Security review: [SEMGREP-REPORT.md](SEMGREP-REPORT.md) and [issue #2](https://github.com/MartinPuli/Argentina-is-fuck-ng-opensourced/issues/2).

All documents are fictional. No real government system is connected. Detection can miss things. This is not a guarantee that every private document is caught. The [incident research](../docs/INCIDENTS.md) and [team problem analysis](../PAMI%20Data%20Exposure%20Problem%20Analysis.md) give context.

## What happens to a file

1. Rule-based detectors run first, with no model. They catch DNI and CUIL numbers, PAMI affiliate numbers, birth dates, home addresses, ICD-10 codes, disability certificates and ID card copies. Company tax IDs stay public on purpose.
2. Scanned pages are read with Spanish OCR and an AkashML vision model.
3. An AkashML text model reads the text. It flags re-identification risk, such as age plus town plus hospital, and lists the exact phrases that point to a person.
4. Rules learned from documented incidents run too (see below).
5. The gate decides. Clean files are published. Wholly clinical or identity files are kept private. Files with removable patient details go to the Guild clearance loop. Anything uncertain waits for a person.
6. The public download route checks the decision and the rule version on every request. Public files get neutral names like `compra-12-adjunto-34.pdf`, because an upload name can contain a patient's name.

Models can only add caution. A rule-based block is final. A missing or failed check keeps the file private.

## Clearance levels and the Guild loop

Each piece of information belongs to one of three levels:

- **clinical:** the full original. Internal only.
- **procurement:** what buyers and suppliers need. No patient identity.
- **public:** procurement minus anything that could point to a person when combined.

The loop, one Guild session per step:

1. The **orchestrator** agent ([prompt](guild-orchestrator/PROMPT.md)) classifies each piece of information into a level.
2. The **public agent** ([prompt](guild-public/PROMPT.md)) lists the exact text to remove for the public level.
3. The app removes that text from the PDF for real (deleted, not covered), then reruns the detectors on the cleaned bytes.
4. The **public review agent** ([prompt](guild-verifier/PROMPT.md)) reads only the cleaned copy and answers PASS or FAIL. On FAIL its feedback goes back to the public agent. At most 3 rounds.
5. The cleaned copy is published only if the reviewer says PASS and the detectors find nothing. Otherwise a person decides.

A **reviewer-note agent** ([prompt](guild-agent/PROMPT.md)) writes a one-line note for each held file from masked findings only.

The app drives the loop. The orchestrator prompt allows native sub-agent calls, but they did not trigger in our tests, so the app calls each agent in turn. Code: [agent.py](src/gate/agent.py) (`clearance()`, `verify()`, `brief()`) and [sanitize.py](src/gate/sanitize.py).

## Sponsor tools

- **ClickHouse:** data storage and analysis at PAMI scale. It holds the audit log of every decision, cleaned copy, agent verdict and human review. It also holds 1,000,000 clearly labeled simulated history events ([simulate_history.py](scripts/simulate_history.py)). The `/dashboard` page runs live queries on them: unsafe uploads by UGL, by data type, by month, and files affected by a rule update. Each shows its measured query time.
- **AkashML:** inference. An open text model (`openai/gpt-oss-120b`) reads each file for re-identification risk and lists exact phrases to remove. A vision model (`Qwen/Qwen3.8-27B`) reads scanned pages. Code: [llm.py](src/gate/llm.py).
- **Guild.ai:** runs the agent procedure above.
- **Semgrep:** reviewed the AI-written code. The first scan ([initial-scan.json](semgrep/initial-scan.json)) found forms with no CSRF protection. Any site could make a signed-in reviewer approve a held medical file. We fixed it with a same-origin check. The later scan's findings were false positives. Our own review found two more bugs in rechecks and public files. See [SEMGREP-REPORT.md](SEMGREP-REPORT.md).

## Live demo site

[argensec.pujia.ar](https://argensec.pujia.ar) runs with `GATE_OPEN_DEMO=1`, so judges can open staff pages without a login. All data there is fictional. This setting is for the demo only. Never set it in a real deployment.

On `/live`, press **Send 8 fictional office files** to run the demo. Press **Reset demo** to clear purchases and files between takes. Learned rules and the audit history stay.

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
- Leave optional sponsor settings empty for local checks. To start with a fresh case, set `GATE_DB` to a new, unused SQLite filename; existing databases are not reset automatically.

Start the application locally, explicitly disabling optional sponsor calls even if the surrounding environment contains credentials:

```bash
AKASHML_API_KEY= GUILD_WORKSPACE= GUILD_AGENT= CLICKHOUSE_HOST= uv run --frozen uvicorn gate.app:app --host 127.0.0.1 --port 8765
```

Open [Documents](http://127.0.0.1:8765) and sign in with the configured account. Select **Upload PDF** to submit documents; synthetic fixtures are available under **Test data**. Use the same hostname throughout the session; mutating requests require a matching browser origin. Follow [DEMO.md](DEMO.md) for the complete review and public-download sequence.

The committed fictional PDFs are ready to use. Spanish OCR additionally needs Tesseract and `spa.traineddata`; `TESSDATA_PREFIX` can identify an existing language-data directory. If required OCR is unavailable or fails, the affected file remains nonpublic pending review. Local tests can also run without OCR.

```bash
uv run --frozen python -m pytest -q tests
```

Tests exercise local request, analysis and publication boundaries. They do not establish a live sponsor integration or a public deployment.

## Frontend

The Documents screen uses React and HeroUI; the remaining screens use server-rendered templates with shared styles. Compiled frontend assets are committed, so the Python server can serve them directly. To change the workspace:

```bash
cd gate/frontend
npm ci
npm run build
```

Commit source and rebuilt `gate/src/gate/static` files together. Dependency notices are in `frontend/THIRD-PARTY-NOTICES.txt`.

## Decisions and enforcement

| Stored decision | Meaning |
|---|---|
| `public` | Required automated analyses completed without a blocking or review finding. Classification can still be wrong. |
| `cleaned` | A checked sanitized copy was cleared for publication; the original stays internal. Public access still requires a current rule check. |
| `hold` | Analysis is missing, failed, incomplete, or uncertain. An authenticated reviewer must inspect the original. |
| `withheld` | A deterministic block or reviewer rejection keeps the file internal. The approval endpoint cannot release this state. |
| `approved` | A reviewer approved a held file and recorded a reason. This is a human decision, not an automated safety certificate. |

Without a text model, files that have no deterministic block are **held**, including the harmless technical specification. Missing vision analysis, OCR failure, extraction failure, malformed model output and oversized model text also produce review findings. There is no silent public fallback when a required check is unavailable.

The pipeline combines identifier rules, text extraction, OCR and optional text/image model analysis. Pages containing images receive rendered-page analysis even when they also contain a substantial text layer. Deterministic blocks take precedence over model output. [Policy references](src/gate/rules.py) explain the rationale; they are not a compliance certification.

Staff authentication protects uploads, original PDFs, the review queue, learning library/exports and audit dashboard. Reviewer attribution comes from the authenticated account, not the submitted form name; approval and rejection require a reason. Public PDF requests check the current decision and learned-rule revision, return 404 for held/withheld or stale files, and use `Cache-Control: no-store`. Downloads already received cannot be recalled.

Uploads accept up to eight PDFs, 10 MiB per file, 25 MiB combined and 50 pages per file. Empty, malformed or password-protected PDFs are rejected before purchase creation. These limits do not replace ingress limits at a deployment proxy.

## Learn from incidents without turning reports into authority

Open **Learning library** at `/learning`. Two sourced cases have authored local recipes: PAMI supporting attachments and a fictional payroll-publication adaptation of Río Negro reporting. The latter does not establish that the actual incident involved public PDFs. Recipes work with sponsor calls disabled; they are authored engineering checks, not rules autonomously discovered from a breach.

The workflow is **source → candidate → example tests → authenticated activation → recheck existing PDFs → export**. Each candidate stores source status, literal phrase groups, an action restricted to `hold` or `withheld`, fictional positive/benign examples, improvement proposals and an immutable digest. All phrase groups must match, with any alternative within a group sufficient. Passing the authored examples is not independent accuracy evidence.

| Operation | Route |
|---|---|
| Read the library / build from a known case | `GET /learning` / `POST /learning/from-case/{case_id}` |
| Propose from a new sanitized summary | `POST /learning/propose` |
| Inspect candidate / run saved examples | `GET /learning/rules/{id}` / `POST /learning/rules/{id}/test` |
| Activate or retire the exact version | `POST /learning/rules/{id}/activate` or `/retire`, with `digest` |
| Recheck stored PDFs | `POST /learning/rescan` |
| Download review artifacts | `GET /learning/rules/{id}/skill.md`, `/proposal.md`, `/bundle.zip` |
| Inspect a fictional example PDF | `GET /learning/rules/{id}/example/{index}.pdf` |

All learning routes require staff authentication; mutations also require the matching origin. Activation requires passing tests tied to the exact digest. Activation and retirement advance the policy revision: previously checked public/approved attachments become unavailable until rechecked. A stale held file cannot be approved to bypass that step. New uploads use active rules immediately. Recheck can restrict a prior public/approved result, preserves an unchanged benign approval, and never automatically releases an existing hold or withheld result. Retirement is not publication approval.

A **new report** requires a configured AkashML model. Its URL is recorded, not fetched; its sanitized summary is sent to that configured provider. Custom submissions remain explicitly unverified even when the submitter describes them as acknowledged. The model can propose only an inactive candidate. When no model is configured, the UI disables this option and direct requests return a clear error; known recipes remain usable offline.

The bundle contains `SKILL.md`, an improvement proposal and saved evidence. Exporting installs nothing and grants no authority. Another enrolled gate needs a new inactive candidate, fresh fictional positive/benign tests, its own review and authenticated activation. Saved source tests are not a fresh evaluation of that installation.

[Integrated request tests](tests/test_learning_flow.py) render the library and lifecycle pages, inspect generated example PDFs, and verify exact public PDF bytes before/after activation and recheck. They use temporary SQLite and constructed model outputs to isolate learned-rule behavior; no live model or sponsor outcome is established. See [DEMO.md](DEMO.md).

## Sponsor setup and limits

- **AkashML:** set `AKASHML_API_KEY`. Defaults are `openai/gpt-oss-120b` and `Qwen/Qwen3.8-27B`. It also drafts inactive rule candidates from new incident reports. An open model does not by itself guarantee private processing or retention.
- **Guild.ai:** needs the `guild` CLI signed in on the host, plus `GUILD_WORKSPACE` and `GUILD_AGENT` (the reviewer-note agent). Agent definitions are in the `guild-*/` folders. If Guild does not answer, the file stays private.
- **ClickHouse:** set `CLICKHOUSE_HOST` and credentials. Without it, events go to SQLite and the simulated history panel is hidden. Fill the simulated table with `uv run python scripts/simulate_history.py --rows 1000000`. Every row is flagged `simulated = 1`.
- **Semgrep:** raw output is in [semgrep/](semgrep/). The first scan is [initial-scan.json](semgrep/initial-scan.json). The scans after the fix are [before.json](semgrep/before.json) and [after.json](semgrep/after.json).

The origin middleware compares scheme, host and port. It rejects missing, null or mismatched origins on every state-changing request. It falls back to a same-origin Referer only when Origin is absent. Request tests check this.

## Limits and data handling

- Use the provided fictional PDFs or other owned synthetic data. No real patient files or leaked records are needed.
- Purchase fields such as item, procedure, office and amount are public immediately. Their plaintext content is not classified. Do not place personal information in these fields. Public files use neutral names; the original upload name stays internal.
- Pattern recognition, OCR, model judgments and human review can miss sensitive content. Mixed-image coverage is improved, not exhaustive document-format verification. No clinical-image accuracy claim or broad prevention rate is established.
- Configured model connectors receive document content. The Guild orchestrator and public agent receive the document text. The public reviewer receives only the cleaned text. The reviewer-note agent receives masked findings and the filename. Audit events include filenames and reviewer identity.
- The single configured staff account is a prototype identity boundary, not a multiuser identity provider. Individual staff accountability, rate limiting, durable job workers and broader authorization remain future work.
- SQLite contains original PDFs; there is no application-level database encryption. Processing remains synchronous. External-service failures and storage availability need operational hardening.
- Alternate publication paths, copies previously downloaded, credential theft and full-host recovery are outside this component's protection. The live site is a demo with fictional data. No real institutional integration exists.

## License

Application code, templates, static assets and fictional fixtures are available under [MIT](LICENSE-MIT). Original documentation remains under the repository's [CC BY 4.0 terms](../LICENSE.md). Dependency licenses and third-party rights remain separate.

## Live activity and exposure comparison

`/live` retains the team's live processing view alongside the detailed `/office`, `/review` and learning screens. Live uploads run in background threads; the staff-only `/api/activity` reports actual processing steps. This small-demo queue is in memory, is not durable across restarts, and is not shared across multiple workers.

`/exposures` compares a bounded set of sourced Argentine exposures, with companies and public bodies separated. No verified company totals support a definitive national ranking in this review. Reported files, claimed records and unknown quantities remain distinct; [methodology and sources](../docs/research/EXPOSURE-RANKING-NOTES.md) explain the limitations.

## Security memory

[Pi implementation plan](../docs/research/PI-IMPLEMENTATION-PLAN.md): proposed integration for turning incident evidence into tested PDF rules, code fixes and credential-response workflows. Pi access and execution are not yet verified.
