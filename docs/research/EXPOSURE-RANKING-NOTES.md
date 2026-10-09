# Argentina exposure comparison: evidence and counting limits

Reviewed **2026-10-09**. Reporting window: **2025-10-09–2026-10-09**. This bounded review does **not** establish which company exposed the most Argentine data. It found no independently verified company total suitable for such a ranking. It is an evidence comparison, not a national census, negligence finding or company security score.

The application data is in [exposure_data.py](../../gate/src/gate/exposure_data.py): **7 entries, 2 companies and 5 public bodies**. Only two entries have numeric quantities: a reported approximate file count and a disputed record claim. There is no verified-number leaderboard. Every unknown quantity remains `None`, never zero.

## What the sources support

| Entity | Evidence classification | Comparison quantity | Public source and date |
|---|---|---|---|
| Work Management / SudamericaData | Alleged collection | Unknown; do not add component claims | [Infobae](https://www.infobae.com/politica/2025/12/19/denuncian-una-masiva-filtracion-de-datos-personales-de-ciudadanos-argentinos-en-la-dark-web/), 2025-12-19; [AAIP inquiry](https://www.argentina.gob.ar/noticias/la-aaip-inicio-una-investigacion-de-oficio-ante-presunta-filtracion-masiva-de-datos), 2025-12-23 |
| Global Visum | Vulnerability and response acknowledged | Approximately 20,000 photographs, researcher-reported | [Cadena 3 municipal response](https://www.cadena3.com/noticia/sociedad/que-dijo-la-municipalidad-tras-el-hackeo-al-sistema-de-transporte_583247), 2026-08-13 |
| IOMA | Affiliation disclosure acknowledged | Unknown | [La Nación, including institutional response](https://www.lanacion.com.ar/sociedad/la-provincia-advirtio-un-hackeo-al-ioma-alerta-por-la-filtracion-de-padrones-de-afiliacion-y-nid31032026/), 2026-03-31 |
| SCBA | Limited repository disclosure confirmed | Unknown | [SCBA statement](https://www.scba.gov.ar/institucional/nota.asp?id=58623&veradjuntos=no), 2026-04-02, updated 2026-04-08 |
| PAMI | Public attachment disclosure confirmed | Unknown total; 40 sampled cases use a different unit | [Chequeado investigation](https://chequeado.com/investigaciones/pami-expone-datos-medicos-y-documentos-sensibles-de-sus-afiliados-en-su-sitio-web/), 2026-05-21 |
| Río Negro government | Extraction acknowledged | Unknown | [Provincial statement](https://rionegro.gov.ar/articulo/59894/el-gobierno-denuncio-filtracion-de-informacion-de-sus-sistemas-informaticos), 2026-06-24 |
| ANSES / SIPA | Disputed; institution denied a hack | 38 million **claimed records** | [Chequeado verification](https://chequeado.com/nota/que-se-sabe-sobre-el-supuesto-hackeo-a-la-anses-y-como-cuidar-tus-datos/), 2026-09-20 |

For Global Visum, acknowledgement does not independently verify the count or establish criminal mass exfiltration. For Work Management, AAIP's investigation establishes official inquiry activity, not a finding that the alleged collection, source attribution or volumes are correct. For IOMA, direct retrieval of the [official March 30 statement](https://www.ioma.gba.gob.ar/index.php/2026/03/30/alerta-por-la-filtracion-de-padrones-de-afiliacion-y-medidas-de-seguridad-adoptadas/) failed during this pass; the record cites the accessible newspaper report reproducing the response.

## Comparison rules for the product

1. Separate **companies** from **public bodies**, and disputed/alleged claims from acknowledged or confirmed disclosures. An evidence label describes the particular event claim, not every asserted number.
2. Compare numeric values only within the same unit **and** quantity-evidence category. Even then, affected-system scope, approximate values and sampling can prevent a meaningful ranking. Do not assign ordinal rank to a group of one.
3. `reported` means an attributed public-source estimate; `claimed` means an unverified allegation. Neither means independently verified. No entry in this snapshot has `quantity_status="verified"`.
4. Do not sum related datasets or convert records, photographs, sample cases, bytes and people into one total. No deduplicated national victim count was computed.
5. `report_date` is the source publication date. `incident_date` is unknown unless separately established; all seven currently preserve `None`. `date_note` retains approximate event timing without inventing a precise intrusion date.
6. `scope_argentina="known"` describes the geographic subject of the report or allegation. It does not authenticate the underlying claimed dataset.
7. Confirmation of past disclosure does not mean data is still accessible. This review did not revisit exposed services, test access or download records. Entries identify the associated institution without adjudicating responsibility or negligence.

## Search boundaries and exclusions

This pass used the existing incident/source ledgers, official statements and accessible original reporting, then bounded company-name searches including Nosis, Work Management/SudamericaData and Global Visum. It is not an exhaustive corporate incident search. No criminal forums, leaked collections or victim documents were consulted.

**Nosis is excluded:** this pass located no adequately corroborated in-window incident. Its [official business-data catalog](https://www.nosis.com/es) is a product description, not a leak announcement; advertised dataset sizes must not become incident counts. This search result does not prove that no incident occurred.

**Historical collections are excluded as new incidents:** old RENAPER and licensing datasets, later resale and recombination cannot establish fresh compromise dates. Broad mixed-sector offers are not additional company cases. Weak listing-only company leads were excluded rather than expanded into a speculative leaderboard.

Useful next evidence would be a dated institutional incident notice, regulator finding or independently documented count with explicit units, scope and deduplication method. Until then, the honest product presents named evidence and limits rather than a “worst companies” ranking.
