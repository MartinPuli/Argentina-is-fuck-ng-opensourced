# Argentina: public social-media leak leads

Evidence cutoff: **2026-10-09**. Research window: **2025-10-09–2026-10-09**. Compared with [the existing incident register](../INCIDENTS.md) and [source list](../SOURCES.md) before inclusion. These are additional research leads and explicit exclusions, not seven new breaches.

**Result: seven records; zero additional confirmed government data leaks.** Two government-related claim groups merit follow-up, two named nongovernment alerts lack corroboration, two alerts lack a resolved victim, and one official nongovernment account-security notice does not establish a data leak. The groups are research identifiers, not verified distinct intrusions. No unique-person total can be calculated.

## Government-related leads

<a id="asl-01"></a>
**ASL-01 — Skull1172 aggregate collection.** CiberSeguridadLatam's **September 1** article attributes a **May 6, 2026** advertisement to Skull1172, concerning alleged **2024–2026** collection from government/education domains: **over 80 million lines**, approximately **155,000 email threads**, **over 32 million images**, and **12 million additional records**. It cites an F6 report without a confirmed public report URL. Treat these as differently measured, potentially overlapping claims; fresh intrusion dates, victims and unique people remain unknown. [Report, “Qué pasó” and “Referencias”](https://ciberseguridadlatam.com/latam-fue-la-region-con-mas-filtraciones-de-datos-del-mundo-entre-2025-y-2026/).

A parliamentary bill's explanatory text also repeats a claim involving **over 900 domains**, without forensic substantiation. A bill is evidence of parliamentary discussion, not incident confirmation. [Bill, PDF page 18](https://rest.hcdn.gob.ar/web/tramites-parlamentarios/render/adjunto/6a1f1b46d2212.pdf). Keep one aggregate lead; do not add 900 breaches or combine this volume with Chronus or older RENAPER totals.

<a id="asl-02"></a>
**ASL-02 — CSJN.** BreachHistory's **July 10, 2026** entry attributes an alleged Supreme Court database offer to DailyDarkWeb reporting. No attested record count, field inventory or institutional confirmation accompanies it; extraction date is unknown. The original social post was not retrievable. Retain as an uncorroborated federal-court lead, separate from the confirmed provincial SCBA notice and the Jujuy allegation. [BreachHistory, opening and “What was alleged”](https://breachhistory.com/blog/argentina-supreme-court-csjn-forum-data-leak-claim-2026).

## Outside-government and unresolved alerts

| ID | Attributed post / public-notice date | Entity and evidence | Count decision |
|---|---|---|---|
| ASL-03 | August 15, 2026; extraction unknown | Undercode attributes a brief DailyDarkWeb listing to **Cabrales**, described as an Argentine company. No amount, stolen-data category or intrusion details. Article publication date is unstable. [Article, opening and “What the Original Report Says”](https://undercodenews.com/argentinas-cabrales-appears-on-the-dark-web-raising-fresh-concerns-over-corporate-cybersecurity-video/). | Nongovernment, uncorroborated alert; not a confirmed leak. |
| ASL-04 | August 22, 2026; extraction unknown | Undercode's public LinkedIn repost attributes a **Socialab Argentina** allegation to DailyDarkWeb. No quantities or confirmation in accessible text; linked article unavailable. Repost date not established. [Public repost](https://www.linkedin.com/posts/undercode-news_socialab-argentina-data-breach-raises-new-activity-7497020292503015424-sjte). | Nongovernment contextual lead; not a confirmed leak. |
| ASL-05 | September 29, 2026; extraction unknown | Indexed Undercode text quotes an incomplete hospital name, **Hospital Universitario Aus…**, and ambiguous “Subscribers” label. No count or established compromise. Another homepage headline expands the name, without sufficient accessible corroboration. [Indexed article](https://undercodenews.com/argentinas-hospital-universitario-aus-appears-in-a-dark-web-intelligence-alert-raising-questions-about-a-potential-data-exposure-video/); [publisher homepage](https://www.undercodenews.com/). | Unresolved entity. Do not automatically identify Hospital Austral or infer leaked patient/subscriber data. |
| ASL-06 | October 8, 2026; extraction unknown | Undercode attributes an Argentina alert to DailyDarkWeb but supplies no victim or quantity. Its Mi Argentina comparison does not establish a relationship. Exact article date unavailable. [Indexed article](https://undercodenews.com/argentina-faces-a-new-dark-web-warning-as-threat-actor-claim-raises-fresh-cybersecurity-questions-video/). | Unresolved entity; no new incident count and no unsupported merge with Mi Argentina. |
| ASL-07 | Official notice July 9, 2026; event date unspecified | **AFA** warned of potentially unauthorized messages from **one institutional account**, with possible unauthorized access still being investigated. It did not disclose a mass database leak. [Official notice, dated heading and paragraphs 1–4](https://www.afa.com.ar/empresas/posts/aviso-importante-sobre-correos-electronicos-enviados-desde-cuentas-de-afa). | Outside government; official security notice, not a confirmed data leak. |

## Access and deduplication limits

Five records above depend on third-party attribution to DailyDarkWeb. Its X profile and attempted original-link access failed; indexed search did not recover usable original post URLs. Original URLs are therefore null in the companion JSON. The public DailyDarkWeb website was accessible, but its available archive/search did not establish comprehensive coverage. This is a bounded search, not an exhaustive account export.

Undercode's articles/reposts and BreachHistory's summary do not provide independent forensic corroboration. Relative timestamps such as “seconds ago” were not converted into publication dates. Missing official confirmation means unresolved evidence, not proof that nothing happened. No breach markets, stolen databases, victim samples or credentials were accessed.

Existing SudamericaData, ANSES/SIPA and Mi Argentina reposts were matched back to the existing register rather than added. National Health (October 2025) and Air Force email (February 2026) remain existing weak leads; this pass did not establish enough corroboration to upgrade them. Government-related records found in a broker's collection do not by themselves prove intrusion into government systems.

For BREACHSTOP, preserve **source → claim → alleged entity → verified incident** as separate records. Store exact measurement units and dates, require an institutional or independently substantiated update before raising confirmation status, and leave partial names unresolved. Social alerts can prioritize authorized investigation; they cannot authorize account revocation, establish a patch target, or prove a root cause.
