<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# BREACHSTOP: a feasible three-sponsor defense workflow

**Documentation checked: October 9, 2026. Status: integration design, not an executed sponsor demonstration.** Account access, credentials, deployed services and tool permissions were not inspected or changed for this review.

Build one chain: **a fictional service credential is exposed; independent observations establish the exposure; Guild investigates using ClickHouse evidence and Semgrep findings; a separate controller revokes that credential; a repair is rehearsed; independent requests verify recovery; the agent publishes a real GitHub PR.** Keep publication mistakes as a second, explicitly different module. This follows [the build proposal](WHAT-TO-BUILD.md) and the [event brief](../EVENT-BRIEF.md), which requires three substantive sponsor integrations and real open-web action.

Publishing research or displaying sponsor logos does not demonstrate this chain. A PR is real public action; the complete proposed defense demonstration additionally needs a controlled release and independent checks of the actual HTTPS service.

## Match each incident to the supported mechanism

| Research evidence | Appropriate control to demonstrate | Unsupported inference to avoid |
| --- | --- | --- |
| Investigations describe stolen account details and unauthorized access; Río Negro acknowledged payroll disclosure with suspected employee misuse. | Approved record scope, separate service identities, corroborated compromise evidence, revocation and independent retry. | A high request count proves theft, or an employee identity authorizes every record. |
| PAMI's 2026 purchasing attachments were publicly accessible. | Separate public package, accountable classification, exact artifact approval and unauthenticated verification. | A database gateway protects files already copied to a public website, or our stale-build fixture reconstructs PAMI's cause. |
| IOMA, SCBA and other cases have varying acknowledgments and incomplete technical detail; other claims remain disputed. | Evidence preservation and owner-authorized investigation; apply a regression only after confirming applicability. | A headline identifies a vulnerable endpoint, exploit, credential or safe patch. |

Use [the incident timeline](../INCIDENTS.md) and [PAMI contribution review](PAMI-CONTRIBUTION-REVIEW.md) as the evidence boundary. The teammate's [PAMI analysis](<../../PAMI Data Exposure Problem Analysis.md>) distinguishes publication, intrusion and fraud. Its reconstructed publication workflow is useful; its unresolved historical details must not become an invented server attack. National incident statistics, where added to the research, must retain their calendar period and incident categories rather than becoming counts of confirmed leaks.

An actual operating-system compromise requires a separately protected enforcement point and trusted host recovery. The existing application and publication experiments do not demonstrate removal of a host intruder.

## Sponsor roles and concrete constraints

### ClickHouse: observed activity and measured outcomes

Use a small external ingestion service to write sanitized gateway and verifier events to ClickHouse, then expose a few parameterized incident queries to Guild. The official Node client supports inserts, parameterized queries and query IDs over HTTP(S). It runs in the adapter, not inside Guild's TypeScript agent. The connection requires a service URL, database and authenticated database user. [Official JavaScript client](https://clickhouse.com/docs/integrations/language-clients/js/index).

