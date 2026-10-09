# In-flight revocation — Build Plan

License: CC BY 4.0. Written before implementation. This plan adapts the required [AppBuilder planning template](../../.agents/skills/app-builder-design-system/references/planning-template.md) to a local research backend. Scope and institutional security/operations audience are already agreed.

## 0. Who this is for
- Target users: institutional security and operations reviewers.
- Problem: a credential can be rejected on new requests while earlier streams and queued jobs still release records.
- Solved for this experiment: reproducible actual HTTP response bytes show the difference between admission-only checks and authorization checks at each protected output boundary; affected legitimate work and independent authority remain visible.
- Scope: Python standard-library research backend and independent client, no UI, model, sponsor, public deployment, real credentials or personal data. Inspired by [RRR-01](../../docs/research/REVOCATION-AND-RECOVERY-RESEARCH.md#rrr-01); not a reproduction or implementation of its complete protocol.

## 1. Three-phase breakdown
| Phase | Theme | Features included | Detail |
|---|---|---|---|
| 1 | Core measured loop | Separate gateway/controller processes; fresh credentials; actual HTTP NDJSON stream and queued output; explicit barriers; entry-only versus per-output generation check; pre/post-ACK client bytes and IDs; legitimate A interruption and B continuation; bounded generic runner; sanitized hashes and cleanup | Full detail below |
| 2 | Independent review | Parent-owned altered workloads and independent checker | Parent review after source-stable handoff; no implementation here |
| 3 | Broader systems questions | Durability/restart, unmediated sinks, backpressure and distributed proxy/socket-buffer races | Deferred; this experiment makes no claims about them |

# Phase 1 detailed plan

## 2. Backend
### Tables
No database. In-memory records by owner; credential generation/active state; admitted stream contexts and queued jobs. State is not durable.
### RLS policies
RLS is inapplicable. Server validates bearer credential, owner and every requested record at admission. Per-output mode also validates admitted generation at every protected line. Controller alone holds revocation authority; separate coordinator capability releases test barriers. All binds are literal 127.0.0.1.
### RPCs needed
| Endpoint family | Purpose | Authorization |
|---|---|---|
| Data stream, queue, ordinary read | Serve only the admitted owner's fictional records | Fresh A/B bearer credentials; admitted queue capability for completion |
| Controller revoke | Forward fixed-enrollment A revocation to gateway | Separate fresh controller command capability |
| Gateway revoke | Change A generation and acknowledge a serialized output boundary | Gateway administrator capability; same mutex as check/write/flush |
| Test barriers | Wait for/continue admitted stream and release queued work | Separate fresh coordinator capability; does not grant data access |
### Storage buckets
None. Save only sanitized fixture data, observed IDs/byte counts/body hashes, source/workload hashes and process IDs. Credentials remain in memory and are never logged or persisted.

## 3. Screen inventory
Not applicable: no screens. JSON results and an English README are the reviewer interface.

## 4. Navigation flow
Start gateway/controller → A/B authorized reads → admit A stream and queue → client receives declared prefix → await server barrier → controller revokes and client observes ACK → release stream and queued worker → client receives exact outcomes → new A read/B batch → stop processes.

## 5. Component needs
No UI components. Service startup, response stream, job and control operations have explicit success, denial, timeout and cleanup paths. Tests fail visibly rather than reporting containment after missing evidence.

## 6. Edge cases to handle explicitly
Mobile/share/safe-area/image-picker/form/type checks do not apply. Backend cases: no records; invalid owner/credential; bounded bodies/lines; multiple prefix lengths; queued work admitted before revocation; new A denial; B continuity; explicit server barrier; EOF; duplicate release; process cleanup. Admission-only queue results intentionally use the admitted job capability and are not re-authorized as a new ordinary read.

## 6b. Architecture & performance checklist
No mobile lists/animations/shared-screen state. Python standard library is deliberate, not TypeScript: a small backend measurement harness. Bounded fixture sizes and socket/event timeouts. Two service processes plus parent HTTP client; same OS user is not a sandbox boundary. No latency/throughput claim.

## 6c. Lifecycle & pre-launch checklist
No production environment, EAS, Supabase, device permissions, push or account lifecycle. Exceptions are local test failures; no external crash reporter. English docs only. Meaningful end-to-end assertions required. Network is loopback only; offline external access is not needed. Always stop child processes on success or failure.

## 6d. Security checklist
No database/RLS or client-side service keys. Every privileged endpoint verifies its own capability. Tokens use secure randomness and remain in process memory/spawn IPC. Loopback URL allowlist, bounded parsing and request timeouts. No SDKs, telemetry, secret values or real data persisted. This does not resist a malicious process with the same OS user. The trusted controller is explicitly invoked; compromise detection is not tested.

## 6e. Store publishing checklist
No app store, public service, accounts or real user data. Publishing the sanitized research artifacts is parent-owned; this task makes no git changes.

## 6f. Motion & delight checklist
No UI, animation, gestures or celebration. Token/motion/reduced-motion requirements are inapplicable.

## 7. Open questions for the user
None needed for the authorized narrow experiment. Limits are predeclared: already emitted bytes cannot be recalled; unmediated writes or separate check/write operations reintroduce races; serialization can delay revocation under slow output; no durability or distributed-provider proof.
