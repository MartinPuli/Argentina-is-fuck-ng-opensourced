"""Actual HTTP/PDF boundaries with constructed model/context results; no live calls."""

import json
from copy import deepcopy
from uuid import uuid4

from test_learning_flow import web, pdf, upload, public, POSITIVE, BENIGN
from test_learning_proposer import mock_model
from gate import senso_context
from gate.learning_sources import CASES
from gate.rules import model_guidelines


def test_guidelines_are_public_cited_and_distinguish_local_policy(web):
    page = web.anonymous.get("/guidelines")
    assert page.status_code == 200
    assert "Official source" in page.text and "Application safeguard; not legislation" in page.text
    pack = web.anonymous.get("/api/guidelines").json()
    assert len(pack["sources"]) == 9 and pack["digest"] == model_guidelines()["digest"]
    for key in ("aaip_public_policy", "aaip_security", "aaip_responsible_ai", "cert_ar_2024", "cert_ar_2025"):
        source = pack["sources"][key]
        assert source["url"].startswith("https://www.argentina.gob.ar/")
        assert source["title"] in page.text and source["locator"] in page.text
    # Research and architecture guidance must not become new publication checks.
    assert set(pack["policies"]) == {"personal_id", "health", "reidentification", "company_ok", "unreadable", "learned"}
    assert all(not source.startswith("cert_ar_") for rule in pack["policies"].values() for source in rule["source_ids"])
    assert "not blanket permission" in pack["policies"]["company_ok"]["text"]
    assert "SENSO_API_KEY" not in json.dumps(pack)


def test_senso_actions_require_authentication_and_same_origin(web):
    assert web.anonymous.get("/api/senso/status").status_code == 401
    for path in ("/learning/senso/sync", "/learning/senso/refresh"):
        assert web.anonymous.post(path).status_code == 401
        assert web.client.post(path, headers={"origin": "https://other.example"}).status_code == 403


def test_failed_senso_retrieval_creates_no_candidate(web):
    def unavailable(_topic):
        raise ValueError("Senso is unavailable.")
    web.monkeypatch.setattr(senso_context, "retrieve", unavailable)
    result = web.client.post("/learning/propose", data={"title": "Fictional report",
        "url": "https://example.org/report", "summary": "Fictional private attachments were published without review.",
        "evidence_status": "reported", "use_senso": "true"})
    assert result.status_code == 400 and web.learning.list_rules() == []


def test_senso_guidance_enters_proposal_but_cannot_activate_or_release_pdf(web):
    rows = upload(web, {"private.pdf": pdf(POSITIVE), "benign.pdf": pdf(BENIGN)})
    assert public(web, rows["benign.pdf"]).status_code == 200
    context = {"provider": "Senso", "guideline_digest": model_guidelines()["digest"],
        "retrieved_at": 1, "authority": "Quoted context; no publication authority", "passages": [{
            "text": "Patient confidentiality", "content_id": str(uuid4()), "version_id": str(uuid4()),
            "node_id": str(uuid4()), "title": "Guideline pack"}]}
    web.monkeypatch.setattr(senso_context, "retrieve", lambda _: deepcopy(context))
    calls = mock_model(web.monkeypatch, json.dumps(CASES[0]["recipe"]))
    response = web.client.post("/learning/propose", data={"title": "Fictional report",
        "url": "https://example.org/report", "summary": "Fictional private attachments were published without review.",
        "evidence_status": "reported", "use_senso": "true"}, follow_redirects=False)
    assert response.status_code == 303
    rule = web.learning.list_rules()[0]
    assert rule["status"] == "draft" and "Senso context" in rule["generator"]
    quoted = json.loads(calls[0]["messages"][1]["content"])
    assert quoted["reviewed_publication_guidelines"]["digest"] == model_guidelines()["digest"]
    assert quoted["untrusted_senso_context"] == context
    route = response.headers["location"]
    assert "Senso context used" in web.client.get(route).text
    assert web.client.post(route + "/activate", data={"digest": rule["digest"]}).status_code == 400
    assert web.client.post(route + "/test", follow_redirects=False).status_code == 303
    assert web.learning.get_rule(rule["id"])["status"] == "tested"
    assert web.client.post(route + "/activate", data={"digest": rule["digest"]}, follow_redirects=False).status_code == 303
    assert public(web, rows["benign.pdf"]).status_code == 404  # old revision no longer sufficient
    assert web.client.post("/learning/rescan", follow_redirects=False).status_code == 303
    assert public(web, rows["private.pdf"]).status_code == 404
    assert public(web, rows["benign.pdf"]).content == bytes(rows["benign.pdf"]["pdf"])
