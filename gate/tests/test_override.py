"""Humans audit automatic restrictions afterward and can release them. Never a deterministic block.

Offline: every PDF is a fictional fixture; no model or Guild call is made.
"""

import json

import pytest

from test_gate import PDFS, STAFF, add_attachment, offline_environment, web  # noqa: F401  (fixtures)

CLEANED = b"%PDF-1.4 fictional cleaned copy"
HOLD_FINDING = {"kind": "model_context", "label": "Model flagged context risk", "evidence": "",
                "page": 0, "severity": "review", "rule": "reidentification"}
BLOCK_FINDING = {"kind": "dni", "label": "National ID", "evidence": "31.***.275",
                 "page": 1, "severity": "block", "rule": "identifiers"}


@pytest.fixture
def auto(web, monkeypatch):
    monkeypatch.setenv("GATE_AUTONOMOUS", "1")
    return web


def restricted(web, findings, public_pdf=None):
    """A held row settled by the autopilot, exactly as settle() leaves it."""
    att_id, original = add_attachment(web, "hold", public_pdf=public_pdf)
    with web.store.db() as con:
        con.execute("update attachments set findings=?, reasons=? where id=?",
                    (json.dumps(findings), json.dumps(["Needs a person."]), att_id))
    assert web.app.settle(att_id)
    return att_id, original


def row(web, att_id):
    with web.store.db() as con:
        return dict(con.execute("select * from attachments where id=?", (att_id,)).fetchone())


def release(web, att_id, note="Inspected: no personal data.", action="release", **kwargs):
    return web.client.post(f"/review/{att_id}/release", data={"action": action, "note": note},
                           follow_redirects=False, **kwargs)


def test_release_publishes_the_cleaned_copy(auto):
    att_id, original = restricted(auto, [HOLD_FINDING], public_pdf=CLEANED)
    assert auto.anonymous.get(f"/public/file/{att_id}").status_code == 404
    review = auto.client.get("/review").text
    assert "Restricted automatically" in review and f"/review/{att_id}/release" in review
    assert f"/internal/clean/{att_id}" in review

    assert release(auto, att_id).status_code == 303
    stored = row(auto, att_id)
    assert stored["decision"] == "approved" and stored["reviewed_by"] == STAFF[0]
    assert stored["review_note"] == "Inspected: no personal data." and stored["reviewed_at"]
    served = auto.anonymous.get(f"/public/file/{att_id}")
    assert served.status_code == 200 and served.content == CLEANED and served.content != original
    with auto.store.db() as con:
        assert con.execute("select count(*) from events where event='released' and actor=?"
                           " and attachment_id=?", (STAFF[0], att_id)).fetchone()[0] == 1
    assert f"/review/{att_id}/release" not in auto.client.get("/review").text
    assert release(auto, att_id).status_code == 409  # one decision per restriction


def test_release_without_cleaned_copy_serves_the_original(auto):
    att_id, original = restricted(auto, [HOLD_FINDING])
    assert release(auto, att_id).status_code == 303
    served = auto.anonymous.get(f"/public/file/{att_id}")
    assert served.status_code == 200 and served.content == original


def test_release_requires_a_reason(auto):
    att_id, _ = restricted(auto, [HOLD_FINDING])
    for note in ("", "   "):
        assert release(auto, att_id, note=note).status_code == 400
    assert release(auto, att_id, action="approve").status_code == 400
    assert row(auto, att_id)["decision"] == "withheld"
    assert auto.anonymous.get(f"/public/file/{att_id}").status_code == 404


def test_block_finding_is_never_releasable(auto):
    att_id, _ = restricted(auto, [HOLD_FINDING, BLOCK_FINDING])
    assert any(f["kind"] == "autopilot_restricted" for f in json.loads(row(auto, att_id)["findings"]))
    assert f"/review/{att_id}/release" not in auto.client.get("/review").text
    assert release(auto, att_id).status_code == 409
    assert release(auto, att_id, action="keep").status_code == 409
    assert row(auto, att_id)["decision"] == "withheld"
    assert auto.anonymous.get(f"/public/file/{att_id}").status_code == 404


def test_plain_withheld_is_not_releasable(auto):
    att_id, _ = add_attachment(auto, "withheld")
    assert release(auto, att_id).status_code == 409
    assert auto.anonymous.get(f"/public/file/{att_id}").status_code == 404


def test_stale_rule_revision_is_rejected(auto, monkeypatch):
    att_id, _ = restricted(auto, [HOLD_FINDING])
    monkeypatch.setattr(auto.app.learning, "current", lambda _att_id: False)
    review = auto.client.get("/review").text
    assert "Rules changed since this file was checked" in review
    assert release(auto, att_id).status_code == 409
    assert row(auto, att_id)["decision"] == "withheld" and row(auto, att_id)["reviewed_by"] is None


def test_keep_private_records_the_reviewer(auto):
    att_id, _ = restricted(auto, [HOLD_FINDING])
    assert release(auto, att_id, note="Patient context is too specific.", action="keep").status_code == 303
    stored = row(auto, att_id)
    assert stored["decision"] == "withheld" and stored["reviewed_by"] == STAFF[0]
    assert stored["review_note"] == "Patient context is too specific."
    assert auto.anonymous.get(f"/public/file/{att_id}").status_code == 404
    assert f"/review/{att_id}/release" not in auto.client.get("/review").text


def test_cross_origin_release_is_blocked(auto):
    att_id, _ = restricted(auto, [HOLD_FINDING])
    response = release(auto, att_id, headers={"origin": "https://evil.example"})
    assert response.status_code == 403
    assert row(auto, att_id)["decision"] == "withheld"
    assert auto.anonymous.get(f"/public/file/{att_id}").status_code == 404
