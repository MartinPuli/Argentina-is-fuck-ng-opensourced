<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# Reviewed lesson transfer - Build Plan

Written before code, October 9, 2026, using the selected [AppBuilder template](../../.agents/skills/app-builder-design-system/references/planning-template.md). The skill and backend, architecture, lifecycle, security and file-structure references were read for the preceding experiment at the same pinned version. Their mobile/Supabase examples are inapplicable here.

## 0. Who this is for
- Users: institutional security/operations teams and research reviewers.
- Problem: a fixed endpoint check may not transfer when another enrolled application exposes the same kind of credential through changed JSON fields and routes.
- Solved: measure whether an explicitly reviewed synthetic mechanism rule catches changed exposures without blocking harmless public metadata or expanding its authority.
- Scope: standard-library local backend experiment. No UI, mobile, LLM, sponsor or public deployment.

## 1. Three-phase breakdown
| Phase | Theme | Features | Detail |
| --- | --- | --- | --- |
| 1 | Core loop | Actual source exposure; static reviewed lesson; digest-pinned owner policy; original-path and mechanism checks; changed/benign/unsupported/unenrolled cases; independent corroboration; HTTP effects; mutation rejection and results. | Full below. |
| 2 | Completeness | Real authenticated human review, durable provenance, broader route discovery and enforced OS isolation. | Deferred, not claimed. |
| 3 | Depth and delight | Possible agent-assisted proposal/review and product interface. | Deferred to product work. |

# Phase 1 detailed plan

## 2. Backend
### Tables
No database. In-memory service credentials/permissions reuse the prior gateway. A separate controller receives a fixed owner enrollment and exact approved lesson digest. The served route inventory is a fixture; the observer receives only the owner-approved subset. Client results retain sanitized responses and fictional record IDs.

### RLS policies
Gateway owner scope remains enforced independently of the observer/controller. A lesson's `approved` string grants nothing: controller policy separately pins the full digest, service identity, permitted route inventory and the single revoke action. Changed action/applicability/provenance or extra target fields are denied.

### RPCs needed
Bounded GETs of known fixture JSON routes; authenticated controller evidence POST; gateway current-generation lookup and conditional revoke. Reuse the prior gateway and HTTP/process helpers. No arbitrary URLs, candidate-token probes against records, repair, rotation or code execution in this lesson check.

### Storage buckets
None. Source, lesson and fixture schemas are local; result files contain only fictional records and redacted evidence. Raw source and target credentials remain in memory and are never embedded in the lesson.

## 3. Screen inventory
N/A. English README and JSON artifacts are the review interface.

## 4. Navigation flow
Observe source → inspect static reviewed rule and external policy pin → run two checks over matched changed fixtures → compare real data responses and legitimate operations.

## 5. Component needs
Fixture application, reused gateway, separate corroborating controller and external client/observer. Explicit states: no route; no matching credential; unsupported response; unenrolled route; altered lesson; malformed evidence; successful conditional revocation; legitimate A interruption and B continuity.

## 6. Edge cases to handle explicitly
Mobile forms, media, sharing, safe areas and responsive layouts are N/A. Cover nested renamed credential field, legitimate token-like metadata, non-object response, inventory mismatch, untrusted text requesting broader authority and modified lesson payloads. Source labels and evaluator expectations are never sent to gateway/controller.

## 6b. Architecture & performance checklist
Python chosen for standard-library reuse; no TypeScript/UI layer. Literal loopback only; bounded JSON depth/candidates, response bytes and timeouts. Sequential calls, no latency or throughput claims. Independent controller re-fetches exact enrolled route and compares a candidate with the live current gateway credential before revocation.

## 6c. Lifecycle & pre-launch checklist
Fresh credentials and ephemeral processes per case/mode. Cleanup after failures; no production config, crash SDK, localization, notifications or offline support. Main assertions check actual outcome bodies. Independent checker/results filenames are reserved for parent review.

## 6d. Security checklist
Server-side control authorization and exact lesson hash allowlist; no trust in labels or prose. Same local OS user and privileged harness remain assumptions. The code-writing assistant authors the lesson; the harness pins its exact digest as a simulated owner-review precondition. No actual human approval event, automatic rule induction or authenticated owner workflow is demonstrated.

## 6e. Store publishing checklist (once shipping is in view)
N/A: research backend only.

## 6f. Motion & delight checklist
N/A: no interface or animation.

## 7. Open questions for the user
None needed for the bounded experiment. Real approval, enrollment and integration arrangements remain future product work.
