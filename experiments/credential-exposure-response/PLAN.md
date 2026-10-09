<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# Credential exposure response - Build Plan

Written before implementation, October 9, 2026. Adapted from the user-selected repository-local [AppBuilder planning template](../../.agents/skills/app-builder-design-system/references/planning-template.md). This is a research backend experiment, not the application build.

## 0. Who this is for
- Target users: institutional security/operations teams and reviewers of BREACHSTOP's evidence.
- Current problem: the earlier experiment receives a trusted compromise event rather than corroborating exposure.
- Solved: an observer detects a known synthetic exposed-credential route; a separate controller verifies the exposure and current generation before a bounded response; independent clients observe both prevented disclosure and interrupted legitimate work.
- Scope: Python standard-library local backend experiment. UI, mobile, Supabase, sponsors and LLMs are not part of this phase.

## 1. Three-phase breakdown
| Phase | Theme | Features included | Forward-look detail level |
| --- | --- | --- | --- |
| 1 | Core loop | Separate app/gateway/controller/observer processes; known-route observation and independent corroboration; four matched modes; A/B scope; replacement; false/stale/duplicate command cases; independent response counting; protocol, results and limits. | Full below. |
| 2 | Completeness | Possible later enforced OS isolation, crash recovery and authenticated external evidence. | Deferred; not promised by this experiment. |
| 3 | Depth & delight | Possible later real agent/sponsor evaluation and interface. | Deferred to the product plan. |

# Phase 1 detailed plan

## 2. Backend
### Tables
| In-memory state | Key fields | Notes |
| --- | --- | --- |
| Gateway identity registry | identity, generation, token, active, allowed owners | Fresh values; no credential persistence. Issuing a replacement does not revoke an older generation. |
| Application | current credential/generation, exposed-route flag | Separate process; legitimate requests use the current credential at the gateway. |
| Controller | fixed enrolled origin/route/identity, mode, completed operation IDs | Privileged gateway and repair credentials stay out of the app/observer processes. |
| Client observations | status, redacted body, actual delivered fictional IDs | Evaluator labels stay in the harness, never go to services. |

### RLS policies
No SQL tables or RLS engine. Gateway enforces owner scope on every request in every mode. A can read owner A; B is allowed both owners and large batches. Controller verifies exact enrolled target and corroborates content rather than trusting a compromise flag. Same OS user and privileged test harness remain explicit trust assumptions.

### RPCs needed
| HTTP operation | Purpose | Authorization |
| --- | --- | --- |
| Application known exposure GET | Intentionally disclose its fictional current credential until repaired | Deliberately unauthenticated fixture. |
| Application legitimate read | Forward requests to gateway | Separate synthetic client bearer. |
| Gateway records | Enforce current or older unrevoked token's scope | Service bearer. |
| Controller evidence POST | Validate bounded metadata, independently GET fixed route, compare gateway generation/digest, respond | Observer bearer; no arbitrary URL/action. |
| Gateway revoke/issue; app repair/replace | Execute exact bounded state changes | Separate controller-only control bearers. |
| Controller recover POST | Issue replacement and provision app | Harness recovery bearer, fixed identity/generation, idempotency. |

### Storage buckets
None. Fixtures are fictional. Persist only sanitized transcripts, hashes and aggregates in this new directory. Credential-bearing responses stay in memory; output serialization checks known token values are absent.

## 3. Screen inventory
None. Machine-readable results and an English README are the review interface.

## 4. Navigation flow
Read protocol/workload → run baseline and response modes → independently observe HTTP results → validate declared checks → inspect limitations. No mobile navigation.

## 5. Component needs
HTTP services and harness only. Handle permission denied, malformed/oversized evidence, missing exposure, generation mismatch, duplicate/conflicting operation, transport failure and unsuccessful response without claiming containment.

## 6. Edge cases to handle explicitly
Mobile sharing, safe areas, images, forms and responsive typography are N/A. Required backend cases: false digest; wrong target/origin; stale generation; unauthenticated evidence; duplicate/conflicting response; old credential after replacement; renewed leak after revoke-only; legitimate A interruption and B continuity. Fixed known-endpoint observation is not a general scanner.

## 6b. Architecture & performance checklist
No UI list/animation/cache needs. Python chosen for standard-library reproducibility, adapting the template's TypeScript default. Spawn distinct processes, use literal127.0.0.1 only, refuse redirects and proxies, bound request/response sizes and HTTP timeouts. Sequential workloads; report request outcomes, not unmeasured production latency or concurrent cancellation.

## 6c. Lifecycle & pre-launch checklist
One local synthetic environment; no production config, credentials, SDKs or telemetry provider. English docs. Explicit network/process failure stops the run. Process cleanup in all outcomes. Meaningful assertions cover the actual control and availability effects. No push notifications or offline behavior beyond clear failure.

## 6d. Security checklist
No database migrations or client UI. Every privileged HTTP operation checks a bearer. Fresh credentials travel only in process pipes or loopback HTTP. Logs suppress request bodies and tokens. No external networking or public binds. This is not hardened authentication, TLS, rate limiting, operating-system isolation or protection from a compromised trusted controller/gateway. The harness owns setup credentials; this is an evaluator boundary, not a production secret-distribution design.

## 6e. Store publishing checklist (once shipping is in view)
N/A: no app-store build, personal accounts or public deployment.

## 6f. Motion & delight checklist
N/A: no visual interface or animation.

## 7. Open questions for the user
None needed for this bounded authorized experiment. Unknown production hosting, evidence authentication and sponsor access remain outside this phase.
