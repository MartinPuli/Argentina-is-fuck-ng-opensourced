"""Generate fictional procurement attachments for the demo.

Every person, number and diagnosis here is invented. Each page carries a
"DATOS FICTICIOS" watermark so no file can be mistaken for a real record.
"""

import io
import json
from pathlib import Path

import pymupdf as fitz
from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).parent / "pdfs"
WATERMARK = "DATOS FICTICIOS - DEMO HACKATHON"


def cuit(prefix: str, body: str) -> str:
    """Return a CUIT/CUIL with a valid check digit."""
    digits = prefix + body
    weights = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2]
    check = 11 - sum(int(d) * w for d, w in zip(digits, weights)) % 11
    check = {11: 0}.get(check, check)
    assert check != 10, "pick another body"
    return f"{prefix}-{body}-{check}"


def text_pdf(path: Path, title: str, lines: list[str]) -> None:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 60), title, fontsize=15, fontname="helv")
    y = 95
    for line in lines:
        page.insert_text((50, y), line, fontsize=10.5, fontname="helv")
        y += 17
    page.insert_text((50, 800), WATERMARK, fontsize=9, fontname="helv", color=(0.7, 0, 0))
    doc.save(path)


def _font(size: int) -> ImageFont.ImageFont:
    for name in ("DejaVuSans.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default(size)


def scanned_pdf(path: Path, lines: list[tuple[str, int]], tilt: float = 0.6) -> None:
    """A PDF whose only content is an image, like a phone scan. No text layer."""
    img = Image.new("RGB", (1240, 1754), (246, 243, 236))
    draw = ImageDraw.Draw(img)
    y = 120
    for text, size in lines:
        draw.text((110, y), text, fill=(25, 25, 30), font=_font(size))
        y += int(size * 1.7)
    draw.text((110, 1620), WATERMARK, fill=(170, 20, 20), font=_font(30))
    img = img.rotate(tilt, fillcolor=(246, 243, 236), resample=Image.BICUBIC)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=80)
    doc = fitz.open()
    page = doc.new_page()
    page.insert_image(page.rect, stream=buf.getvalue())
    doc.save(path)


