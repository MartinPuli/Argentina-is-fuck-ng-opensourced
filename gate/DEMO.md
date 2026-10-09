# Demo

## 2-minute video script

Site: [argensec.pujia.ar](https://argensec.pujia.ar). All files are fictional.

**Before each take:** open **Activity** (`/live`), open **Test data** and press **Clear workspace**. Wait until no file is still being checked. Keep these tabs ready: **Activity** (`/live`), **Public** (`/public`), **Audit** (`/dashboard`), [issue #2](https://github.com/MartinPuli/Argentina-is-fuck-ng-opensourced/issues/2). The Guild rounds take time, so press the button before you start talking about it, or cut the wait in editing.

| Time | Screen | Say |
|---|---|---|
| 0:00-0:15 | Chequeado article | "In May 2026, Chequeado found medical histories, disability certificates and ID cards on PAMI's public purchase site. Nothing checked the files before they went up. We built that check." |
| 0:15-0:25 | Activity | Choose **Test data > Load synthetic files**. "Three local offices upload eight purchase files. Some are clean. Some carry patient data." |
| 0:25-0:50 | Activity **Files** cards | Point at the steps as they run. "Rule-based detectors look for IDs. AkashML's open text model reads for re-identification risk. Its vision model reads scanned pages. For files that can be cleaned, Guild agents take over. The orchestrator sorts the information into clinical, procurement and public. The public agent lists what to remove. A public reviewer checks the cleaned copy. If it fails, the feedback goes back for another round, up to three." Name the round and verdict you see on screen. |
| 0:50-1:05 | A card under **Review** | "If the agents can't agree, or the file is uncertain, it waits for a person. A Guild agent writes a one-line note. The reviewer opens the original and decides." |
| 1:05-1:20 | **Purchase details** of a cleaned file | Show the **Removed** list. Open **Original (internal)**, then **Public copy**. "The text is deleted from the PDF, not covered. Each removal is listed by type and page. The public copy no longer points to anyone." |
| 1:20-1:35 | Public | "This is what the public sees. Neutral file names, because an upload name can carry a patient's name. No patient data. Blocked files have no link at all." |
| 1:35-1:50 | Audit | "Every decision goes to ClickHouse. To show PAMI scale we loaded one million simulated events, clearly labeled. Unsafe uploads by office, by data type, by month, and files affected by a rule update. Each query shows its time in milliseconds." |
| 1:50-2:00 | Issue #2 | "Most of this code was written by AI, so we ran Semgrep on it. Its first scan found a CSRF hole that could publish a held medical file. We fixed it. Patient files stay private. Public purchases stay public." |

Do not claim a FAIL round or a specific count unless it shows on screen in that take.

## Extend the same gate with a lesson

Approve one harmless file first, such as the technical specification, as the legitimate-publication counterpart.

1. **Open Rules.** Visit `/learning` while signed in. Read the PAMI source card, its evidence status and stated limits. Choose **Create rule** (`POST /learning/from-case/pami-private-attachments`). A draft appears at `/learning/rules/{id}`. Río Negro is a separate fictional publication adaptation, not a reconstruction of that incident's access mechanism.
2. **Inspect before testing.** Read the phrase groups, proposed HOLD action and improvement suggestions. Open a positive and a benign example using **Open fictional PDF** (`/learning/rules/{id}/example/{index}.pdf`). These contain fictional references, not leaked records.
3. **Run the examples.** Select **Run rule tests**. Explain that “Before” means this candidate was absent; the table measures candidate matching on its authored examples, not the entire gate's accuracy or a model's performance. Inspect both positive matches and benign non-matches before proceeding.
4. **Activate the exact reviewed version.** Select **Activate tested rule** and confirm. This submits the saved digest to `/learning/rules/{id}/activate`. In the unauthenticated public session, the previously approved specification is temporarily unavailable because its old checks predate the new revision. This visible interruption is part of the control's cost.
5. **Recheck existing files.** Select **Recheck existing PDFs** (`POST /learning/rescan`). Confirm that the unchanged technical specification returns and its exact PDF is still readable. Matching content is moved to review; existing withheld content stays internal. The integrated test additionally exercises a previously approved fictional positive and verifies that rechecking holds it while preserving its benign counterpart.
6. **Try a new fictional PDF.** Upload a downloaded positive example through **Upload** (`/office`) and inspect its learned-rule finding. Active rules apply immediately. In the offline run, missing model analysis can independently cause HOLD too; do not attribute every held result solely to the new rule. The request tests use an explicitly constructed safe model result to isolate that difference.
7. **Share the evidence.** Download `skill.md`, `proposal.md` or `bundle.zip` from the rule page. Show the source, digest and saved test outcomes. These are review artifacts: they do not install a skill, activate a rule elsewhere, or complete the proposed improvements. A recipient must create and test a new inactive candidate in its own enrolled gate.
8. **Optional retirement.** Retire the exact version. Retirement also requires rechecking older publication approvals; it does not release previously held/withheld files. Show the resulting status instead of promising automatic recovery.

## New-report and sponsor extension

With AkashML configured, **New source** (**Propose rule**) accepts a sanitized summary and source URL through `/learning/propose`. The URL is stored rather than fetched or independently verified. The submission remains labeled unverified; the model produces a candidate requiring the same tests and authenticated activation. Do not paste real leaked records, identifiers or credentials. Offline, use the authored cases and show the clear unavailable-model state.

Open **Exposures** (`/exposures`) for the sourced comparison. It separates companies from public bodies and does not invent an ordinal ranking from incomparable or unverified quantities.

## Running locally without sponsors

Without AkashML, Guild and ClickHouse, the same **Activity** flow runs, but files that need a model stay private for review, and the simulated history panel is hidden. See [README.md](README.md) for setup.
