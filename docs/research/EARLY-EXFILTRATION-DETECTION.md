<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# Early exfiltration detection: evidence and a proposed test

Reviewed October 9, 2026. Both versioned papers were read in full HTML, including appendices, equations, tables and figure captions. PDF requests failed; figure pixels and author code were not inspected. No datasets, private records or runnable author artifacts were downloaded. Numerical extraction and precise locators are in [the accompanying records](early-exfiltration-detection.json).

- [Anytime-valid detection of LLM weight exfiltration](https://arxiv.org/html/2610.11843v1): fixed-seed inference verification; transfer to citizen databases is untested. Preserving its calibration assumptions is essential.
- [A Bayesian Correlated Equilibrium for Early Insider-Threat Detection](https://arxiv.org/html/2609.03096v1): simulated behavioral coordination; bounded expected detection is not guaranteed pre-loss intervention. Its empirical averages remain after exfiltration.

The underlying CERT dataset contains synthetic background and malicious actors, as its [CMU/SEI owner explains](https://sei.cmu.edu/library/insider-threat-test-dataset/). Do not describe the second paper as a government deployment or a study of observed employee psychology.

## Proposed BREACHSTOP experiment — our design, not either paper's result

Keep the candidate detector outside the enrolled application's process and feed it observations from the protected data service. Start with a synthetic service-account use case. Do not infer employee disposition, intent or psychological state. A request made with a stolen credential can be observationally identical to its owner's request; fixture labels belong only to the evaluator.

Freeze a workload contract, calibration partition, monitor version, decision policy and maximum permitted legitimate disruption before testing. Compare three conditions over identical requests: ordinary scope enforcement; scope plus a simple volume cutoff; scope plus a candidate sequential evidence score. These are proposed baselines, not claims that either reviewed method already implements database protection. Until its statistical assumptions are established for this service, label the candidate's false-alarm results empirical rather than anytime-valid.

Use fresh, separately generated calibration, tuning and held-out runs. Include routine use, approved large batches, benign workload changes, slow within-scope misuse, abrupt misuse and an initial period of benign activity followed by compromise. Evaluate both a fixed misuse schedule and a synthetic opponent allowed to select schedules after seeing the public policy and prior response outcomes. Give both opponents the same record target, duration and query budget. Keep final evaluation seeds and scenarios outside tuning. Include missing or corrupted application logs while preserving the independent gateway observations.

For every arm and workload, report these distinct outcomes:

- Actual fictional records and bytes received before the first alarm, before enforcement and afterward; distinct records and repeated transmissions separately.
- Alarm before the first unauthorized record, alarm before a declared loss budget, and no alarm within the fixed horizon. Preserve misses as censored observations; do not report only the delay of successful detections.
- Legitimate users ever alarmed, ever restricted and their denied operations, each with its denominator. Report passive monitoring separately from a block, including availability loss for legitimate users of the affected credential.
- Alarm delay, decision delay and enforcement delay separately, using elapsed time and request count. Preserve uncertainty across independently generated runs; reordered copies of one trace are sensitivity checks.
- Delivered records versus legitimate disruption as thresholds vary, separately for fixed and adaptive misuse and before/after benign distribution shift. A candidate is useful only if it improves that tradeoff under the declared operating constraint.

Do not supply a confirmed-compromise event to the candidate detector as ground truth. Such an event can remain a separate oracle-containment reference, clearly labeled. Inspect the client-observed response bodies independently of detector scores. A failure to beat simple permissions or volume controls is a valid result; early warnings alone do not establish prevented leakage.

This document proposes the next experiment. It adds no implemented detector, production integration or demonstrated citizen-database protection.
