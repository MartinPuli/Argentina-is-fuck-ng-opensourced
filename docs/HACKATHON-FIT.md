# BREACHSTOP: hackathon fit assessment

**Date:** October 9, 2026
**Status:** Proposed product design. A separate [local reference experiment](research/MEASURED-EFFECTS.md) now measures deterministic controls using fictional data. The autonomous product, sponsor integrations, public deployment, submission and production evaluation remain incomplete.

## Product promise

BREACHSTOP is a proposed incident-response system for data leaks. It connects evidence about an entry point, a service identity and downstream data access; contains the affected identity through an independent enforcement service; repairs the application in isolation; and verifies a controlled recovery. It publishes a sanitized record of what happened and what the checks actually establish.

The user requested a more substantial system after reviewing the initial patch-and-test proposal. The revised architecture adds a resource relationship map, independent containment, explicit recovery states and service-continuity checks. The demo remains one complete attack chain rather than a claim to solve every kind of intrusion.

The Argentina research supplies the motivation, not a forensic diagnosis of every incident. It documents multiple mechanisms and unknown causes. This prototype addresses one application vulnerability that exposes database records; it does not claim to protect an arbitrarily compromised operating system, stop every breach, or recover previously leaked data.

## Requirements and evidence

The persistent event requirements are recorded in [EVENT-BRIEF.md](EVENT-BRIEF.md). Treat that brief as the project's event constraint reference; it preserves the distinction between the supplied portal text and independently checked sources.

