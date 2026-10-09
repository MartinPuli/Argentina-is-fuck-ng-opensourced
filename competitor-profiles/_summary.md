# Comparable defenses: what exists and what we should build

**Later same-day addition:** [Pi Security assessment](../docs/research/PI-ASSESSMENT.md) documents close overlap with the proposed memory/repair loop and an optional public MCP integration. The six profiles below remain the original comparison set; Pi was researched separately at the user's request.

**Snapshot: October 9, 2026.** This targeted comparison found substantial prior art. It does not establish an empty market or a capability gap across every vendor.

| Organization | Main role in this comparison | Evidence |
|---|---|---|
| [Cloudflare / Accenture](cloudflare-accenture.md) | Block known malicious destinations | UK government identifies providers |
| [HackerOne](hackerone.md) | Find government-service vulnerabilities | Singapore government historical program |
| [Pentera](pentera.md) | Validate exposures and recheck remediation | Vendor product description and named historical customer |
| [SafeBreach](safebreach.md) | Simulate attacks and coordinate AI workflows | Vendor product descriptions |
| [Netskope](netskope.md) | Control sensitive data movement | Vendor product description |
| [Wazuh](wazuh.md) | Execute configured response actions | Official implementation documentation |

## Positioning

These products occupy different parts of the same defense process. Discovery, prevention, response, validation and recovery are related but not interchangeable. We did not run a common benchmark, so a numerical ranking or a “better than all competitors” claim would be invented.

The proposed BREACHSTOP positioning is **an open-source way to turn a documented failure into a reproducible test, a bounded repair and independently checked recovery for an enrolled public service**. That is a focused implementation and usability hypothesis. Neither AI orchestration nor retesting is new.

## Design decisions

1. Reuse mature access, logging and endpoint controls. Put engineering effort into a trustworthy connection between evidence, actions and outcomes.
2. Publish synthetic incident packages with sources, assumptions, expected permissions and legitimate-use tests.
3. Show actual record transmissions, failed access attempts and service interruptions. A risk score alone cannot demonstrate protection.
4. Prove the exact deployed revision. A passing sandbox does not establish that a different production artifact is fixed.
5. Keep public-sector deployment evidence separate from vendor marketing. A historical program is not a current nationwide contract.

The [country comparison](../docs/research/COUNTRY-PRECEDENTS.md), [sandbox assessment](../docs/research/SANDBOX-ARCHITECTURE.md) and [revised build proposal](../docs/research/WHAT-TO-BUILD.md) turn these findings into a concrete design.

## Research limits

This is a capability-focused scan of selected comparators, not an exhaustive landscape or a novelty search. No pricing, SEO, reviews or private customer contracts were evaluated. Source dates vary and are disclosed in the individual profiles. Raw retrievals are kept locally under the gitignored `raw/research/2026-10-09/scrapes/`; source text is not republished.