def xray_pdf(path: Path) -> None:
    """A drawn x-ray of a leg below a knee: a medical image with no readable text."""
    img = Image.new("L", (1240, 1754), 8)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((470, 140, 770, 1500), radius=140, fill=55)  # soft tissue
    d.rounded_rectangle((585, 160, 655, 760), radius=30, fill=225)  # femur
    d.ellipse((540, 720, 700, 860), fill=235)  # knee
    d.rounded_rectangle((560, 850, 640, 1150), radius=25, fill=215)  # tibia stump
    d.line((560, 1150, 640, 1150), fill=120, width=6)  # amputation line
    d.ellipse((900, 150, 1020, 270), outline=200, width=6)  # side marker
    d.text((935, 180), "D", fill=200, font=_font(70))
    img = img.convert("RGB")
    ImageDraw.Draw(img).text((110, 1620), WATERMARK, fill=(170, 20, 20), font=_font(30))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=80)
    doc = fitz.open()
    page = doc.new_page()
    page.insert_image(page.rect, stream=buf.getvalue())
    doc.save(path)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    patient_cuil = cuit("27", "31846275")
    patient_dni = "31.846.275"
    supplier_cuit = cuit("30", "71583920")

    text_pdf(OUT / "especificacion_tecnica_silla.pdf", "Especificación técnica - Silla de ruedas motorizada", [
        "Compulsa abreviada 1042/2026 - UGL XXIII Jujuy",
        "",
        "Ítem: silla de ruedas motorizada, plegable, 1 unidad.",
        "Ancho de asiento: 45 cm. Capacidad de carga: 120 kg.",
        "Batería de litio con autonomía mínima de 20 km.",
        "Control por joystick ajustable a izquierda o derecha.",
        "Garantía mínima: 12 meses. Entrega en sede de la UGL en 15 días hábiles.",
    ])

    text_pdf(OUT / "justificacion_medica.pdf", "Resumen de historia clínica y justificación médica", [
        "Paciente: Juana Ficticia Pérez",
        f"DNI: {patient_dni}    CUIL: {patient_cuil}",
        "N.º de afiliada PAMI: 150318462750/00",
        "Domicilio: Calle Inventada 1234, San Salvador de Jujuy",
        "Fecha de nacimiento: 14/03/1951",
        "",
        "Diagnóstico: esclerosis lateral amiotrófica (ELA), evolución de 3 años.",
        "Antecedentes: hipertensión arterial, diabetes tipo 2 en tratamiento.",
        "Evolución: pérdida progresiva de la marcha; no puede propulsar silla manual.",
        "Indicación: silla de ruedas motorizada con control por joystick.",
        "",
        "Dra. Laura Ejemplo - M.P. 4471 - Neurología",
    ])

    scanned_pdf(OUT / "dni_escaneado.pdf", [
        ("REPÚBLICA ARGENTINA", 44),
        ("DOCUMENTO NACIONAL DE IDENTIDAD", 38),
        ("Apellido: FICTICIA PÉREZ", 40),
        ("Nombre: JUANA", 40),
        ("Sexo: F    Nacionalidad: ARGENTINA", 36),
        ("Fecha de nacimiento: 14 MAR 1951", 36),
        (f"Documento: {patient_dni}", 46),
    ])

    scanned_pdf(OUT / "certificado_discapacidad.pdf", [
        ("CERTIFICADO ÚNICO DE DISCAPACIDAD", 42),
        ("Ley 22.431", 34),
        ("Titular: Juana Ficticia Pérez", 36),
        (f"DNI {patient_dni}", 36),
        ("Diagnóstico: G12.2 Enfermedad de la neurona motora", 32),
        ("Orientación prestacional: rehabilitación, transporte", 32),
        ("Junta evaluadora - Jujuy", 32),
    ], tilt=-0.8)

    text_pdf(OUT / "cotizacion_proveedor.pdf", "Cotización - Ortopedia Ejemplar S.A.", [
        f"Razón social: Ortopedia Ejemplar S.A.    CUIT: {supplier_cuit}",
        "Domicilio comercial: Av. Proveedores 500, San Salvador de Jujuy",
        "",
        "Ítem 1: silla de ruedas motorizada plegable, joystick ajustable.",
        "Precio unitario: $ 4.850.000,00    Cantidad: 1",
        "Plazo de entrega: 10 días hábiles. Garantía: 18 meses.",
    ])

    text_pdf(OUT / "especificacion_protesis.pdf", "Especificación técnica - Prótesis transfemoral", [
        "Compulsa abreviada 1057/2026 - UGL XXX Chivilcoy",
        "",
        "Ítem: prótesis transfemoral con rodilla hidráulica, 1 unidad.",
        "Usuaria de 74 años, residente en Alberti, amputación por pie diabético,",
        "atendida en el Hospital Municipal de Alberti desde marzo de 2026.",
        "Encaje de contacto total; pie de respuesta dinámica.",
        "Entrega con 3 sesiones de adaptación en la sede de la UGL.",
    ])

    text_pdf(OUT / "especificacion_cama.pdf", "Especificación técnica - Cama ortopédica articulada", [
        "Compulsa abreviada 1063/2026 - UGL XIX Misiones",
        "",
        "Ítem: cama ortopédica articulada de tres tramos con barandas, 1 unidad.",
        "Colchón antiescaras de celdas de aire con compresor.",
        "Destinada al afiliado de 81 años de Campo Viera que volvió a su casa",
        "el 2 de septiembre tras la operación de cadera en el Hospital SAMIC de Oberá.",
        "Entrega e instalación en domicilio dentro de las 72 horas.",
    ])

    xray_pdf(OUT / "radiografia_muñon.pdf")

    text_pdf(OUT / "nota_pedido.pdf", "Nota de pedido - UGL XXIII Jujuy", [
        "Compulsa abreviada 1042/2026",
        f"Beneficiaria: Juana Ficticia Pérez - DNI {patient_dni} - CUIL {patient_cuil}",
        "",
        "Se solicita la adquisición de 1 (una) silla de ruedas motorizada plegable",
        "con control por joystick, según especificación técnica adjunta.",
        "Presupuesto de referencia: $ 4.900.000,00.",
        "Lugar de entrega: sede de la UGL XXIII, Av. Belgrano 800, San Salvador de Jujuy.",
        "Plazo de entrega: 15 días hábiles desde la notificación de la orden de compra.",
    ])

    purchases = [
        {
            "office": "UGL XXIII Jujuy",
            "procedure": "Compulsa abreviada 1042/2026",
            "item": "Silla de ruedas motorizada",
            "amount": 4850000,
            "files": [
                "especificacion_tecnica_silla.pdf",
                "nota_pedido.pdf",
                "justificacion_medica.pdf",
                "dni_escaneado.pdf",
                "certificado_discapacidad.pdf",
                "cotizacion_proveedor.pdf",
            ],
        },
        {
            "office": "UGL XXX Chivilcoy",
            "procedure": "Compulsa abreviada 1057/2026",
            "item": "Prótesis transfemoral",
            "amount": 9200000,
            "files": ["especificacion_protesis.pdf", "radiografia_muñon.pdf"],
        },
        {
            "office": "UGL XIX Misiones",
            "procedure": "Compulsa abreviada 1063/2026",
            "item": "Cama ortopédica articulada",
            "amount": 2100000,
            "files": ["especificacion_cama.pdf"],
        },
    ]
    (OUT / "purchases.json").write_text(json.dumps(purchases, ensure_ascii=False, indent=2))
    print(f"wrote {len(list(OUT.glob('*.pdf')))} PDFs to {OUT}")


if __name__ == "__main__":
    main()
