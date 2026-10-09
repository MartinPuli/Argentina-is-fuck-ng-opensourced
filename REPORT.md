# Argentina’s government data leaks

## What happened, why it keeps happening, and who bears the consequences

**Research period:** October 9, 2025–October 9, 2026  
**Prepared:** October 9, 2026  
**Audience:** Readers without a cybersecurity background or prior knowledge of Argentine institutions.

## Executive findings

Argentina has a serious, recurring problem protecting personal information held by public institutions and organizations connected to them. The evidence points to several different failures: criminals gaining access through accounts, possible misuse by employees, sensitive documents being published openly, and records circulating through intermediaries long after their original disclosure.

The clearest established harms are loss of medical privacy and criminal exploitation of traded records. Federal investigators connect the latter to fraud, extortion and threats. [Federal Police, May 27, 2026](https://www.argentina.gob.ar/noticias/el-dfi-de-la-pfa-desarticulo-una-importante-banda-de-hackers); [PAMI investigation, May 21, 2026](https://chequeado.com/investigaciones/pami-expone-datos-medicos-y-documentos-sensibles-de-sus-afiliados-en-su-sitio-web/).

Three qualifications are essential:

- **A headline about millions of records is not proof that millions of different people were newly hacked.** Records may overlap, concern earlier years, or come from a private copy rather than the named agency’s live system.
- **The most prominent claims are not always the best-established incidents.** Recent ANSES and Mi Argentina allegations have substantially weaker confirmation than the narrower PAMI, IOMA, judicial-personnel and Río Negro cases described below.
- **There is no defensible total economic-loss figure in the evidence reviewed.** Nor does this evidence establish that Argentina has more government leaks than every comparable country.

My assessment is that the most persistent danger is the combination of enduring personal information and repeated opportunities to misuse it. A password can be replaced; a person cannot replace their life history. Stopping an intrusion or taking down a webpage does not retrieve copies already made.

## 1. Scope and how to read this report

I interpreted “front-page leaks” as incidents receiving substantive national or provincial news coverage, supplemented by official notices and investigations. This is a review of the major publicly discoverable cases, **not a verified archive of every newspaper front page or an exhaustive census of all incidents**.

Research covered national reporting, including Chequeado, Infobae, La Nación and C5N; relevant provincial outlets; and statements from government agencies, courts, prosecutors, police, the privacy regulator and the national incident-response team. Searches used Spanish terms for leaks, hacks, stolen databases and ransomware, with dates and institution names. Official acknowledgements were checked against reporting where possible. No leaked databases were obtained or searched, and no private individuals’ information is reproduced.

The chronology uses **public disclosure or response dates**, unless an intrusion date is actually established. These can be months or years apart. An arrest in May does not establish that the underlying records were stolen in May.

Evidence labels mean:

- **Confirmed disclosure:** an institution acknowledged information escaping its intended control, or direct reporting documented public exposure with an institutional response. This does not validate every claimed field or victim count.
- **Incident acknowledged:** an attack or system impact is acknowledged, but information theft remains unestablished or incompletely described.
- **Alleged/disputed:** a public claim exists, but independent verification is missing, the institution disputes it, or both.
- **Enforcement development:** police or courts report investigating an information market. Findings remain allegations unless established through a final judgment.

## 2. The Argentine context in ordinary language

Argentina has national, provincial and municipal governments. Their computer systems are not one unified database. An incident in a provincial court does not automatically mean the national judiciary or every provincial agency was breached.

| Name you will encounter | What it means |
|---|---|
| **DNI** | The national identity document and its identifying number, used extensively in everyday administration. A document copy contains more information than the number alone. |
| **CUIT / CUIL** | Identification numbers used for tax or employment/social-security administration. They can help link information about the same person across records. |
| **RENAPER** | The national civil-identification registry responsible for identity documents. |
| **ANSES / SIPA** | ANSES administers social-security benefits; SIPA is the national pension system referred to in the September allegation. |
| **ARCA / former AFIP** | The national tax and customs administration. Older records and reporting may still use the AFIP name. |
| **PAMI** | A public health-coverage institution serving mainly retirees and pensioners. |
| **IOMA / OSEP** | Provincial health-coverage institutions: IOMA in Buenos Aires province and OSEP in Mendoza. An *obra social* is a health-coverage organization, not necessarily a hospital. |
| **Mi Argentina** | The government’s app and portal for digital documents and services. |
| **DNRPA / SISA** | The vehicle-registration system and an integrated health-information system, respectively. |
| **SCBA** | The Supreme Court of **Buenos Aires province**, distinct from Argentina’s national Supreme Court. |
| **AAIP / CERT.ar** | The privacy regulator, and the national team that receives and coordinates responses to computer-security incidents. Their functions differ. |

For the technical language, a **database** is an organized collection of records. A **record** is an entry, not necessarily a unique person. **Credentials** are the secrets or account details used to obtain access. **Phishing** means impersonating someone trustworthy to trick a person into revealing information or granting access. **Ransomware** is malicious software used to lock systems or data, often alongside a demand for payment; its presence does not by itself prove that information was published.

## 3. Major cases and developments during the period

The rows below are **not additive breach counts**: some are parts of the same campaign, some are disputed, and some concern enforcement against earlier theft.

| Public date | Institution or episode | What the evidence supports |
|---|---|---|
| **October 16, 2025** | “Dictadores” / “Sherlock” investigation | **Enforcement development.** Federal Police described stolen account details, access to government and private databases, and automated tools selling personal information. The investigation began in March 2025, before this report’s window. This announcement is not evidence of a single fresh October leak. [Official announcement](https://www.argentina.gob.ar/noticias/el-dfi-de-la-pfa-desmantelo-una-organizacion-cybercriminal-que-hackeaba-y-filtraba-datos-de). |
| **December 18–23, 2025** | WorkManagement / SudamericaData | **Alleged mass exposure at a private information broker.** Reporting described a claimed approximately one-terabyte collection containing tax, employment, vehicle and telecom records. Government sources denied a direct compromise of official systems. AAIP opened an inquiry on December 19; the original extraction date and unique affected population were not established. [Infobae](https://www.infobae.com/politica/2025/12/19/denuncian-una-masiva-filtracion-de-datos-personales-de-ciudadanos-argentinos-en-la-dark-web/); [AAIP](https://www.argentina.gob.ar/noticias/la-aaip-inicio-una-investigacion-de-oficio-ante-presunta-filtracion-masiva-de-datos). |
| **March 5, 2026** | IBR-CONICET, Rosario | **Alleged attack and threatened publication.** C5N reported an extortion claim against a public research institute. The institute said its technical staff were examining a presumed incident. A completed leak, affected-person count and inventory of stolen research were not established. March 6 was the reported threat deadline, not the first news report. [C5N](https://www.c5n.com/tecnologia/ciberataque-al-conicet-una-agrupacion-criminal-amenaza-filtrar-datos-n231386). |
| **March 27–31, 2026** | “Chronus Team” claims across public bodies | **Umbrella allegation under investigation.** Claims involving roughly 28–30 organizations circulated. Prosecutors investigated, but this did not validate every named agency or establish that all records came from new intrusions. The national Health Ministry denied a recent leak to Chequeado. Treat the following institution-specific responses separately. [Salta prosecutor](https://www.fiscalespenalesalta.gob.ar/ciberdelincuencia-se-investiga-el-accionar-en-argentina-de-una-banda-internacional-de-hackivistas/); [Chequeado](https://chequeado.com/el-explicador/que-se-sabe-sobre-el-hackeo-a-ioma-y-otros-organismos-publicos-y-como-cuidar-tus-datos/). |
| **March 30, 2026** | IOMA, Buenos Aires province | **Affiliation-roll disclosure acknowledged.** IOMA reported an attack affecting membership lists, while saying sensitive information and normal operations were unaffected. Membership details remain personal information: the agency’s wording does not imply zero privacy harm. The attacker’s million-scale count was unverified. IOMA announced legal action and warned about impersonation attempts. [La Nación, quoting IOMA’s announcement](https://www.lanacion.com.ar/sociedad/la-provincia-advirtio-un-hackeo-al-ioma-alerta-por-la-filtracion-de-padrones-de-afiliacion-y-nid31032026/). |
| **March 30, 2026** | OSEP, Mendoza | **Disputed allegation.** OSEP said it had found no evidence of unauthorized access at that point and described preventive measures. The advertised volume and alleged disclosure remain unverified in the sources located. [El Sol, reporting OSEP’s statement](https://www.elsol.com.ar/mendoza/que-dijo-osep-sobre-el-supuesto-hackeo-a-sus-sistemas-y-la-amenaza-de-filtracion-de-datos/). |
| **March 31, 2026** | Salta Police | **Incident acknowledged.** The provincial Security Ministry said police information-storage servers were affected and a complaint was filed, while normal systems continued operating. This does not confirm every record type or figure in the broader criminal claim. [El Tribuno, quoting the ministry](https://www.eltribuno.com/salta/2026-3-31-14-51-0-grave-ciberataque-masivo-el-ministerio-de-seguridad-salud-y-la-policia-de-salta-fueron-hackeados). |
| **April 2; updated April 8, 2026** | SCBA judiciary personnel | **Limited disclosure confirmed.** The court acknowledged a repository concerning judicial personnel. It said passwords, sensitive/accounting information, digital-identity access and case-management, remote-work and digital-signature systems were not compromised. No complete field inventory or verified affected-person count was published. [Court’s original notice and update](https://www.scba.gov.ar/institucional/nota.asp?id=58623&veradjuntos=no). |
| **May 21–June 4, 2026** | PAMI purchasing website | **Exposure independently documented and acknowledged.** Medical histories, diagnoses, disability certificates and identity-document copies appeared in public purchasing files. Chequeado found at least 40 cases in a sample of January–February procedures; that is not a national victim count. On June 4 it verified removal of access to the sensitive attachments. [Initial investigation](https://chequeado.com/investigaciones/pami-expone-datos-medicos-y-documentos-sensibles-de-sus-afiliados-en-su-sitio-web/); [removal verified](https://chequeado.com/investigaciones/finalmente-pami-dejo-de-mostrar-en-su-web-la-informacion-privada-de-sus-afiliados/). |
| **May 27, 2026** | Resale of government-linked records | **Enforcement development.** Federal Police reported investigating sellers of identity, vehicle and medical records, and credentials for Mi Argentina and PAMI. The inquiry began in October 2025. This establishes an investigated criminal distribution network, not fresh simultaneous breaches of every agency named. [Official announcement](https://www.argentina.gob.ar/noticias/el-dfi-de-la-pfa-desarticulo-una-importante-banda-de-hackers). |
| **June 7–8, 2026** | Catamarca provincial systems | **Allegation being checked.** A provincial communiqué said the incident-response team was investigating, with authenticity not yet established. Legislators requested details of systems, records and measures taken. Those unanswered questions are not evidence that all the proposed harms occurred. [Communiqué reported by Radio Valle Viejo](https://radiovalleviejo.com/la-secretaria-de-modernizacion-de-catamarca-informo-sobre-presunta-filtracion-de-datos/); [El Ancasti](https://www.elancasti.com.ar/politica-y-economia/fadel-presento-un-proyecto-que-el-ejecutivo-informe-la-presunta-filtracion-datos-n614364/amp). |
| **June 24, 2026** | Río Negro executive-branch payroll information | **Disclosure acknowledged; suspected employee misuse.** The province said officials’ payslip information had been extracted and possible unauthorized access by an employee was under investigation. A computer was secured for judicial examination. This is not a confirmed mass leak of the province’s entire population. [Provincial government](https://rionegro.gov.ar/articulo/59894/el-gobierno-denuncio-filtracion-de-informacion-de-sus-sistemas-informaticos). |
| **September 14–20, 2026** | ANSES / SIPA | **Unverified and denied by ANSES.** A seller claimed 38 million records concerning approximately 9.5 million people. Chequeado found no independent public confirmation and obtained an agency denial. Neither number should be presented as established; accompanying WhatsApp warnings do not prove that this allegation caused those scams. [Chequeado](https://chequeado.com/nota/que-se-sabe-sobre-el-supuesto-hackeo-a-la-anses-y-como-cuidar-tus-datos/). |
| **Late September–October 3, 2026** | Mi Argentina | **Conflicting, insufficiently corroborated reporting.** Reports described a possible six-million-record exposure under investigation. An October 3 commentary instead described a much smaller, largely recycled collection, without a linked forensic report substantiating that conclusion. Neither the mass-breach claim nor a definitive debunking is established by these sources. [September 30 report](https://www.datatrendslatam.com/argentina-investiga-posible-filtracion-de-6-millones-de-datos-de-mi-argentina); [October 3 commentary](https://empre.ar/analisis/se-vienen-seis-meses-caoticos-para-la-ciberseguridad-gubernamental/). |

### A related incident that should not be counted as a confirmed confidential-data leak

**Chaco Legislature, November 10–25, 2025:** ransomware disrupted the website, legislative tracking and legal-reference systems. Later reporting of the forensic presentation said the affected information was public rather than confidential. Administrative deadlines were suspended, and a legislator subsequently described difficulties retrieving documents electronically. This is evidence of disruption to government work, even though a leak of private citizen records was not established. [Initial notice reported by Diario Norte](https://www.diarionorte.com/318976-la-legislatura-informa-sobre-un-incidente-de-seguridad-informatica); [forensic presentation](https://www.diariolavozdelchaco.com/2025/11/18/la-legislatura-recibio-informes-periciales-de-ecom-sobre-el-incidente-de-ciberseguridad/); [November 25 follow-up](https://chacodiapordia.com/slimel-sobre-las-nuevas-autoridades-de-camara-queremos-que-respeten-los-lugares-que-le-corresponden-a-la-oposicion/).

### Older cases and weak leads kept out of the confirmed list

The original RENAPER episode in **2021**, the driving-licence investigation in **April 2024**, and the **December 2024** government-website defacement are outside the window. Republishing or reselling their contents does not create a new intrusion date. Defacement means changing a website’s visible content; it does not automatically establish theft of its users’ records. [RENAPER statement](https://www.argentina.gob.ar/noticias/el-renaper-detecto-el-uso-indebido-de-una-clave-otorgada-un-organismo-publico-y-formalizo); [driving-licence investigation](https://www.fiscales.gob.ar/ciberdelincuencia/la-ufeci-abrio-una-investigacion-preliminar-por-la-sustraccion-de-datos-de-licencias-de-conducir/); [December 2024 reporting](https://www.minutouno.com/politica/hackearon-el-portal-argentinagobar-fuck-milei-n6096676).

A September 2026 Jujuy judiciary ransomware listing was marked **claimed** by the monitoring source; I found no institutional confirmation. Other leads concerning national Health in October 2025 and Air Force email in February 2026 did not yield enough accessible corroboration to classify them as confirmed leaks. They are research gaps, not proven non-events. [Jujuy monitoring entry](https://socradar.io/free-tools/ransomware-intelligence/victims/judicial-branch-of-the-province-of-jujuy-emperador-cf6caefe).

## 4. Which parts of government appear most often?

**There is no sufficiently complete public dataset here to rank ministries by actual leak frequency.** A reliable ranking would require consistent reporting, verified distinct incidents and knowledge of how many systems each institution operates.

Within the cases reviewed, three groups recur:

1. **Health, benefits and personal identity.** PAMI and IOMA provide confirmed examples; identity and health records also appear in the police-described resale market. ANSES, OSEP and Mi Argentina attract prominent allegations, but their disputed cases cannot be added to the confirmed group.
2. **Provincial administration, courts and police.** SCBA, Río Negro and Salta show that exposure is not confined to national ministries. Their data, responsibilities and levels of confirmation differ.
3. **Tax, employment and vehicle information held by intermediaries.** These feature in the broker allegation and resale investigations. A database containing an agency’s name does not identify the point at which the information escaped.

This is a **qualitative pattern in the reviewed coverage**, not a statistical league table. It also reflects what attracts headlines: population-wide identifiers generate different coverage from a small employee-file exposure.

For context, CERT.ar recorded **520 security incidents in calendar 2025**, compared with **438 in 2024**. Its “Estado” category accounted for **254** in 2025, versus **267** in 2024. Of the 2025 government incidents, **108 concerned compromised accounts**. These are reported or detected security incidents, not all national leaks or victim counts; calendar years also differ from this report’s window. The roughly 19% increase applies to the overall recorded total, **not government data leaks**. [CERT.ar 2025 report](https://www.argentina.gob.ar/sites/default/files/2026/09/informe_cert_2025.pdf); [2024 report](https://www.argentina.gob.ar/sites/default/files/2025/07/informe_cert-ar_2024.pdf).

**Source-quality note:** the 2025 report’s comparison incorrectly assigns a 2024 phishing percentage to government that the 2024 table assigns to finance. This report uses the underlying counts rather than repeating that comparison.

## 5. Where the leaks come from—and why the problem persists

### A. Access through real accounts

Police described stolen passwords and deceptive messages in the October investigation. That does not establish the entry method for every agency named elsewhere. [Federal Police, October 16](https://www.argentina.gob.ar/noticias/el-dfi-de-la-pfa-desmantelo-una-organizacion-cybercriminal-que-hackeaba-y-filtraba-datos-de).

The practical problem is straightforward: a system can recognize an account without knowing whether the legitimate owner is using it. Strong sign-in checks reduce that risk; limiting what each account can retrieve reduces the damage when those checks fail. **Authentication** means checking who is entering; **authorization** means deciding what they may do after entering. They solve different problems. [NIST digital-authentication guidance](https://pages.nist.gov/800-63-4/sp800-63b.html).

### B. Possible misuse from inside an institution

Río Negro’s explanation points to suspected employee access to reserved documentation. It remains an allegation about responsibility, but illustrates why protection cannot focus exclusively on outsiders. Systems need rules and records of employee access as well. [Río Negro government](https://rionegro.gov.ar/articulo/59894/el-gobierno-denuncio-filtracion-de-informacion-de-sus-sistemas-informaticos).

### C. Administrative publication without adequate safeguards

PAMI’s local offices uploaded procurement files independently, exposing private supporting documents. This was a failure to separate confidential material from information suitable for public release. [PAMI investigation](https://chequeado.com/investigaciones/pami-expone-datos-medicos-y-documentos-sensibles-de-sus-afiliados-en-su-sitio-web/).

A later check found that exposure continued after the initial report. That shows why announcing an investigation and reliably changing the workflow are different achievements. [May 29 follow-up](https://chequeado.com/investigaciones/a-una-semana-de-la-revelacion-de-chequeado-el-pami-continua-mostrando-en-su-web-datos-privados-de-sus-afiliados/comment-page-1/).

### D. Copies outside the original agency

The broker allegation raises a question that a denial of direct government intrusion does not answer: **where did the intermediary’s information come from, and under what conditions was it stored or shared?** The lawful or unlawful origin of every part of the alleged collection remains unresolved. Vía Libre specifically sought explanations about these relationships. [Vía Libre’s request](https://www.vialibre.org.ar/la-fundacion-via-libre-pide-explicaciones-a-las-autoridades-sobre-la-filtracion-masiva-de-datos-de-la-ciudadania-argentina/).

My inference is that security must follow the information through its copies and recipients. Protecting the original database cannot protect an exported file automatically. This is often called **third-party risk**: dependence on the security of another organization holding or accessing your information.

### E. Reusable information creates a continuing criminal market

The police operations describe sellers and automated lookup tools, showing how information can become a repeatable commercial product. [October operation](https://www.argentina.gob.ar/noticias/el-dfi-de-la-pfa-desmantelo-una-organizacion-cybercriminal-que-hackeaba-y-filtraba-datos-de); [May operation](https://www.argentina.gob.ar/noticias/el-dfi-de-la-pfa-desarticulo-una-importante-banda-de-hackers).

The broader implication is that names, identity numbers, family relationships and medical histories can remain useful long after disclosure. Combining collections can also make a profile more revealing than any individual file. Publication is therefore not necessarily the final stage of harm.

### F. Incomplete disclosure makes accountability and measurement difficult

Many public statements do not establish the intrusion date, exact fields, number of distinct people or final cause. AAIP’s December notice said it had learned of the alleged mass disclosure publicly and had not yet received formal notification. That creates uncertainty for both affected people and researchers. It does not prove that every institution concealed incidents. [AAIP notice](https://www.argentina.gob.ar/noticias/la-aaip-inicio-una-investigacion-de-oficio-ante-presunta-filtracion-masiva-de-datos).

Argentina already has a privacy law: **Law 25,326**, enacted in 2000. It requires security, confidentiality and proportionate collection of information; health information receives specific protection. A lack of rules is therefore not the whole explanation. [Current consolidated law, articles 4 and 7–10](https://www.argentina.gob.ar/normativa/nacional/64790/actualizacion).

The AAIP said a proposed modernization bill, including a general 72-hour notification requirement, lost parliamentary status in 2025. That proposal must not be described as enacted law. Separately, the national public-sector cybersecurity framework requires covered organizations to report incidents to the cyber authority within **48 hours of learning of their occurrence or potential occurrence**. Those confidential reports are different from notifying affected individuals or publishing findings. [AAIP](https://www.argentina.gob.ar/noticias/la-aaip-inicio-una-investigacion-de-oficio-ante-presunta-filtracion-masiva-de-datos); [Disposición 3/2023, annex section 5](https://www.argentina.gob.ar/normativa/386227_disp3_pdf/archivo).

### What the evidence does not establish

Old software, delayed updates, too few security staff, excessive account permissions and poor monitoring are plausible contributors. Public evidence does **not** identify them as the cause of every case above. Nor does it justify a single explanation based on Argentine culture, corruption, one political party or recent budget cuts.

Likewise, group nicknames and foreign-hosted websites do not establish an attacker’s nationality or prove foreign-government involvement. Investigations show both local participants and cross-border connections; the location of a sale is not necessarily the location of the original theft.

The best-supported diagnosis is **inconsistent protection throughout the information’s lifetime**: collection, staff access, sharing, publication, storage and eventual deletion. It is a combination of technical and organizational failures, rather than one universal vulnerability.

## 6. The worst consequences for people

### Documented: loss of privacy, fraud, extortion and threats

The PAMI disclosures made private health information accessible outside its intended purpose. That loss of confidentiality is harm in itself, even where nobody proves a subsequent financial scam. The May police announcement separately links traded information to fraud, extortion and threats, without giving a reliable victim total or monetary loss. These are investigative findings, not final judgments against every suspect. [PAMI investigation](https://chequeado.com/investigaciones/pami-expone-datos-medicos-y-documentos-sensibles-de-sus-afiliados-en-su-sitio-web/); [Federal Police](https://www.argentina.gob.ar/noticias/el-dfi-de-la-pfa-desarticulo-una-importante-banda-de-hackers).

### Severe plausible outcomes—not established for every listed case

| Risk | What it could mean for a person |
|---|---|
| **More convincing scams** | A caller who knows your employer, health provider or recent paperwork can sound legitimate and persuade you to send money or reveal a sign-in code. Argentina’s own public guidance describes this type of deception. [Government guidance](https://www.argentina.gob.ar/node/158780). |
| **Identity and account misuse** | Exposed identity information may help defeat weak identity checks. Financial loss depends on additional failures, such as accepting inadequate proof or tricking the victim. A DNI number alone does not automatically unlock a bank account. Knowledge of personal facts should not substitute for secure authentication. [NIST guidance](https://pages.nist.gov/800-63-4/sp800-63b.html). |
| **Health-related humiliation or discrimination** | A diagnosis or disability record can expose something a person deliberately kept private, damaging relationships or creating opportunities for unfair treatment. |
| **Intimidation and physical danger** | Combining an address with sensitive personal information can increase the risk of stalking or coercion. This is a serious potential consequence, not evidence that these particular disclosures caused a kidnapping or death. |
| **Persistent distress and recovery work** | People may have to dispute activity, correct records and distrust future communications long after the technical incident ends. |

The last three are recognized categories of privacy harm, applied here as a risk assessment rather than measured Argentine outcomes. The UK privacy regulator’s guidance describes discrimination, reputational damage, financial loss, distress and physical harm; it is cited for those general risk categories, **not as Argentine law**. [ICO breach-risk guidance](https://ico.org.uk/for-organisations/report-a-breach/personal-data-breach/personal-data-breaches-a-guide/).

**A severe credible individual outcome is a chain of harms:** exposure helps someone impersonate or intimidate a victim, leading to financial loss or personal danger, while the information remains available for reuse. The evidence cannot identify an absolute worst outcome or imply that everyone whose information appears in a file experiences this chain.

## 7. Consequences for the economy

The reviewed sources do not provide a reliable economy-wide cost attributable to these incidents. A general cybercrime-loss estimate, a ransom demand or the seller’s asking price would not measure that cost.

The main economic channels are nevertheless clear. The following are **analytical consequences**, not quantified findings:

- **Household and business losses:** fraud can transfer money from legitimate users to criminals. Investigating and reversing transactions also consumes resources.
- **Costs passed to others:** banks, payment services, employers and households may bear additional verification and support costs even when the originating disclosure happened in government.
- **Lost working time:** people and staff spend time correcting records, answering complaints or replacing disrupted procedures.
- **Higher friction in digital services:** stronger checks may become necessary. Poorly designed checks can make legitimate access harder, particularly for people who already struggle with online procedures.
- **Recovery spending:** technical investigation, rebuilding systems, legal work and improved controls use money that could otherwise support services.

Chaco provides a concrete illustration of work disruption and reliance on physical files, but the available reporting does not quantify the economic loss. IOMA, by contrast, said normal operations continued. A leak and an outage are distinct problems; one should not be assumed from the other. [Chaco follow-up](https://chacodiapordia.com/slimel-sobre-las-nuevas-autoridades-de-camara-queremos-que-respeten-los-lugares-que-le-corresponden-a-la-oposicion/); [IOMA response](https://www.lanacion.com.ar/sociedad/la-provincia-advirtio-un-hackeo-al-ioma-alerta-por-la-filtracion-de-padrones-de-afiliacion-y-nid31032026/).

There is insufficient evidence here to attribute changes in Argentina’s GDP, inflation, exchange rate, sovereign borrowing costs or foreign investment to these leaks. Their human and institutional costs can be serious without a demonstrable macroeconomic effect.

## 8. Consequences for government

**Operational disruption is documented in the related Chaco incident.** Restoring systems and accessing legislative records became immediate administrative problems. This should not be misreported as proof of confidential information theft.

**Official records can lose reliability if attackers gain permission to change them.** In the October police investigation, authorities described manipulation of records and false prescriptions as part of the alleged criminal activity. This is a different danger from merely copying information. A copied record exposes someone; an altered record can make an institution act on false information. [October police announcement](https://www.argentina.gob.ar/noticias/el-dfi-de-la-pfa-desmantelo-una-organizacion-cybercriminal-que-hackeaba-y-filtraba-datos-de).

**Investigation and response consume public resources.** Court complaints, technical examinations, police operations and administrative inquiries are visible in the case record. Their total cost is not published in the material reviewed.

**Exposure of personnel can create targeting opportunities.** Judicial, police or executive staff may become easier to impersonate, pressure or approach deceptively. This is a prospective risk; SCBA specifically denied exposure of material enabling access to its digital systems. [SCBA update](https://www.scba.gov.ar/institucional/nota.asp?id=58623&veradjuntos=no).

**Public trust can deteriorate when citizens cannot avoid supplying information but cannot learn what happened to it.** This is an institutional implication, not a measured change in trust attributable to these cases. Citizens generally cannot replace their government provider as easily as a commercial service.

The severe government scenario is a combination of exposed people, unreliable records and interrupted services. The evidence reviewed does not establish a nationwide collapse of those functions, compromise of military operations or control of critical infrastructure.

## 9. What tends to happen after a leak is reported?

Across these cases, a recurring sequence is visible, although not every event follows every step:

1. **An advertisement, monitoring post or investigation appears.** It may provide a sample, a claimed record count or screenshots.
2. **News and social media amplify the claim.** “Records,” “people,” “new hack” and “old dataset” can become blurred together.
3. **Institutions respond with different levels of detail.** Some acknowledge a limited incident; others deny a direct intrusion or say investigations are continuing.
4. **Technical and legal responses proceed at different speeds.** A complaint proves that a matter was reported, not that every allegation was validated.
5. **Copies can keep circulating after the immediate problem is fixed.** Resale and repackaging prolong exposure and can generate another round of headlines.

This is a synthesis of the broker investigation, March campaign, September ANSES reporting and enforcement cases above. It explains why counting news articles is a poor way to count distinct leaks.

Two implications follow. **“No new intrusion” does not mean “no continuing harm.”** Equally, the fact that a criminal advertises a dataset does not mean its claimed origin or size is genuine.

## 10. What would most directly reduce the problem?

These are priorities inferred from the evidence, rather than claims that every institution currently lacks these controls:

| Priority | Plain-English purpose |
|---|---|
| **Protect accounts and restrict their reach** | Require strong sign-in verification and give each person only the access their job requires. Watch for unusually large or inappropriate searches. |
| **Separate public documents from private attachments** | Check files before publication and remove identifying details where they are unnecessary. PAMI’s eventual retention of basic purchasing information while restricting sensitive attachments shows that transparency and privacy can coexist. |
| **Know who holds copies** | Track which offices and outside organizations receive data, why they need it, how they protect it and when they should delete it. |
| **Make misuse traceable** | Keep reliable records of who accessed or changed information; review unusual activity and remove obsolete access. |
| **Communicate findings clearly** | Distinguish the date of theft from discovery; report verified data categories and distinct affected people; explain uncertainty and publish meaningful updates. |
| **Restore services without claiming the leak is undone** | Backups can help bring systems back. They cannot erase information already copied by others. |

These recommendations reflect the duties to protect, limit and properly retain data in Argentine law, the national incident-management framework and the concrete publication correction documented at PAMI. Stronger authentication is supported by NIST’s technical guidance. [Law 25,326](https://www.argentina.gob.ar/normativa/nacional/64790/actualizacion); [national incident framework](https://www.argentina.gob.ar/normativa/386227_disp3_pdf/archivo); [PAMI correction](https://chequeado.com/investigaciones/finalmente-pami-dejo-de-mostrar-en-su-web-la-informacion-privada-de-sus-afiliados/); [NIST](https://pages.nist.gov/800-63-4/sp800-63b.html).

## Research limits

This report cannot determine the total number of Argentines affected, the frequency of unreported incidents, or a national economic loss. Many cases lack public final technical reports; institutional denials and criminal claims are both insufficient on their own to settle disputed facts. Public police descriptions are evidence of what investigators report, not substitutes for final court findings.

The central finding is nevertheless well supported: **the danger continues after information leaves the original system.** Reducing it requires controlling legitimate access and publication as carefully as blocking intruders, then helping affected people when prevention fails.
