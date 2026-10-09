# File-first PDF intake verification - October 9, 2026

## Shipped behavior

Home, Upload and Live accept file selection or a page-wide file drop. JavaScript starts an authenticated upload immediately and opens Live after the server accepts the batch. No purchase fields are required. A native file form remains usable without JavaScript. Manual purchase entry is available under an optional disclosure on Upload.

The existing bounded worker queue, PDF validation, privacy checks, cleaning/verifier flow and publication enforcement are reused. A full queue rejects before creating a purchase. File type/count/size errors appear inline; network failures offer explicit retry and advise checking Activity when acceptance is uncertain. Retries are not automatic or guaranteed idempotent.

Explicit office/procedure/item/amount labels in the first three text pages per file are saved as private hints with filename and page. Unknowns remain absent; hints are not a validated identity, legal authority or public purchase metadata. Scanned-page metadata extraction is not implemented; existing OCR/vision privacy checks still run. Neutral intake references and an unknown amount are used instead of fabricated business facts. Metadata approval/mapping is deferred.

## Synthetic PDF

`fixtures/pdfs/fictional_patient.pdf` is a one-page, visually checked PDF with conspicuously fictional identifiers and medical details. Authenticated staff can download it at `/documents/sample.pdf` or through **Download test PDF**. Deterministic scanning detected `dni`, `birth_date`, `home_address` and `health_terms`. In the offline HTTP test, its original is withheld and its public URL returns 404. The exact outcome with live models and cleaning depends on configured providers and existing verifier checks.

## Checks

- Backend after integrating the team's Senso decision-citation change: **331 passed** (5 existing PyMuPDF deprecation warnings).
- tester-army/e2e Chromium: **16 passed**, run `01a122dc-f071-71a9-8f65-7a3abd561205`.
- New browser checks cover selection without purchase fields, a real DOM file-drop event, automatic navigation, loaded Live activity, withheld original, private extracted hints and invalid-drop/no-write behavior.
- Existing browser tests cover all ten fictional PDF fixtures and both human approval paths, including exact benign PDF bytes.
- First browser run found a removed-form listener that stopped Live initialization. It was removed, the activity assertion strengthened and the entire suite rerun successfully. Failure traces retained locally in `.e2e/failed-intake-live-before-fix/`.
- Sample PDF text extracted and rendered successfully; rendered page inspected for clipping and overlap. No production PDFs or real victim records were used.

This records local verification. It does not establish deployment on the team's server, general extraction accuracy or live sponsor/model performance.
