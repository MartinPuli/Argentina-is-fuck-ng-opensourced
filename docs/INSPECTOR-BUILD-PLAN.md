# Document inspector - Build Plan

## 0. Who this is for
Institutional operators checking a document before publication. Today the PDF, agent trace and policy references live on separate screens. Solved: see the original and resulting file, actual changed text regions, processing steps and cited sources together. Frontend and backend; existing English copy, thin type and blue/white system.

## 1. Three-phase breakdown
| Phase | Theme | Features included | Detail |
|---|---|---|---|
| 1 | Core loop | Authenticated document comparison, page navigation, actual processing steps, masked removal manifest and official/Senso citations | Full below |
| 2 | Completeness | Visible public-news query and results through existing discovery, links to reviewed rule proposals | Full below as an existing workflow connection |
| 3 | Depth | Saved run playback and synchronized zoom | Deferred; never fabricate activity or historical receipts |

## 2. Backend
### Tables
No schema change. Read existing attachment bytes, findings, manifests, clearance results and citation snapshots. Existing incident_leads stores reporting leads.
### RLS policies
SQLite staff authorization on HTML, metadata and both preview images. Public download enforcement unchanged. No external PDF URLs accepted.
### RPCs needed
GET /inspect/{id}, GET /api/inspect/{id}?page=1 and GET /internal/preview/{id}/{page}?copy=original|cleaned. Render one bounded PNG at a time; metadata never returns document text. Existing discovery POST gains an Accept: application/json response; staff/same-origin rules remain.
### Storage buckets
No new storage. Images computed on request; no-store/private responses. No personal records committed.

## 3. Screen inventory
Inspector: two document panes and a narrow evidence rail. On narrow screens panes stack. Workspace activity and purchase details link to the inspector. Sources section offers the actual fixed news query, retrieved headlines, dates and publishers, clearly marked unverified.

## 4. Navigation flow
Upload -> Workspace -> Inspect -> original/cleaned page -> sources or rule proposal. Public-copy button appears only for a current published decision.

## 5. Component needs
Comparison: original only, pending clean, ready clean, missing/error, multiple pages, toggle difference overlay. Trace: recorded/running/completed/error/no receipt. Sources: cited/unavailable/searching/results/empty/error with retry. Buttons use existing tokens, visible focus and 44px targets. No new icon library, logo or decorative labels.

## 6. Edge cases
Handle absent/stale cleaned copies, rotated pages, different page counts, missing in-memory jobs after restart, inactive providers and failed news lookup. Preserve last successful data on transient errors. Escape all text; never treat source text as instructions. Image-based files may have no text difference overlay, so label it as text changes rather than complete visual differences.

## 6b. Architecture & performance
Existing Jinja and native JavaScript; no new dependencies. Load only the selected page, PNG longest edge <=1400px; poll metadata while visible, slower once processing ends for late citations. No fake progress percentages. Scope classes to the inspector; reuse shared blue tokens and 300/400/500 font weights.

## 6c. Lifecycle
No secrets/config changes or mobile permissions. English web UI. Provider-free backend and requested tester-army browser tests; live provider and deployment claims separate. Offline error preserves current view with retry.

## 6d. Security
Same staff boundary as original-file downloads. No public preview route. No raw PDF text, raw removal values or provider response in metadata; page pixels are staff-only. News search never activates a rule or changes a publication decision.

## 6e. Store publishing
Web application; app-store requirements inapplicable.

## 6f. Motion
No added animation. Actual state changes drive indicators. Original/cleaned pages remain aligned and stable; reduced-motion equivalent is the default.

## 7. Open questions
Optional clarification requested about including web research. Existing context supports showing source discovery alongside the PDF; do not add remote-browser automation or imply arbitrary pages were visited.

## Phase 2 extension: visible Senso retrieval
Operators need to distinguish a local policy from an actual provider response. No schema change: extend the existing citation JSON with the exact bounded query, retrieval time and up to five readable guideline passages. Add a staff-only, same-origin POST `/api/inspect/{id}/senso` to repeat the server-derived lookup without accepting document text, URLs or policy instructions from the browser. It cannot change publication decisions or activate rules.

The inspector gains a Senso tab: query, connection receipt, explicit Run lookup action, loading/error/empty states, cited passages and expandable content/version/digest evidence. Existing blue/white tokens, native keyboard tabs and narrow-screen wrapping remain. Local preview may enable only the existing server-side Senso key; other providers stay disabled. Verify real retrieval separately from offline HTTP/browser tests. Supply existing fictional PDFs for removable identifiers, benign equipment and a clinical document; do not guarantee automatic publication when reviewer providers are disabled. No new dependency, animation, mobile feature or public storage is needed.

## Phase 2 extension: operational History
Remove the generated-workload dashboard and its warning banner from the product. History and the workspace count use actual audit events from `Events.stats()`, on ClickHouse or its SQLite fallback. Preserve benchmark generator/storage as separate developer tools; do not relabel benchmark rows as activity. No schema or auth changes. Keep actual decision counts, finding types and review history, with zero/empty states and measured scan latency. Verify that adding audit events changes the view and that neither operational route calls the synthetic history adapter. Existing blue/white styles and thin type remain.
