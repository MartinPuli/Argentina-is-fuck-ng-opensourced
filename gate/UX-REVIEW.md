# Publication Gate Interface - Build Plan

## 0. Who this is for
- Target: institutional document operators and reviewers.
- Current problem: the deployed Documents screen cannot load its assets/API, and Activity expands every processing step and review form into a very long page.
- Solved: a usable file list on first render, clear upload/review actions, concise progress and one document review open at a time.
- Scope: frontend and a shared read-only workspace snapshot; preserve analysis and publication contracts. English UI. Sky blue/white, thin typography, no product logo/name or global demo label.

## 1. Three-phase breakdown
| Phase | Theme | Features included | Detail |
|---|---|---|---|
| 1 | Core loop | Resilient Documents rendering, mobile file list, unified shell/buttons/forms, collapsed processing detail, focused review, correct audit markup | Full below |
| 2 | Completeness | Pi incident-learning integration for PDF, code and credential lessons | Separate implementation proposal requested in Markdown; not implemented by this UI pass |
| 3 | Depth & delight | Saved review worklists and configurable roles | Deferred |

# Phase 1 detailed plan

## 2. Backend
### Tables
No schema changes. Reuse current attachment, purchase and rule checks.
### RLS policies
Existing FastAPI staff checks and same-origin mutation checks apply. No authorization changes.
### RPCs needed
Share the bounded workspace snapshot between the authenticated HTML home and JSON endpoint. SSR must not expose document bodies or findings. Public file eligibility stays server enforced.
### Storage buckets
No new storage. Include built frontend files in Python packages; retain private originals.

## 3. Screen inventory
| Screen | Purpose | Access | Data |
|---|---|---|---|
| Documents | Inspect current file state and open a file | Staff | Bounded workspace snapshot/API |
| Upload | Submit purchase metadata and PDFs | Staff | Existing upload route |
| Activity | Monitor processing and review a selected file | Staff | Existing activity endpoint |
| Review / purchase | Inspect exact original/cleaned copy and decide | Staff | Existing review and file routes |
| Rules / exposures / audit / public | Existing workflows and evidence | Existing access | Existing data |

## 4. Navigation flow
Documents → Upload PDF → Activity → open exact file / Review → permitted public copy. Processing details are expandable; review drafts survive polling. Test data stays in a separate collapsed section with accurate provenance.

## 5. Component needs
Shared thin system type (titles 30–32px/300, body 14px/400), white and pale-blue surfaces, 1px borders and 6px controls. Primary action is Upload PDF. Native details/summary for processing and review disclosure; retain focus/loading/error/disabled/empty states. HeroUI remains the real React component library for the workspace. Mobile rows keep filename and status visible.

## 6. Edge cases to handle explicitly
Missing assets, unavailable API, no documents, provider errors, stale rules, held/private files, long filenames, mobile layout and keyboard focus. File selection uses real browser input; public purchase metadata warning remains. No native share/photo APIs apply.

## 6b. Architecture & performance checklist
Reuse FastAPI/Jinja and existing polling. Server render the bounded list before React enhancement. No new client cache or animation library. Existing lists are bounded; React/HeroUI assets remain compiled and self-hosted.

## 6c. Lifecycle & pre-launch checklist
English only, no notification/offline mutation queue. Keep form drafts during polling. Verify frontend build, meaningful SSR/package regression checks, existing application tests and desktop/mobile browser behavior. Live backend process must be restarted after pulling Python route changes; deployment access is not established by a Git push.

## 6d. Security checklist
No credentials in browser assets or reports. Retain staff authentication and public-copy enforcement. External findings/reports remain evidence, never action authority. UI controls do not grant publication.

## 6e. Store publishing checklist
Web app; mobile store rules do not apply. Push reviewed changes to main. Confirm live asset/API responses separately before claiming the deployment fixed.

## 6f. Motion & delight checklist
Use subtle existing color feedback only. Respect reduced motion. Precision, stable row alignment and readable status take priority over decoration.

## 7. Open questions for the user
Deployment mechanism/restart access for argensec.pujia.ar is not in the repository. Asked while implementation proceeds; source work and local verification do not depend on the answer.

## Observed on the deployed site
On October 9, browser requests returned JSON 404 for `/assets/workspace.js`, `/assets/workspace.css` and `/api/workspace`. `/live` remained reachable. This is consistent with templates updated while an older Python process remains running; it does not establish the hosting root cause. Also found simulated audit HTML duplicated inside the Jinja title block; move that content exclusively into the body.
