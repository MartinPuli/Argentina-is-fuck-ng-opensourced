# PDF intake - Build Plan

## 0. Who this is for
Institutional staff who need to check a PDF without transcribing purchase fields. Solved means choosing or dropping files starts the existing analysis immediately. Frontend and backend together; English interface, existing blue/white tokens.

## 1. Three-phase breakdown
| Phase | Theme | Features | Detail |
|---|---|---|---|
| 1 | Core loop | File-only upload, automatic analysis, private detection of explicit document labels, fictional downloadable PDF | Full below |
| 2 | Completeness | Review and map detected metadata to approved purchase records | Deferred; no inferred values published automatically |
| 3 | Depth | Richer document classification and scanned metadata extraction | Deferred; existing OCR/security analysis retained |

## 2. Backend
### Tables
Existing purchases gain a nullable `intake_details` JSON text column through the idempotent migration list. Original PDFs remain in authenticated attachment storage. Extracted values are untrusted, staff-only hints.
### RLS policies
SQLite application authorization applies, no Supabase. File-only POST requires staff and existing same-origin checks; public endpoints never serialize intake_details.
### RPCs needed
POST /documents/upload validates the complete batch, reserves bounded queue capacity, creates neutral metadata and queues existing checks. Unknown amount is NULL, not a fabricated zero. Existing manual upload stays available.
### Storage buckets
No new bucket; private existing PDF storage and publication enforcement remain.

## 3. Screen inventory
Home, Upload and Live share a file-only upload component. Purchase detail shows private extracted labels. PDFs follow the existing Live progress and review workflow.

## 4. Navigation flow
Choose/drop PDF anywhere on these pages -> validate -> queue -> Live -> file outcome. Manual purchase details remain optional on Upload.

## 5. Component needs
Upload region: empty, drag-active, submitting, recoverable error/retry; keyboard file picker and no-JavaScript submit. Limits visible, no required business fields.

## 6. Edge cases
Reject invalid, empty, encrypted and oversized PDFs before creating records; retain client file selection on failure. Multiple files share an intake; hints retain per-file source and page. Unknown fields remain absent. Bounded text-only label extraction never substitutes for OCR/security checks. Narrow layouts wrap. No automatic retry after uncertain network outcome.

## 6b. Architecture & performance
Use existing templates and queue, no new dependency/cache layer. Extraction reads at most three text pages per file and bounded characters. No large frontend list or animation.

## 6c. Lifecycle
Existing server config; no new provider keys or permissions. Blocking offline error with explicit retry. Unit/API tests and tester-army PDF browser regression checks required.

## 6d. Security
No client trust or inferred identity. Detected document text never becomes public purchase metadata. Authorization, same-origin and PDF publication checks unchanged. Synthetic test records only.

## 6e. Store publishing
Web application; mobile store requirements inapplicable.

## 6f. Motion
No animation added; static drag and loading feedback.

## 7. Open questions
None blocking; metadata approval and scanned metadata extraction deferred explicitly.
