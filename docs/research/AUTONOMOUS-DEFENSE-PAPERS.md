# Autonomous defense evidence for BREACHSTOP

Reviewed 9 October 2026. This is a selected eight-paper evidence map, not a claim to have read all cybersecurity research. Seven works were first submitted inside 9 October 2025–9 October 2026; CyberGym is an older foundation updated during that window. AIxCC ran in 2023–2025; the included 2026 SoK analyzes that competition.

The [structured evidence records](defense-papers.json) contain dates, exact versions, review status, protocols, denominators, limitations and extraction locations. Reading depth is **relevant full-text sections**, rather than abstract-only screening or a claim that every appendix was read. None of these experiments was reproduced here. No live systems or leaked records were accessed.

| Work / version | Why it affects this project | Evidence status |
|---|---|---|
| [CyberGym-E2E v2](https://arxiv.org/html/2606.04460v2) | Distinguish fixing any discovered defect from fixing the intended leak. | ICML 2026; methods, results and limitations read. |
| [PatchBench v1](https://arxiv.org/html/2609.04075v1) | A stopped crash is insufficient evidence of correct repair. | September preprint; validation and failure analysis read. |
| [AIxCC SoK v5](https://arxiv.org/html/2602.07666v5) | Reliability, resource management and accuracy affect deployment success. | USENIX Security 2026; official proceedings verified. |
| [PatchIsland v2](https://arxiv.org/html/2601.17471v2) | Deduplicate remediation work and tolerate failing workers. | Preprint; evaluation and limitations read. |
| [ARTEMIS v2](https://arxiv.org/html/2512.09882v2) | Evidence and independent triage matter in realistic environments. | ICLR 2026 per author publication list; full evaluation sections read. |
| [Cyber Defense Benchmark v3](https://arxiv.org/pdf/2604.19533v3) | Report investigative coverage separately from raw-event recall. | Vendor preprint; PDF tables supersede stale abstract numbers. |
| [Cyber Range Response v1](https://arxiv.org/html/2609.16541v1) | Include the operational cost of defensive actions. | September preprint; RL study, not an LLM evaluation. |
| [CyberGym v3](https://arxiv.org/html/2506.02548v3) | Keep benchmark scope, hints and sample sizes visible. | Older foundation; ICLR 2026 revision. |

## Proposed acceptance contract

These are engineering inferences for BREACHSTOP, not effects demonstrated by those papers on government data leaks.

1. Each case declares its intended sensitive-data flow and security invariant before a repair is proposed.
2. An independent verifier checks the original case, held-out variants, legitimate transactions and service health. The proposing agent cannot rewrite the checks or the expected result.
3. Treat a candidate fix, a validated fix and a deployed fix as separate states. Retain the exact inputs, evidence, versions and results behind each transition.
4. Test worker failures, duplicate events, stale evidence, unavailable dependencies, exhausted budgets and rollback. A polished incident narrative cannot substitute for a successful check.
5. Compare against simple deterministic controls and a no-action baseline. Measure sensitive records released, investigation completeness, response delay, false interventions and legitimate transactions preserved.

For a safe demonstration, replay synthetic authorization, credential-reuse and export-control incidents locally. Show the same event sequence before and after a scoped fix, including legitimate requests. Present the measured result as a result on that scenario, with no implied real-world prevention percentage.

## Reading caveats

The code-security studies largely measure C/C++ sanitizer failures; they do not validate access-control, identity or database-export protections automatically. The response studies use distinct environments and scoring rules. Their percentages must not be combined into a shared leaderboard.

CyberGym's 22.0% reasoning result belongs to its 300-instance experiment. CyberGym-E2E's expanded evaluation contains 920 tasks, unlike its initial 615-task analysis. PatchIsland's internal plausible-patch result and live competition denominator are different. Cyber Defense Benchmark's v3 body and abstract disagree; the JSON uses the body tables and labels the discrepancy.
