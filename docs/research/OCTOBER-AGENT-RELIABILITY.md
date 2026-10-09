# October agent reliability: two full-text reviews

Reviewed 2026-10-09. Both are new October 2026 preprints. Metadata was checked against their versioned arXiv records. Methods, result tables, and limitations were read; neither implementation was run. Numerical observations below are authors’ benchmark results, not measured BREACHSTOP effects. JSON carries metadata and section locators without repeating the narrative.

## OAR-01

**From Investigation Failures to Reliable SOC Agents: Understanding and Improving LLM-Based Alert Triage.** Saimon Amanuel Tsegai, Alex Kantchelian, Danfeng (Daphne) Yao, Peng Gao. First publication and version: **2026-10-07, v1**. Preprint; no accepted venue claimed.

[Version record](https://arxiv.org/abs/2610.10608v1) · [Full text](https://arxiv.org/html/2610.10608v1) · [PDF](https://arxiv.org/pdf/2610.10608v1)

AIDA combines typed retrieval outcomes, an append-only ledger, separate challenge context, and adjudication. On 1,247 russellmitchell alerts (225 attack; 1,022 benign), GPT-4.1 missed 7/225 attacks versus Direct-Prompt’s 91/225. This measures triage, not prevented incidents. All 31 adjudication reversals corrected benign escalations. The 300-alert ablation did not isolate a significant Adversary benefit. Evaluation covers two emulated scenarios from one dataset family; incomplete retrieval still defeats agreement among agents. BREACHSTOP inference: distinguish empty results from failed queries, require affirmative grounds before closure, and test missing context, misleading narrow searches, benign activity, and reviewer regressions. Evaluate separate adjudication before adding every role.

Locators: §§III-A–D/Table I; §§IV-A, V-B–C/Algorithm 1; §§VI-A–D/Figure 6/Table II; §VII. Reading depth: relevant full-text methods, results, ablations, limitations.

## OAR-02

**NOMOS: Compiling Written Policies into Statically Verified Tool-Call Gates for LLM Agents.** Min-Young Yu, Tony Kim, Jang Won Choi. First publication and version: **2026-10-08, v1**. Preprint, submitted to IEEE Access; submission is not acceptance.

[Version record](https://arxiv.org/abs/2610.11030v1) · [Full text](https://arxiv.org/html/2610.11030v1) · [PDF](https://arxiv.org/pdf/2610.11030v1)

NOMOS compiles policies against human-authored predicate vocabularies and gates tool calls deterministically. Airline encoded-clause violations fell 234/353→3/116 executed writes; changing denominators and confirmation semantics matter. Banking standard-attack success fell 134/288→0/288 pairs, yet injected payments reached known payees in 8/288 gated pairs. Structural checks prove neither policy completeness nor semantic fidelity. Structured tool fields remain trusted; poisoning them was untested. Slack legitimate-task utility fell sharply. Implementation is proprietary. BREACHSTOP inference: audit rule-to-tool bindings, replay legitimate traces, measure harmful effects beyond benchmark flags, and test poisoned structured evidence. Agent assertions must not become authorization facts.

Locators: §§3.1–3.4/Algorithm 1/Tables III–IV; §4; §§5.1–5.3/Tables V–VII; §5.8/Table XI; §§5.10–5.11/Tables XV–XVII; §6. Reading depth: relevant full-text methods, results, checker audit, ablations, limitations.

Source budget: narrative 99 words (OAR-01), 93 words (OAR-02), plus short metadata/locators; JSON adds no repeated source-derived narrative. No quoted passages.
