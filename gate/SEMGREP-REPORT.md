# Semgrep review of the AI-written gate

Tracking issue: https://github.com/MartinPuli/Argentina-is-fuck-ng-opensourced/issues/2

Scan run on 2026-10-09 with Semgrep CLI 1.180.0, from the repository root:

```
uvx semgrep scan --config auto --config p/python --config p/secrets --json -o gate/semgrep/before.json gate/src gate/fixtures
```

Raw results: [semgrep/before.json](semgrep/before.json) (3 findings) and [semgrep/after.json](semgrep/after.json) (1 finding, a false positive). Semgrep could only partly parse the Jinja templates, so it logged parse warnings. Those files were partly scanned, not skipped.

| # | Finding | Rule id | File:line | Verdict | Impact | Fix | Verification |
|---|---|---|---|---|---|---|---|
| 1 | HTML forms lacked CSRF protection | Semgrep CSRF rule (earlier run) | `src/gate/app.py` POST routes | Real, fixed earlier | A foreign page could make a reviewer approve a held medical file | Commit aeea1ec: `same_origin_posts` middleware rejects state-changing requests from other origins | `test_cross_site_approval_is_rejected`; the rule no longer fires |
| 2 | f-string SQL | `python.lang.security.audit.formatted-sql-query.formatted-sql-query` | `src/gate/store.py:41` | False positive | None: the column names come from a constant tuple | Hardened anyway: constant `MIGRATIONS` statements | Not in after.json; suite passes |
| 3 | Raw SQL execute | `python.sqlalchemy.security.sqlalchemy-execute-raw-query.sqlalchemy-execute-raw-query` | `src/gate/store.py:41` | False positive | None: same line; the app uses sqlite3, not SQLAlchemy | Same as #2 | Not in after.json |
| 4 | Missing subresource integrity | `html.security.audit.missing-integrity.missing-integrity` | `src/gate/templates/base.html:4` | False positive | None: the flagged link is an inline `data:` favicon, not an external resource | None | Still reported; accepted |
| 5 | Recheck kept leaky cleaned copies public | Manual review | `src/gate/app.py` `rescan_learning_rules` | Real | The recheck scanned the original instead of the published cleaned copy. `cleaned` was missing from the strictness table, so it counted as strictest and was never downgraded. The row was then marked current and stayed public | Scan the bytes `/public/file` serves; rank `cleaned` with the public states; only learned rules or lost coverage reopen a verified cleaned copy | `test_recheck_restricts_a_cleaned_copy_that_still_identifies_someone`, `test_recheck_keeps_a_clean_cleaned_copy_public` |
| 6 | `cleaned` row could serve the original | Manual review | `src/gate/app.py` `public_file` | Real, low | A `cleaned` row with no stored copy fell back to the original PDF | Return 404 instead | `test_cleaned_decision_never_falls_back_to_the_original` |

Checked by hand and found sound: staff-only routes, including `/internal/*`, which anonymous requests get 401 on; `/public/file`, which never serves held or withheld rows; upload filename handling (nothing is written to disk); the `guild` subprocess (argument list, no shell, timeout); secrets (`p/secrets` found none); and logging (no extracted text is logged). `GATE_OPEN_DEMO=1` opens staff pages on purpose for the fictional public demo. It must never be set in a real deployment. Follow-up: a published cleaned copy keeps its original filename, which could contain a name.

Tests: `cd gate && uv run python -m pytest -q tests` gives 226 passed.
