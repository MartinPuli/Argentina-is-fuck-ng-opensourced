# Publication Gate Operations UI - Build Plan

## 0. Who this is for
- Users: institutional document reviewers and procurement operators.
- Problem: the current workspace reads like a landing page and spreads a single review task across explanatory screens.
- Solved: users immediately see pending work, open the relevant file and take the next action; learning rechecks report actual outcomes.
- Scope: existing web frontend plus a read-only operational summary endpoint. User specifies sky blue and white, no logo, no slogans or explanatory subtitles. Product language stays English.

## 1. Three-phase breakdown
| Phase | Theme | Features included | Forward-look detail level |
|---|---|---|---|
| 1 | Core loop | Operational home, concise navigation/tables/forms, sky blue/white system, real document status filters, preservation of review and learning controls | Full below |
| 2 | Completeness | Corrected-file version workflow and granular reviewer roles | Future work; requires version-specific publication authorization and separate scope |
| 3 | Depth & delight | Saved worklists, cross-case navigation and workload preferences | Future work after the operational flow is validated |

# Phase 1 detailed plan

## 2. Backend
### Tables
No existing attachment or rule schema changes. No new tables. Corrected-file revisions and durable recheck-result reports are deferred.
### RLS policies
Existing server-side staff authentication and exact-origin mutation checks continue. Operational summaries and recheck results are staff-only; public eligibility still checks the current rule revision.
### RPCs needed
Home context reads attachment counts and a bounded recent list from stored facts. The read-only workspace API returns current counts and a bounded recent list; no new mutation flow. Existing mutation contracts remain compatible.
### Storage buckets
No new public storage. Source PDFs remain private.

## 3. Screen inventory
| Screen | Purpose | View | Data source |
|---|---|---|---|
| Documents / home | Pending work, real counts, recent files, direct actions | Staff | Existing purchases/attachments plus current rule checks |
| Live | Running jobs and reviewer actions | Staff | Existing activity API |
| Upload, purchase, review | Submit, inspect findings and record decisions | Staff | Existing app routes |
| Rules and recheck results | Test, activate, recheck and see consequences | Staff | Existing rules plus actual recheck results |
| Exposures / audit / public | Source evidence, event records and eligible downloads | Appropriate existing access | Existing data |

## 4. Navigation flow
Documents → upload or inspect → review → public file. Rules → candidate tests → activation → existing recheck flow → affected purchase/review. Preserve detailed sources and operational error explanations where they inform a decision.

## 5. Component needs
Compact text navigation, 1px table borders, 4–6px corner radii, system typography, restrained sky-blue controls and white content. No logo, monogram, decorative symbol, hero illustration, eyebrow, slogan or explanatory subtitle. Status labels and necessary validation remain. Forms retain disabled/loading/error/empty states and keyboard focus. Tables scroll internally on narrow screens.

## 6. Edge cases to handle explicitly
Empty documents/review/rule lists, stale approvals, unavailable providers, failed or partial rechecks, invalid inputs and inaccessible files. Narrow screen navigation and horizontal table scroll. No mobile-native APIs or platform share flows apply.

## 6b. Architecture & performance checklist
Keep FastAPI/Jinja and existing JavaScript for existing screens. Use actual HeroUI v3 components in a small React 19 + Tailwind 4 document workspace, compiled with Vite into self-hosted static assets. Bound home results and avoid unbounded browser polling. Only the document workspace adds React/HeroUI; preserve server-rendered forms and backend contracts. Commit the lockfile and compiled assets so Python deployments do not need Node at startup. Reuse server authorization and existing current-rule checks.

## 6c. Lifecycle & pre-launch checklist
No new secrets or services. Tests isolate storage and disable providers. Verify functional changes with meaningful outcome tests; visually inspect desktop and phone widths. English UI. No notifications or offline mutation queues.

## 6d. Security checklist
Keep staff-only operational data, same-origin POST checks and fail-closed file access. Never replace source evidence labels or mask missing analysis. Source titles and filenames remain escaped. A recheck summary cannot itself grant publication.

## 6e. Store publishing checklist
Web app, not an app-store release. Pull teammates' changes, inspect the final diff, run relevant checks and push to the user-requested main branch. Do not imply a verified hosted deployment.

## 6f. Motion & delight checklist
No decorative animation. Existing loading indicators may remain with reduced-motion support. Prioritize readable, stable tables and persistent review inputs.

## 7. Open questions for the user
None. Audience, team product, English text, main branch and visual direction are explicit.


## Final visual brief

Read as: an operational document workspace for institutional reviewers, with quiet sky-blue and white surfaces, light sans-serif typography, and HeroUI controls. User-selected `design-taste-frontend` is primarily a landing-page skill; use its audit, consistent-system and interaction principles that fit this workspace. The explicit minimal operational brief overrides its marketing-image and cinematic defaults. `frontend-design` informs restrained spacing and clear action labels.

Tokens: paper #ffffff, navigation #f0f8ff, selected #deeffb, primary control #c4e8f9, text #253d4b, secondary text #607583. Page titles 28–32px/300, sections 16px/400, controls and body 13px/400. No visible product name, logo, explanatory subtitles or decorative hero.

Layout: slim text navigation → compact document header/actions → current counts → filter/search toolbar → file table. Main action is Upload PDF; row actions open the exact file within its purchase. The characteristic content is the document's current publication state, never an invented protection score. Later request narrows this pass to visual simplification and read-only workspace data; new correction workflows and recheck reports are deferred, with incoming teammate work retained.
