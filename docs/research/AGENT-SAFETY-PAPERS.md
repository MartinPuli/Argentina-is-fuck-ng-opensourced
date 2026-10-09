# Agent safety evidence for BREACHSTOP

Review cutoff: 2026-10-09. Primary window: 2025-10-09–2026-10-09. This is a targeted selection, not an exhaustive census. All nine records were checked against primary full text; the listed sections, methods, results and limitations were read. No experiments were independently reproduced. Dates, versions and structured measurements are in [agent-safety-papers.json](agent-safety-papers.json).

Design inference: the model may propose containment; a separate controller must own authorization and enforce it at execution. Attacker-controlled logs, retrieved documents, tool outputs and their summaries are evidence, never authorization. An agent cannot make its own actions legitimate by rewriting a policy, reporting success, or declaring itself trusted.

## Within the primary window

### AS01 — LogInject

[Full text](https://arxiv.org/html/2607.14493v1), §§5.1–5.3, 7.5, 8; Table 9. [USENIX Security 2026](https://www.usenix.org/conference/usenixsecurity26/presentation/karanjai).

Injected log fields test concealment, fabricated alerts, exfiltration and output manipulation. On GPT-4o, layered filtering, spotlighting and output validation reduce ASR from 87.3% to 8.4% across 2,569 adversarial samples, with five trials/configuration; benign accuracy falls 94.2%→90.8%. These are controlled-context results using older models and partly synthetic logs, not production breach rates. BREACHSTOP should label attacker-controlled fields, preserve provenance through retrieval, and test fragments distributed across entries. Filtering must supplement controller enforcement; never let a log instruction authorize revocation or publication.

### AS02 — AgentBound / execution boundaries

[Full text](https://arxiv.org/html/2510.21236v3), §§2.3, 3, 4.1.4, 4.2.2. FSE 2026; first preprint 2025-10-24.

Declarative capability manifests drive process-level isolation for MCP servers. Generated permissions match human references in 787/816 capability decisions across 48 servers. Security experiments explicitly leave allowed-endpoint parameter misuse and an in-boundary SQL injection unblocked. The headline 80.9% developer agreement concerns a small responding subset, not all 296 surveyed servers. BREACHSTOP should sandbox connectors with exact filesystem and network permissions, then separately validate incident scope, action parameters and targets in the controller. A network allowlist alone cannot decide whether a permitted API call is authorized.

### AS03 — ActGov

[Full text](https://arxiv.org/html/2609.24446v2), record schema, experimental setup, Tables 2–5. Preprint; 2026-09-22 revision.

Finite records feed deterministic policies; an LLM still extracts some semantic fields. Policies are refined with human review, then frozen. AgentDyn comprises 560 attack pairs split equally: 280 test pairs by arithmetic. Across four models, reported ASR is 0.4–0.7%; exact success counts are not tabulated. Utility is not uniformly preserved: DeepSeek clean utility falls 76.7%→60.0%, and transferred policies reach 10.0%. BREACHSTOP should freeze reviewed policies per evaluation, treat semantic extraction as fallible, and score authorized task completion alongside blocked attacks; domain transfer requires new validation.

### AS04 — TMA-NM / memory authority

[Full text](https://arxiv.org/html/2606.24322v1), Algorithm 1, §§IV–VI, IX; Table I. Preprint; 2026-06-23.

Write-time origin binding and independent corroboration gate consequential actions after memory retrieval. The unified eight-model study reports 0/192 successful attacks per channel for direct, summarization, tool-echo and corroboration attacks; each zero has a 95% Wilson upper bound near 2%. The machine-checked result is bounded to three slots and at most two sessions, and trusts origin labeling and corroborators. BREACHSTOP should carry source identity into incident memory and derived summaries; duplicated evidence must not become independent corroboration. Historical incident notes must never mint new authority.

### AS05 — MUZZLE

[Proceedings full text](https://www.usenix.org/system/files/usenixsecurity26-syros.pdf), §§3–4, Table 2 (PDF p.10), Appendix A.1. [USENIX Security 2026](https://www.usenix.org/conference/usenixsecurity26/presentation/syros).

Adaptive red-teaming selects injection surfaces from agent trajectories and revises attempts using execution feedback. With GPT-4o/BrowserUse, Table 2 reports credential exfiltration in 4/5 Postmill runs and cross-application database deletion in 2/5 runs. Small samples and sandboxed web applications limit generalization; these are end-to-end effects, not merely malicious text. BREACHSTOP's regression suite should include adaptive attacks spanning connectors and judge actual backend state. An attack that fails once must not be retired without testing alternate retrieval positions, surfaces and continuation steps.

### AS06 — BenchJack

[Full text](https://arxiv.org/html/2605.12673v1), §§4–5, Table 1, Appendix E.8. Preprint; 2026-05-12.

Benchmark auditing combines a flaw taxonomy, static checks and generated exploits. The reported SWE-bench Verified exploit produces false success on 500/500 tasks by compromising test reporting; the wider audit covers ten benchmarks. This is a clairvoyant audit of evaluated harness versions, not a measured spontaneous cheating rate. BREACHSTOP needs an evaluator outside the patcher's writable environment, trusted dependencies and outcome collection, and hidden post-state checks. Freezing test files alone is insufficient when agent-controlled plugins, binaries or output parsers can influence the verdict.

## 2026 publication milestone, earlier preprint

### AS07 — SAGA

[NDSS 2026 full text](https://www.ndss-symposium.org/wp-content/uploads/2026-s869-paper.pdf), §§III.C, IV.D–E, VI.B–C; Table II (PDF p.12). First preprint: 2025-04-27.

A trusted provider maintains user-defined contact policies and supports cryptographic, quota-limited agent access. Three demonstrated workflows each incur 0.165 seconds of protocol overhead at token quota ten; these are demonstrations, not a broad security success rate. Assumptions include secure authentication, confidential keys and a trusted provider; token lifetime affects the compromise window. BREACHSTOP should bind permissions to the owning principal, target and expiration, propagate narrower delegation, and measure actual revocation latency. Agent registration or an inter-agent message must not grant system-wide incident-response authority.

## Earlier foundations

### AS08 — CaMeL

[Full text](https://arxiv.org/html/2503.18813v2), §§3–5, 6.1–6.2; Tables 2, 4. Preprint revision: 2025-06-24.

A privileged planner is separated from untrusted-data processing; interpreter capabilities constrain information flows. Table 4 reports o3 attack success falling 11→0 over 949 cases with policies; Table 2 clean utility falls 84.5%→77.3%. Other model rows retain evaluator-marked successes outside the stated threat model. BREACHSTOP should keep executable plans and credentials outside log-reading contexts and pass constrained evidence objects between components. Guarantees depend on policies and the interpreter; tasks requiring untrusted instructions to choose new actions expose an expressiveness tradeoff, not permission to bypass the boundary.

### AS09 — Fides

[Full text](https://arxiv.org/html/2505.23643v2), §§4–8; Table 1, Appendix D. Preprint revision: 2025-09-03.

Confidentiality and integrity labels propagate through tools; selective hiding preserves useful planning. Across 949 AgentDojo attacks, averaged over five runs, GPT-4o Fides has 24 evaluator-marked successes without enforcement and one with enforcement; authors classify zero remaining cases as policy violations. Text-only manipulation and policy-allowed behavior explain exclusions. This is not an unrestricted zero-attack result. BREACHSTOP should distinguish evidentiary trust from disclosure sensitivity and validate tool effects separately from narrative accuracy. Preserve both raw benchmark outcomes and adjudicated policy outcomes in reports so exclusions remain inspectable.

## Concrete evaluation additions

The following are proposed engineering tests, not performance claims from the papers:

- Inject instructions into a synthetic request header and error message; verify that analysis can cite the evidence while the controller denies unrelated actions.
- Split the same instruction across log records, retrieval chunks and successive incident-memory summaries; rerun under shuffled retrieval order.
- Propose revocation for the wrong tenant, an expired authorization, and a resource outside delegated scope; require controller denial with a durable reason.
- Replay an already consumed action authorization and revoke a previously issued capability; measure which downstream operations can still execute and for how long.
- Try to alter the evaluator, its dependencies, generated reports and parser inputs; require independently collected backend state to determine success.
- Report containment success, clean-task completion, false revocations, residual exfiltration, controller denial reasons, rollback success, and time to containment separately. A system that blocks every operation is not a successful defender.

No paper above demonstrates BREACHSTOP's production effectiveness or proves prevention of every future leak. The defensible claim is that prior incidents can become regression scenarios, while authorization, isolation, provenance and independent evaluation constrain recurring failure modes.
