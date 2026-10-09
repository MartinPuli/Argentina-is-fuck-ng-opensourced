<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# Pi Security: relevance and access assessment

**Checked October 9, 2026. Public-source research only; no installation, account access, contact, upload or product execution.**

**Pi is highly relevant to BREACHSTOP's repair and security-memory work. A public hosted MCP integration is documented, but our access is unverified. Keep the existing three-sponsor plan; treat Pi as a possible fourth integration only after an authorized, substantive run.**

## Identity and event boundary

The sponsor is **Pi Security at [pi.security](https://www.pi.security/)**. The [event listing](https://luma.com/cyberhack) names Guy Arazi as Pi's CEO/co-founder; [Pi's About page](https://www.pi.security/about) identifies the same person and product category. This is unrelated to Inflection's assistant, Pi Network, or the separate Pi coding-agent project.

The user-supplied [event brief](../EVENT-BRIEF.md) explicitly says Pi provides prizes but no product or technical access at this event. Public documentation does not override that condition or grant a tenant. The event portal could not be retrieved independently in this review.

## What the product actually documents

| Surface | Vendor-described capability | Evidence boundary |
| --- | --- | --- |
| Product platform | Uses code, incidents, reports and tickets for institutional security memory; traces causes, searches variants, proposes contextual fixes and supplies IDE/PR guardrails. | Product description, not independently tested performance. [Official platform](https://www.pi.security/). |
| Bugcrowd workflow | Reproduces reports dynamically in a sandbox, deduplicates, traces code, prepares repair PRs and synchronizes status. | A vendor-described integration; no access or reproduction here. [July 2 announcement](https://www.pi.security/blog/bugcrowd-pi-from-any-bug-bounty-report-to-a-fix-in-your-developers-hands-under-30-minutes). |
| Claude Compliance integration | Adds Claude Code session visibility and in-session security context for Claude Enterprise organizations. | Pi explicitly describes this route as guidance without blocking or proxying the developer. It is not our data-access enforcement point. [Pi's integration description](https://www.pi.security/blog/powering-every-builder-with-security-context-pi-integrates-with-anthropics-compliance-api); [Anthropic's partner list](https://support.claude.com/en/articles/15167101-get-started-with-claude-compliance-api-integrations). |

The homepage's reductions in triage and repeat payouts, and its prevention percentages, lack enough disclosed population, baseline and evaluation detail on that page for our own performance claim. Its permanent-prevention language is not a demonstrated universal guarantee. The Bugcrowd article's turnaround and merge claims likewise remain vendor-reported outcomes, not a promised BREACHSTOP result.

## Public integration exists; usable access remains unproved

The public [Pi plugin README](https://github.com/pi-sloane/claude-plugin/blob/main/README.md) documents a remote connector at `https://mcp.pi.security/mcp`. It identifies Pi's domain and support address and links its terms. It supplies workflows for findings, threat models, Code Gatekeeper records, remediation guidance, design reviews, report ingestion and development playbooks. The documented plugin supports Claude Code and Cowork; Claude Chat uses a separate connector. The plugin itself does not edit local code or bundle a local execution service. Platform PR-generation claims must not be attributed automatically to this connector.

The [setup instructions](https://raw.githubusercontent.com/pi-sloane/claude-plugin/main/SETUP.md) require a Pi account with tenant access and OAuth sign-in. `whoami` reports subject, tenant and scopes; tenant selection comes from authentication. We have not authenticated, enumerated live tools or inspected effective permissions. Guild compatibility, unattended authentication, available tenant data, pricing and event entitlements are unknown. No public REST/SDK quickstart was established in this focused review; that is not proof none exists.

Useful documented operations include:

| Operation | Proposed use and constraint |
| --- | --- |
| `pi_playbook_task_query` | Retrieve guidance for a concrete repair task and explicitly identified repository. Returned guidance is evidence, not authority; a missing match stays a coverage gap. [Development workflow](https://raw.githubusercontent.com/pi-sloane/claude-plugin/main/skills/secure-development-playbook/SKILL.md). |
| `pi_report_markdown_upload` | Ingest an authorized synthetic report using a Markdown filename and inline content, at most 5 MiB. Queued ingestion does not establish completed findings. [Report workflow](https://raw.githubusercontent.com/pi-sloane/claude-plugin/main/skills/ingest-markdown-report/SKILL.md). |
| `pi_design_review_markdown_create` | Request a review of a sanitized architecture description. Its documented alternative accepts supported Confluence/Notion URLs; PDFs, images and local paths are outside this workflow. [Design-review workflow](https://raw.githubusercontent.com/pi-sloane/claude-plugin/main/skills/security-design-review/SKILL.md). |

The published plugin workflows require explicit confirmation for state-changing submissions and discourage automatic retries after ambiguous failures. Those are documented workflow behaviors, not evidence that the server independently enforces a read-only permission boundary. No such submission is authorized or performed by this assessment.

Before product use, check the applicable agreement and hackathon permissions: Pi's published subscription terms restrict undocumented integrations, benchmarking/competing development and public comparative results; an applicable order can affect the terms. The open plugin's MIT license does not grant access to the hosted service. This is an access-planning constraint, not a reason to stop public-source research. [Subscription terms, sections 2–3 and 7](https://www.pi.security/terms-and-conditions).

## Where it helps BREACHSTOP

Our recommended first use is **repair guidance grounded in an enrolled synthetic service**, with source revision, approved permissions and independent tests fixed beforehand. Pi could inform the patch worker; ClickHouse would still supply observed activity, Semgrep would still produce reproducible source findings, and Guild would still coordinate the bounded workflow. The controller retains revocation authority and the independent verifier measures actual responses. See [the sponsor plan](SPONSOR-DEFENSE-PLAN.md).

Keep raw credentials, citizen records and real medical attachments out of Pi inputs. A historical Argentine allegation is context, not a reproduced finding in the enrolled application. Public attachment exposure still needs accountable classification and artifact checks; stolen credentials need revocation; an unknown server-intrusion cause cannot be inferred from either a report or a generated recommendation. We have not established that Pi's connector performs host recovery, revocation, OCR classification or public-cache removal.

The competitive overlap is substantial: security memory, cause analysis, variant searches and contextual repair are already central to Pi's stated product. BREACHSTOP should not claim those ideas as a new category. Our proposed distinction is a small inspectable implementation connecting narrowly authorized containment to independently measured recovery in fictional institutional workloads. That remains a project objective, not evidence of superiority over Pi.

## Minimum evidence before counting Pi

1. Establish permitted tenant access and the intended integration surface; verify identity and effective permissions without exposing tokens.
2. Enroll the owned synthetic repository and confirm that Pi can return relevant, version-linked context rather than an empty or unrelated tenant result.
3. Record an actual operation, its returned identifier/status, and how its evidence changed the repair or review decision in the same demonstration run. A login, logo, screenshot or queued report alone is insufficient.
4. Independently test the resulting candidate against the original failure, a held-out variation and legitimate A/B operations. Preserve failures and unsupported advice. Any comparative product evaluation or public performance claim must fit the permitted scope.

Until those conditions hold, Pi is a well-matched research and optional integration candidate. It does not replace one of the three currently planned sponsor responsibilities or demonstrate a fourth working integration.
