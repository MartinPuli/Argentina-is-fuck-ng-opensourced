"""Public incident summaries and explicitly fictional, reviewable adaptations.

Evidence comes from docs/INCIDENTS.md and docs/SOURCES.md. Recipes are authored
engineering proposals, not recovered victim documents or historical findings.
"""

CASES = [
    {
        "id": "pami-private-attachments",
        "title": "PAMI: private documents in public purchasing files",
        "url": "https://chequeado.com/investigaciones/pami-expone-datos-medicos-y-documentos-sensibles-de-sus-afiliados-en-su-sitio-web/",
        "evidence_status": "Independently documented exposure; fictional rule adaptation",
        "summary": (
            "Chequeado documented medical and identity documents accessible in public PAMI "
            "purchasing attachments in May 2026. The local-record phrases and tests below are "
            "invented defensive examples, not quoted victim data or verified incident fields."
        ),
        "mechanism": (
            "Private supporting documents crossed a publication boundary. The proposed phrase "
            "combination is an engineering inference for this gate, not a reconstruction."
        ),
        "recipe": {
            "title": "Review individual patient records with local reference codes",
            "groups": [
                ["ficha asistencial individual", "registro asistencial individual"],
                ["código de paciente:", "identificador de paciente:"],
                ["prestación asignada:", "turno asignado:"],
            ],
            "action": "hold",
            "rationale": (
                "An individual care record can link a local patient reference to an assigned "
                "service without using a national identifier. This narrow phrase rule requests "
                "review; it does not prove identity, reconstruct PAMI's incident, or detect all records."
            ),
            "improvements": [
                "Separate private supporting files from the public purchase package. Verify from an anonymous client that the exact held PDF cannot be downloaded while the public equipment specification remains available.",
                "Review and remove individual reference codes and assigned-care details from any proposed public derivative. Re-run the gate on that derivative and verify its exact bytes; do not change the original file's evidence.",
                "Add mixed text/image and OCR-unavailable versions of these fictional examples. Verify that missing coverage remains held and record benign-document false positives before broadening the phrases.",
            ],
            "tests": [
                {"name": "Fictional local patient record", "text": "Documento ficticio. Ficha asistencial individual. Código de paciente: DEMO-ALFA. Prestación asignada: visita domiciliaria.", "should_match": True},
                {"name": "Alternative fictional record wording", "text": "Registro asistencial individual. Identificador de paciente: DEMO-BETA. Turno asignado: servicio ficticio.", "should_match": True},
                {"name": "Equipment specification mentioning a form", "text": "Compra de impresoras para ficha asistencial individual. Código de paciente: no se recopila ni publica en esta compra.", "should_match": False},
                {"name": "Aggregate service requirements", "text": "Compra de equipamiento. Totales agregados por centro. Sin registros individuales ni referencias personales.", "should_match": False},
            ],
        },
    },
    {
        "id": "rio-negro-payroll",
        "title": "Río Negro: acknowledged payroll-information disclosure",
        "url": "https://rionegro.gov.ar/articulo/59894/el-gobierno-denuncio-filtracion-de-informacion-de-sus-sistemas-informaticos",
        "evidence_status": "Acknowledged disclosure; access mechanism unresolved; fictional adaptation",
        "summary": (
            "The provincial government acknowledged extraction of officials' payslip information "
            "in June 2026 and described suspected employee misuse under investigation. This does "
            "not establish a public-PDF failure. The payroll attachment recipe is a fictional "
            "adaptation for the publication gate."
        ),
        "mechanism": (
            "The underlying access mechanism was unresolved in the cited statement. Individual "
            "payroll publication checks below are an engineering proposal, not the proven cause."
        ),
        "recipe": {
            "title": "Review individual payroll attachments with staff references",
            "groups": [
                ["recibo de sueldo individual", "liquidación individual de haberes"],
                ["legajo personal:", "agente identificado:"],
                ["neto a cobrar:", "importe neto individual:"],
            ],
            "action": "hold",
            "rationale": (
                "An individual payslip combining a staff reference and net payment requires "
                "a publication review. Aggregate budgets and public salary scales differ from "
                "individual supporting records; this rule does not decide their legal status."
            ),
            "improvements": [
                "Keep individual payroll attachments separate from public budget tables. Verify that a fictional payslip is held while an aggregate salary-scale PDF remains eligible after complete analysis.",
                "Require attributable human review of any payroll publication exception. Verify that an unprivileged request cannot approve the attachment and that the authenticated identity and reason are recorded.",
                "Assess payroll access permissions separately from this publication rule. Use fictional accounts to test denied cross-employee retrieval and permitted authorized retrieval; a phrase match cannot establish or contain an insider intrusion.",
            ],
            "tests": [
                {"name": "Fictional individual payslip", "text": "Recibo de sueldo individual. Legajo personal: DEMO-GAMMA. Neto a cobrar: importe ficticio.", "should_match": True},
                {"name": "Alternative fictional payroll wording", "text": "Liquidación individual de haberes. Agente identificado: DEMO-DELTA. Importe neto individual: valor de prueba.", "should_match": True},
                {"name": "Public aggregate salary scale", "text": "Escala salarial por categoría. Presupuesto agregado del personal. No contiene recibos individuales ni referencias de agentes.", "should_match": False},
                {"name": "Procurement for payroll software", "text": "Software para recibo de sueldo individual. Legajo personal: campo que no se publica en la especificación. Precio total del proveedor.", "should_match": False},
            ],
        },
    },
]
