# Official public documents

Reviewed October 9, 2026. The guideline pack now cites nine official sources: the
four existing law/guidance sources, AAIP Resolutions 40/2018 and 47/2018, AAIP's
2025 responsible-AI guide, and CERT-Ar's 2024 and 2025 incident reports.

The five additions expand policy and incident context. They do not add an
enforcement rule. CERT statistics count recorded incidents, not leaked records,
confirmed leaks or unique victims. The AAIP resolutions provide recommendations;
their scope must not be presented as universal, institution-specific certification.

## What Senso receives

Senso receives the versioned, reviewed summaries and official citations in
`src/gate/rules.py`, not the full downloaded PDFs. The digest changes with this
expansion. Sync the new pack and refresh until it is ready. Retrieval remains
scoped to that exact pack; old proposal receipts remain tied to their old version.
Senso context can inform an inactive improvement proposal. The proposal still
needs tests and staff approval. Merely downloading or uploading more documents
does not train a model, change its weights or automatically activate rules.

## Download the unchanged originals

From the repository root:

```bash
gate/.venv/bin/python gate/scripts/fetch_public_documents.py --output output/pdf/public-documents
```

Add `--offline` to verify existing copies without downloading. The script checks
each official HTTPS URL, bounds download size, and verifies the pinned SHA-256,
byte length and page count in `fixtures/public-documents.json`. If a source changes,
review it before updating the pin. The original binary files are downloaded locally,
not bundled into Git. Official public-author names or contact details may appear;
these are public guidance/statistics, not leaked personal records.

| Original | Pages | Use |
|---|---:|---|
| [CERT-Ar 2024](https://www.argentina.gob.ar/sites/default/files/2025/07/informe_cert-ar_2024.pdf) | 14 | Real report for PDF intake and incident context. |
| [CERT-Ar 2025](https://www.argentina.gob.ar/sites/default/files/2026/09/informe_cert_2025.pdf) | 17 | Real report for PDF intake and incident context. |
| [AAIP archive-access toolkit](https://www.argentina.gob.ar/sites/default/files/aaip_caja_de_herramientas_archivos.pdf) | 49 | Longer document for intake; anonymization guidance for context. |
| [AAIP responsible-AI guide](https://www.argentina.gob.ar/sites/default/files/guia_ai-final-2025.pdf) | 62 | Knowledge reference; exceeds the current 50-page intake limit. |

The first three fit the current size/page limits. Their publication outcome is
not predetermined: these documents discuss sensitive concepts and contain graphics.
Analysis must distinguish examples and policy discussion from patient-linked data;
incomplete extraction or unavailable reviewers must not count as clearance. Use
the existing fictional fixtures to assert exact cleaning and publication behavior.

## Maintaining the collection

1. Select an official public source and read the relevant sections.
2. Record its purpose, date, locator and evidence unit. Keep statistics distinct
   from policy and allegations distinct from established facts.
3. Add a bounded authored summary/citation to the pack. For a downloadable PDF,
   record its URL, SHA-256, size and page count in the manifest.
4. Run guideline and publication-boundary tests; sync the new Senso digest and
   verify scoped retrieval separately from mocked tests.
5. Propose any behavioral change separately, with positive/benign controls and
   explicit approval of the tested candidate.

There is no recurring collection job or automatic rule promotion.

## Executed verification

October 9, 2026, local application and the configured Senso organization:

- All four original PDF downloads matched their pinned hashes, sizes and page
  counts. Covers and relevant content pages were rendered and visually inspected.
- The application's actual intake validator accepted the 14-, 17- and 49-page
  files. It rejected the unchanged 62-page guide with HTTP 400 and the existing
  50-page limit. This verifies intake, not a complete model review or publication.
- **343 backend tests passed**, including unchanged publication boundaries and
  checks that incident statistics are not new enforcement policies.
- **One Chromium Guidelines test passed** with tester-army/e2e, run
  `01a1233c-c4d0-71ae-854a-3d5ba206f738`. It opened the AAIP security and CERT-Ar
  2025 entries and checked their source locators.
- Real Senso ingestion initially reported processing. A later refresh and scoped
  retrieval succeeded with five passages from digest
  `5d531a08383a9f8b141a58bfc421480be14a2b8c55ff8f437b817bd0dba23cca`.
  Only the authored pack was sent, not the original PDFs. This receipt proves
  local provider integration, not deployment or an improvement in detection rate.
