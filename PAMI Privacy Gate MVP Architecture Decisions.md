# PAMI Privacy Gate MVP: Architecture Decisions and Open Questions

**Prepared:** October 9, 2026  
**Status:** Pre-architecture discovery  
**Product scope:** PAMI procurement-to-public document release  
**Document purpose:** Record settled product decisions, required architectural constraints and remaining questions before producing the final product architecture specification.

## 1. Product objective

The product is a privacy and policy-enforcement gate for PAMI procurement documents.

It reviews Spanish-language PDF files before they move from an internal procurement process to an unrestricted public destination. It identifies information that is not permitted in the public version, records why that information is not permitted, creates a proposed sanitized PDF and sends the proposal to an independent review agent. A government employee remains responsible for the final publication decision.

The product is intended to create a consistent interpretation of the public-release standard across PAMI offices while preserving human accountability for the final decision.

## 2. Decisions already settled

| Area | Decision |
|---|---|
| Institutional scope | PAMI |
| Workflow boundary | Procurement to public |
| Supported input | Digitally generated Spanish-language PDFs |
| Product output | Proposed sanitized PDF and Spanish-language explanation log |
| Final authority | Government employee |
| Agent orchestration | Guild |
| Agent roles | Orchestrator, sanitization agent and independent review agent |
| Low confidence or disagreement | Mandatory human review |
| Operator override | Permitted but permanently logged |
| Analytics and policy data | ClickHouse |
| Code security | Semgrep Guardian review of the AI-generated codebase |
| Product language | English |
| Source document language | Spanish |
| Operator actions and document findings | Spanish |
| Final planning deliverable | Product architecture specification, not an implementation specification |

## 3. Proposed workflow

```text
Government employee submits procurement PDF
                        |
                        v
Orchestrator creates restricted processing job
                        |
                        v
Sanitization agent applies the PUBLIC release standard
  - identifies prohibited information
  - records finding categories and reasons
  - creates proposed sanitized PDF
  - creates page-by-page change manifest
                        |
                        v
Independent review agent examines the result
  - independently checks the source
  - scans the sanitized candidate
  - checks preservation of required procurement information
  - compares changes with the applicable standard
                        |
             +----------+----------+
             |                     |
             v                     v
      Agents agree           Disagreement, finding
      candidate is safe      or low confidence
             |                     |
             +----------+----------+
                        |
                        v
Government employee reviews report and flags
                        |
                +-------+-------+
                |               |
                v               v
             APPROVE          REJECT
                |
                v
Approved public PDF and permanent audit event
```

## 4. Mandatory architectural corrections

### 4.1 Real leaked medical records must not be used

The MVP must not acquire, store or process leaked PAMI medical records.

