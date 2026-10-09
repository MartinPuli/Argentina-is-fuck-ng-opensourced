# Access control and exposure: additional papers

Review cutoff: **2026-10-09**. Target window: **2025-10-09–2026-10-09**. Five additional primary papers, checked against the existing research records to avoid duplicates. This selection emphasizes enforceable authorization boundaries; it is not an exhaustive review of file publication or AI-generated privacy defects.

All five have accessible full text. Methods, relevant results, threat models, and limitations were read; experiments were not reproduced. Only scholarly papers and publication metadata were inspected. No leaked databases, victim files, live credentials, or production targets were accessed. The companion JSON records exact versions, denominators, and reading locators.

Publication dates are distinguished from preprint dates. For AE03 and AE04, the 2026 proceedings publication is confirmed but an earlier preprint date was not established. No reviewed paper is being represented as a new 2026 discovery solely because an older preprint received a venue label.

## AE01 — Plaintext Recovery Against Post-Filtering Access Control

**Status:** USENIX Security 2026 proceedings, August 12–14; first arXiv version **2026-08-12**. Reviewed the official proceedings PDF; arXiv v1 is separately identified as the expanded version. [Official record](https://www.usenix.org/conference/usenixsecurity26/presentation/espiritu) · [Reviewed PDF](https://www.usenix.org/system/files/usenixsecurity26-espiritu.pdf) · [Preprint history](https://arxiv.org/abs/2608.11730)

Rich queries amplify timing and scoring leakage despite filtered results. A PostgreSQL 18.1 experiment reports **100.0% recall and precision on a 100,000-row target**, over three runs. It assumes expressive query access and memory-resident data. Combining tenant-leading indexes with planner-visible policy closes the measured channel for that policy form; neither change alone suffices. **BREACHSTOP implication:** test confidential-data isolation beyond empty responses, including query-plan behavior. The mitigation is conditional, not a general replacement for row-level security. (§2; §3.3/Table 4; §3.4/Table 5 and limitations.)

## AE02 — eMicro: Real-Time Multi-Hop Access Control for Microservices with eBPF

**Status:** arXiv **2608.05300v1, 2026-08-05**; accepted CCS 2026, with the November conference still forthcoming at cutoff. [Version](https://arxiv.org/abs/2608.05300) · [Reviewed full text](https://arxiv.org/html/2608.05300v1) · [Official acceptance](https://www.sigsac.org/ccs/CCS2026/program/accepted-papers.html)

eMicro enforces administrator-defined request histories through compact automata and kernel tracing. It reports blocking **three selected attack classes across eight network settings**; individual malicious-request counts are not reported. The kernel/runtime must remain trusted. Queues and shared storage require additional propagation; multiplexing requires observable request identifiers. **BREACHSTOP implication:** authorize the originating workflow as well as the immediate service, and test indirect routes and interrupted policy updates. Production traces test scalability; they do not establish production prevention rates. (§2.4; §4; §6.1/Fig. 6; §6.5; §7.)

## AE03 — The Dark Side of Flexibility: Detecting Risky Permission Chaining Attacks in Serverless Applications

**Status:** NDSS 2026 proceedings, February 23–27; reviewed official proceedings version. Earlier preprint date not established. [Official record](https://www.ndss-symposium.org/ndss-paper/the-dark-side-of-flexibility-detecting-risky-permission-chaining-attacks-in-serverless-applications/) · [Reviewed PDF](https://www.ndss-symposium.org/wp-content/uploads/2026-s819-paper.pdf)

The analyzer models combinations of function permissions and shared resources across applications/accounts. It identifies **28/363 selected applications**, with **12/28 vendor-confirmed**; unconfirmed findings are not established false positives. Tests use researchers’ accounts and assume one function is already compromised. Selection favors popular applications with custom policies; complete ground truth is unavailable. **BREACHSTOP implication:** inspect effective deployed roles and cross-account dependencies together; regression-test whether containment also cuts indirect privilege paths. This is vulnerability discovery, not measured automatic remediation. (§III-A; §IV; §V-A–B/Table II; §VI.)

## AE04 — Raising the Flag: Detecting Missing Permission Controls in Mini-Program APIs

**Status:** USENIX Security 2026 proceedings, August 12–14; reviewed official proceedings version. Earlier preprint date not established. [Official record](https://www.usenix.org/conference/usenixsecurity26/presentation/wei-zhiao) · [Reviewed PDF](https://www.usenix.org/system/files/usenixsecurity26-wei-zhiao.pdf)

PERMSCOPE combines static resource mapping, generated test cases, and instrumented execution to compare actual access with declared scopes. It identifies **183 inconsistent APIs among 258 reaching protected resources**, within **2,067 tested APIs** across four Android super-apps. Permission categories involve semantic comparisons; other platforms remain outside scope. **BREACHSTOP implication:** test what each connector can actually reach, including inherited permissions, against approved scopes. Documentation and parent-process permission grants do not establish child authorization. The proposed permission-synthesizer mitigation was not implemented. (§3.2–3.5; §4–5; §6/Tables 4–5; §7.)

## AE05 — Prezta: Provable Remote Execution of Zero-Trust Authorization using SNARKs

**Status:** USENIX Security 2026 proceedings, August 12–14; first preprint **2026-07-13**, revised **2026-07-27**. Reviewed official proceedings PDF. [Official record](https://www.usenix.org/conference/usenixsecurity26/presentation/wei-zhongjing) · [Reviewed PDF](https://www.usenix.org/system/files/usenixsecurity26-wei-zhongjing.pdf) · [Version history](https://arxiv.org/abs/2607.11466)

Clients prove execution of signed authorization policies; the protected device verifies the proof and authenticates its real-world inputs. **323/323 supported tests pass**, covering **323/389 testable cases** from a 397-case suite. Proof generation takes roughly 14–28 seconds in the evaluated setup; faster revocation is proposed, not measured. **BREACHSTOP implication:** independently bind permission decisions to actual identity, resource, context, and current policy. Correct policy execution cannot establish that administrator-supplied policy is appropriate; cryptographic proofs are not required for the prototype. (§3; §4.1.5–4.2/Table 1; §5.1; §6.1.)

## Synthesis for the next design iteration

Add tests for four distinct failures: a child inheriting broader access than intended, allowed calls composing into a forbidden workflow, a stale authorization surviving a policy change, and private information escaping through observable query behavior. Use actual deployed permissions and independent clients. Choose a proportionate control only after reproducing the relevant mechanism; these papers do not justify inserting every research prototype into BREACHSTOP.
