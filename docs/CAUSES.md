# Recurring targets, origins and cybersecurity drivers

**Research window:** October 9, 2025–October 9, 2026  
**Evidence cutoff:** October 9, 2026

This chapter is an excerpt of the [full report](../REPORT.md). Preserve its evidence labels and dates when quoting or reusing it.

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

[Back to the repository guide](../README.md)
