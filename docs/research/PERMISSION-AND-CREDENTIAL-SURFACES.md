# Permission, credential and query trust surfaces

Review cutoff: 2026-10-09. Two relevant full-text reviews; two access gaps retained without promotion into the reviewed-paper count. Metadata and precise reading locators are in [permission-credential-surfaces.json](permission-credential-surfaces.json). Results below are authors' measurements; no experiments, author code, exploits or credentials were executed or tested by us. Proposed tests are our design implications.

<a id="pcs-01"></a>
## PCS-01 / AD14 — Dangers Behind Access Control

**Index only; not counted as reviewed.** The publisher returned HTTP 403. Author publication lists supplied the same publisher link or no downloadable paper. Methods, denominators and limitations remain unverified. The university lists publication on 2025-11-22 and the CCS event on 2025-10-13–17; neither establishes earliest public availability. No implementation claim is inferred from the abstract. [University record](https://experts.umn.edu/en/publications/dangers-behind-access-control-understanding-and-exploiting-implic/), [author list](https://wenboshen.org/publications/), [publisher](https://dl.acm.org/doi/10.1145/3719027.3765106).

<a id="pcs-02"></a>
## PCS-02 / AD12 — CRX-ray

**Index only; not counted as reviewed.** Queen's University Belfast identifies a final published version dated 2026-06-04, but its linked PDF and ACM full text were inaccessible in this session. Earliest preprint availability remains unresolved. Abstract key counts are deliberately excluded from reviewed results. Method coverage, false positives, validation permissions and remediation outcomes require full-text inspection. [University record](https://pure.qub.ac.uk/en/publications/crx-ray-large-scale-detection-of-api-key-leakage-in-browser-exten/), [public PDF link, retrieval failed](https://pure.qub.ac.uk/files/691094097/3779208.3785378.pdf).

<a id="pcs-03"></a>
## PCS-03 / AD16 — Effective and Efficient Threat Hunting with Small Language Models

**Reviewed:** arXiv v3, 2026-09-17; first preprint 2025-12-07. Methods §§3.3–3.5; evaluation §4, Tables 4–5; limitations §5.

DeepSeek drafts KQL from retrieved schemas; Gemini refines it. On 230 Defender pairs, schema validity is 0.906. On 83 independently authored pairs using the same schema, validity is 0.831 but literal-filter Jaccard is 0.100. These measure parser/reference agreement, not detection or authorization correctness. Shared Gemini roles can share blind spots; unseen schemas remain untested. Repetition counts for final table scores are unspecified; Appendix C's five iterations concern error diagnostics. Proposed tests: independently seed expected result rows, exact indicators, tenant boundaries and time windows; reject unauthorized queries outside the model. Label this query assistance, not incident prevention. [Versioned full text](https://arxiv.org/html/2512.06660v3), [version history](https://arxiv.org/abs/2512.06660).

<a id="pcs-04"></a>
## PCS-04 — TLBAC

**Reviewed:** publisher version of record, 2026-06-22. Design; evaluation RQ3–RQ4; discussion; future work.

Endpoint context enters TCP labels; a gateway enforces cloud-issued policy. Authors report 400/400 correct port decisions: 20 tenants × two ports × ten rounds. A separate 20-tenant load test times out on 150/300 requests. Labels lack cryptographic integrity/origin authentication; compromised endpoints can defeat the boundary. Cryptographic anti-replay protection is future work. Evaluation uses one Android model and TCP; L7 proxies lose labels and block service. RQ3 inconsistently describes 30 versus more-than-30 vulnerability cases; no exact attack success rate is adopted here. Proposed tests: forged/replayed labels, compromised authorized clients, revocation freshness and legitimate availability. Treat this as a boundary warning, not evidence that context labels stop stolen-credential misuse. [Publisher full text](https://link.springer.com/article/10.1186/s42400-026-00616-0).