For this demo, use acknowledged batches or `async_insert=1, wait_for_async_insert=1`. Async data cannot be queried before flushing; fire-and-forget acknowledgement does not establish persistence. Record event time, ingestion acknowledgement and first successful query separately. This prevents an ingestion delay from being mislabeled detector latency. [Async insert behavior](https://clickhouse.com/docs/concepts/features/operations/insert/asyncinserts).

Give the ingestion account only the needed write privileges and the incident-query account only the needed read privileges; keep administration separate. ClickHouse provides users, roles and grants, but an analytics account is not the application's containment controller. [Access management](https://clickhouse.com/docs/concepts/features/security/access-rights).

Proposed event fields: `run_id`, unique `event_id`, trusted source, service identity, opaque credential reference, source/deployment revision, operation, authorization outcome, response byte count, fictional record count, event time and receipt time. Preserve request attempts separately from successful deliveries. Deduplicate analysis by event ID and reconcile totals with the verifier's independent record set. No citizen rows, medical files, request-body dumps or credential values enter analytics.

Substantive evidence: the actual inserted event count, query ID and result used by the agent, ingestion lag, query latency and a reconciliation against independently observed responses. Report the measured scale; a small working dataset does not establish national-scale capacity.

### Guild: the hosted agent and its bounded tools

Use a TypeScript LLM agent with a small typed tool list. Current SDK documentation identifies `@guildai/agents-sdk` 0.6.0 with Zod `~4.3.0`, root object schemas, no arbitrary npm/Node imports and no direct outbound HTTP. External calls must go through Guild integrations. Its experimental fetch is intended for public unauthenticated URLs; its `max_bytes` limit does not cap JSON bodies. Enforce result limits at our adapter. [SDK/runtime restrictions](https://docs.guild.ai/guide/sdk-introduction).

Create an authenticated REST integration for the adapter using self-contained OpenAPI 3.0/3.1 schemas. Integration URLs cannot target loopback/private networks, and publishing freezes the endpoint URL. Consequently, the current `127.0.0.1` experiments cannot simply be registered as hosted tools: a new controlled, authenticated HTTPS adapter is required. Test the integration before choosing it for the demonstration. [Custom integration setup](https://docs.guild.ai/services/create-an-integration).

Guild documents server-side credential injection and tool-call policy checks. **New credentials initially have an allow-all policy**: replace that with narrowly permitted operations and test denials for another repository, identity and workspace. Its session event log can supply execution evidence. These are vendor-documented capabilities; our deployment's effective policy still needs verification. [Security architecture](https://docs.guild.ai/platform/security-architecture).

Use the official GitHub integration for the allowed repository and selected PR operations. It uses a GitHub App scoped to installed repositories; repository installation and appropriate permissions are prerequisites. A published PR URL and Guild session/tool trace establish the action. [GitHub integration](https://docs.guild.ai/integrations/github).

### Semgrep: reproducible source findings and candidate rescanning

Run Semgrep in the isolated external repair/check runner. The lowest-dependency path is Community Edition SAST with pinned local rules and JSON output. CE supports custom rules but does not supply the AppSec Platform's Secrets/Supply Chain capabilities or managed finding history. A custom SAST rule identifying a credential-returning route must be described as that rule, not as validated secret discovery. [CE deployment and differences](https://docs.semgrep.dev/deployment/oss-deployment).

Do not equate exit code zero with a clean scan: `semgrep scan` normally does not fail on findings; `--error` changes that behavior. Check scan errors and expected file coverage as well. Save scanner version, rule revision, source SHA, rule ID, path and location, plus baseline/candidate output. Parse actual JSON fields rather than inventing platform-only identifiers. [CLI reference](https://docs.semgrep.dev/cli-reference), [JSON/SARIF fields](https://docs.semgrep.dev/semgrep-appsec-platform/json-and-sarif).

Guardian is a separate authoring-time integration. Its recommended Claude Code/Codex plugins use a hosted server and OAuth with a fixed ruleset; local CLI paths behave differently. Installing Guardian on a developer machine does not show that a Guild run performed a scan. The candidate repair can be authored with Guardian if available, while the reproducible runner remains responsible for the demonstrated scan. [Guardian overview](https://docs.semgrep.dev/semgrep-guardian/overview).

First prove that the selected rule detects the exact fixture before promising that connection. A deliberately seeded weakness is valid demo material but is not a novel vulnerability discovery or automatically eligible for the Semgrep bounty. For a separately discovered problem in AI-generated code, retain its generation history, unmodified finding and independent reproduction; award eligibility remains an event decision.

## One continuous run, with evidence before action

1. **Enroll and freeze context.** Record the owned repository, allowed patch paths, deployment target, A/B service identities, permitted data operations, required legitimate workflows, approved response policy and immutable verification revision. Store permissions outside the app and repair worker. An unknown or conflicting policy prevents mutation.
2. **Establish the baseline.** An independent client reproduces a labeled disclosure fixture in A and records fictional IDs actually received through A's credential. B completes an approved batch. The protected service supplies its own events; an application log alone cannot certify compromise. Keep the recovered synthetic credential in the verifier/controller boundary, passing only an opaque reference and proof metadata to the agent.
3. **Investigate with all three sponsors.** The runner scans the exact baseline revision with Semgrep. ClickHouse correlates the relevant events. Guild reads the approved contract, actual query result and finding, then explains the supported link and selects the allowed response. A scanner finding alone does not prove exploitation; ordinary volume alone does not identify a thief.
4. **Contain through a separate controller.** Guild proposes `revoke_identity` with run ID, enrolled target, evidence references, policy version, expiry and idempotency key. Controller code corroborates the evidence and validates scope before executing. It owns the privileged credential; the agent does not. The app has no direct database route around enforcement. A separate client proves the old credential fails and B continues; measure the legitimate A operation interrupted by revocation.
5. **Prepare and rehearse a repair.** Guild proposes a patch to allowed application files. A disposable runner applies it, rescans and builds a fresh candidate. Independently controlled tests check the original disclosure, renamed paths, cross-owner requests, permitted operations and old-credential rejection. Neither the patch worker nor its generated code can change tests, approval rules or the expected permissions.
6. **Publish and recover.** After the candidate is reviewable, Guild creates the real PR with sanitized evidence. A separately authorized release executor promotes only the verified artifact and provisions replacement access. The external HTTPS verifier retries the original credential, checks the new deployment revision and measures restored A/B workflows. A failing check leaves the incident unresolved; it does not silently re-enable compromised access.

The minimal custom tool surface is `get_contract`, `get_incident_evidence`, `get_scan`, `propose_revocation`, `rehearse_patch` and `get_verification`; each targets a fixed enrolled environment. These are proposed BREACHSTOP API operations, not existing sponsor APIs. The controller and runner may share an API facade but must have separate execution credentials and permissions. No arbitrary shell command, SQL string, target URL or cloud administrator operation is exposed to the agent.

## Effects to measure and claims to keep separate

Reuse identical workloads across ordinary scope enforcement, scope plus simple volume cutoff, and the proposed response workflow. Count client-received records/bytes before and after enforcement, legitimate A/B completions, time to obtain sufficient evidence, decision delay, enforcement delay, verification time and missed/false actions. Slow within-scope misuse and legitimate large batches are required contrasts. Preserve no-alarm cases; do not average only successful detections.

The [current measured effects](MEASURED-EFFECTS.md) support deterministic scope/revocation and publication checks in local synthetic systems. They do not measure Guild reasoning, ClickHouse performance or Semgrep repair quality. The additional AI claim must be evaluated separately: did the agent choose a supported action, produce a correct repair and reduce response effort under the same evidence and permissions? Include incomplete evidence and a misleading log to expose unsupported decisions.

For the optional PAMI-inspired module, the same sponsors can record public-file observations, inspect relevant publishing code and coordinate a candidate release. The actual gate remains accountable classification plus exact artifact approval. Real PDFs, OCR, images, contextual health information, authenticated reviewer decisions and historical public copies require additional work. Our known-content verifier is not a general medical-document classifier; our misclassification counterexample already demonstrates that limitation.

## Access and work still missing

**Pi follow-up requested by the user:** the [separate assessment](PI-ASSESSMENT.md) establishes that a public OAuth MCP integration is documented. Evaluate it as an optional source of enrolled-service security context and repair guidance. Tenant access and Guild compatibility are unverified, and the event brief does not provide product access. Keep the three-tool core runnable independently; only count Pi after its actual output contributes to the demonstrated decision. Pi's output does not replace the controller or outcome verifier.

| Dependency | Must be established before claiming a working integration |
| --- | --- |
| ClickHouse | An accessible instance; service version; scoped credentials; endpoint/network configuration; working insert/query; latency and completeness measurements. Cloud credits and event entitlements are unverified. |
| Guild | Workspace/model access; agent publication; adapter integration; narrowed credential policies; GitHub App installation; actual session trace. Current runtime support must be tested against the chosen SDK version. |
| Semgrep | Available runner, selected language/rules, actual positive baseline and candidate scan; error/coverage handling. Guardian OAuth and paid engine/Secrets entitlements are unverified. |
| Our control plane | Authenticated public adapter; independently protected gateway/controller; evidence corroboration; isolated patch runner and verifier; version-bound release/rollback policy. |
| Real action | Agent-created PR; owned HTTPS target; approved release credentials; observed deployed hash and responses; shareable demonstration evidence. |

These are implementation prerequisites, not requests to install tools, create accounts, spend money or expose the local experiments during this research pass. The repository currently provides research and bounded local effects evidence; the hosted chain remains to be built and demonstrated.

Senso and Akash are optional extensions, not substitutes for getting the three required integrations working. Senso could retrieve reviewed incident lessons and exact contract revisions, but its approval tags are conventions, not authorization enforcement. Validate accepted versions outside the model. [Senso shared context](https://docs.senso.ai/docs/shared-context). AkashML offers managed inference through compatible APIs; its current onboarding describes a payment method for trial credits. Event credits, model availability and compatibility with the chosen Guild route remain unverified. It would provide inference, not containment. [AkashML introduction](https://akashml.com/docs/getting-started/introduction).

The [competitor review](../../competitor-profiles/_summary.md) already documents response automation, simulation and repair validation elsewhere. The defensible pitch is an inspectable open-source workflow connecting a supported failure mechanism to a bounded action and independently measured recovery. Neither orchestration nor rescanning is a proven novelty, and no common benchmark establishes superiority over those products.
