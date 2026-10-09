# Detection and response evaluation

Reviewed **October 9, 2026**. Two targeted full-text reviews, with methods, result definitions and deployment limitations checked. No author code executed or independent reproduction claimed. [The evidence ledger](detection-response-evaluation.json) records versions and locators. Product implications below are our inferences.

<a id="dre-01"></a>
## DRE-01 · A First-Principles Evaluation of Graph-Based Network Intrusion Detection Systems

Rui Zhao, Wajih Ul Hassan. **arXiv:2609.12263v1, September 10, 2026**; author-reported acceptance at CCS 2026, whose conference follows this review cutoff. [Version and status](https://arxiv.org/abs/2609.12263v1); [versioned full text](https://arxiv.org/html/2609.12263v1).

GIDS-Eval reimplements five detectors on four datasets with chronological splits. Its 54 streaming-replay jobs cover 18 detector–dataset pairs: 14 classify as batch, four near-real-time, none real-time-ready; median buffering is 40 minutes at 1× arrival rate. This simulates arrivals from archived runtime and batch measurements, not live operational deployment. Datasets include injected or simulated attacks; explanation quality is not evaluated. Complex graph components do not consistently outperform simpler alternatives. Our inference: measure collection delay, decision delay and actual enforcement separately; compare against ordinary access controls before crediting an agent with prevention.

Reading locators: §3 and Table 1; §4 EG6, EG9 and Table 4; §5.2; §6; Appendices B and F.9. The real-time categories use this study's operational criteria and tested pairs, not every intrusion detector.

<a id="dre-02"></a>
## DRE-02 · Incident Response Planning Using a Lightweight Large Language Model with Reduced Hallucination

Kim Hammar, Tansu Alpcan, Emil C. Lupu. **NDSS 2026 publisher PDF** reviewed. First preprint **arXiv:2508.05188v1, August 7, 2025**, before the primary window; the later venue publication is inside it. [Preprint history](https://arxiv.org/abs/2508.05188v1); [venue record](https://www.ndss-symposium.org/ndss-paper/incident-response-planning-using-a-lightweight-large-language-model-with-reduced-hallucination/); [reviewed venue PDF](https://www.ndss-symposium.org/wp-content/uploads/2026-f358-paper.pdf).

The planner combines a fine-tuned model, retrieval and lookahead over predicted states. Evaluation uses 25 incidents from four datasets, five false-positive cases and five random seeds. Reported “recovery time” is action cost—one per action, two for superfluous actions—not elapsed time. Mean cost is 13.46 versus 16.21 for the next-best tested comparator. Predicted states are not independently observed enforcement outcomes. The paper explicitly positions the system as decision support, not automated response; real SOC evaluation remains future work. Our inference: use generated plans as proposals and verify each permitted action against actual service responses.

Reading locators: §IV (training and architecture); §V (retrieval/lookahead); §VII-A and Figure 12 (evaluation and action-cost definition); §VII-B–D (simulation, limitations and decision-support scope); Appendix E (hardware). Numerical results above come from the venue PDF, not an assumed identical preprint revision. We did not establish the exact semantic-grading implementation, so no plan-accuracy claim is adopted here.

## Implementation consequence

Neither good investigation scores nor inexpensive proposed action sequences establish that data stopped leaving a service. [BREACHSTOP](WHAT-TO-BUILD.md) must retain an external client that measures returned records, a controller whose authority is independent of the model, and a legitimate-use workload. Our local experimental counts must remain separate from paper results and from any future sponsor integration.
