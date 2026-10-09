"""Evidence comparison stays attributed, unit-aware and behind staff access."""

import importlib
import re
from datetime import date
from html import unescape
from types import SimpleNamespace
from urllib.parse import urlsplit

import dotenv
import pytest
from fastapi.testclient import TestClient

from gate.exposure_data import EXPOSURES, RESEARCH_WINDOW, REVIEWED_AT

STAFF = ("exposure-test-reviewer", "fictional-exposure-test-password")


@pytest.fixture
def web(monkeypatch, tmp_path):
    for name in ("AKASHML_API_KEY", "GUILD_WORKSPACE", "GUILD_AGENT", "CLICKHOUSE_HOST"):
        monkeypatch.setenv(name, "")
    monkeypatch.setenv("GATE_DB", str(tmp_path / "exposures.sqlite3"))
    monkeypatch.setenv("GATE_STAFF_USERNAME", STAFF[0])
    monkeypatch.setenv("GATE_STAFF_PASSWORD", STAFF[1])
    monkeypatch.setattr(dotenv, "load_dotenv", lambda *args, **kwargs: False)
    store = importlib.import_module("gate.store")
    monkeypatch.setattr(store, "DB_PATH", tmp_path / "exposures.sqlite3")
    app_module = importlib.import_module("gate.app")
    monkeypatch.setattr(app_module, "events", store.Events())
    with TestClient(app_module.app) as client:
        yield SimpleNamespace(client=client, monkeypatch=monkeypatch)


def text(fragment):
    return " ".join(unescape(re.sub(r"<[^>]+>", " ", fragment)).split())


def case_rows(html):
    return [text(row) for row in re.findall(r'<tr>\s*<th scope="row">(.*?)</tr>', html, re.S)]


def test_staff_page_renders_all_cases_in_separate_entity_sections(web):
    response = web.client.get("/exposures", auth=STAFF)
    assert response.status_code == 200
    content = text(response.text)
    assert "Companies & suppliers" in content
    assert "Public bodies" in content
    assert "Report dates are not intrusion dates." in content
    assert "A national “largest leak” ranking is not established." in content
    rows = case_rows(response.text)
    assert len(rows) == len(EXPOSURES) == 7
    for record in EXPOSURES:
        matching = [row for row in rows if row.startswith(record["name"] + " ")]
        assert len(matching) == 1, record["name"]
        assert record["report_date"] in matching[0]
        assert record["evidence_status"].capitalize() in matching[0]
        assert record["limitations"] in matching[0]


def test_figures_keep_their_units_and_unknown_counts_stay_unknown(web):
    response = web.client.get("/exposures", auth=STAFF)
    assert response.status_code == 200
    rows = case_rows(response.text)
    global_visum = next(row for row in rows if row.startswith("Global Visum "))
    assert "20,000 files" in global_visum
    assert "Reported quantity" in global_visum
    assert "approximate" in global_visum
    anses = next(row for row in rows if row.startswith("ANSES / SIPA "))
    assert "38,000,000 records" in anses
    assert "Claimed quantity" in anses
    assert "Disputed" in anses
    for record in EXPOSURES:
        if record["quantity"] is None:
            row = next(row for row in rows if row.startswith(record["name"] + " "))
            assert "Unknown No comparable total" in row
            assert not re.search(r"(?<![\d,])0 (?:records|people|files)\b", row)


def test_anonymous_and_incorrect_credentials_cannot_open_comparison(web):
    for credentials in (None, (STAFF[0], "wrong-fictional-password")):
        response = web.client.get("/exposures", auth=credentials)
        assert response.status_code == 401
        assert "Basic" in response.headers["www-authenticate"]
        assert response.headers["cache-control"] == "no-store"
        assert "Who exposed Argentine data?" not in response.text


def test_unconfigured_staff_password_disables_comparison(web):
    web.monkeypatch.delenv("GATE_STAFF_PASSWORD", raising=False)
    for credentials in (None, STAFF):
        response = web.client.get("/exposures", auth=credentials)
        assert response.status_code == 503
        assert response.headers["cache-control"] == "no-store"
        assert "Staff access is disabled" in response.text


def test_curated_data_preserves_source_dates_and_evidence_contract():
    start = date.fromisoformat(RESEARCH_WINDOW["start"])
    end = date.fromisoformat(RESEARCH_WINDOW["end"])
    assert date.fromisoformat(REVIEWED_AT) >= end
    assert len({record["name"] for record in EXPOSURES}) == len(EXPOSURES)
    for record in EXPOSURES:
        assert record["entity_type"] in {"company", "public_body"}
        assert record["evidence_status"] in {"confirmed", "acknowledged", "alleged", "disputed"}
        assert record["quantity_status"] in {"reported", "verified", "claimed", "unknown"}
        assert record["unit"] in {"records", "people", "files", "unknown"}
        assert record["scope_argentina"] in {"known", "uncertain"}
        assert start <= date.fromisoformat(record["report_date"]) <= end
        assert record["date_note"] and record["limitations"]
        if record["incident_date"] is not None:
            assert date.fromisoformat(record["incident_date"]) <= date.fromisoformat(record["report_date"])
        if record["quantity"] is None:
            assert record["quantity_status"] == "unknown"
        else:
            assert type(record["quantity"]) in {int, float} and record["quantity"] > 0
            assert record["unit"] != "unknown"
        urls = [record["source_url"], *(source["url"] for source in record.get("supporting_sources", []))]
        for url in urls:
            parsed = urlsplit(url)
            assert parsed.scheme == "https" and parsed.hostname
            assert parsed.username is None and parsed.password is None
    # This snapshot must not acquire a spurious verified company-volume claim.
    assert sum(record["entity_type"] == "company" for record in EXPOSURES) == 2
    assert not any(record["entity_type"] == "company" and record["quantity_status"] == "verified"
                   for record in EXPOSURES)
