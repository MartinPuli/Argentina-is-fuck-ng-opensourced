# Detection reproducibility and observed credential outcomes

Reviewed on **2026-10-09**, against the research window **2025-10-09–2026-10-09**. This batch adds **two targeted full-text reviews** and preserves **one unread metadata record**. Relevant methods, evaluation definitions, results and limitations were read; no experiments were reproduced and no author code was executed. The companion [machine-readable ledger](detection-reproducibility-research.json) preserves identifiers, versions, locators and counting units.

## DRR-01 — AD06: From Claims to Crashes

**R+R: From Claims to Crashes: A Systematic Re-evaluation of Graph-Based Network Intrusion Detection Systems** — Chenglong Wang, Pujia Zheng, Jiaping Gui, Cunqing Hua and Wajih Ul Hassan. [ACSAC program](https://www.acsac.org/2025/program/final/s147.html), [publisher DOI](https://doi.org/10.1109/ACSAC67867.2025.00050), [reviewed author manuscript](https://dartlab.org/assets/pdf/rr-gids.pdf).

The program says **three** public datasets; the manuscript's abstract, §4 and Table 2 name **four**: LANL, OpTC, CIC-IDS-2017 and CTU-13. No version history resolves this discrepancy. Five systems receive differing dataset coverage. §3 describes test-set tuning. Enterprise evaluation samples one day and merges three simulated attack traces; the 101-day source corpus is not its evaluation denominator. Table 4's Sandworm/ARGUS row reports edge-level FPR 0.227 and precision 0.010; raw confusion counts are unavailable. Adjacent event-level counts cannot safely reconstruct that row. These choices limit deployment generalization. [Manuscript, §§3–4, Table 4, Appendices B–D](https://dartlab.org/assets/pdf/rr-gids.pdf).

The December 2025 venue is within the window; first public release is unverified. PDF creation metadata says October 8, 2025, which is not publication evidence. This is distinct from DRE-01's two-author *First-Principles Evaluation* (different title and DOI).

## DRR-02 — AD17 remains unread

**Sometimes Less is More: A Minimalist Approach to Neighborhood-level Provenance-based Intrusion Detection** — Cheng Zhou, Guangxia Li, Zhiwei Zhang, Anyuan Sang, Jiatong Li and Yulong Shen. [Official accepted-paper index](https://raid2026.org/accepted.html), [index data](https://raid2026.org/data/accepted_papers.csv), [author publication list](https://anyuan1999.github.io/).

The official index and author list confirm acceptance metadata. The conference page describes attendee access codes; the author's paper link returns the homepage. Bounded title, author and preprint searches found no accessible public full text. RAID runs October 11–14, after this cutoff; first publication and manuscript version remain unknown. **No methods, effectiveness or reproducibility claims are adopted. This record does not count as reviewed.** CredLeakBench is a separate addition, not completion of AD17.

## DRR-03 — CredLeakBench

**CredLeakBench: Evaluating Credential Leakage and Recovery in LLM Agents** — Rafid Ahmed, Joseph Fioresi, Mubarak Shah and Yuzhang Shang. **arXiv:2610.08871v1, October 6, 2026**; preprint. [Version metadata](https://arxiv.org/abs/2610.08871v1), [reviewed full text](https://arxiv.org/html/2610.08871v1).

Seven models use a local simulator with fictional services and synthetic vault values. Submission logs, rather than agent narration, determine outcomes. On 768 primary recovery cases, GPT-5-mini records 186 clean recoveries, 96 leaks and 486 non-completions (Table 13). Recovery requires the correct password at the trusted endpoint and no vault-value disclosure to the lure throughout the run; downstream transactions are untested. Legitimate-control utility requires only a form submission, not a correct password. The primary denominator retains 96 certificate-warning cases without a distinct recovery route. Vault policies are instructions, not enforced restrictions. Cautious instructions can legitimately cause deferral. Results do not establish real-browser or production secret-broker effectiveness. [§§3–5; Appendices A–C and E, Tables 4, 10–13](https://arxiv.org/html/2610.08871v1).

## Reviewer proposals for our evaluation

These are proposed acceptance checks, **not implemented controls, reproduced experiments or measured product results**:

1. **Publish a denominator manifest.** Freeze the evaluation day, source population, sample, graph conversion, seed, threshold and software revision. Keep training, tuning and final evaluation separate. Preserve mappings between events, edges, alerts and incidents; never divide one unit's numerator by another unit's denominator.
2. **Use an independent outcome recorder.** In an isolated environment with fictional accounts, record submitted synthetic values and destination identities outside the agent. A reassuring final message cannot override an observed unauthorized submission. Evaluate the entire run, including actions after apparently successful recovery.
3. **Separate four questions.** Report unauthorized disclosure, trusted authentication, completion of the requested operation and legitimate-service availability independently. A refusal may be correct when approval is required; label that case separately from autonomous completion failure.
4. **Distinguish advice from enforcement.** Evaluate a prompt-only policy separately from a controller that binds a synthetic credential to an authorized destination. Test both unauthorized denial and legitimate completion. Missing routes, unreachable services, model errors and verifier failures remain visible outcomes rather than disappearing from the denominator.
5. **Make publication uncertainty explicit.** Pin the reviewed artifact and retain conflicting source metadata. Do not use an acceptance index, an old PDF creation date or a new venue date to claim a newly published, fully reviewed experiment.

Paper results above are author-reported. They do not estimate prevention of Argentine institutional leaks, provide a production false-positive rate, or establish end-to-end containment and recovery.
