"""File-only intake: automatic checks without making PDF metadata public."""
import json
from pathlib import Path

from test_learning_flow import web, pdf
from gate import intake

SAMPLE = Path(__file__).parents[1] / "fixtures/pdfs/fictional_patient.pdf"


def test_detect_explicit_labels_and_keep_unknowns_absent():
    hints = intake.details([("test.pdf", SAMPLE.read_bytes())])
    assert hints[0]["fields"] == {"office": "UGL VI Capital Federal", "procedure": "TEST-PDF-2026-001",
        "item": "Motorized wheelchair", "amount": "ARS 4.850.000"}
    assert hints[0]["page"] == 1
    assert intake.details([("no-labels.pdf", pdf("A fictional unlabeled document. No purchase amount is specified."))]) == []


def synchronous_queue(web):
    def queue(purchase, item, uploads, actor):
        for filename, body in uploads:
            web.app.process_live(purchase, filename, body, None)
    web.monkeypatch.setattr(web.app, "queue_live", queue)


def test_only_pdf_required_checks_identifiers_and_keeps_inferred_metadata_private(web):
    synchronous_queue(web)
    response = web.client.post('/documents/upload', files={"files": ("test.pdf", SAMPLE.read_bytes(), "application/pdf")},
                               headers={"Accept": "application/json"})
    assert response.status_code == 202, response.text
    pid = response.json()["purchase_id"]
    assert response.json()["location"] == "/live"
    with web.store.db() as con:
        purchase = con.execute("select * from purchases where id=?", (pid,)).fetchone()
        attachment = con.execute("select * from attachments where purchase_id=?", (pid,)).fetchone()
    assert purchase["amount"] is None
    assert purchase["office"] == "Unassigned"
    assert purchase["procedure"].startswith("UPLOAD-")
    assert json.loads(purchase["intake_details"])[0]["fields"]["procedure"] == "TEST-PDF-2026-001"
    assert attachment["decision"] == "withheld"
    assert any(f["kind"] == "dni" for f in json.loads(attachment["findings"]))
    assert web.anonymous.get(f'/public/file/{attachment["id"]}').status_code == 404
    assert web.anonymous.get(f'/purchase/{pid}').status_code == 401
    detail = web.client.get(f'/purchase/{pid}')
    assert detail.status_code == 200
    assert "TEST-PDF-2026-001" in detail.text and "Staff only" in detail.text
    assert "TEST-PDF-2026-001" not in web.anonymous.get('/public').text
    assert "intake_details" not in web.client.get('/api/workspace').text


def test_intake_validation_auth_and_same_origin_before_persistence(web):
    data = {"files": ("test.pdf", SAMPLE.read_bytes(), "application/pdf")}
    assert web.anonymous.post('/documents/upload', files=data).status_code == 401
    assert web.client.post('/documents/upload', files=data, headers={"origin": "https://other.example"}).status_code == 403
    assert web.client.post('/documents/upload', files={"files": ("bad.pdf", b'not a PDF')}).status_code == 400
    assert web.client.post('/documents/upload').status_code == 422
    with web.store.db() as con:
        assert con.execute('select count(*) from purchases').fetchone()[0] == 0


def test_queue_full_creates_no_purchase(web):
    def full(_count):
        from fastapi import HTTPException
        raise HTTPException(503, 'The live queue is full. Wait and retry.')
    web.monkeypatch.setattr(web.app, 'reserve_live', full)
    response = web.client.post('/documents/upload', files={"files": ("test.pdf", SAMPLE.read_bytes())})
    assert response.status_code == 503
    with web.store.db() as con:
        assert con.execute('select count(*) from purchases').fetchone()[0] == 0


def test_no_javascript_upload_and_sample_access(web):
    synchronous_queue(web)
    assert web.anonymous.get('/documents/sample.pdf').status_code == 401
    sample = web.client.get('/documents/sample.pdf')
    assert sample.status_code == 200 and sample.content == SAMPLE.read_bytes()
    response = web.client.post('/documents/upload', files={"files": ('test.pdf', sample.content)}, follow_redirects=False)
    assert response.status_code == 303 and response.headers['location'] == '/live'
    assert 'data-pdf-intake' in web.client.get('/office').text
    for path in ['/', '/live']:  # Home drop is enabled without a second visible upload entry point.
        assert 'data-workspace-intake hidden' in web.client.get(path).text


def test_purchase_progress_is_authenticated_and_tracks_completion(web):
    synchronous_queue(web)
    response = web.client.post('/documents/upload', files={"files": ('test.pdf', SAMPLE.read_bytes())},
                               headers={"Accept": "application/json"})
    pid = response.json()['purchase_id']
    with web.store.db() as con:
        ident = con.execute('select id from attachments where purchase_id=?', (pid,)).fetchone()[0]
    job = {'purchase_id': pid, 'attachment_id': ident, 'done': False}
    web.monkeypatch.setattr(web.app.activity, 'snapshot', lambda: [job])
    url = f'/api/purchase/{pid}/status'
    assert web.anonymous.get(url).status_code == 401
    pending = web.client.get(url)
    assert pending.headers['cache-control'] == 'no-store'
    assert set(pending.json()) == {'processing', 'processing_ids', 'revision'}
    assert pending.json()['processing_ids'] == [ident]
    page = web.client.get(f'/purchase/{pid}')
    assert 'Processing' in page.text and 'not the final result' in page.text
    assert '<title>Purchase decisions</title>' in page.text
    assert pending.json()['revision'] == web.client.get(url).json()['revision']
    job['done'] = True
    finished = web.client.get(url).json()
    assert not finished['processing'] and finished['processing_ids'] == []
    assert pending.json()['revision'] != finished['revision']
    assert web.client.get('/api/purchase/999999/status').status_code == 404


def test_queued_purchase_progress_changes_when_worker_finishes(web):
    purchase = web.app.create_purchase('Test office', 'QA-STATUS', 'Office chairs', None)
    job = {'purchase_id': purchase['id'], 'attachment_id': None, 'done': False}
    web.monkeypatch.setattr(web.app.activity, 'snapshot', lambda: [job])
    pending = web.app.purchase_status(purchase['id'])
    assert pending['processing'] and pending['processing_ids'] == []
    assert web.client.get(f'/purchase/{purchase["id"]}').status_code == 200
    job['done'] = True
    assert web.app.purchase_status(purchase['id'])['revision'] != pending['revision']
