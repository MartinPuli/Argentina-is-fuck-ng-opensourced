"""The gate's promises, checked against the fictional fixtures.

Run: uv run python -m pytest -q   (from gate/)
"""

import os
import sys
from pathlib import Path

os.environ["GATE_DB"] = str(Path(__file__).parent / "test.db")
# Empty values win over .env (load_dotenv never overrides), so tests stay offline.
for var in ("AKASHML_API_KEY", "GUILD_WORKSPACE", "GUILD_AGENT", "CLICKHOUSE_HOST", "GATE_STAFF_PASSWORD"):
    os.environ[var] = ""

from fastapi.testclient import TestClient  # noqa: E402

from gate.detect import cuit_valid, mask, scan  # noqa: E402
from gate.policy import decide  # noqa: E402

PDFS = Path(__file__).parents[1] / "fixtures" / "pdfs"
EXPECTED = {
    "especificacion_tecnica_silla.pdf": "public",
    "cotizacion_proveedor.pdf": "public",
    "justificacion_medica.pdf": "withheld",
    "dni_escaneado.pdf": "withheld",
    "certificado_discapacidad.pdf": "withheld",
    "especificacion_protesis.pdf": "hold",
    # No identifier and no clinical keyword: only the model can see the risk.
    "especificacion_cama.pdf": "public",
}


def test_each_fixture_gets_the_expected_decision():
    for name, expected in EXPECTED.items():
        decision, _, _ = decide(scan((PDFS / name).read_bytes()), None)
        assert decision == expected, name


def test_model_can_add_caution_but_never_release_a_block():
    s = scan((PDFS / "justificacion_medica.pdf").read_bytes())
    lenient = {"safe_for_public": True, "personal_data": False, "health_data": False,
               "reidentification_risk": "none", "reasons": []}
    assert decide(s, lenient)[0] == "withheld"
    clean = scan((PDFS / "especificacion_tecnica_silla.pdf").read_bytes())
    worried = {"safe_for_public": False, "personal_data": False, "health_data": True,
               "reidentification_risk": "medium", "reasons": ["mentions a condition"]}
    assert decide(clean, worried)[0] == "hold"


def test_findings_never_carry_raw_identifiers():
    for name in EXPECTED:
        for f in scan((PDFS / name).read_bytes()).findings:
            if f.kind in ("dni", "person_cuil", "affiliate_number"):
                assert "*" in f.evidence, (name, f.evidence)
    assert mask("31.846.275") == "31.***.275"


def test_company_cuit_is_public_person_cuil_is_not():
    assert cuit_valid("30715839209")
    kinds = {f.kind for f in scan((PDFS / "cotizacion_proveedor.pdf").read_bytes()).findings}
    assert kinds == {"company_cuit"}


def test_public_portal_never_serves_withheld_or_held_files():
    Path(os.environ["GATE_DB"]).unlink(missing_ok=True)
    from gate.app import app

    client = TestClient(app)
    assert client.post("/demo/seed", follow_redirects=False).status_code == 303
    from gate.store import db

    with db() as con:
        rows = con.execute("select id, filename, decision from attachments").fetchall()
    assert {r["filename"]: r["decision"] for r in rows} == EXPECTED
    for r in rows:
        status = client.get(f"/public/file/{r['id']}").status_code
        assert status == (200 if r["decision"] == "public" else 404), r["filename"]
    page = client.get("/public").text
    for r in rows:
        assert (r["filename"] in page) == (r["decision"] == "public"), r["filename"]

    held = next(r for r in rows if r["decision"] == "hold")
    client.post(f"/review/{held['id']}", data={"action": "approve", "reviewer": "Revisora Demo"})
    assert client.get(f"/public/file/{held['id']}").status_code == 200
    Path(os.environ["GATE_DB"]).unlink(missing_ok=True)


if __name__ == "__main__":
    sys.exit(__import__("pytest").main([__file__, "-q"]))
