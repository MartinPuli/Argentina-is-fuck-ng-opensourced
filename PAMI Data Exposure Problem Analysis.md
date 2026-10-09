# PAMI Data Exposure: Problem Analysis

**Prepared:** October 9, 2026  
**Geographic scope:** Argentina  
**Institution:** Instituto Nacional de Servicios Sociales para Jubilados y Pensionados (PAMI)  
**Focus:** Exposure and criminal misuse of affiliates' identity and healthcare information

## Executive summary

PAMI's information-security problem is not one recurring type of "hack." Public evidence points to at least three distinct failure modes:

1. **External intrusion:** a 2023 ransomware attack disrupted PAMI's systems, and investigators later found that information attributed to the incident had been offered for sale.
2. **Unsafe publication:** in 2026, PAMI procurement pages made medical records and identity documents publicly accessible as attachments to purchasing procedures.
3. **Fraudulent or unauthorized use:** earlier investigations documented schemes involving false prescriptions, deceased affiliates and alleged misuse of affiliate information by insiders and providers.

The common weakness is inconsistent control of sensitive information as it moves between clinical care, local offices, medical review, procurement, suppliers, public-transparency systems and archives.

The 2026 incident is the clearest process failure. Information collected to establish a patient's medical need was carried into a procurement file, and that file was then treated as a publication package. The institution failed to create a separate, privacy-safe public version.

This is best understood as **purpose collapse**: the same dossier was reused for several incompatible purposes without reducing its contents at each transition.

## 1. Scope and evidentiary standard

This analysis examines:

- The 2026 exposure of medical and identity records through PAMI's purchasing website.
- The administrative process that appears to have produced the exposure.
- The 2023 ransomware incident and subsequent criminal investigation.
- Earlier fraud cases demonstrating the value and possible uses of PAMI affiliate information.
- The institutional roles involved in collecting, reviewing, publishing and protecting the records.

It does not reproduce leaked information or assert that every allegation has been proven. Where PAMI has not published a complete technical post-mortem, the process is reconstructed from its purchasing dispositions, organizational material, audit findings and documented website behavior.

## 2. The 2026 public-document exposure

### 2.1 What was exposed

Chequeado found sensitive files accessible through PAMI's public search system for purchases conducted by its local management units, known as **Unidades de Gestión Local** (UGLs).

The exposed material included:

- Full names and DNI numbers.
- Copies of identity documents.
- Home addresses and contact information.
- Diagnoses and clinical histories.
- Prescriptions and treatment plans.
- Laboratory results.
- Disability certificates.
- Photographs of injuries.
- Images from medical procedures, including colonoscopies.
- Information about treating professionals.
- Procurement, supplier and pricing information.

