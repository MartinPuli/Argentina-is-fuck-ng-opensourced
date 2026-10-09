# PDF verification — October 9, 2026

## Executed locally

The final browser run used integrated application `e0a03e9` plus the form-action fix. The backend suite passed at `5366e63` plus that fix; subsequent upstream changes only adjusted the home and public-page presentation.

- **11/11 actual Chromium tests passed**, using the requested [tester-army/e2e](https://github.com/tester-army/e2e) framework. [Run receipt and fixture hashes](e2e-2026-10-09.json).
- **9/9 isolated HTTP upload checks passed**, without provider mocks or external calls. [Results](offline-pdfs-2026-10-09.json).
- **270 backend tests passed**, with five dependency deprecation warnings. This suite includes mocked provider tests and is not evidence of live provider execution.

The browser suite covers all nine fictional fixtures: identity scans, disability certificate, medical justification, X-ray, purchase note, supplier quote and three equipment specifications. All remain private without completed model checks or explicit human approval. An inspected benign equipment specification publishes with its exact original bytes after approval in both Review and Live. Anonymous access to originals returns 401 in this authenticated local configuration.

## Defect found and repaired

Both approval forms contain buttons named `action`. In browsers those controls shadow the form's `action` property with a `RadioNodeList`. The JavaScript posted to `/[object%20RadioNodeList]` instead of `/review/{id}`, so publication failed even though a direct API call worked.

Both submit handlers now read the HTML action attribute. The browser suite reproduces the original failing button flow and verifies the resulting public download through each screen.

## Live execution evidence

Nine fictional PDFs were uploaded to `https://argensec.pujia.ar`, purchases 4 and 5, procedures `QA-PDF-20261009-1501` and `QA-PDF-20261009-1502`. [Partial provider receipts](live-pdf-partial-2026-10-09.json) preserve the captured processing steps. They are historical, incomplete evidence, not a passing nine-file run.

Before the shared workspace changed, the following were observed:

- AkashML text responses on the uploaded PDFs and vision responses on the three image PDFs.
- Guild orchestration and review sessions; the purchase note became a published cleaned copy. The medical justification, identity scan and disability certificate stayed private; the X-ray remained held for review. Two benign documents were public. The bed specification later became a cleaned copy; the prosthesis run was not confirmed complete.
- The downloaded cleaned purchase note differed from the original. Its fictional name, DNI and CUIL were absent from extracted text; wheelchair procurement content remained. The rendered PDF was visually inspected.
- The audit page displayed ClickHouse query timings and one million explicitly simulated history events. Those timings are application-reported evidence, not an independently authenticated provider audit.

At recheck, the shared site contained only nine earlier fixture records, purchases 1–3; the new purchases and queue receipts were absent. The cause is unconfirmed. A complete current remote run could not be certified. Intermittent HTTP 502 responses also occurred during polling.

The deployed fictional workspace has staff access open by configuration. The local 401 result must not be presented as proof that the deployed original-file route is authenticated.

## Integration status and remaining gaps

| Tool or feature | Evidence | Limit |
|---|---|---|
| AkashML | Live text and image processing steps | Not enabled in the isolated browser suite |
| Guild | Live sessions, orchestration and cleaned-note review | Complete nine-file provider run not retained |
| ClickHouse | Live audit query timings; simulated volume labeled | Independent provider-side audit not performed |
| Semgrep | Committed scan artifacts and prior remediation report | Not rerun in this session; CLI unavailable locally |
| Pi | New adapter contract integrated from teammates | Explicitly not connected; no Pi tenant/OAuth session |
| Senso | No implemented connection found | Not integrated |
| Learned rules | Rule workflow and tests implemented | Live receipts showed zero active rules |

The provided event brief calls for three or more sponsor tools. AkashML, Guild and ClickHouse have substantive application evidence; Semgrep has prior scan evidence. Pi and Senso must not be counted as connected. Submission still needs the accessible repository, shareable video, tool description and team contacts listed in [the event brief](../../docs/EVENT-BRIEF.md).

The cleaned note also removed a public UGL delivery-address fragment, despite the prompt saying to retain institutional addresses. This is an over-redaction issue: privacy checks passed, but full procurement usefulness was not preserved. Resolve it with a fixture regression and verified context before claiming clean output is always ready to publish. The current tests do not establish coverage of arbitrary PDFs, handwriting, hidden image text or every possible personal identifier, and do not establish protection against government-server intrusion.