Public availability following a leak does not make medical information a legitimate hackathon dataset. Argentine Law 25,326 classifies health information as sensitive data. It defines processing broadly enough to include storage, evaluation, modification and transfer and requires security and confidentiality protections. It also requires personal information to be adequate, relevant and not excessive for its stated purpose. See [Law 25,326, Articles 2, 4 and 7–10](https://www.argentina.gob.ar/normativa/nacional/64790/actualizacion).

Using actual leaked records could reproduce the original harm by moving victims' information through:

- Application infrastructure.
- Temporary file storage.
- ClickHouse.
- Guild.
- Model providers.
- Developer logs.
- Demo recordings.
- Hackathon infrastructure.

The safe dataset is a **synthetic Argentine PAMI-style corpus** containing realistic but fictitious DNI formats, diagnoses, prescriptions, disability certificates and procurement forms. It may reflect documented categories of exposure but must not reproduce information belonging to real people.

Public procurement templates may also be used after confirming that they contain no personal information.

### 4.2 Logs must not reproduce sensitive information

The operator must understand what was detected and why it was removed. The central log must not become a second database of medical and identity information.

A finding should resemble:

```text
Finding: DNI
Page: 3
Location: upper-right section
Masked value: •••••••123
Policy result: not permitted in PUBLIC output
Action: redacted
Confidence: 0.99
```

ClickHouse should normally receive:

- Finding category.
- Page and approximate location.
- Masked preview where necessary.
- Detector and agent identity.
- Confidence score.
- Policy rule and version.
- Remediation action.
- Review outcome.

It should not receive a full DNI, diagnosis, address, clinical history or unredacted page text.

The review agent may inspect the original inside the restricted processing environment. Central analytics must receive only minimized findings.

### 4.3 `INTERNAL_RESTRICTED` is the default source state, not an error

Every submitted source document begins as `INTERNAL_RESTRICTED`. A procurement document may legitimately contain medical evidence while it remains inside the restricted workflow.

The error occurs when the document cannot safely complete the requested transition to a public destination.

```text
INTERNAL_RESTRICTED
        |
        | sanitization attempted
        v
PUBLIC_CANDIDATE
        |
        +--> APPROVED_PUBLIC
        |
        +--> HUMAN_REVIEW_REQUIRED
        |
        +--> BLOCKED_POLICY_VIOLATION
```

The system should distinguish between:

- Sensitive information that is legitimate in the original internal file.
- Sensitive information that is prohibited in the public candidate.
- Missing procurement information that makes the proposed public record incomplete.
- A failed or invalid transformation attempt.

### 4.4 ClickHouse should index and analyze documents, not store raw PDFs

ClickHouse should determine which reports contain which categories of information by storing structured detection and decision records. It should not become the raw PDF repository.

| Component | Intended contents |
|---|---|
| Temporary restricted file store | Original PDF and proposed sanitized PDF |
| ClickHouse | Document hash, classifications, findings, policy variables, decisions, timings and audit events |
| Guild | Agent identities, workflow state, tool calls and review orchestration |
| Web application | Authorized report views and temporary document previews |

The original and sanitized PDFs should be referenced by opaque identifiers and cryptographic hashes. Retention and deletion rules for temporary files must be defined before implementation.

## 5. Agent responsibilities

### 5.1 Orchestrator agent

The orchestrator manages workflow state. It should not independently decide that a document is safe for publication.

Its responsibilities are:

- Create a processing job.
- Record the source and intended destination.
- Select the applicable policy version.
- Invoke the sanitization agent.
- Invoke the review agent independently.
- Compare structured outcomes.
- Route disagreements and low-confidence results to human review.
- Prevent publication without the required approvals.
- Write minimized workflow events to ClickHouse.

### 5.2 Sanitization agent

The sanitization agent applies the `PUBLIC` release standard to the restricted source document.

Its responsibilities are:

- Identify prohibited personal and health information.
- Identify the page and region containing each finding.
- Associate every finding with a policy rule.
- Select an appropriate remediation action.
- Produce a proposed sanitized PDF.
- Produce a page-by-page change manifest.
- Record confidence and uncertainty.
- Preserve the unmodified original.

### 5.3 Independent review agent

The review agent must not merely repeat the sanitization agent's conclusion. It receives the same public-release standard but performs an independent assessment.

Its responsibilities should include:

- Independently scan the original restricted PDF.
- Independently scan the sanitized candidate.
- Detect prohibited information that remains.
- Confirm that required procurement information remains intact.
- Compare the sanitized candidate with the original.
- Confirm that every alteration appears in the change manifest.
- Detect unexpected additions, missing pages or malformed output.
- Return `PASS`, `FAIL` or `HUMAN_REVIEW_REQUIRED` with reasons.

### 5.4 Government operator

The government employee remains the final accountable decision-maker.

The operator should see:

- Intended destination: `PUBLIC`.
- Overall decision: `ALLOW`, `BLOCK` or `REVIEW`.
- Findings by page and category.
- Highlighted location of each finding.
- Applicable policy and source.
- Spanish-language explanation.
- Sanitization and review agent outcomes.
- Areas of disagreement or uncertainty.
- Proposed sanitized PDF.
- Page-by-page change manifest.
- Approval, rejection and override controls.
- Immutable audit timeline.

## 6. Mandatory sensitive-data categories

The MVP must recognize the following categories in Spanish-language procurement PDFs:

1. DNI, CUIT and CUIL identifiers.
2. Names of patients or affiliates.
3. Home addresses.
4. Telephone numbers and email addresses.
5. Diagnoses and clinical histories.
6. Prescriptions and laboratory results.
7. Disability certificates.
8. Identity-document images.
9. Patient photographs.
10. Medical-procedure images.

Because the MVP is limited to digitally generated PDFs, support expectations for embedded images remain an open decision.

## 7. Decision rules

The proposed asymmetric decision model is:

| Sanitization result | Review result | Outcome |
|---|---|---|
| Safe | Safe | Eligible for government approval |
| Sensitive information found and removed | Sanitized result verified | Eligible for government approval with visible findings |
| Sensitive information remains | Any | Blocked |
| Safe | Sensitive information found | Human review required |
| Sensitive information found | Reviewer finds additional information | Human review required and candidate regenerated |
| Any | Low confidence | Human review required |
| Any | Agent disagreement | Human review required |
| System, parser or model failure | Any | Blocked pending review |

No agent may publish a document autonomously.

## 8. ClickHouse role

ClickHouse is the structured evidence, policy-variable and analytics layer.

It should support:

- Document inventory without raw document contents.
- Field and finding inventories by document.
- Permitted and prohibited variables for the public destination.
- Policy versions and rule identifiers.
- Agent decisions and confidence scores.
- Human approval, rejection and override events.
- Processing latency and throughput.
- Findings by UGL and document category.
- Detection of repeated unsafe-publication attempts.
- Comparison of agent and reviewer performance.
- Historical re-evaluation when a policy changes.

The hackathon demonstration should combine a small number of live synthetic PDF scans with a large synthetic history of document-analysis events. This shows how the system could analyze millions of PAMI disability-related procurement processes without claiming that millions of real PDFs were processed during the event.

## 9. Guild role

Guild manages how the agents are run, orchestrated and reviewed against one another.

The intended Guild responsibilities are:

- Provide an identity for each agent.
- Run the orchestrator, sanitization and review agents.
- Restrict the tools available to each agent.
- Maintain workflow and execution traces.
- Separate sanitization from independent review.
- Enforce the human-approval boundary.
- Version the agents and their instructions.
- Make failures and disagreements observable.

The final architecture must prevent the review agent from being reduced to an uncritical confirmation step.

## 10. Semgrep Guardian role

The application will be substantially generated by Claude. Semgrep Guardian will review the codebase for security mistakes and insecure assumptions introduced during AI-assisted development.

The review should examine areas such as:

- Missing authorization checks.
- Unauthenticated document or publication endpoints.
- Hard-coded credentials.
- Accidental logging of extracted medical information.
- Unsafe temporary-file handling.
- Path traversal in PDF uploads.
- Insecure direct object references.
- Unrestricted outbound requests from document-processing services.
- Injection vulnerabilities.
- Unsafe parsing or command execution.
- Dependency and supply-chain vulnerabilities.
- Incorrect enforcement of approval state.

The team will produce a separate Guardian findings report describing:

- The AI-generated mistake.
- How Guardian found it.
- The security impact.
- The affected component.
- The remediation.
- Verification that the issue was fixed.

## 11. Open architecture questions

### 11.1 Meaning of removal

Sensitive information could be handled by:

- Removing an entire attachment or page.
- Permanently redacting a region.
- Replacing a necessary patient reference with a neutral case identifier.

Recommended policy:

- Remove wholly clinical attachments.
- Remove identity-document pages.
- Redact isolated identifiers in otherwise publishable procurement pages.
- Replace necessary patient references with generated case identifiers.

**Decision required:** Approve or revise this removal policy.

### 11.2 PDF reconstruction method

Drawing a black rectangle over text can leave the underlying text extractable.

**Recommendation:** Generate a flattened sanitized PDF in which removed information no longer exists in the text layer, metadata or embedded objects.

**Decision required:** Confirm that flattened reconstruction is required for the MVP.

### 11.3 Review-agent input contract

Recommended review input:

- Original restricted PDF.
- Sanitized candidate.
- Page-by-page change manifest.
- Sanitization agent's structured findings.
- Applicable public-level standards.

The reviewer should confirm that prohibited content is absent, required information remains and every modification is accounted for.

**Decision required:** Approve or revise this review contract.

### 11.4 Post-approval behavior

Options:

- Mark the document approved and provide a download.
- Simulate sending the document to a public portal.
- Connect to an actual publication destination.

**Recommendation:** Provide an approved download and record a simulated publication event. A real portal integration is outside the four-hour MVP.

**Decision required:** Select the desired behavior.

### 11.5 Embedded-image support

Digitally generated PDFs can still contain embedded photographs, medical images or scanned identity documents.

**Recommendation for the four-hour MVP:**

- Selectable-text inspection is mandatory.
- Detection of an embedded image triggers `HUMAN_REVIEW_REQUIRED`.
- Full visual interpretation of embedded images is post-MVP.

**Decision required:** Confirm whether this limitation is acceptable.

### 11.6 Required public information

Proposed public minimum:

- Procurement or procedure identifier.
- UGL identifier.
- Generic product or service description.
- Quantity.
- Budget or reference price.
- Procurement method.
- Submission dates.
- Supplier and bidder information.
- Evaluation and award decision.
- Non-identifying delivery requirements.

**Decision required:** Confirm or revise the public minimum.

### 11.7 Override controls

Recommended override design:

- The original restricted PDF can never be directly approved for public release.
- An override applies only to the sanitized candidate.
- The operator must enter a written Spanish justification.
- The event records operator identity and timestamp.
- A second employee must approve the override.
- Referenced policy exceptions are recorded.
- ClickHouse receives a permanent audit event.

**Decision required:** Determine whether the hackathon UI simulates two distinct approving employees or allows one demo operator to represent both steps.

### 11.8 Million-process demonstration

Recommended demonstration:

- Scan 20–30 synthetic PDFs live.
- Generate approximately one million synthetic document-analysis events in ClickHouse.
- Query those events in real time.
- Display unsafe-publication attempts by UGL, category and policy version.
- Demonstrate historical identification of documents affected by a policy update.
- Clearly label the large dataset as simulated telemetry.

**Decision required:** Confirm that the scale demonstration uses simulated analysis events rather than claiming actual processing of one million PDFs.

### 11.9 Model dependency

Recommended model-agnostic interfaces:

```text
analyze_document(input, policy, destination) -> structured findings

review_candidate(original, sanitized, manifest, policy) -> review decision
```

This allows the hackathon model to be replaced later with a model hosted inside an approved government environment.

**Decision required:** Confirm a model-agnostic architecture or identify the required model provider.

## 12. Conditions for the final product architecture specification

The final architecture specification can be completed after the nine open decisions above are resolved. It will define:

- Product purpose and non-goals.
- User roles and jobs to be done.
- Document and workflow states.
- Agent boundaries and responsibilities.
- Data classification and transformation policy.
- ClickHouse's logical data model.
- Guild's orchestration responsibilities.
- Government-operator review experience.
- Security and privacy boundaries.
- Semgrep Guardian review workflow.
- Audit and override requirements.
- MVP success criteria.
- Hackathon demonstration boundaries.

