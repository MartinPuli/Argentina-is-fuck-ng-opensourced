# Other countries already use parts of this defense

**Evidence cutoff: October 9, 2026.** This is a comparison of documented programs and architectures, not a claim that any country has eliminated leaks. Historical deployments are labeled as historical. Product capabilities are not treated as measured national outcomes.

## Country precedents

| Country | What is documented | What we can take from it |
|---|---|---|
| United Kingdom | NCSC identifies Cloudflare and Accenture as providers of its protective DNS service. [NCSC](https://www.ncsc.gov.uk/information/pdns) | Put an enforceable control in the network path; a dashboard alone cannot stop traffic. |
| Singapore | CSA/GovTech appointed HackerOne for their 2019 government bug-bounty program. [Government release](https://www.csa.gov.sg/news-events/press-releases/second-government-bug-bounty-programme-expanded-to-cover-more-systems-and-digital-services/) | Give discoveries an authorized route to a responsible owner and verified repair. |
| Estonia and Finland | X-Road's official case-study site documents the September 2020 population-register connection. The article is dated January 8, 2021; national deployments have their own operators. [Case study](https://x-road.global/xroad-case-studies-library/2024/10/21/estonia-and-finland-launch-automated-data-exchange-between-population-registers) | Separate participating institutions and make the allowed exchange explicit. |
| Australia | ASD documents government use of protective DNS, including blocking known malicious destinations. This review did not establish a current commercial provider. [Government guidance](https://www.cyber.gov.au/publication/gateway-security-guidance-package-gateway-technology-guides) | Destination filtering is useful, but it covers only some ways data can leave. |
| Israel | Pentera's 2020 release names the Henrietta Szold public nonprofit research institute as a customer. This is vendor-reported institutional adoption, not nationwide government deployment. [Vendor release](https://pentera.io/press-release/israel-national-research-institute-henrietta-szold-selects-pcysys-to-automate-cyber-security-validation/) | Testing whether fixes work already has real institutional demand. |

These examples answer “has anyone done something comparable?” with **yes**. They do not establish that the full proposed BREACHSTOP system has already been deployed in those countries, or that our combination is unique.

## The most useful architectural precedent: Estonia

Estonia's RIA describes X-tee as its data-exchange layer, with authenticated participants, multiple authorization levels, signed/encrypted traffic and logging. X-Road is the underlying jointly developed technology. This is an exchange architecture, not an AI agent that repairs government servers. [RIA overview](https://www.ria.ee/en/state-information-system/data-exchange-platforms/data-exchange-layer-x-tee).

Its [security architecture](https://docs.x-road.global/Architecture/arc-sec_x_road_security_architecture.html) specifies controls over service requests and monitoring, with protected message records. RIA's historical introduction credits Cybernetica as one contributor; current X-Road governance should not be collapsed into a single company's product. [Historical account, written 2016](https://www.ria.ee/en/introduction-x-tee).

**Our engineering inference:** adopt the pattern of explicit institutional identities and independently enforced access. Keep private records inside their owning systems, and send only the minimum required result. Do not make BREACHSTOP a central copy of every agency's database. Signed logs help establish what was recorded; they do not prove every recorded action was legitimate.

There is also a practical availability lesson. RIA's June 2026 account describes timestamp-service certificate trust problems affecting some X-tee members and recommends an alternate timestamp service. That was a service incident, not a reported data leak. Security dependencies need failure and recovery tests as well. [RIA incident account](https://ria.ee/en/situation-cyberspace-june-2026).

## Why blocking destinations is not enough

Australia's guidance explicitly notes bypass limits for protective DNS: direct connections to IP addresses and name resolution through another resolver are outside that control. DNS filtering also does not decide whether an otherwise allowed recipient should receive a particular citizen record. [ASD gateway guidance](https://www.cyber.gov.au/publication/gateway-security-guidance-package-gateway-technology-guides).

For our design, there are three separate checks:

1. **Access:** may this authenticated service retrieve this record for this operation?
2. **Transfer:** may this result leave through this destination or publication route?
3. **Recovery:** after containment and repair, does the old route remain closed while legitimate work succeeds?

A compromise may still misuse data legitimately available to the affected application before it is detected. Reducing the amount and duration of that access limits exposure; it does not make the application immune.

## What is already competitive

[SafeBreach](../../competitor-profiles/safebreach.md) and [Pentera](../../competitor-profiles/pentera.md) already overlap with the simulation, investigation and revalidation idea. [Netskope](../../competitor-profiles/netskope.md) addresses monitored data movement. [Wazuh](../../competitor-profiles/wazuh.md) supplies configurable response mechanisms.

The proposed advantage to test is a **small, open and reproducible incident-to-repair workflow** for a clearly defined public service. Public source references, fictional test data, explicit permissions and a separately generated outcome report make its behavior inspectable. This is our proposed product direction, not evidence of superior performance or an unoccupied market.

## Recommendation for Argentina

Start with one willing institution and one owned application. Identify its data owner, operational owner, allowed callers, direct database routes, deployment authority and essential public workflow. Translate a supported historical failure mechanism into a synthetic test; do not invent a vulnerability from an unverified breach claim.

Keep the first demo focused on application compromise, credential revocation and recovery. Public-file checks are a separate module addressing another pattern in the report. National rollout, replacement of existing security tools and a full copy of government infrastructure are outside the hackathon.

See the [updated build design](WHAT-TO-BUILD.md), [sandbox comparison](SANDBOX-ARCHITECTURE.md) and [competitive summary](../../competitor-profiles/_summary.md).