Chequeado reviewed a sample of abbreviated purchasing procedures from January and February 2026 and identified **at least 40 exposed cases**. This is a documented minimum, not an estimate of the total number of affected people. See [Chequeado's initial investigation](https://chequeado.com/investigaciones/pami-expone-datos-medicos-y-documentos-sensibles-de-sus-afiliados-en-su-sitio-web/).

### 2.2 Institutional response

PAMI described the exposure as a serious anomaly contrary to its protocols and announced administrative investigations. It also disabled or restricted relevant parts of the purchasing system.

The response did not immediately stop the underlying behavior. One week after the original report, Chequeado found that previously identified files remained accessible and that new sensitive files had been added. See [Chequeado's May 29 follow-up](https://chequeado.com/investigaciones/a-una-semana-de-la-revelacion-de-chequeado-el-pami-continua-mostrando-en-su-web-datos-privados-de-sus-afiliados/comment-page-1/).

Approximately ten days after the initial report, PAMI restricted public access to the sensitive PDF attachments while retaining basic purchasing information. See [Chequeado's verification of the restriction](https://chequeado.com/investigaciones/finalmente-pami-dejo-de-mostrar-en-su-web-la-informacion-privada-de-sus-afiliados/).

That final configuration demonstrates an important point: procurement transparency did not require publishing the underlying medical evidence.

## 3. Reconstructed process flow

PAMI has not published a complete technical account of the 2026 failure. The following flow is reconstructed from PAMI purchasing decisions and the behavior documented by Chequeado.

```text
Affiliate needs an exceptional treatment, device or service
                         |
                         v
Doctor or provider creates a prescription and medical justification
                         |
                         v
UGL receives or scans clinical records, studies, DNI and certificates
                         |
                         v
UGL initiates the request in an internal system such as SII
                         |
                         v
Medical management reviews the diagnosis and clinical justification
                         |
                         v
Procurement confirms that no existing contract covers the item
                         |
                         v
An exceptional abbreviated purchase is created
                         |
                         v
Supporting evidence becomes attached to the procurement file
                         |
              CRITICAL PUBLICATION BOUNDARY
                         |
                         v
The purchasing call and attachments are published; suppliers are invited
                         |
                         v
Offers -> evaluation -> legal review -> award -> delivery
```

PAMI purchasing dispositions show that a UGL can raise a request through the SII system, after which the medical-management area reviews the diagnosis and supporting history. Procurement personnel determine whether an existing contract covers the item, prepare an exceptional abbreviated purchase and publish the call while inviting suppliers. One example is [Compulsa Abreviada 823/2025](https://institucional.pami.org.ar/files/boletines_inssjp/13-01-26.pdf).

### 3.1 The critical design error

The same dossier was apparently used for two incompatible functions:

- **Internal clinical justification:** proving why a particular patient needs a treatment, device or service.
- **External procurement:** providing the market and public with sufficient information about what PAMI is buying and how it selected a supplier.

These functions require different information. A medical reviewer may require a detailed clinical history. A supplier generally needs a technical specification, quantity, delivery conditions and commercial requirements—not the patient's identity or full medical record.

A properly separated process would produce at least three views:

| Information product | Purpose | Expected access |
|---|---|---|
| Clinical file | Establish medical need and support treatment | Authorized clinical personnel |
| Procurement file | Authorize, quote and evaluate the purchase | Authorized administrative personnel and appropriate suppliers |
| Public record | Demonstrate transparent use of public funds | General public |

The public record should normally contain the item or service, procedure, price, supplier and decision. Identifiable medical evidence should remain in the restricted clinical or administrative layer.

## 4. Why the process fails

### 4.1 Decentralized publication creates many failure points

PAMI told Chequeado that each UGL independently uploaded purchasing information. Privacy therefore depended on consistent decisions by staff distributed across multiple local offices.

This creates several problems:

- Different offices may interpret publication rules differently.
- Staff may upload complete dossiers because they are unsure which evidence is required.
- A central policy may not be reflected in each local workflow.
- Correcting the public website does not automatically change the behavior of every uploader.
- Detecting a problem at one UGL does not ensure that equivalent files elsewhere are reviewed.

The fact that new sensitive documents appeared after the initial report is consistent with an unresolved workflow problem rather than a single mistaken upload.

### 4.2 No publicly demonstrated privacy gate

PAMI's public documentation describes medical review, procurement classification, supplier invitations, evaluation, legal review and approval. The materials reviewed do not demonstrate a mandatory final control where a designated person or system verifies that:

- Every attachment has been classified.
- Medical evidence has been excluded from the public package.
- Identifiers have been removed where appropriate.
- Scanned pages and images have been visually inspected.
- A second person has approved the public version.
- The published version is distinct from the retained original.

This does not establish that no internal rule existed. PAMI stated that the publication violated its protocols. It does show that any existing control failed to prevent, promptly detect or immediately stop repeated exposure.

### 4.3 Urgent purchasing rewards speed and completeness

Exceptional purchasing exists partly because patients may need treatments or equipment that are not available under an existing contract. Delay can affect care.

That produces conflicting incentives:

- Clinical staff want to demonstrate urgency and necessity.
- Procurement staff need evidence supporting the exception.
- Suppliers need enough detail to provide an accurate quotation.
- Local offices want the purchase completed quickly.
- Privacy review can be perceived as an additional delay.

Under these conditions, uploading the complete source file can feel operationally safer than deciding which pages should be excluded. It reduces the risk of a procurement objection while transferring privacy risk to the patient.

### 4.4 Unstructured files resist reliable detection

The exposed information was contained in heterogeneous PDFs, scanned forms and images—not only structured database fields.

An identifier can appear in:

- A filename.
- Typed or handwritten text.
- A scanned identity document.
- Headers, footers and stamps.
- Photographs or medical images.
- A barcode or QR code.
- Embedded PDF metadata.

Health information is also contextual. A document can reveal a diagnosis without using the word "diagnosis." Removing a name and DNI may still leave a person identifiable through a combination of locality, age, rare condition, procedure, provider and date.

For this reason, a simple pattern matcher—or an AI model instructed only to "remove PII"—would be an incomplete control.

### 4.5 Responsibility becomes ambiguous during handoffs

PAMI's electronic-document rules state that functional areas retain ownership of information related to their responsibilities, including when the information exists in shared platforms. Its GDE environment operates alongside other institutional systems. See [PAMI's GDE rules](https://institucional.pami.org.ar/files/boletines_inssjp/RESOL-2021-1278-INSSJP-DE-INSSJP.pdf).

In the exceptional-purchase flow, responsibility can be distributed among:

- The clinician who creates the medical evidence.
- The UGL that receives and uploads it.
- Medical management, which verifies necessity.
- Procurement, which creates the purchasing procedure.
- Technology teams, which operate the systems.
- Transparency personnel, who oversee access obligations.
- Information-security personnel, who define protective controls.
- Data-protection personnel, who advise on privacy compliance.

Each area can own its own stage without any one area clearly owning the final question: **Is this exact package safe for unrestricted public release?**

### 4.6 Transparency was treated as publication of source documents

Argentina's access-to-information law favors disclosure but permits personal information to be withheld when it cannot be disassociated from the record, subject to lawful exceptions. See [Law 27,275, Article 8](https://www.argentina.gob.ar/normativa/nacional/ley-27275-265949/texto).

AAIP guidance describes anonymization, disassociation and partial public copies as mechanisms for reconciling transparency with privacy. An institution may preserve the complete original internally while releasing a sanitized derivative. See [AAIP guidance on archives and anonymization](https://www.argentina.gob.ar/sites/default/files/aaip_caja_de_herramientas_archivos.pdf).

The PAMI incident was therefore not an unavoidable conflict between transparency and confidentiality. It was a failure to construct a purpose-limited public record.

### 4.7 Security governance matured late

An Auditoría General de la Nación audit covering 2020–2021 found that PAMI lacked an adequate institution-wide organization for information-security policies and procedures. It identified the absence of an active security committee and a security role that remained vacant during the audited period. PAMI subsequently reported corrective work, including a strategic security plan and a dedicated information-security management area. See the [AGN audit report](https://www.agn.gob.ar/sites/default/files/informes/2024-162-Informe.pdf).

PAMI's own 2024 management review stated that the security committee established under its 2015 policy had only then held its first meeting and that a new policy was being developed. See [PAMI's "100 acciones en 100 días"](https://www.pami.org.ar/pdf/100_acciones_en_100_dias_de_gestion.pdf).

A separate audit finding concerned the absence of a comprehensive data dictionary, increasing the risk of inconsistent definitions and duplicated information. PAMI approved a data-dictionary procedure in March 2025. See [PAMI's 2025 corrective measure](https://institucional.pami.org.ar/files/boletines_inssjp/26-03-25.pdf).

These findings do not prove the direct cause of the 2026 publication incident. They provide evidence of a broader environment in which institution-wide information governance and consistent data handling developed later than the systems and workflows they were expected to govern.

## 5. Previous PAMI security and misuse incidents

### 5.1 The 2023 ransomware attack

On August 2, 2023, a Rhysida ransomware incident disrupted PAMI's website, application and operational systems. PAMI activated contingencies for prescriptions, medical attention and provider processes and restored affected virtual machines from backups. Some ANMAT services were also affected because they were hosted in PAMI infrastructure. See [contemporaneous reporting containing PAMI's response](https://tn.com.ar/tecno/internet/2023/08/02/pami-no-funciona-la-pagina-ni-la-app-de-la-obra-social/).

PAMI initially said its audits found no alteration to the availability or integrity of affiliate databases. That statement did not fully answer whether information had been copied:

| Security property | Question |
|---|---|
| Availability | Can authorized users access the information? |
| Integrity | Was the information changed or damaged? |
| Confidentiality | Was the information accessed or copied by an unauthorized party? |

A database can remain intact and available while a copy is stolen.

In July 2025, an appellate court reopened the criminal investigation. UFECI had identified information attributed to PAMI being advertised on the dark web seven days after the attack for 25 bitcoin. A related Córdoba case concerned an alleged buyer who sought one or more PAMI databases through Telegram to access electronic prescriptions. These are investigative and judicial allegations, not final convictions. See [reporting on the reopened investigation](https://www.infobae.com/judiciales/2025/07/21/reabrieron-la-investigacion-por-el-hackeo-al-pami-encontraron-en-cordoba-un-comprador-de-la-base-de-datos-robada/).

The investigation also exposed a response failure: restoration occurred without adequately preserving the affected digital environment. Investigators reportedly lacked preserved system images, a sufficient network diagram and other evidence needed to reconstruct entry and movement through the network.

Backups helped PAMI restore service. They could not recover stolen copies, and restoration without forensic preservation reduced the institution's ability to determine what happened.

### 5.2 Earlier fraud using affiliate information

PAMI-related identity and prescription fraud predates the ransomware attack.

In 2016 and 2017, federal prosecutors described schemes involving false prescriptions, duplicated records and the identities of deceased affiliates. One investigation concerned 14,872 medicines or medical supplies attributed to 811 deceased people. See the [Federal Prosecutors' 2017 account](https://www.fiscales.gob.ar/pami/la-fiscalia-especializada-realizo-el-viernes-36-denuncias-por-estafas-al-pami/).

Another investigation in Tucumán alleged that PAMI personnel enrolled affiliates in a diabetes register and that other participants used affiliate information for false dispensations. See the [Tucumán investigation](https://www.fiscales.gob.ar/pami/investigan-millonarias-maniobras-de-defraudacion-al-pami-en-tucuman/).

These were fraud and potential insider-misuse cases, not necessarily public leaks. They demonstrate concrete criminal uses for affiliate information:

- Supporting fraudulent prescriptions.
- Making a false medical transaction appear legitimate.
- Identifying people entitled to expensive medicines or devices.
- Connecting a real identity to a provider and treatment.
- Passing weak administrative verification.

The specialized UFI-PAMI prosecutor's remit includes illegitimate use of affiliate data to obtain medicines and fraud involving implants or prostheses. PAMI identifies Javier Arzubi Calvo as the responsible prosecutor. See [PAMI's UFI-PAMI description](https://prestadores.pami.org.ar/me_in_ufi.php?vm=3).

### 5.3 The criminal information market

In May 2026, Federal Police described an investigated network trading identity, vehicle and medical records, as well as credentials connected to Mi Argentina and PAMI. Investigators linked the activity to fraud, extortion and threats. See the [Federal Police announcement](https://www.argentina.gob.ar/noticias/el-dfi-de-la-pfa-desarticulo-una-importante-banda-de-hackers).

The available evidence does **not** establish that the documents exposed through PAMI's purchasing website entered this particular network. The operation demonstrates criminal demand and distribution capability, not a proven chain from the PAMI website to those sellers.

## 6. People and institutions in the information lifecycle

The following table identifies roles rather than assigning personal culpability. No public final report identifies a particular employee as responsible for the 2026 incident.

| Participant | Role |
|---|---|
| Affiliate or patient | The data subject; often depends on rapid completion of the process for access to care. |
| Doctor or healthcare provider | Produces prescriptions, histories, studies and medical justification. |
| UGL administrative staff | Receive, scan and upload documents and initiate the purchasing request. |
| Medical reviewers | Confirm diagnosis, necessity and supporting evidence. |
| Exceptional-purchase personnel | Convert the clinical request into a procurement procedure. |
| Procurement personnel | Prepare the call, publish information, invite suppliers and register offers. |
| Suppliers | Quote and deliver the requested product or service; should receive only the information necessary for that purpose. |
| Offer-evaluation and legal units | Evaluate proposals and the legality of the award. |
| Platform and IT teams | Operate SII, GDE, purchasing portals, permissions and logs. |
| Information Security Management | Defines and monitors security controls across systems and processes. |
| Data Protection Officer | Advises on protection of personal information. PAMI lists **Agustín Malpede** in this role. |
| Access to Public Information authority | Oversees transparency obligations. PAMI lists **Mariana Galán** as the responsible official. |
| Executive leadership | Owns institutional risk and remediation. PAMI lists **Esteban Ernesto Leguizamo** as Executive Director. |
| UAI, SIGEN and AGN | Internal and external oversight and audit functions. |
| AAIP | National regulator for personal data and access to public information. |
| UFI-PAMI and cybercrime investigators | Investigate fraud, unauthorized use and criminal distribution. |

Current institutional names are drawn from PAMI's [information-management page](https://transparenciaactiva.pami.org.ar/gestion-de-la-informacion/) and [authorities page](https://transparenciaactiva.pami.org.ar/autoridades-y-personal/). Listing these officials identifies relevant accountability offices; it does not imply involvement in causing the exposure.

## 7. Why PAMI information is particularly dangerous

PAMI records can combine four powerful categories of information:

1. **Identity:** name, DNI, date of birth, address and document image.
2. **Institutional relationship:** confirmation that the person is a PAMI affiliate.
3. **Medical context:** diagnosis, disability, provider, treatment and clinical history.
4. **Transaction timing:** evidence that a particular procedure, device or approval is currently being sought.

Together, these facts can make impersonation highly convincing. A criminal may be able to refer to the victim's actual provider, diagnosis or pending treatment rather than relying on a generic story.

The consequences can include:

- Targeted impersonation and payment fraud.
- Attempts to capture login or verification codes.
- Fraudulent prescriptions or medical claims.
- Extortion involving stigmatizing diagnoses or images.
- Discrimination or humiliation.
- Targeting of older, ill, disabled or socially isolated people.
- Persistent risk because a medical history cannot be replaced like a password.

Removing only the DNI does not necessarily anonymize a record. A combination of UGL, locality, age, rare diagnosis, date, provider and procedure may still identify the person.

## 8. Root-cause model

The deepest failure is **purpose collapse**.

```text
Necessary clinical collection
        |
        v
Excessive administrative copying
        |
        v
Clinical and procurement records become entangled
        |
        v
Publishing the complete file becomes the easiest workflow
        |
        v
No reliable release-time privacy gate
        |
        v
Public exposure and permanent copy risk
```

The contributing causes are:

- Collection of detailed clinical evidence for a legitimate purpose.
- Reuse of that evidence for procurement without data minimization.
- Decentralized uploads by local offices.
- Urgency incentives that favor completeness and speed.
- Reliance on unstructured PDFs, scans and images.
- Ambiguous ownership during departmental handoffs.
- Transparency implemented through source-document publication.
- No publicly demonstrated mandatory approval gate before release.
- Delayed institution-wide security and data-governance maturity.
- Incident response focused on restoring access before preserving evidence.

No single cause explains every PAMI incident. The publication exposure, ransomware intrusion and fraudulent use involved different mechanisms. They converge on the same lifecycle problem: PAMI has not consistently controlled what happens to affiliate information after its original collection.

## 9. Established facts and unresolved questions

### Established

- Sensitive medical and identity documents were publicly accessible through PAMI's purchasing website.
- UGL purchasing information was uploaded through a decentralized process.
- At least 40 exposed cases were documented in a limited sample.
- Exposure continued for several days after the initial report.
- PAMI eventually separated public purchasing information from sensitive attachments.
- PAMI suffered a disruptive ransomware incident in 2023.
- Investigators found information attributed to the incident being offered for sale.
- Earlier cases demonstrate real misuse of PAMI affiliate information in prescription and reimbursement fraud.

### Unresolved

- The total number of people exposed through the purchasing portal.
- How long each document remained accessible.
- Whether search engines, archives or automated scrapers retained copies.
- Whether every affected person was notified.
- Whether PAMI reviewed all historical procurement attachments.
- Which personnel, system settings or handoff decisions caused each publication.
- Whether publicly exposed documents were later sold or used in crimes.
- Whether a mandatory pre-publication privacy gate now exists.
- Whether PAMI will publish final technical and disciplinary findings.

## 10. Implication for a prevention system

An automated redaction agent could contribute to prevention, but it should not be treated as the principal control. Placing an AI model at the end of the existing process would leave the underlying mixing of clinical and public records intact.

The more defensible intervention point is:

> **Prevent any procurement record containing an unclassified or insufficiently reviewed attachment from crossing from PAMI's internal environment to its public purchasing system.**

An effective control would require:

- A separate public version of every procurement package.
- Classification of every attachment before publication.
- Deterministic checks for DNI, CUIT/CUIL and other structured identifiers.
- OCR and visual analysis for scanned documents and images.
- Detection of health information and contextual re-identification risk.
- A hard block when classification or redaction confidence is insufficient.
- Human review for uncertain or high-risk documents.
- A second-person approval for sensitive purchasing categories.
- Complete logs showing who submitted, reviewed, changed and released each file.
- Retrospective scanning of previously published attachments.
- Monitoring for unusual downloads and bulk access.
- Preservation of originals and forensic evidence in a restricted environment.

The goal is not merely to redact documents. It is to enforce a controlled transition between a confidential patient process and a public procurement process.

## Conclusion

PAMI's most important vulnerability is the movement of information between legitimate functions. A medical record can be properly collected, properly reviewed and properly stored at one stage, yet become exposed when reused in procurement or publication.

The 2026 incident shows that transparency and privacy can coexist: PAMI ultimately retained public purchasing information while restricting the sensitive attachments. The failure was not that PAMI published procurement decisions. It was that the institution did not reliably create a privacy-safe public record before publication.

Any technical solution should therefore address the publication boundary, document lineage and accountability for release. Detection and redaction are supporting capabilities. The core control is preventing a confidential attachment from becoming public without an explicit, logged and reviewable decision.
