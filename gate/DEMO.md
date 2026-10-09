# Publication Gate and incident-learning demonstration

Use a fresh local database and the offline startup command in [README.md](README.md). Configure a staff password first; the default username is `reviewer`. Do not disable authentication. All documents below are fictional. Publication Gate is the primary deliverable; incident learning extends its publication workflow. This walkthrough demonstrates local controls, not a live sponsor run or public deployment. The broader server-defense experiments are separate future work.

1. **Frame the problem.** Open the overview. Explain: “A public purchase record can include supporting documents that should stay private. We check each attachment separately.” The reporting link supplies context; the demonstration does not access real patient records.
2. **Load the case.** Select **Open demo workspace**, authenticate, then **Run fictional case**. It creates three purchases containing eight attachments. On a fresh database with sponsor calls disabled, none is automatically public: missing model analysis sends otherwise unblocked files to review. Purchase metadata is already public.
3. **Read the findings.** Open the wheelchair purchase. The medical justification is withheld by identifier rules. Scanned identity/disability documents are withheld if OCR finds a blocking identifier; if OCR is absent or fails, they remain held. A technical specification and supplier quote are also held because the context check is unavailable. Show the explicit reason instead of claiming the model ran.
4. **Inspect and approve one safe file.** In **Review queue**, find `especificacion_tecnica_silla.pdf`. Select **Inspect original PDF** and read the entire fictional specification. Enter a reason such as “Inspected every page: fictional technical requirements only; no patient details.” Select **Approve publication** and confirm. The server records the authenticated identity; a typed name cannot replace it. Do not approve the medical, identity, prosthesis, bed or x-ray examples merely to make the demo look successful.
5. **Verify both outcomes.** Open the public portal in a private/unauthenticated browser session. The approved specification is available; the remaining held/withheld files have no public download links. Record the numeric attachment ID from a withheld original link, then request `/public/file/<that-id>` in the unauthenticated session: expect 404. Do not confuse it with `/internal/file/<id>`, which requires staff credentials. Confirm the approved PDF opens as expected.
6. **Show the audit.** Return to the authenticated **Audit trail**. Point out the initial hold/withheld decisions and the later approval attributed to the reviewer. Initial-decision counts are historical and do not change into a current-inventory count after approval. In this offline run the displayed backend is local SQLite.
7. **Close with the measured scope.** “We observed a held file become downloadable only after authenticated review, while another private attachment remained blocked. Missing analysis did not silently publish it. This does not prove every private document will be detected.”

Pressing **Run fictional case** again adds new records. For another clean demonstration, restart with a new unused `GATE_DB` path rather than deleting an existing database.

For sponsor demonstrations, first record actual model responses, Guild session completion and ClickHouse writes/queries using the intended accounts. A configured status alone does not establish any of those outcomes. Keep that evidence separate from this offline script.


## Extend the same gate with a lesson

Keep the approved fictional technical specification from the first walkthrough as the legitimate-publication counterpart.

1. **Open the source-backed library.** Visit `/learning` while signed in. Read the PAMI source card, its evidence status and stated limits. Choose **Build a rule** (`POST /learning/from-case/pami-private-attachments`). A draft appears at `/learning/rules/{id}`. Río Negro is a separate fictional publication adaptation, not a reconstruction of that incident's access mechanism.
2. **Inspect before testing.** Read the phrase groups, proposed HOLD action and improvement suggestions. Open a positive and a benign example using **Open fictional PDF** (`/learning/rules/{id}/example/{index}.pdf`). These contain fictional references, not leaked records.
3. **Run the examples.** Select **Run rule tests**. Explain that “Before” means this candidate was absent; the table measures candidate matching on its authored examples, not the entire gate's accuracy or a model's performance. Inspect both positive matches and benign non-matches before proceeding.
4. **Activate the exact reviewed version.** Select **Activate tested rule** and confirm. This submits the saved digest to `/learning/rules/{id}/activate`. In the unauthenticated public session, the previously approved specification is temporarily unavailable because its old checks predate the new revision. This visible interruption is part of the control's cost.
5. **Recheck existing files.** Select **Recheck existing PDFs** (`POST /learning/rescan`). Confirm that the unchanged technical specification returns and its exact PDF is still readable. Matching content is moved to review; existing withheld content stays internal. The integrated test additionally exercises a previously approved fictional positive and verifies that rechecking holds it while preserving its benign counterpart.
6. **Try a new fictional PDF.** Upload a downloaded positive example through `/office` and inspect its learned-rule finding. Active rules apply immediately. In the offline run, missing model analysis can independently cause HOLD too; do not attribute every held result solely to the new rule. The request tests use an explicitly constructed safe model result to isolate that difference.
7. **Share the evidence.** Download `skill.md`, `proposal.md` or `bundle.zip` from the rule page. Show the source, digest and saved test outcomes. These are review artifacts: they do not install a skill, activate a rule elsewhere, or complete the proposed improvements. A recipient must create and test a new inactive candidate in its own enrolled gate.
8. **Optional retirement.** Retire the exact version. Retirement also requires rechecking older publication approvals; it does not release previously held/withheld files. Show the resulting status instead of promising automatic recovery.

## New-report and sponsor extension

With AkashML configured, **Bring a new report** accepts a sanitized summary and source URL through `/learning/propose`. The URL is stored rather than fetched or independently verified. The submission remains labeled unverified; the model produces a candidate requiring the same tests and authenticated activation. Do not paste real leaked records, identifiers or credentials. Offline, use the authored cases and show the clear unavailable-model state.

The current walkthrough does not verify the event's three-sponsor requirement. A separate observed run must record the intended AkashML result, Guild brief/session completion and ClickHouse write/query, or another approved substantive sponsor combination. Neither configuration nor mocked tests establish those integrations. Open `/exposures` for the sourced comparison. It separates companies from public bodies and does not invent an ordinal ranking from incomparable or unverified quantities.

## Team live view

Open `/live` and press **Send 8 fictional office files**. Observe the actual queued checks and review cards; without configured model/OCR services, incomplete cases remain private for review. This view preserves the team’s live flow while the detailed office/review pages remain available.
