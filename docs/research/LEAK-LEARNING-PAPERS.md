# Learning from incidents: what the evidence supports

Reviewed October 9, 2026. These five selected studies complement the [defense](AUTONOMOUS-DEFENSE-PAPERS.md) and [agent safety](AGENT-SAFETY-PAPERS.md) reviews. Relevant methods, results and limitations were read in full text; this does not mean every appendix was read or any experiment reproduced. Versions and reading locations are recorded in [leak-learning-papers.json](leak-learning-papers.json).

Here, **threat intelligence** means documented information about attacks. **Provenance** means a record of where information came from or how programs interacted. **Federated learning** means training across organizations without collecting all their raw records in one place; it is not automatically a privacy guarantee.

## LL01 — CTI-REALM

[March 2026 preprint, v2](https://arxiv.org/html/2603.13517v2), §§3–5.7, 7 and Appendix H.

The benchmark tests detection-rule construction against emulated Azure/Linux/AKS activity. Its memory experiment improves GPT-5-Mini's composite reward from 0.3714 to 0.4324 using prewritten workflow guidance, tool tips and templates; query execution stays unchanged. This is not automatic learning from new breaches, nor a percentage of attacks prevented. The main collection contains 50 tasks and the smaller collection 25. Production volume, long observation periods and other cloud platforms remain outside its evaluation. For our design, store reviewed procedures and reproducible test cases, then measure whether retrieval improves actual decisions on unseen incidents.

## LL02 — Cutting the Fuse / PROVX

[USENIX Security 2026 proceedings](https://www.usenix.org/system/files/usenixsecurity26-wu-weiheng.pdf), §§4.3–7, especially §6.3's metric definition.

PROVX identifies interactions whose simulated removal changes a graph detector's verdict. Its mitigation metric measures that prediction change, not demonstrated denial of a real attacker's request. The paper explicitly positions the system as post-detection decision support; translating recommendations into safe host actions remains deployment-specific. Its feedback experiment uses adversarially modified graphs, while a complete operational feedback system remains future work. Our implication is to separate a suggested containment point from an enforced action and a verified outcome. A chart turning green cannot establish that records stopped leaving the service.

## LL03 — ENTENTE

[NDSS 2026 proceedings](https://www.ndss-symposium.org/wp-content/uploads/2026-s93-paper.pdf), §§IV.C–VI and Tables II–VII. Initial preprint: March 2025; this is a 2026 publication milestone, not a newly invented 2026 method.

ENTENTE studies sharing learned intrusion-detection models across differently distributed network logs. Evaluation includes OpTC, LANL and Pivoting, with clients simulated on one workstation and partitions inferred through clustering. LANL labeling limitations weaken precision; the poisoning evaluation covers a particular attack family. The authors also discuss privacy leakage through model updates. These results support investigating cross-organization learning, not claiming a proven privacy-preserving nationwide defense. Initially share reviewed behavioral tests and minimal evidence descriptors. Training shared models requires a separate assessment of poisoned contributors, privacy, communication overhead and local false alarms.

## LL04 — Operationalizing Cyber Threat Intelligence with GraphRAG

[August 2026 preprint, v1](https://arxiv.org/html/2608.13050v1), §§5–7.3, Tables 7–8.

The study compares generated hunting plans, including whether an evaluator judges their rules dependent on changeable addresses and domains. The headline rotation result comes from one report: 6/6 and 8/8 graph-based plan detections versus 4/14 ordinary retrieval detections are classified as surviving. These are not measured blocks on live attacks. Across nine reports, best-of-run total scores favor graph retrieval four times and ordinary retrieval five times; parser failures and sparse graphs complicate comparison. We should test behavioral rules after changing incidental indicators, without assuming a graph database or extra retrieval machinery necessarily improves protection.

## LL05 — CyTReX

[October 3, 2026 preprint, v1](https://arxiv.org/html/2610.04286v1), §§V–VII, Tables IV–VII. Authors report presentation at Resilience Week 2026; independent proceedings status was not established in this review.

CyTReX combines detection signals, model explanations and attack references to produce threat hypotheses for an industrial-network case study. It evaluates five configurations and two held-out labels. Added context does not consistently improve exact classification; unfamiliar cases can be pulled toward known categories. Table V shows reasoning costs on the order of minutes, and the MCP component explicitly does not perform mitigation. The practical lesson is to separate fast access enforcement from slower investigation. This paper motivates traceable hypotheses and uncertainty handling, not a claim that a reasoning model can safely guard every database request in real time.

## Decisions these studies change

The following are our engineering proposals, not measured results from the papers:

- Preserve an incident's evidence, assumptions, known mechanism and unresolved questions separately.
- Turn a known mechanism into an executable test with an expected denial and a permitted-use counterpart.
- Change hostnames, record identifiers, ordering and request pace in evaluation so a rule cannot succeed only by memorizing the example.
- Require fresh evidence from the receiving service after an intervention. A model's explanation or confidence is not an outcome measurement.
- Share approved tests across services only after mapping their local permissions. An incident in one office does not authorize shutting down another.
- Keep model training and automatic memory promotion outside the first prototype. A suggested lesson enters active policy only after review, versioning and independent tests.
