# Incident learning for Publication Gate - Build Plan

## 0. Who this is for
- Target users: the team's institutional document reviewers and procurement operators.
- Problem: a publication gate's fixed checks do not incorporate newly understood disclosure patterns.
- Solved: a reviewer turns a sourced incident into a tested, attributable PDF rule, applies it to new and existing files, and exports a reusable skill and improvement proposal.
- Scope: frontend and backend in the existing Publication Gate. This extends the team product; it does not replace it with a server-defense product.

## 1. Three-phase breakdown
| Phase | Theme | Features | Detail |
|---|---|---|---|
| 1 | Core loop | Source evidence → candidate PDF rule → positive/benign tests → reviewed activation → PDF enforcement/recheck → skill and proposal export | Full below |
| 2 | Completeness | Source monitoring, independently curated evaluation sets, granular reviewer roles, background rescans, deployment/sponsor receipts | Future work; no unattended web scraping or activation claimed |
| 3 | Depth and delight | Cross-institution lesson exchange, rule drift analysis and measured broader generalization | Future work; no universal learning/prevention claim |

# Phase 1 detailed plan

## 2. Backend
### Tables
- Existing private attachment storage is retained.
- `learning_rules`: immutable source/spec/digest, generator, author, test results, status and activation attribution. Source status is evidence metadata, not authorization.
- `learning_checks`: attachment ID and applied active-rule revision. Changed active rules invalidate previous public eligibility until an explicit recheck.
### RLS policies
SQLite server authorization applies. All learning creation, test, activation, retirement, rescan and export routes require the configured staff identity and same-origin mutation checks. Anonymous access remains public-only. External text cannot authorize activation.
### RPCs needed
- Known case → a deterministic reviewed recipe, explicitly labeled.
- Sanitized report + source URL → optional AkashML candidate proposal. Missing provider produces an honest error, not simulated AI output.
- Test candidates against explicit positive and benign examples; activation requires a passing current digest.
- Recheck stored PDFs; learned findings can restrict access but never automatically release an existing restriction. Retirement never republishes a file.
- Export a template-generated SKILL.md and improvement proposal; downloading neither installs a skill nor activates a rule.
### Storage buckets
None new. PDF blobs remain private. Store sourced summaries and declarative rules, not breached databases. No source URL is fetched by this feature. Test texts must be fictional.

## 3. Screen inventory
| Screen | Purpose | View | Source |
|---|---|---|---|
| Learning library | Read source cases, create candidates, see active checks and remaining rechecks | Staff | Curated source metadata + SQLite |
| Rule detail | Inspect evidence, phrases, rationale, tests, status, improvements, activation and exports | Staff | Immutable rule record |
| Existing PDF views | Identify new learned findings and stale policy checks | Staff/public | Stored decision + current rule revision |

## 4. Navigation flow
Learning library → choose documented case or paste sanitized report → candidate → run tests → inspect positive/benign outcomes → activate exact version → recheck existing PDFs → inspect changed access → export skill/proposal. New uploads apply active rules immediately.

## 5. Component needs
Reuse the current sidebar, panels, badges, loading/error states, evidence tables and design tokens. Add source cards, a rule-status timeline, readable phrase groups, before/after test rows, genuine revision counts and download actions. English UI; fictional PDF contents may be Spanish.

## 6. Edge cases to handle explicitly
- Alleged/reported evidence stays labeled; unknown historical mechanisms remain unknown. A recipe is an engineering inference.
- No raw breach data in the input. Untrusted source text stays evidence, never executable instructions.
- Empty/malformed model output, source URL with credentials, unbounded rules, stale digests, no passing tests, false-positive test failure, OCR failure and missing analysis.
- Existing public approvals need rechecking after a rule change; do not keep serving stale decisions.
- Rules use bounded declarative phrase groups, not arbitrary Python, shell, regex or generated scanner code.
- Existing deterministic blocks stay blocked; learned HOLD rules remain reviewable; learned WITHHELD findings cannot be approved through the held-file route.
- Narrow/mobile layout, keyboard labels, errors and empty library states. No native mobile capabilities apply.

## 6b. Architecture & performance checklist
Keep FastAPI/Jinja and SQLite. Matching is bounded literal phrase matching with Unicode normalization. Existing PDF size/page limits apply. Rechecks are synchronous for the small fictional demo, with explicit incomplete results; a durable queue is Phase 2.

## 6c. Lifecycle & pre-launch checklist
Use existing optional AkashML configuration. Tests clear all external credentials and use temporary SQLite files. Live sponsor execution is not established by connector code or fixture tests. Recorded checks describe their real denominator; example tests are not independent proof of real-world accuracy. The local preview uses fictional documents.

## 6d. Security checklist
Authenticated mutation and private exports, exact-origin checks, immutable digest pinning, no arbitrary source fetch, no executable rule payloads, no private values in matching evidence. Skills clearly separate quoted evidence from trusted instructions. Do not grant exported skills automatic deployment authority. Revalidation controls newly served responses, not copies already downloaded or in-flight buffers.

## 6e. Store publishing checklist
Not an app-store product. Deliver tested code, English docs, local browser demonstration and public repository changes. Account-backed deployment and a same-run three-sponsor demo remain separate verification work.

## 6f. Motion & delight checklist
Reuse named CSS durations and loading feedback, honor reduced motion. Show only actual test/activation/recheck transitions, without invented agent progress.

## 7. Open questions for the user
None needed: the user explicitly selected the team product and requested incident learning, new PDF checks, reusable skills and improvement proposals. Implement these within the existing prototype.

## Integrated team activity and evidence comparison

Keep the team's live processing view at `/live` while retaining detailed upload/review screens. The background worker must use the same authenticated submission, PDF limits, learning revision and fail-closed decision path; in-memory activity is a demo limitation. The staff-only `/exposures` screen presents sourced cases by organization type and original counting unit. An unknown quantity is never zero, and unverified volumes cannot create a factual national leaderboard. These are additions to the current phase, not replacements for the team product.
