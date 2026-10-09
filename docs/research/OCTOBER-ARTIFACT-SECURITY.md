# Admission checks for executable artifacts

**Reviewed October 9, 2026.** Two additional targeted full-text reviews are recorded in [the evidence ledger](october-artifact-security.json): [OA01](https://arxiv.org/html/2610.10612v1) and [OA02](https://arxiv.org/html/2610.10735v1). Bibliography, version dates, methods, result denominators and limitations appear there once. These are preprints, not independently reproduced results. We read the relevant methods, evaluation and limitations; we did not execute their code, download model artifacts or test external systems.

The following is **our proposed engineering policy**, not a claim that either paper implements BREACHSTOP or establishes its efficacy. The papers concern executable inputs to our defender. They do not establish that a citizen-facing publication is properly anonymized.

## Proposed checks

| ID | Admission or execution rule | Evidence to retain | Inert acceptance test |
|---|---|---|---|
| A1 | Bind approval to the full artifact digest, dependency manifest, loader, runtime image and policy revision. Require fresh approval after any change. | Immutable review record and launch record referencing identical revisions. | Modify one harmless resource after approval; launch must stop before reading it. |
| A2 | For the initial Python adapter, reject supplied caches and compile reviewed source in a separate clean builder. Do not accept a scanner's prose verdict as an exception. | Builder identity, pinned interpreter, source digest and resulting artifact digest. | A benign package containing a cache is rejected; an approved source-only package passes the build path. |
| A3 | If cache compatibility is later required, separately review the reproduction comparator and supported loader contract. Treat unknown loaders, source failures and unresolved artifacts as unresolved—not approved. | Explicit artifact inventory and coverage outcomes. | Benign missing-source and unsupported-loader fixtures stay quarantined. |
| A4 | Start with no production secrets, no public-release credential and no general network access in the inspection worker. Keep fetching dependencies, executing tools and releasing information under separate authority. | Broker decisions, egress policy and denied-action logs. | An inert request for an unapproved destination or release operation is denied without transmitting a record. |
| A5 | Exclude third-party executable model serialization from the first demo. If later needed, require a declared supported loader and an isolated review path; never deserialize merely to establish a file's format. | Loader configuration, inspection status and human disposition. | An unknown model format is quarantined without opening it through a framework loader. |
| A6 | Treat model-generated scanner judgments as evidence for review. Require complete bounded processing; disagreement, truncation, timeout or missing trace yields an unresolved result. Keep proprietary traces local unless separately authorized. | Deterministic observations, verdict, analyzer version and processing status. | Inject an error into a mock scanner response; admission must remain closed. |

These tests are proposed, not run. Use harmless synthetic fixtures; no offensive payload or real patient data is needed. Measure legitimate completion and unnecessary rejection alongside blocked actions.

## What a successful check would establish

Let **A** be approved bytes, **E** the bytes selected for execution, **R** the runtime configuration, and **P** the enforced policy. An authenticated manifest plus an isolated launch that consumes exactly the approved immutable artifact can support the narrow claim `E = A` under the recorded `R`. That equality does **not** establish that A is benign, that its author was authorized, or that it may access a particular record. Hash comparison alone also says nothing about who approved the hash.

For our implementation, admission should require all of: verified provenance, a supported inspection path, a complete review, a matching launch configuration and permitted capabilities. The model cannot replace a failed prerequisite with a favorable explanation. These are proposed acceptance conditions, not a machine-checked theorem or a demonstrated implementation.

Keep separate outcomes for **inspection completed**, **correspondence established**, **behavioral concerns found**, **admission granted**, and **runtime action permitted**. Never convert an unscanned file into a clean result. A successful benchmark assessment does not authorize future files or changed dependencies.

## Relationship to the publication and repair workflow

Apply these checks to the software that parses attachments, classifies records, proposes repairs and verifies outcomes. If any such component can load unreviewed executable material, its later “safe to publish” report must not carry release authority. Give the public-release broker a narrow independent contract that checks the approved document digest, review state and intended public destination.

A scanner approved under this policy may still misclassify a document. A source-derived program may still contain dangerous logic. An inspected model may still produce inappropriate output. Keep document privacy review, record-access authorization, network controls and legitimate-service recovery tests as separate controls.

## Remaining validation

- Review the trusted builder, framework loader, inspection parser and broker as part of our trusted computing base.
- Implement immutable artifact consumption; then test replacement between inspection and launch.
- Establish bounded memory/time behavior for malformed or oversized inert inputs.
- Test changes to loaders, dependencies and semantic analyzers before accepting a new configuration.
- Verify false rejection costs on our real authorized workflow; literature results do not supply our deployment error rate.

This review advances two queued papers to `fulltext_targeted`. It does not complete the broader request to read all new cybersecurity research.
