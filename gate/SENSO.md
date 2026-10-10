# Guidelines, public reporting and Senso

## Server setup

Pull `main`, install the updated dependencies (`cd gate && uv sync`) and restart the existing application process. Set `SENSO_API_KEY` in the server's `gate/.env` or secret manager. `AKASHML_API_KEY` is required for custom rule generation. Optionally set `SENSO_FOLDER_ID` to an editor-accessible destination folder. Never put these keys in Git or browser code.

Open `/learning` as staff. Expand **Senso** and choose **Sync guidelines**. Refresh after processing completes. A configured key alone does not count as a connected, searchable library. A new server can reconcile an existing pack only if its remote body exactly matches the local reviewed pack in the same organization.

## Working flow

1. **Inspect guidelines:** `/guidelines` links to nine official sources: Laws 27.275, 25.326 and 26.529, AAIP's anonymization recommendations, Resolutions 40/2018 and 47/2018, the 2025 responsible-AI guide, and CERT-Ar's 2024/2025 reports. Each application policy names its sources; the added incident statistics are research context, not legal authority. These are reviewed operational summaries, not complete legal texts or a legal-compliance certification. See [official public documents](PUBLIC-DOCUMENTS.md) for the reproducible PDF collection and intake limits.
2. **Find public reports:** **Find recent reports** searches Google News RSS for Argentina disclosure/cyberattack headlines in the last 30 days. Up to 12 leads are retained for display. This is a bounded discovery sample, not an exhaustive incident census. Multiple reports may describe one event. Article bodies and leaked records are never fetched.
3. **Inspect and select a source:** **Use source** prefills an explicitly unverified headline lead. Read the report separately and replace/extend the sanitized summary with substantiated facts. Unknown mechanisms and quantities must remain unknown. Existing authored cases remain available offline.
4. **Propose with context:** select **Use cited Senso guideline context**. The server checks that the exact synced pack is still present, then requests passages scoped to its content ID. It rejects foreign IDs, missing version references and text that does not match the reviewed pack. AkashML receives the locally reviewed guidelines plus the quoted incident and Senso passages. Provider failure creates no candidate; it never silently pretends Senso was used.
5. **Review, test and activate:** proposals start inactive. Their exact content must pass positive and benign controls, then staff approves the tested digest. Senso and the model cannot activate rules. Active checks add HOLD/WITHHELD only and cannot release another check's restriction.
6. **Recheck PDFs:** existing approvals require the current learned-rule revision. Recheck restores eligible benign files and restricts matching files. The PDF public-download enforcement remains independent of Senso.
6b. **Decision citations:** after a HOLD/WITHHELD decision is stored, a background lookup asks Senso (`POST /org/search/context`, scoped to the synced pack) for the passage governing the cited rule ids. The purchase page shows "Policy source: Senso" with the passage; the live agent log shows "Senso · rule lookup" with latency. The result lives in its own `attachment_senso` table and can never change the decision or release a file. If Senso is unavailable the field says so and nothing else changes.
7. **Inspect evidence/export:** rule detail shows the saved Senso passages, content/version IDs and guideline digest used for that proposal. The ZIP's `evidence.json` includes this context snapshot. Skill and proposal exports preserve the bounded workflow, not permission to deploy it elsewhere.

The search runs when staff requests it; there is no recurring background monitor. Incident summaries are not automatically promoted to legal guidance, confirmed incidents or Senso knowledge-base records. Only the authored public guideline pack is uploaded to Senso. Uploaded PDFs, patient identities and credentials are excluded from this integration.

## Verification

See [the verification record](verification/SENSO-GUIDELINES-2026-10-09.md). The real Senso test covers authentication, ingestion and scoped retrieval. Mocked transport/model tests separately cover failures, candidate approval and actual PDF publication boundaries. Server deployment and live AkashML generation must be verified in the team's configured server environment.

To repeat a real provider check from the repository root:

```bash
gate/.venv/bin/python gate/scripts/verify_senso.py --output /tmp/senso-check.json
```

Reference contract: [Senso concepts](https://docs.senso.ai/docs/concepts), [public OpenAPI specification](https://docs.senso.ai/specs/sdk-api.yaml). API calls use the fixed HTTPS base `https://apiv2.senso.ai/api/v1`, a server-only `X-API-Key`, explicit content scoping, bounded responses, no redirects and redacted error messages.

## Semgrep

The official Guardian plugin was installed in the local Codex environment from `semgrep/guardian`. It needs a new Codex session and browser OAuth to enable its hosted tools. The recorded scan for this change used **Semgrep Community**, not Guardian OAuth. Do not count plugin installation as an executed Guardian scan.
