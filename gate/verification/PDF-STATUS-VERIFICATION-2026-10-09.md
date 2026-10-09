# PDF result feedback verification — October 9, 2026

## Change

The unified workspace had stopped accepting page-wide PDF drops. It also displayed a provisional private decision while a clearance job was still running, and the document list did not refresh when the job finished.

The workspace accepts drops again. Activity shows Checking until completion and refreshes the document table when outcomes change. Purchase details show Processing, exclude running files from final summary counts and reload automatically when the authenticated status token changes. The status response contains only processing IDs, a boolean and an opaque revision hash. Publication authorization is unchanged.

## Executed locally

Backend and build checks used integrated main `c464289` plus this fix. Browser checks were repeated after incorporating the teammate home-page change `4620552`:

- 336 backend tests passed; five existing dependency deprecation warnings.
- 17 Chromium tests passed with tester-army/e2e. Run: `01a122ec-6499-7658-bbd1-47392bfd6036`.
- Frontend TypeScript and Vite production build passed.

Browser checks cover automatic file selection, restored workspace drop, invalid input, private metadata hints, activity completion and table refresh, all ten fictional PDF fixtures, and exact-byte publication of an inspected benign specification through both review entry points. The activity transition test intercepts responses to exercise running and completed states; the backend tests separately verify the real status endpoint, authentication, change token and queued/completed states.

The initial run exposed the missing drop handler and a stale approval-button test selector following the workspace merge. Failed traces were retained locally under `gate/e2e/.e2e/failed-status-before-fix/`. Final browser traces are under `gate/e2e/.e2e/results/`; both directories are gitignored.

These isolated checks use fictional records and disable external providers. They do not establish live sponsor execution, arbitrary PDF redaction coverage or deployment of this change. Prior provider evidence remains separate.
