# ArgenSec Gate (Publication Gate)

**Visual inspector:** Open a file from Workspace or select **Inspect document** in its details. Compare real original/cleaned pages, text changes, recorded agent steps, guidelines, Senso citations and public-news research in one view. [Workflow and verification](INSPECTOR.md).

**Guidelines and learning:** [SENSO.md](SENSO.md) documents the official-source browser, real Senso context integration, public-news discovery and tested rule-approval workflow. Server setup requires `SENSO_API_KEY`, dependency sync and a process restart.

ArgenSec Gate checks every PDF before PAMI, Argentina's national health insurer for retirees and pensioners (about 5 million members), publishes it on its public purchase site. In May 2026, [Chequeado found](https://chequeado.com/investigaciones/pami-expone-datos-medicos-y-documentos-sensibles-de-sus-afiliados-en-su-sitio-web/) medical histories, disability certificates and ID card copies on that site. Nothing checked the files first. This is that check.

Application: [argensec.pujia.ar](https://argensec.pujia.ar). Video script: [DEMO.md](DEMO.md). Security review: [SEMGREP-REPORT.md](SEMGREP-REPORT.md) and [issue #2](https://github.com/MartinPuli/Argentina-is-fuck-ng-opensourced/issues/2).

All documents are fictional. No real government system is connected. Detection can miss things. This is not a guarantee that every private document is caught. The [incident research](../docs/INCIDENTS.md) and [team problem analysis](../PAMI%20Data%20Exposure%20Problem%20Analysis.md) give context.

## File-first uploads

Drop PDFs on Documents, Upload or Live, or choose a file: analysis starts without filling purchase fields. Explicit purchase labels are detected as staff-only hints; unrecognized fields stay unknown. **Download test PDF** provides a fictional attachment that exercises identifier and medical-data checks. Manual entry is optional. See [verification and limits](verification/PDF-INTAKE-2026-10-09.md). Pull the code and restart the application to load the new route and templates; the SQLite migration runs automatically.

## What happens to a file

1. Rule-based detectors run first, with no model. They catch DNI and CUIL numbers, PAMI affiliate numbers, birth dates, home addresses, ICD-10 codes, disability certificates and ID card copies. Company tax IDs stay public on purpose.
2. Scanned pages are read with Spanish OCR and an AkashML vision model.
3. An AkashML text model reads the text. It flags re-identification risk, such as age plus town plus hospital, and lists the exact phrases that point to a person.
4. Rules learned from documented incidents run too (see below).
5. The gate decides. Clean files are published. Wholly clinical or identity files are kept private. Files with removable patient details go to the Guild clearance loop. Anything uncertain waits for a person. With `GATE_AUTONOMOUS=1`, it is restricted automatically instead (see [Autonomous mode](#autonomous-mode)).
6. The public download route checks the decision and the rule version on every request. Public files get neutral names like `compra-12-adjunto-34.pdf`, because an upload name can contain a patient's name. The public page is titled "PAMI · Public procurement", shows a demo badge and a fictional-data footer, and opens in a new tab from the staff side.

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
5. The cleaned copy is published only if the reviewer says PASS and the detectors find nothing. Otherwise a person decides, or with `GATE_AUTONOMOUS=1` the file is restricted automatically.

A **reviewer-note agent** ([prompt](guild-agent/PROMPT.md)) writes a one-line note for each held file from masked findings only.

The app drives the loop. The orchestrator prompt allows native sub-agent calls, but they did not trigger in our tests, so the app calls each agent in turn. Code: [agent.py](src/gate/agent.py) (`clearance()`, `verify()`, `brief()`) and [sanitize.py](src/gate/sanitize.py).

## Sponsor tools

- **ClickHouse:** stores the audit log of decisions, cleaned copies, agent verdicts and human reviews. History (`/dashboard`) and the workspace event count use actual recorded audit events, with decisions by office, finding types, review history and measured scan duration. The separate benchmark generator ([simulate_history.py](scripts/simulate_history.py)) writes generated rows to `gate_events_sim`; operational pages do not query that table.
- **AkashML:** inference. An open text model (`openai/gpt-oss-120b`) reads each file for re-identification risk and lists exact phrases to remove. A vision model (`Qwen/Qwen3.8-27B`) reads scanned pages. Code: [llm.py](src/gate/llm.py).
- **Guild.ai:** runs the agent procedure above.
- **Pi Security:** not connected. Pi's hosted connector needs a Pi tenant and an OAuth sign-in, and the event gives no Pi access. [pi_context.py](src/gate/pi_context.py) holds the read-only `PiContextProvider` contract from [the Pi plan](../docs/research/PI-IMPLEMENTATION-PLAN.md), plus bounds on any returned text. The only provider reports `not_connected`. `/api/pi/status` shows why and what access is needed. No decision uses Pi, and nothing is labeled a Pi result without a Pi reference ID.
- **Semgrep:** reviewed the AI-written code. The first scan ([initial-scan.json](semgrep/initial-scan.json)) found forms with no CSRF protection. Any site could make a signed-in reviewer approve a held medical file. We fixed it with a same-origin check. The later scan's findings were false positives. Our own review found two more bugs in rechecks and public files. See [SEMGREP-REPORT.md](SEMGREP-REPORT.md).

## Live demo site

[argensec.pujia.ar](https://argensec.pujia.ar) runs with `GATE_OPEN_DEMO=1`, so judges can open staff pages without a login. All data there is fictional. This setting is for the demo only. Never set it in a real deployment.

The staff navbar has Documents, Live, Review and Public ↗. The home page has a hero with the flow diagram and an **Upload a PDF** button (`/office`). Rules (`/learning`), Exposures (`/exposures`) and History (`/dashboard`) are not in the navbar. Open them by URL or from page links.

Upload PDFs from Workspace or `/office`. Sample-loading controls are not part of the operator interface. **Clear workspace** clears purchases and files; rules and audit history stay.

The live site runs with `GATE_AUTONOMOUS=1`. In a measured run on October 9, 2026, 9 of 9 files finished without a person in 68.5 seconds: 2 published, 3 cleaned, 4 withheld.

Deploys from `main` run the tests first. The proxy holds requests while the server restarts, so a deploy does not show errors.

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

Open [Documents](http://127.0.0.1:8765) and sign in with the configured account. Select **Upload a PDF** to submit documents; synthetic fixtures are available under **Test data**. Use the same hostname throughout the session; mutating requests require a matching browser origin. Follow [DEMO.md](DEMO.md) for the complete review and public-download sequence.

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
| `hold` | Analysis is missing, failed, incomplete, or uncertain. An authenticated reviewer must inspect the original. With `GATE_AUTONOMOUS=1` this state is temporary and becomes `withheld`. |
| `withheld` | A deterministic block, a reviewer rejection or, with `GATE_AUTONOMOUS=1`, an automatic restriction (`autopilot_restricted` finding) keeps the file internal. The approval endpoint cannot release this state. |
| `approved` | A reviewer approved a held file and recorded a reason. This is a human decision, not an automated safety certificate. |

Without a text model, files that have no deterministic block are **held**, including the harmless technical specification. Missing vision analysis, OCR failure, extraction failure, malformed model output and oversized model text also produce review findings. There is no silent public fallback when a required check is unavailable.

### Autonomous mode

`GATE_AUTONOMOUS=1` makes every upload reach a final outcome without a person. It is off by default. It was on for the live demo when checked on October 9, 2026.

- When a file's background checks end and it is still `hold`, it becomes `withheld` with an `autopilot_restricted` finding and an `autopilot` audit event. Uncertainty never leads to publication.
- At startup, unreviewed holds are settled the same way.
- Activating or retiring a learned rule rechecks stored files automatically. The recheck only restricts.
- `/live` shows "Finished without a person: X of Y". `/public` shows how many attachments were held back automatically.
- People audit afterward through the audit log (`autopilot` events) and the purchase pages. The Review page also lists automatic restrictions under "Restricted automatically". A person can release one with a written reason, or confirm it stays private. Files with a deterministic block, or checked under old rules, cannot be released. Implemented and tested in [test_override.py](tests/test_override.py).

The rationale is in [§13 of the architecture decisions](<../PAMI Privacy Gate MVP Architecture Decisions.md>). Tests are in [test_autonomy.py](tests/test_autonomy.py).

The pipeline combines identifier rules, text extraction, OCR and optional text/image model analysis. Pages containing images receive rendered-page analysis even when they also contain a substantial text layer. Deterministic blocks take precedence over model output. [Policy references](src/gate/rules.py) explain the rationale; they are not a compliance certification.

Staff authentication protects uploads, original PDFs, the review queue, learning library/exports and audit dashboard. Reviewer attribution comes from the authenticated account, not the submitted form name; approval and rejection require a reason. Public PDF requests check the current decision and learned-rule revision, return 404 for held/withheld or stale files, and use `Cache-Control: no-store`. Downloads already received cannot be recalled.

Uploads accept up to eight PDFs, 10 MiB per file, 25 MiB combined and 50 pages per file. Empty, malformed or password-protected PDFs are rejected before purchase creation. These limits do not replace ingress limits at a deployment proxy.

## Learn from incidents without turning reports into authority

Open **Rules** at `/learning`. It is not in the navbar. Two sourced cases have authored local recipes: PAMI supporting attachments and a fictional payroll-publication adaptation of Río Negro reporting. The latter does not establish that the actual incident involved public PDFs. Recipes work with sponsor calls disabled; they are authored engineering checks, not rules autonomously discovered from a breach.

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

A **New source** report (**Propose rule**) requires a configured AkashML model. Its URL is recorded, not fetched; its sanitized summary is sent to that configured provider. Custom submissions remain explicitly unverified even when the submitter describes them as acknowledged. The model can propose only an inactive candidate. When no model is configured, the UI disables this option and direct requests return a clear error; known recipes remain usable offline.

The bundle contains `SKILL.md`, an improvement proposal and saved evidence. Exporting installs nothing and grants no authority. Another enrolled gate needs a new inactive candidate, fresh fictional positive/benign tests, its own review and authenticated activation. Saved source tests are not a fresh evaluation of that installation.

[Integrated request tests](tests/test_learning_flow.py) render the library and lifecycle pages, inspect generated example PDFs, and verify exact public PDF bytes before/after activation and recheck. They use temporary SQLite and constructed model outputs to isolate learned-rule behavior; no live model or sponsor outcome is established. See [DEMO.md](DEMO.md).

## Sponsor setup and limits

- **AkashML:** set `AKASHML_API_KEY`. Defaults are `openai/gpt-oss-120b` and `Qwen/Qwen3.8-27B`. It also drafts inactive rule candidates from new incident reports. An open model does not by itself guarantee private processing or retention.
- **Guild.ai:** needs the `guild` CLI signed in on the host, plus `GUILD_WORKSPACE` and `GUILD_AGENT` (the reviewer-note agent). Agent definitions are in the `guild-*/` folders. The app polls only the agent's answer events and runs at most four Guild calls at once, so a batch of files queues instead of timing out. If Guild does not answer, the file stays private.
- **ClickHouse:** set `CLICKHOUSE_HOST` and credentials. Without it, events go to SQLite and History uses that audit log. Fill the simulated table with `uv run python scripts/simulate_history.py --rows 1000000`. Every row is flagged `simulated = 1`.
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

`/live` retains the team's live processing view alongside the detailed `/office`, `/review` and learning screens. Live uploads run in background threads; the staff-only `/api/activity` reports actual processing steps. The **Agent log** panel lists timestamped events per agent, with links to Guild sessions and no personal data. Each file card shows a step timeline with durations. This small-demo queue is in memory, is not durable across restarts, and is not shared across multiple workers.

`/exposures` compares a bounded set of sourced Argentine exposures, with companies and public bodies separated. No verified company totals support a definitive national ranking in this review. Reported files, claimed records and unknown quantities remain distinct; [methodology and sources](../docs/research/EXPOSURE-RANKING-NOTES.md) explain the limitations.

## Security memory

[Pi implementation plan](../docs/research/PI-IMPLEMENTATION-PLAN.md): proposed integration for turning incident evidence into tested PDF rules, code fixes and credential-response workflows. Pi access and execution are not yet verified.

## PDF verification

Run the [tester-army/e2e browser suite](e2e/README.md) to check actual uploads and publication from both review screens. See the [executed results and integration limits](verification/PDF-VERIFICATION-2026-10-09.md).
