# Document inspector

## Use

Open a file in Workspace, or choose **Inspect document** on a purchase. `/inspect/{attachment_id}` shows the actual original and resulting page. Use the page arrows to compare a multi-page PDF and toggle **Show text changes** to see changed text lines on the original.

The right-hand tabs keep evidence beside the document:

- **Process:** recorded steps, provider names, statuses and measured durations. No invented progress. If the server restarted or the job aged out, the view says no live trace is retained.
- **Guidelines:** finding-linked operational policies and official references.
- **Senso:** exact lookup query, server configuration/ingestion receipt, retrieved passages, measured latency and expandable content/version/digest receipt. **Run lookup** repeats a real scoped retrieval using rule titles only; the server derives the query. Missing configuration, empty findings, loading and provider failure are explicit. Link directly with `/inspect/{attachment_id}#senso`. Retrieved context cannot release a document.
- **Web:** the actual fixed Google News query, saved reporting leads and **Search reporting**. The request runs the existing RSS discovery and returns headlines, publisher and publication date. **Review source** opens the existing proposal flow. Search never creates or activates rules.

A cleaned candidate is labeled internal until the current publication decision permits release. A published unchanged original is shown as such. Missing/failed previews retain original-download and refresh actions. Stale files have no public-copy action.

## Architecture

`inspection.py` renders only the requested page at a maximum 1400px edge and compares word positions between stored PDF bytes. It returns normalized changed-line coordinates, not the words. This overlay does not cover image/annotation differences or certify complete redaction. Both previews remain the real rendered PDFs, without an overlay baked into the bytes.

All inspector HTML, metadata, research and image routes use the existing staff dependency; private responses use no-store. Public-file authorization is unchanged. Metadata contains masked removals and authored policy references, not raw document text or model prompts. The existing open-staff event configuration is not a production authentication guarantee.

Templates and scoped styles reuse the white/blue palette, light headings, compact type, existing links and narrow borders. No dependency or logo was added. Mobile panes stack; the evidence tabs support arrow/Home/End keyboard navigation.

## Executed verification — October 9, 2026

Based on main `e5ce548` plus this change:

- **342 backend tests passed**, five existing dependency deprecation warnings. New checks cover real text differences and rotation, staff-only bounded PNGs, missing copies/pages, stale decisions and JSON discovery authorization.
- **21 Chromium tests passed** with tester-army/e2e, run `01a12321-44d4-7603-9d37-27866dca1737`. This includes desktop/mobile inspector interactions, actual PDF image loading, overlays/page navigation and research success/failure. Research response states in browser tests are intercepted and fictional.
- Frontend TypeScript/Vite production build passed; inspector JavaScript syntax check passed. Desktop and mobile screenshots were inspected.
- A separate real Google News RSS call returned and stored **12 reporting leads** in a disposable local database. No rules changed. This proves the search adapter response in this run, not the truth of the articles or a live Senso/model run.

These checks do not establish deployment, arbitrary PDF coverage, live sponsor execution or a breach-prevention rate. Originals and test fixtures here use fictional records only.

### Visible Senso extension

- **343 backend tests passed**. The new HTTP test checks staff/same-origin enforcement, ignored client topic/URL inputs, stored citation evidence, unavailable providers and unchanged publication/rules.
- **22 Chromium tests passed**, run `01a12329-bc37-73a0-a9bd-aef86d6bf5eb`. Senso browser responses are intercepted and fictional; coverage includes disconnected, loading, cited, receipt and failure states and safe rendering of provider text.
- Final direct-link testing exposed same-page hash navigation not selecting the tab. Added a hash-change handler; all four inspector browser tests then passed in run `01a1232b-82e7-76aa-9473-7a226b013393`. The failed intermediate trace is retained locally.
- Separately, the loopback preview used the existing server-only Senso credential. A real POST `/api/inspect/1/senso` returned HTTP 200, five passages and a version reference in **1291 ms**. The document stayed withheld and unpublished. Only the authored public guideline pack and rule titles were used; no PDF content was sent to Senso. Other preview model providers remained disabled. This is a local integration receipt, not evidence of server deployment.

## Fictional PDFs to try

Drag these files into Workspace:

| PDF | Purpose |
|---|---|
| [inspection_purchase.pdf](fixtures/pdfs/inspection_purchase.pdf) | Two-page equipment purchase with a fictional DNI and birth date. Inspect the actual candidate with those identifiers removed and the equipment/price retained. |
| [especificacion_tecnica_silla.pdf](fixtures/pdfs/especificacion_tecnica_silla.pdf) | Equipment specification without personal identifiers; benign control. |
| [justificacion_medica.pdf](fixtures/pdfs/justificacion_medica.pdf) | Fictional clinical information; restriction control. |

A cleaned preview is not publication authorization. Automatic publication requires the configured review/check workflow to pass; when those providers are disabled or unavailable, the file stays internal. Senso citations explain policy and cannot approve publication.
