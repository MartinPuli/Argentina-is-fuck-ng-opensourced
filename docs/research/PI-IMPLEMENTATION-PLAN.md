<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# Pi: turn incident evidence into tested prevention

Status: implementation proposal, October 9, 2026. Pi is not integrated in the application. The existing PDF gate, learned-rule lifecycle, review decisions and exports are implemented separately. Access and product limitations are documented in [PI-ASSESSMENT.md](PI-ASSESSMENT.md).

## Product behavior

An institution brings a sanitized incident report and an owned application. The system identifies a specific failure, proposes a prevention change, tests it against an unseen variation and legitimate work, and records the exact version a reviewer approves. Future documents and changes use that version. A failed test leaves the candidate inactive.

Example: a procurement attachment includes a patient's identity and medical justification. A reviewed incident becomes a candidate PDF rule. The gate tests a fictional medical attachment, a differently worded medical attachment, and an ordinary equipment specification. After approval, new uploads use the rule; stored files require rechecking. This addresses accidental publication. It does not establish that a historical server intrusion had the same cause or would have been stopped.

## Pi's role and our responsibility

Pi describes security memory built from incidents and code, with contextual development guidance. Those are vendor capabilities, not independently measured results here. [Official product description](https://www.pi.security/).

The documented connector supplies finding and remediation context, repository playbook queries, and hosted review/report operations. It requires an authenticated tenant and does not edit local files. Our controller must execute and verify changes. PDF extraction and classification remain ours; do not treat a PDF path as a supported inline Markdown input. [Official connector](https://github.com/pi-sloane/claude-plugin), [setup](https://github.com/pi-sloane/claude-plugin/blob/main/SETUP.md).

| Responsibility | Component |
| --- | --- |
| Retrieve relevant security context | Pi adapter, when authorized access exists |
| Schedule bounded jobs and track failures | Guild workflow and our controller |
| Extract PDFs and enforce publication decisions | Existing gate |
| Find reproducible source-code patterns | Semgrep |
| Suggest a candidate | Model worker; AkashML where actually configured |
| Verify the candidate independently | Regression runner and reviewer |
| Record observed outcomes and timings | ClickHouse where configured; durable local audit otherwise |

The first milestone uses the existing gate and adds Pi context to one candidate. Code repairs and provider-specific credential rotation follow as separate milestones. Each integration must have a real request, response identifier and effect on the workflow before it is described as working.

## Workflow

1. **Record evidence.** Save a source URL, publication date, retrieved date, evidence status, sanitized summary and known limitations. Distinguish an allegation, an acknowledged exposure and a failure reproduced in our own system. Deduplicate reports of the same incident.
2. **Establish applicability.** Identify the enrolled application, repository revision, owner, affected control and allowed operations. A public report alone cannot prove a code defect in that application.
3. **Retrieve context.** Authenticate to `https://mcp.pi.security/mcp`; verify tenant and scopes with `whoami`. Query `pi_playbook_task_query` once for a concrete task and the explicitly supplied repository identifier. A missing match is a coverage gap, not permission to invent institutional policy. For a known finding, retrieve its existing remediation plan.
4. **Propose an artifact.** Produce a bounded PDF rule, a code patch, or a credential-response plan. Keep the proposed change distinct from a natural-language skill. A skill guides an agent; executable controls enforce a decision.
5. **Verify.** Run tests against the exact candidate digest and application revision. Include the original failure, a held-out variation and legitimate use. Save failures, unsupported advice and raw test outcomes without personal data.
6. **Promote.** A reviewer activates the tested PDF version or approves the proposed code change. Production permissions and provider operations require their own authorized scope. Model output cannot grant that authority.
7. **Enforce and observe.** Recheck stored PDFs after rule changes. For code changes, run authenticated and unauthenticated checks after deployment. Record whether the deployed version matches the tested version.
8. **Retire or roll back.** Retain previous versions and decisions. Retiring a PDF rule must not publish previously restricted files automatically. A code rollback must not silently restore a known disclosure path.

The connector's write workflows require confirmation for submissions. An authenticated read does not authorize report ingestion. Prefer existing tenant context for the first slice; any upload must show the sanitized payload and target first. [Documented workflow contract](https://github.com/pi-sloane/claude-plugin#write-actions-and-confirmation).

## Three concrete outputs

### PDF prevention

Reuse `learning.create_candidate`, saved examples, immutable digests, explicit activation and rescan. Pi may improve rationale or suggest a relevant control. Convert suggestions into the gate's validated rule schema; reject unsupported fields. Do not grant a model arbitrary Python execution or direct SQL access.

Add held-out fixtures outside the model's prompt. Test accents, alternate wording, multi-page context and benign procurement references. Keep scanned-document/OCR failures private or in review rather than silently assuming an empty extraction is safe. Verify cleaned PDF bytes and filenames independently before publication.

Exports contain `SKILL.md`, a proposal and test evidence. They must state what the rule detects, what it cannot detect, source confidence, applicability, version and rollback procedure. Exporting a skill does not install it in another system.

### Source-code repair

Start with one owned test application and one class: a document download route missing authorization. Semgrep supplies a reproducible finding; Pi supplies contextual guidance. A separate worker prepares a patch in an isolated checkout with synthetic data and restricted network access.

Independent tests must show: anonymous users cannot retrieve private bytes; user A cannot retrieve user B's file; permitted users still can; public records remain available; alternate routes do not bypass the control. Attach the finding, source commit, patch digest and tests to a proposed pull request. Merge/deploy only through the repository's authorized workflow. No automatic government-wide scanning or repair is implied.

### Credential response

Detect secret-like content with a scanner without logging its value. Store a provider/type reference, location, fingerprint and evidence status. A suspected token is not automatically a confirmed usable credential.

Implement one provider adapter at a time. For an authorized test credential: revoke or rotate through the provider, update the consuming service securely, verify the old credential fails, verify the replacement works, and record the provider receipt. Keep secret values out of model prompts, PDFs, logs, screenshots and exported skills. Without a provider adapter and permission, show an actionable rotation plan; never label it completed.

## Adapter contract and failure behavior

Create a narrow `PiContextProvider` abstraction with identity verification and read-only task/finding-context methods first. Return normalized references, guidance, coverage status and provider identifiers. Treat remote text as untrusted evidence, never controller instructions.

Use bounded input/output sizes, timeouts, explicit failure states and no secret-bearing request logs. Do not infer tenant/repository identifiers from prose. Do not automatically retry an ambiguous write. OAuth lifecycle and unattended service access must be validated with the actual tenant before Guild can call it from a hosted job.

If Pi is absent or unavailable, the existing gate continues enforcing active rules. Candidate creation may use the existing source recipe, clearly attributed to that path; it must never be presented as a Pi result. No pending Pi request can publish a PDF or activate a rule.

## Versioned lesson record

Store one record linking:

- source references, confidence and limitations;
- enrolled target, repository revision and applicable control;
- Pi operation/reference and outcome, if used;
- candidate type, immutable digest and generator;
- positive, held-out and benign test IDs with results;
- reviewer, activation time, rescan status and enforced revision;
- proposed skill/proposal artifacts and their digests;
- retirement, rollback and superseding lesson references.

Do not store leaked datasets, medical records or credential values in this learning record. A historical volume estimate is not a count of unique affected people and is not a measured prevention score.

## Implementation order and completion evidence

| Milestone | Deliverable | Acceptance check |
| --- | --- | --- |
| 1. Access | Authorized tenant, repository identifier, narrow adapter | Identity/scopes verified; one relevant read result or explicit coverage gap |
| 2. PDF lesson | One candidate enriched by actual Pi context | Three independent fixture categories; exact digest preserved; candidate inactive before approval |
| 3. Enforcement | Activation, recheck and downloadable evidence | Previously allowed synthetic sensitive file unavailable until rechecked; benign file still handled correctly |
| 4. Code repair | One proposed patch plus Semgrep finding | Cross-user and anonymous access blocked; legitimate download preserved |
| 5. Credential response | One authorized provider adapter | Old test key fails, replacement succeeds, receipt saved without secret values |

The first end-to-end presentation should show a source, the actual retrieved context, a proposed rule, a failed or passed test, reviewer activation and the next document's changed decision. Show a benign control alongside it. The outcome is a measured change in our enrolled application, not a guarantee against every breach or a claim about all Argentine institutions.