The latest event text supplied by the user requires defensive AI, real autonomous action on the open web, truthful sources, and at least three sponsor tools. These are design constraints. The portal could not be retrieved independently on this pass. [Luma](https://luma.com/cyberhack) independently confirms autonomous remediation as an event focus and a 4:30 PM Pacific submission deadline.

| Requirement | Planned implementation | Evidence needed before claiming compliance |
|---|---|---|
| Defensive AI | Agent correlates an exposure event with source code and an actual scanner finding, then proposes a repair. | Incident, finding, source revision, patch and agent execution record. |
| Real open-web action | Agent opens a real GitHub pull request; a controlled release workflow updates our own public HTTPS demo after checks. | PR URL, deployed commit identifier and externally observed responses. |
| Autonomy | Within owner-defined scope, evidence gathering, selection of an allowed containment action, repair, verification and PR publication proceed without prompting for each step. | One continuous run trace; unknown permissions prevent mutation and failed tests prevent restoration. |
| Truthful grounding | Use actual code, observed requests, scanner output and an owner-approved access policy. Use the cited Argentina report only for background. | Every incident claim links to a captured observation; assumptions remain labeled. |
| Three sponsor tools | ClickHouse, Semgrep and Guild each participate in the executed workflow. | Query results, scan output and a Guild execution ID from the same run. |
| Security context before editing | Load a versioned application contract describing roles, data, permitted changes and expected behavior. | Contract revision attached to the run; checks enforce its boundaries. |

## Architecture: five connected responsibilities

1. **Resource and permission map.** Record which service uses which identity to access which dataset, who owns it, and what normal activity is permitted. Bootstrap from a small versioned inventory. Observed traffic supplies evidence, not permission to invent new trusted relationships.
2. **Investigation.** Correlate gateway events, application observations and scanner findings. Every proposed link in the attack chain carries its source and confidence. Count synthetic records actually delivered, separately from requests attempted and the larger set potentially accessible.
3. **Independent containment.** An external enforcement service validates a bounded action such as revoking service identity A. The affected application cannot change that policy or issue a replacement credential to itself. Give service B a separate identity so that its permitted work can continue.
4. **Isolated repair and recovery.** Preserve the evidence, patch in a separate checkout and construct a new deployment from a controlled build. A credential-exposure fix also requires rejecting the old credential and provisioning a replacement for the approved instance. Patching alone does not revoke a stolen credential.
5. **Independent verification and evidence.** Tests outside the repair agent's edit permissions verify denied access, continued healthy-service access, recovery of the repaired service, and the exact released revision. Public artifacts contain sanitized summaries and links, never real secrets or records.

Containment requires actual network and access boundaries: the application must not retain an unmediated route or direct credential to the underlying database. A disconnected telemetry dashboard cannot enforce containment. Real integrations would be institution-specific.

The workflow records explicit states: investigating, contained, repair under test, recovery under verification, restored or incomplete. If a patch fails, the affected component remains restricted; the system does not automatically undo containment just to restore a green status. Record the affected workflow's downtime honestly.

## Deploying guardians and deciding what to compare

The user's proposed interaction is to deploy agents to protected services and compare what they observe. Implement this as small per-service connectors plus an external reasoning coordinator and enforcement service. A full language model on every server is unnecessary.

Enrollment binds a connector to an owner-approved service identity, deployment revision, allowed data operations and response scope. In the prototype, a controlled deployment script installs connectors in our own application instances. It is not a universal installer for arbitrary government hosts. A connector sends request metadata, outcomes and health signals; the coordinator does not need a second copy of citizen records. Evidence from the external data-access service is particularly important because a compromised application may lie or stop reporting.

Useful comparisons are:

- **Observed access versus an approved purpose.** An individually scoped lookup credential must not inherit the rights of an approved batch-processing job.
- **Current configuration versus the approved version.** Identify newly public endpoints, expanded permissions or unexpected deployment changes using actual configuration evidence.
- **Multiple services sharing a component.** A reproduced flaw in one service creates a check for other services using the same component. Confirm each service's exposure and preserve its own access rules before proposing a change; do not copy permissions or declare a fleet-wide compromise from similarity alone.
- **Before versus after a response.** Confirm actual denial for the revoked identity, continued operation of permitted jobs and successful recovery of the fixed service.

A strong comparison for the demo is an approved batch job on B continuing to process many records while an unauthorized extraction using A is stopped. Request volume alone cannot explain or justify the decision. The batch authorization must come from a trusted policy outside either requesting application, not from a caller's self-declared purpose.

The core working slice remains A, B and the independently protected data-access service. Cross-service propagation of a new vulnerability check is an extension after the independent containment and repair loop works. Missing connector reports indicate lost visibility, not proof that the service is safe or proof that all services should be stopped.

This separation of identity, resource permissions and enforcement follows established defensive architecture principles; it is not a claim of inventing access control. [NIST SP 800-207](https://csrc.nist.gov/pubs/sp/800/207/final).

## One end-to-end scenario

Use two small applications, A and B, an independently protected data-access service, and fictional citizen records. A controlled credential-disclosure fixture in A starts the chain. It is deliberately introduced test material, not a claimed discovery in an Argentine government server. Before committing to the fixture, verify that the selected Semgrep rules or an explicitly documented custom rule produce a real, reproducible finding.

1. A controlled test obtains A's synthetic service credential through the fixture and uses it to request records from the data-access service. Capture the resulting responses and markers. This demonstrates application exposure and credential misuse, not operating-system takeover.
2. ClickHouse stores request metadata. Guild retrieves the evidence window, approved service map and actual Semgrep output to connect the entry point with downstream activity.
3. The agent selects a preauthorized response. The external enforcement service revokes A's credential; a separate probe proves the old credential is denied. B uses a different identity and its legitimate requests continue succeeding. A's affected operation may be unavailable during containment.
4. An isolated runner creates a candidate repair and a controlled build. Fixed tests verify that the disclosure is closed, normal ownership checks hold, B still works and the old credential stays invalid. The agent cannot edit these tests or the access policy.
5. The agent opens a real GitHub PR with sanitized evidence. A separate release service provisions replacement access only for the approved deployment and releases the exact tested revision to the preauthorized demo.
6. An external verifier confirms the repaired public service works, the old credential still fails and the original disclosure path no longer works. Failed checks leave the incident unresolved; a later healthy request alone is not sufficient proof of recovery.

The public fixture contains no real personal information or production credentials. Its purpose is observable defensive work on a system we control. The PR and the deployed verification are real actions; the institution and citizens are fictional.

## What the agent must know before it writes

The proposed application contract must specify:

- Which records each role may read, including record ownership and any explicitly approved staff access.
- Which fields are private and which operations must keep working.
- How identity is established; request text is not proof of identity or authorization.
- Which repository, paths, environment and deployment target it may change.
- Which tests and policies are outside the repair agent's edit permissions.
- The permitted response when evidence is incomplete or the patch fails verification.

Example: an authenticated citizen may retrieve their own record; another citizen must be denied; an approved staff role retains its explicitly permitted workflow. Closing the entire service would fail the availability checks.

The agent may interpret evidence and propose a code change. It cannot invent access rights, widen its own deployment scope, rewrite the acceptance tests, or turn attacker-controlled log text into instructions. Release authorization is checked by code outside the model.

## Sponsor responsibilities

| Sponsor | Substantive role | Integration boundary |
|---|---|---|
| ClickHouse | Correlate application and downstream data-access events; measure observed exposure, containment delay and service continuity. | Analytics informs the workflow. It does not itself block requests or guarantee synchronous containment. |
| Semgrep | Produce a real finding in the supported fixture and rescan the candidate. | Runtime request tests remain necessary even when scanner findings disappear. |
| Guild | Host the response agent and coordinate investigation, bounded containment, isolated repair, tests and GitHub tools. | Use authenticated integrations for our enforcement service, runner and GitHub. Ordinary direct HTTP calls do not work in the documented SDK runtime. |

References: [ClickHouse incremental views](https://clickhouse.com/docs/concepts/features/materialized-views/incremental-materialized-view), [Semgrep Guardian](https://docs.semgrep.dev/semgrep-guardian/overview), [Guild SDK and network boundaries](https://docs.guild.ai/guide/sdk-introduction).

Guardian runs while code is being authored. A hosted workflow needs an appropriate Semgrep integration or isolated CLI runner; installing a developer plugin alone does not establish that our deployed agent scanned anything.

Pi does not count as an integration because the supplied event rules provide no product access. Akash and Senso are optional, not prerequisites for this three-tool design. Senso could retrieve operational context, but its approval tags are conventions rather than enforced security decisions; our external policy check must validate accepted document revisions. AkashML could provide model inference if access is ready; it is not by itself the server-containment layer. [Senso shared context](https://docs.senso.ai/docs/shared-context), [AkashML introduction](https://akashml.com/docs/getting-started/introduction).

## Demo and scope

The proposed short demo shows: a synthetic credential escaping; downstream records being retrieved; the agent relating the events to the permission map and finding; actual independent revocation; healthy service B continuing to work; and A recovering after a verified repair with replacement access. The old credential remains rejected.

Display measured event count, query latency, time to containment, recovery time, observed records exposed and legitimate-request outcomes for each service. Do not invent scale or timing. Label generated traffic and deliberate vulnerabilities as fixtures. Counts in the historical Argentina report are not prototype measurements.

The smallest complete slice of this expanded design is two tiny applications, one data-access service, two distinct service identities, one controlled disclosure path, one explicit response policy, a bounded repair attempt, three sponsor integrations and one verified recovery. The relationship map can live in a small versioned file; a graph database, multiple reasoning agents and additional sponsors are unnecessary for proving the chain. This is more work than the earlier one-route demo and is not yet validated as achievable within the remaining event time.

No government scanning, nationwide monitoring, arbitrary host repair, unsupported root-cause claims or unbounded agent shell access is included. If the operating system, deployment pipeline or enforcement service is itself compromised, this demo's isolation assumptions no longer establish recovery. Already extracted copies cannot be revoked.

Semgrep's supplied prize terms require an interesting vulnerability found in AI-generated code. A deliberately seeded fixture demonstrates our workflow; it must not be presented as a novel accidental discovery. ClickHouse award strength depends on measured scale, latency and actionable use, not merely the presence of a chart. No award eligibility or outcome is guaranteed.

## How the hackathon-guide skill applies

This is a fit assessment, not an invocation or completion of `/onboard`, `/scope`, `/prd`, `/spec`, `/checklist` or `/build`.

For formal implementation, follow the skill's artifact sequence: learner profile, scope, PRD, specification, checklist, build, optional iteration and reflection. Preserve decisions and corrections in `process-notes.md`; keep documents under `docs/`. Do not fabricate the learner's experience or mark unexecuted steps complete. Existing conversation answers should be reused instead of interviewing the user again about settled decisions.

The skill's educational documents are process artifacts. The actual submission requirements in the user's event text are an accessible repository, a shareable demo video, what was built and tools used, plus team names and contact emails. A website and screenshot are optional. No submission or external messaging has been performed.

## Readiness verdict

The research checkpoint adds [27 selected paper records](research/SEARCH-PROTOCOL.md), a [detailed implementation proposal](research/WHAT-TO-BUILD.md), and [measured local effects](research/MEASURED-EFFECTS.md). The reference experiment enforces scope and revocation through real loopback HTTP requests, but does not implement detection, code repair, protected deployment isolation or the three sponsor integrations. Its trusted compromise event is supplied by the scenario. It therefore supports control-level feasibility without completing the product's required evidence chain.

**The design covers the supplied requirements; compliance and delivery feasibility have not yet been demonstrated.** Reproduce the observed revocation and B-continuity behavior under the intended deployment boundaries. Validate a real Guild tool call, Semgrep finding and ClickHouse query, then complete isolated repair and externally verified recovery. If a sponsor integration is unavailable, replace it with another substantive sponsor integration; do not silently fall below three.

[Research report](../REPORT.md) · [Causes](CAUSES.md) · [Consequences](CONSEQUENCES.md)
