# Document inspector

## Use

Open a file in Workspace, or choose **Inspect document** on a purchase. `/inspect/{attachment_id}` shows the actual original and resulting page. Use the page arrows to compare a multi-page PDF and toggle **Show text changes** to see changed text lines on the original.

The right-hand tabs keep evidence beside the document:

- **Process:** recorded steps, provider names, statuses and measured durations. No invented progress. If the server restarted or the job aged out, the view says no live trace is retained.
- **Guidelines:** finding-linked operational policies, official references and the saved Senso citation/version when one exists. Retrieved context cannot release a document.
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
