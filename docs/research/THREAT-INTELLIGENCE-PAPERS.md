# Threat intelligence, provenance, and leak remediation papers

Review cutoff: **2026-10-09**. Target window: **2025-10-09–2026-10-09**. Five selected primary papers; this is not an exhaustive literature census. All five had accessible full text. Reading was targeted to methods, results, threat models, and limitations; experiments were not reproduced. Only papers and official publication metadata were inspected, never stolen records, marketplaces, exposed credentials, or victim systems.

The companion JSON holds version metadata, structured results, and exact reading locators. “BREACHSTOP implication” is our design inference, not an experimentally established effect of BREACHSTOP. Keep evidence quality, detection, containment, and recurrence prevention as separate outcomes.

## TI01 — KnowHow: Automatically Applying High-Level CTI Knowledge for Interpretable and Accurate Provenance Analysis

**Status:** NDSS 2026 proceedings; first preprint **2025-09-06**, before the target window. Reviewed the proceedings PDF, not an unspecified latest preprint. [Official record](https://www.ndss-symposium.org/ndss-paper/knowhow-automatically-applying-high-level-cti-knowledge-for-interpretable-and-accurate-provenance-analysis/) · [Full text](https://www.ndss-symposium.org/wp-content/uploads/2026-s199-paper.pdf)

KnowHow maps behavioral CTI to system events and reasons over attack lifecycles. Graph recall is 1.00 on five datasets containing 16 campaigns; campaign count is **not** the graph-recall denominator. In the incomplete-attack experiment, retaining 60% or 70% of steps detects only **2/3 graphs**. It assumes uncompromised kernel auditing and cannot recognize wholly unprecedented behavior. **BREACHSTOP implication:** turn past incidents into behavioral regression cases, but measure detection and containment before exfiltration; completed-graph accuracy establishes detection evidence, not prevention. (§II; §IV–VI; Tables IV, VI, XI; §IX limitations.)

## TI02 — Stayin’ Alive: How Global Stolen Data Markets Thrive on Telegram

**Status:** USENIX Security 2026 proceedings, August 2026. Earlier preprint date not established. [Official record](https://www.usenix.org/conference/usenixsecurity26/presentation/marjanov) · [Full text](https://www.usenix.org/system/files/usenixsecurity26-marjanov.pdf)

Multilingual discovery, snowball sampling, and longitudinal observation identify **155 gateway channels among 1,521 sampled channels**. Gateways redirect communities to replacement channels; associations with survival do not establish a causal takedown effect. Publicly discoverable content, language coverage, and survivorship limit representativeness. Channel claims are not authenticated local incident evidence. **BREACHSTOP implication:** marketplace disappearance cannot close an incident; retain source provenance and distinguish an external allegation from locally verified exposure and revocation. This is ecosystem evidence, not a tested leak-prevention system. (§3; §4.1; §6.2; §8; §9.3.)

## TI03 — Sealing the Window: Efficient Tamper Protection for Provenance Logs

**Status:** IEEE S&P 2026. Reviewed the author-hosted version explicitly marked as minor revisions to the conference version; revision date and first preprint date unknown. [Official acceptance](https://sp2026.ieee-security.org/accepted-papers.html) · [Author full text](https://www.seclab.cs.sunysb.edu/seclab/pubs/winseal.pdf)

WinSeal combines rapid remote log flushing with cryptographic tamper detection. Mean overhead rises from **9.5% to 15%** when detection is enabled, across four workloads and four concurrency settings; repeat counts are not specified in the inspected evaluation. Protection concerns records preceding root compromise, assumes a clean initialization and protected remote collector, and cannot prevent offline deletion. **BREACHSTOP implication:** preserve records outside the agent’s host, record integrity gaps and compromise boundaries, and test collection latency. Log-tamper prevention does not itself prevent data exfiltration. (§2.1; §4–6; Figs. 5, 11.)

## TI04 — A Context is Worth a Thousand Lies: Evading Intrusion Detectors via Intelligent Context Distortion

**Status:** IEEE S&P 2026; reviewed author-hosted paper. Earlier preprint and author-copy revision dates not established. [Official acceptance](https://sp2026.ieee-security.org/accepted-papers.html) · [Author full text](https://azadeht.github.io/papers/Contorter_sp26.pdf)

Contorter changes surrounding activity to make malicious nodes resemble benign context while preserving the attack objective. Table 3 reports recall **0.00 in 8/24 black-box settings**: four detectors × six datasets, our count of rounded table entries. This is not a victim-level success rate. Auditors remain trusted; execution feasibility can still require manual checks. **BREACHSTOP implication:** replay incidents with plausible distracting activity and test detection stability. Integrity-protected logs can faithfully record adversarial context; integrity alone does not guarantee accurate interpretation. (§2.3; §3; §4.1.1/Table 3; §6.)

## TI05 — Keys on Doormats: Exposed API Credentials on the Web

**Status:** first preprint **2026-03-12**; reviewed **arXiv v3, 2026-09-14**. Accepted CCS 2026, whose November 15–19 conference is after this review cutoff. [Accepted list](https://www.sigsac.org/ccs/CCS2026/program/accepted-papers.html) · [Version history](https://arxiv.org/abs/2603.12498) · [Reviewed full text](https://arxiv.org/html/2603.12498v3)

Dynamic web-resource analysis and disclosure follow-up distinguish exposure removal from credential revocation. At day 14, **699/1,405 exposures disappeared**, while **310/1,175 validated credentials became inactive**. Denominators differ, likely from service IP blocking; these are not identical cohorts. Detection covers 14 service types, and notification effects are observational. **BREACHSTOP implication:** require both exposure removal and controller-confirmed revocation, scan generated deployment assets, and recheck recurrence. A removed key may remain usable. (§4.1 limitations; §6.1/Fig. 8; §7.)

## Design consequence

Past leaks become useful prevention material only when converted into an independently evaluated case: evidence references and trust assumptions, a reproducible exposure condition, an authorized containment action, a regression check that catches recurrence, and confirmation that the credential or access path is actually disabled. None of these five papers establishes that an autonomous agent may authorize its own actions. Information gathered from logs or external intelligence remains evidence; the controller must enforce the separately supplied action policy.
