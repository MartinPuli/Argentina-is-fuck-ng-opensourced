# Changelog

## 2026-10-09 - Autonomous pipeline documented

- Documented the autonomous mode added in `dce982b`. With `GATE_AUTONOMOUS=1`, every upload reaches a final outcome without a person. Uncertain files become `withheld` with an `autopilot_restricted` finding; they are never published.
- Added §13 to the architecture decisions. It supersedes the operator approval step in §3, the operator as final decision-maker in §5.4 and the "no autonomous publication" line in §7. Earlier sections stay as written.
- Six autonomy tests and the full gate suite (276 tests) pass locally. A Semgrep scan of the change reported 0 findings.
- The code is deployed. The flag was on at argensec.pujia.ar when checked at 22:21 UTC on October 9, 2026. Updated the README, DEMO and SUBMISSION lines that said uncertain files wait for a person.
- Not built yet: a way for a person to release an automatic restriction from the app. The Review page acts only on held files.

## 2026-10-09 — Team publication gate, incident learning and evidence comparison

- Kept the team's PDF publication gate as the primary build, with a live activity workspace alongside detailed upload/review screens. The broader server-defense proposal remains future work.
- Added sourced incident recipes, optional model-proposed rules, immutable version checks, positive/benign tests, reviewed activation, existing-file rechecks and downloadable skill/proposal bundles. Rule changes suspend stale public approvals; retirement does not automatically release held files.
- Added a sourced Argentina comparison with two companies and five public bodies. Unknown counts, file estimates, disputed record claims and report dates remain separate. This sample does not establish a verified largest-company ranking.
- Hardened staff access, request origin checks, upload bounds, mixed-content PDF coverage and incomplete-analysis handling. Local provider mocks and fictional PDFs are explicitly separated from live sponsor proof.
- Added six targeted paper reviews beyond the previous checkpoint: 55 reviews in 16 evidence files, with four metadata-only exclusions. Reconciled corpus now has 35 matched groups and 2,327 unmatched groups. Added a 77-assertion in-flight revocation experiment; earlier downloaded data remains unrecoverable.
- Changes were first pushed to `codex/incident-learning` while the team continued updating `main`. The branch's public deployment and a same-run three-sponsor demonstration remain unverified.

## 2026-10-09 - Transferred checks, reconciled corpus and teammate review

- Added five targeted full-text reviews after the 44-record checkpoint, bringing the evidence to 49 reviewed records across 13 files. Three metadata-only inaccessible records remain excluded. Eleven of 18 prioritized discovery candidates are now reviewed.
- Recovered all ten historical index snapshots by exact hashes. Reconciled 2,364 entries into 2,362 candidate groups; 29 groups match reviews and 2,333 do not. Preserved versions, uncertain aliases, grouping evidence and the original discovery counts; corrected an arXiv identifier parsing gap without rewriting the old snapshot.
- Added an authored lesson-transfer experiment with 129 main checks. A separate checker passed 520 assertions over 140 read responses in 20 further runs. Changed supported exposures were contained; unsupported formats, incomplete inventory and an unapproved rule remained explicit misses. Containment also interrupted the affected legitimate identity.
- Kept simulated rule approval, same-user processes and deterministic checking distinct from autonomous learning, institutional authorization, hardened isolation or deployment.
- Fetched the shared repository; main remained current and a new publication-gate branch appeared. Inspected the teammate's separate document-protection prototype and recorded three grounded findings without merging or changing that branch. Sponsor adapters and offline tests do not establish a live integrated run.

## 2026-10-09 — Observed exposure, independent response checks and six paper reviews

- Added an observed-credential experiment with separate app, gateway, controller and observer processes. The controller corroborates an actual fictional exposure instead of accepting a trusted compromise flag.
- Compared scope-only, repair-only, revoke-only and combined responses. Combined mode prevented post-response misuse while B continued; three records escaped earlier and A lost one legitimate operation. Route removal is deterministic, not an agent-written code repair.
- Passed 88 main checks and 304 independently specified assertions over 120 additional HTTP read responses. Recorded same-user isolation limits, nontransactional recovery and the absence of AI, sponsors or public deployment.
- Added six targeted full-text reviews, bringing the count to 44. Eight of the 18 priority discovery candidates now have targeted reviews; AD18 remains unread and its substitute is counted separately.
- Added a direct hackathon assessment: finish one measurable containment-and-recovery demonstration before broadening the product. Pi remains optional repair context with unverified access.

