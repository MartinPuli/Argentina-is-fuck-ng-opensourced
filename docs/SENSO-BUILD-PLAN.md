# Senso and official guidelines - Build Plan

## 0. Who this is for
Institutional publication reviewers need inspectable guidance and incident lessons, rather than unsupported model instructions. Scope: the existing Python web application and backend; no mobile application or new authentication model.

## 1. Three-phase breakdown
| Phase | Theme | Features included | Detail |
|---|---|---|---|
| 1 | Core loop | Correct cited guidelines, inspect them, ingest the reviewed pack into Senso, retrieve scoped context for inactive proposals, retain receipts, test PDF boundaries | Below |
| 2 | Completeness | Discover public incident reporting, inspect leads, use selected sanitized lessons | Delivered after the core loop |
| 3 | Depth | Larger held-out evaluation and additional document controls | Future; not a claim of current coverage |

## 2. Backend
### Tables
`senso_documents`: guideline-pack digest, content/node IDs, ingestion state and timestamp. `learning_rule_context`: immutable proposal context snapshot keyed by rule ID. Existing learning tables retain approval authority.
### RLS policies
SQLite has no RLS. Staff authentication and same-origin checks protect all provider operations and receipts. Public access is limited to authored guideline summaries and official links.
### RPCs needed
Staff POST sync/refresh/retrieve actions call fixed Senso endpoints with a server-only key; no client-selected provider URL. A proposal request explicitly selects Senso and fails if its scoped context is unavailable.
### Storage buckets
None. No uploaded PDFs or victim records are ingested into Senso. Only the authored public guideline pack is uploaded in Phase 1. Incident summaries stay explicitly unverified.

## 3. Screen inventory
`/guidelines`: public source browser. `/learning`: staff context state and sync controls. Rule detail: cited context used for that exact candidate.

## 4. Navigation flow
Rules → Guidelines → sync reviewed pack → refresh processing → source proposal with Senso → tests → human activation. Existing upload/review/public routes remain intact.

## 5. Component needs
Reuse existing details, field, notice and asynchronous form components. Distinct not-configured, processing, ready, unavailable and no-match states; never equate a configured key with a verified connection.

## 6. Edge cases
Bounded input/output, duplicate ingestion, stale guideline pack, partial processing, foreign content IDs, missing versions, malformed responses, authentication/credit failures and source-instruction injection. No automatic publication or activation. New views wrap on narrow screens.

## 6b. Architecture & performance
Existing FastAPI/Jinja/httpx stack, synchronous bounded requests in worker routes, no new SDK. Lists bounded; mobile/React Native practices inapplicable.

## 6c. Lifecycle
Server-only environment config, redacted provider errors, explicit offline state, business-boundary tests and browser PDF regressions. No notifications or new permissions.

## 6d. Security
No secrets in responses; scoped content IDs validated against locally recorded guideline digests. Remote context is evidence, never instructions. Local policy remains authoritative. Test activation and public-byte enforcement independently of provider results.

## 6e. Store publishing
Inapplicable: web application. Deployment and live-provider evidence reported separately.

## 6f. Motion
No new motion; reuse existing loading/status feedback.

## 7. Open questions
Live Senso organization access requires `SENSO_API_KEY`. Access was supplied during implementation and verified; the key remains in ignored local configuration. AkashML live generation remains a server-side verification step.

# Phase 2 detailed plan — public reporting discovery

## 2. Backend
`incident_leads` stores a bounded list of public headline metadata. SQLite access is restricted through authenticated staff routes; no new public API exposes the collected leads. A fixed Google News RSS endpoint/query avoids arbitrary URL fetches. Use a hardened XML parser, bounded response size and no redirects. Discovery cannot create or activate rules.

## 3. Screen inventory
Reuse `/learning`: explicit search button, empty/error states, publisher/date/unverified labels and source selection into the existing sanitized-summary form.

## 4. Navigation flow
Find recent reports → inspect original separately → Use source → review sanitized evidence → existing Senso/proposal/test/approval flow.

## 5. Component needs
Existing asynchronous form, source rows and input fields; no animation or new design system.

## 6. Edge cases and implementation checks
Deduplicate identical article URLs, preserve prior leads on request failure, reject malformed feeds/links, keep claim status unverified and do not count headlines as incidents. Staff authorization and same-origin checks apply. Responsive existing source-row layout and browser controls are retained. Mobile/store-specific sections are inapplicable; no SDK, permissions, notifications or background schedule is introduced.

## 7. Open questions
No additional information needed for this bounded discovery flow. Confirming an incident or its cause requires further evidence, never a guessed model classification.
