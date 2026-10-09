# Publication Gate - Build Plan

## 0. Who this is for
- Target users: institutional procurement staff and reviewers; citizens viewing approved public records.
- Problem: private attachments can travel with public purchase records; unclear decisions and incomplete checks make unsafe publication easy.
- Solved: submit a fictional case, understand each decision, review held documents with attributable authorization, and verify public-file access.
- Scope: improve the existing FastAPI/Jinja web application and its defensive backend. Preserve teammate code and sponsor connectors. Product copy is English.

## 1. Three-phase breakdown
| Phase | Theme | Features included | Detail |
|---|---|---|---|
| 1 | Core loop | Integrate team branch, authenticated staff, complete-or-hold analysis, usable upload/review/public/audit screens, bounded PDF inputs, outcome tests | Full below |
| 2 | Completeness | Multiuser identity provider, durable job queue, metadata classification, broader document evaluations, operational sponsor failure recovery | Future work; do not claim complete |
| 3 | Depth and delight | Larger defense workflow, independently verified deployed repair, reviewed cross-service lessons | Separate BREACHSTOP work; this iteration does not implement it |

# Phase 1 detailed plan

## 2. Backend
### Tables
Existing SQLite purchases, attachments and events remain. No schema migration. Current attachment decisions are separate from historical decision events.
### RLS policies
SQLite has no RLS here. Server routes enforce staff authorization for upload, originals, review and audit. Anonymous callers only get public metadata and files whose current decision allows publication. Missing credentials disable staff routes.
### RPCs needed
Existing HTTP form routes remain. Reviewer identity comes from authentication, not the form. Origin checks protect state-changing browser requests. Validate bounded PDFs before storing a purchase. No new external destinations or credential use.
### Storage buckets
Existing private SQLite PDF blobs remain. No public object bucket. Public responses check current decisions and use no-store; this cannot recall previous downloads.

## 3. Screen inventory
| Screen | Purpose | View | Source |
|---|---|---|---|
| Overview | Explain the concrete demo and start a fictional case | Entry | Configuration only |
| Office upload | Submit public procurement metadata and private PDF attachments | Staff | Existing POST /office |
| Purchase detail | Understand file decisions, masked evidence and model availability | Staff | SQLite attachment records |
| Review | Inspect held files; record a decision and reason | Staff | SQLite + existing Guild brief |
| Public portal | Read purchase metadata and permitted attachments | Anonymous | Current enforced decisions |
| Audit | Read initial decisions, latency, finding occurrences and review history | Staff | Existing ClickHouse or SQLite events |

## 4. Navigation flow
Overview → run fictional case or upload → purchase decision view → review → public portal. Audit remains one click away. Public pages are clearly labeled fictional; no government affiliation is implied.

## 5. Component needs
Shared navigation, status badges with text, action buttons, upload fields, accessible evidence tables, decision summaries and empty/error states. Use one CSS token system: pale neutral surfaces, ink text, restrained teal action color; semantic amber/red for review/withholding. Loading shows actual request progress only, never fabricated agent steps. Buttons disable while submitted and recover on failure.

## 6. Edge cases to handle explicitly
- Empty overview, review queue, public list and audit table.
- Invalid PDF, missing file, excessive size/count, missing staff configuration, incorrect login, unavailable OCR/model and malformed model responses.
- Mixed image and text PDFs require image coverage even when text exists.
- All upload metadata is public; labels instruct staff to omit patient details. Metadata classification remains a stated gap.
- Visible labels, keyboard focus, semantic table headers, narrow 360px layout, filenames that wrap safely, restrained reduced-motion behavior.
- Native sharing, safe-area nesting and mobile image-pickers are inapplicable to this web iteration.

## 6b. Architecture & performance checklist
- Preserve FastAPI/Jinja; no React or mobile rewrite. Lists use responsive tables; pagination is deferred.
- No client database access or ad-hoc parallel state caches. Server remains authoritative.
- Bounded PDF inputs; expensive OCR/model processing remains synchronous for this prototype and needs a durable worker in Phase 2.

## 6c. Lifecycle & pre-launch checklist
- Existing environment configuration, no secrets in templates. Local demo uses a separate temporary database and explicitly empty sponsor configuration.
- Browser camera/notifications, app-store localization and push are not relevant. English interface; source fixture documents remain Spanish.
- No new third-party analytics. Show request failures and real configuration status; configured is not proven connected.
- High-consequence decisions require meaningful authorization and incomplete-analysis regression tests.
- Network failure blocks submission with retry; the offline local gate keeps uncertain files for review.

## 6d. Security checklist
- Authenticated server-side mutation and private-file routes; no client administrative key.
- Constant-time configured credentials for this prototype; this is not institutional multiuser authentication.
- Exact origin check on form actions; approved identity owns review attribution.
- Missing or malformed required analysis holds a file. Deterministic blocked files cannot be released by the model or review endpoint.
- PDF responses use no-store and safe filenames. A previously downloaded copy cannot be revoked.
- Existing external model connector can receive document content when configured; local test uses fictional data only. An open model alone does not establish privacy.
- Account lockout, identity-provider integration and metadata classification remain explicit Phase 2 limitations.

## 6e. Store publishing checklist
Not an app-store product. Deliver source, reproducible tests, local preview and current demo instructions. Public hosting and live sponsor execution require separate verification; do not claim either from this iteration.

## 6f. Motion & delight checklist
Named short CSS transition tokens, focus/hover feedback and a loading indicator only. Respect reduced motion. No celebration on blocking or approving private records.

## 7. Open questions for the user
None required for the authorized iteration. Existing audience, English copy, open source, sponsor choices and repository are settled. Live integrations will be labeled from actual configuration and evidence.