## 2026-10-09 — Additional Argentine leads, sponsor feasibility and selected build skill

- Pulled `main`; no newer teammate changes existed beyond the previously reviewed PAMI contribution.
- Added seven social-intelligence leads/exclusions and eleven corroboration records. Preserved inaccessible original-post URLs, disputed claims, private suppliers, enforcement overlap and old incidents in fresh coverage.
- Added an auditable count: four confirmed institution-level government disclosures in the original 15-entry reviewed sample. New search results are not silently counted as confirmed mass leaks or distinct victims.
- Verified practical ClickHouse, Guild and Semgrep roles and constraints; the hosted defense remains proposed, not integrated.
- Evaluated Pi on request: public OAuth MCP documentation exists, while tenant access and Guild compatibility remain unverified. Recorded the strong competitive overlap and an optional context/repair-guidance role.
- Added six selected full-text paper reviews, bringing the recorded total to 38; five earlier discovery candidates now link to completed targeted reviews. No papers were reproduced.
- Installed the user-selected AppBuilder skill locally in the repository at upstream revision `531fe62b6603df4d607d3df484b5dc3ecd9bee8e`. Added agent guidance, provenance hashes and third-party license attribution without changing the established web-demo scope.


## 2026-10-09 — International precedents and stronger repair boundaries

- Compared documented country programs and six selected commercial/open-source comparators. Distinguished government evidence, historical adoption and vendor capability claims.
- Corrected positioning: coordinated agents, attack simulation and remediation revalidation already exist. Open reproducible incident packages are a proposed focus, not a proven market gap.
- Added an official-documentation comparison of Firecracker, gVisor, Kata Containers and E2B, separating code isolation from network policy, credentials and live containment.
- Added five targeted full-text access/exposure paper reviews, bringing the selected evidence count to 32; added a separate discovery ledger with 986 title entries and 18 prioritized candidates.
- Refined the proposal around independent repair, rehearsal and verification jobs, indirect permission paths, exact release artifacts and legitimate-service continuity.
- Kept third-party retrieval text in a local ignored cache. No paid product evaluation, government deployment or sponsor integration was performed.
- Added a secondary synthetic publication experiment: 45 main assertions and 52 independent byte-level assertions across 36 further HTTP requests. Preserved the counterexample showing that false public classification can still leak private content.
- Pulled teammate commit fa859d5 without overwriting local edits; added a separate review with three citation/attribution findings while preserving the original PAMI contribution.

## 2026-10-09 — Defense research and local effects experiment

- Added 27 selected paper records with primary-source versions, reading locations, methods and limitations; no claim of exhaustive reading or paper reproduction.
- Recorded automated title discovery across four 2026 venue indexes: 1,378 entries and 177 keyword matches, with explicit coverage gaps.
- Added the plain-English BREACHSTOP proposal, linking verified historical mechanisms to reviewed tests and independent enforcement.
- Preserved the current event requirements and distinguished proposal fit from completed sponsor integration or submission.
- Added a local synthetic HTTP experiment with four control modes and 34 declared checks, plus six additional runs checking 122 read responses under independently specified variants.
- Reported pre-confirmation exposure, the affected account's legitimate-service interruption, and the absence of AI, production-isolation or national-impact evidence.
- Licensed experiment source and executable fixtures under MIT; documentation and generated evidence remain CC BY 4.0.

## 2026-10-09 — Initial research snapshot

- Published the full English report covering October 9, 2025–October 9, 2026.
- Added separate chapters for methodology, Argentine context, the incident timeline, causes, consequences, and response priorities.
- Added a deduplicated source index and contribution guidance.
- Preserved the distinctions between confirmed exposures, disputed claims, enforcement developments and older incidents.
- Licensed the original text under CC BY 4.0.

This is a dated research snapshot. Any later evidence or correction should be recorded in a new entry.
