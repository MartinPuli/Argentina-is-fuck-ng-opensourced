# Investigation quality and execution trust

Reviewed **October 9, 2026**. Two relevant full-text reviews; no author code executed and no independent reproduction claimed. Findings are centralized below; [the JSON](investigation-execution-trust.json) supplies version metadata and evidence locators. Product implications are explicitly our inferences.

<a id="iet-01"></a>
## IET-01 · Clouseau: A Hierarchical Multi-Agent Approach For Autonomous Attack Investigation

Abdullah Aldaihan, Fahad Alotaibi, Sergio Maffeis. **ACSAC 2025**, presentation **December 10, 2025**. [Official program entry](https://www.acsac.org/2025/program/final/s234.html); [dated program](https://www.acsac.org/2025/program/final/); [author-hosted full PDF](https://www.doc.ic.ac.uk/~maffeis/papers/acsac25.pdf).

Hierarchical agents query normalized SQL logs from a supplied point of interest. Authors evaluate 21 scenarios × 3 POIs, repeating each investigation three times. Table 2 reports 99.79% single-host F1 (four scenarios); Table 4 reports 94.2% GPT-4.1-mini F1 across three OpTC scenarios. Scoring uses LLM-extracted report artifacts matched against log labels, including fallible author OpTC annotations. OpTC covers only the initial host/day. Tamper-proof logging and effective prompt-injection sanitization are assumed; attacks against these assumptions are excluded. No production containment is demonstrated. Our inference: test poisoned/missing logs and require independent gateway outcomes before mutations.

Reading locators: §4 and §4.1–4.4; §5.1.1–5.1.2; §5.2.2–5.2.3; Tables 2 and 4; §7; Appendix B. PDF pages 3–12 and 17. Table 2's 99.79 differs from the abstract's 99.78; the table value is used here.

Version caveat: the author PDF has no numbered version. HTTP Last-Modified was **October 24, 2025, 07:47:51 UTC**; this is server metadata, not a verified first-publication date. The JSON pins the retrieved bytes by SHA-256. The publisher landing page could not be retrieved. No earlier preprint was established.

<a id="iet-02"></a>
## IET-02 · VET Your Agent: Towards Host-Independent Autonomy via Verifiable Execution Traces

Artem Grigor, Christian Schroeder de Witt, Simon Birnbach, Ivan Martinovic. **arXiv:2512.15892v1, December 17, 2025, 19:05:37 UTC**; only v1 appeared in the checked history. Later listed at **ACM ASIACCS 2026**, June 3 session. [Version history](https://arxiv.org/abs/2512.15892v1); [versioned full text](https://arxiv.org/html/2512.15892v1); [official conference program](https://asiaccs2026.cse.iitkgp.ac.in/full-program/).

VET binds component proofs and transcript consistency to an Agent Identity Document. External verification authenticates execution, not decision quality. It assumes correct external services, cryptography and an honest-but-curious notary; suppression, replay and stale proofs remain possible. VeriTrade composes market-data TEE proofs with LLM Web Proofs: authenticated decisions take 4.20±0.71 seconds through a TEE proxy versus 5.80±0.70 through Web Proofs, 20 runs per setting. This author-run deployment measures latency, not leak prevention. Table 5 reaches 7.89× direct-call latency at round 32 for Mistral 3B, limiting the abstract's broad overhead claim. Our inference: bind evidence to fresh challenges and controller-approved revisions; retain independent outcome tests.

Reading locators: §3.1–3.3; §5.2–5.3; §7.2–7.5; §8, Figure 7 and Table 5; §9; §10; Appendices A–B. The conference listing establishes venue status; the reviewed text is the December preprint, not an independently checked ACM revision. ACM full-text access returned 403.

The proposed experiments above address gaps in [our design](WHAT-TO-BUILD.md); they have not been implemented or measured by this review. A valid execution proof cannot replace accountable permission policy, reliable input classification or observation of what the deployed service actually returned.
