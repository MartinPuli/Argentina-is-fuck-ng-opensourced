# Guidelines and Senso verification — October 9, 2026

## Implemented

- Reviewed summaries and source/article locators for Laws 27.275, 25.326, 26.529 and AAIP anonymization recommendations, visible at `/guidelines` and used in text analysis and custom rule proposals.
- Explicit distinction between legislation/regulator guidance and application safeguards. Company CUIT recognition no longer claims blanket permission to publish company records.
- Server-only Senso authentication, ingestion, processing checks, exact-body duplicate reconciliation for a fresh server, scoped passage retrieval and immutable candidate-context receipts.
- Staff-initiated Google News discovery of recent public reporting, with unverified lead labels and a source-review step. No background schedule, article-body crawl, leaked-dataset ingestion or incident-confirmation claim.
- Existing test/approval/digest/recheck workflow and independent public-PDF enforcement retained.

## Real external evidence

Senso authenticated the supplied organization key, accepted the public guideline pack, completed processing and returned **five referenced passages**. A second run using a fresh temporary local database successfully reconciled the existing pack and retrieved five passages, exercising the server setup path. [Saved public-context response](SENSO-LIVE-2026-10-09.json).

Pack digest: `67744fa4f3bf1cf5bec6aed19577de59b4bfb6ff94fa9bad1e55fdb5c1adf52c`.

Google News RSS returned **12 leads** for the fixed Argentina/last-30-days query. These are headlines, not 12 confirmed leaks or 12 distinct incidents. No rules were activated by discovery.

Only the authored public guideline pack was uploaded to Senso. The stored response contains these public summaries and provider source/version references, not the credential or uploaded PDFs.

## Local verification

After integrating the team's latest `main` changes, the backend suite passes **323 tests**, including malformed/unavailable provider responses, authentication and same-origin controls, processing states, foreign scope/version rejection, changed remote text, duplicate recovery and transaction rollback. These include mocked transport/model results and must not be presented as live model-performance evidence.

The tester-army browser suite passes **12 tests**: all nine PDF fixtures stay private before review, both allowed human-publication paths preserve exact benign bytes, and the new official-guideline/context controls are accessible. Its first new-page run found an ambiguous test locator; it was corrected and the suite rerun. The browser server disables sponsor calls and uses a temporary authenticated database.

The HTTP/PDF integration test passes a cited Senso-context snapshot into the proposal, verifies inactive state and test-before-activation, then checks actual public HTTP access and benign-byte continuity after activation/recheck. Model and provider results in that test are constructed.

## Semgrep

The Community scan used the Python and security-audit rule packs. The initial scan flagged native XML parsing; the reader now uses `defusedxml`, rejects declarations and bounds input size. The final scan retains **15 template audit alerts** in [the scan artifact](../semgrep/senso-guidelines.json). This is not a zero-finding scan. They concern interpolated URLs, a fixed navigation HTML fragment and template script output; relevant existing controls include validated HTTP(S) source URLs, server-authored official links, `web_url` and JSON serialization. This change does not claim a complete application security audit.

The official Semgrep Guardian plugin was installed locally, but its new-session/browser-OAuth step has not been completed. The scan above is Community, not an authenticated Guardian scan.

## Not verified here

- Deployment/restart and Senso environment configuration on the team's server.
- Live AkashML generation on that server; the user reports its key is configured there, but the local checkout has no model key.
- Institution-specific legal approval, broad privacy accuracy, general prevention of server intrusions or leaked-credential misuse.
- Autonomous incident confirmation or automatic expansion beyond bounded phrase-group rules.

## Official references checked

- [Ley 27.275](https://www.argentina.gob.ar/normativa/nacional/ley-27275-265949/texto): dissociation, exceptions, partial disclosure and procurement transparency.
- [Ley 25.326](https://www.argentina.gob.ar/normativa/nacional/64790/actualizacion): personal data, sensitive health information, lawful processing and confidentiality.
- [Ley 26.529](https://www.argentina.gob.ar/normativa/nacional/160432/actualizacion): patient privacy/confidentiality and disclosure authorization.
- [AAIP toolkit](https://www.argentina.gob.ar/sites/default/files/aaip_caja_de_herramientas_archivos.pdf): PDF page 31 and Annex II, dissociation and reidentification.
- [Senso public API specification](https://docs.senso.ai/specs/sdk-api.yaml): authenticated organization, raw-content ingestion, content verification and scoped context retrieval schemas.
