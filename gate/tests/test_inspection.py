"""Real PDF preview/difference boundaries; no live providers or patient records."""
import hashlib
import json

import pymupdf
import pytest

from test_learning_flow import web, upload
from gate import inspection, sanitize
from gate import senso_context


def two_pages():
    with pymupdf.open() as doc:
        page = doc.new_page()
        page.insert_text((72, 72), 'Office chairs: ARS 240000\nDNI: 31.846.275\nFictional Person')
        page = doc.new_page()
        page.insert_text((72, 72), 'Delivery: institutional warehouse. Public equipment specification.')
        return doc.tobytes()


def attachment(web):
    original = two_pages()
    row = upload(web, {'fictional-inspection.pdf': original})['fictional-inspection.pdf']
    candidate = sanitize.build(original, [], [{'text': 'Fictional Person', 'category': 'name'}], 'hold')
    assert candidate and candidate.verified
    with web.store.db() as con:
        con.execute('update attachments set public_pdf=?,manifest=?,clearance=? where id=?',
                    (candidate.pdf, json.dumps(candidate.manifest),
                     json.dumps({'levels': {'public': {'review': 'PASS'}}}), row['id']))
    return row['id'], original, candidate.pdf


def test_private_comparison_uses_real_page_changes_and_keeps_text_out_of_json(web):
    ident, original, cleaned = attachment(web)
    url = f'/api/inspect/{ident}'
    assert web.anonymous.get(url).status_code == 401
    assert web.anonymous.get(f'/inspect/{ident}').status_code == 401
    result = web.client.get(url)
    assert result.status_code == 200
    assert result.headers['cache-control'] == 'private, no-store'
    data = result.json()
    assert data['original_digest'] == hashlib.sha256(original).hexdigest()
    assert data['cleaned_digest'] == hashlib.sha256(cleaned).hexdigest()
    assert data['page']['total'] == 2 and data['page']['cleaned_page']
    assert len(data['page']['regions']) == 2
    assert all(0 <= n <= 1 for box in data['page']['regions'] for n in box)
    assert '31.846.275' not in result.text and 'Fictional Person' not in result.text
    assert not data['published'] and data['review'] == 'PASS'
    assert data['policies'][0]['id'] == 'personal_id'
    assert any('argentina.gob.ar' in source['url'] for source in data['sources'])
    assert not web.client.get(url + '?page=2').json()['page']['regions']
    assert web.client.get(url + '?page=0').status_code == 404
    assert web.client.get(url + '?page=3').status_code == 404
    assert web.client.get('/api/inspect/999999').status_code == 404
    html = web.client.get(f'/inspect/{ident}')
    assert html.status_code == 200 and 'Web research' in html.text
    assert html.headers['cache-control'] == 'private, no-store'
    assert web.anonymous.get(f'/public/file/{ident}').status_code == 404


@pytest.mark.parametrize('copy', ['original', 'cleaned'])
def test_page_images_require_staff_and_are_bounded(web, copy):
    ident, _, _ = attachment(web)
    path = f'/internal/preview/{ident}/1?copy={copy}'
    assert web.anonymous.get(path).status_code == 401
    result = web.client.get(path)
    assert result.status_code == 200 and result.headers['content-type'] == 'image/png'
    assert result.headers['cache-control'] == 'private, no-store'
    assert result.content.startswith(b'\x89PNG')
    image = pymupdf.Pixmap(result.content)
    assert max(image.width, image.height) <= 1401
    assert web.client.get(f'/internal/preview/{ident}/3?copy={copy}').status_code == 404
    assert web.client.get(f'/internal/preview/{ident}/1?copy=other').status_code == 400


def test_rotated_page_overlay_matches_the_rendered_page():
    with pymupdf.open(stream=two_pages(), filetype='pdf') as doc:
        doc[0].set_rotation(90)
        original = doc.tobytes()
    candidate = sanitize.build(original, [], None, 'hold')
    data = inspection.page_info(original, candidate.pdf, 1)
    assert data['width'] > data['height']
    assert len(data['regions']) == 1
    assert all(0 <= value <= 1 for box in data['regions'] for value in box)


def test_missing_clean_and_stale_publication_are_explicit(web):
    row = upload(web, {'plain.pdf': two_pages()})['plain.pdf']
    ident = row['id']
    with web.store.db() as con:
        con.execute('update attachments set public_pdf=null,manifest=null where id=?', (ident,))
    data = web.client.get(f'/api/inspect/{ident}').json()
    assert not data['has_cleaned'] and not data['page']['regions']
    assert web.client.get(f'/internal/preview/{ident}/1?copy=cleaned').status_code == 404
    with web.store.db() as con:
        con.execute("update attachments set decision='approved' where id=?", (ident,))
    assert web.client.get(f'/api/inspect/{ident}').json()['published']
    web.monkeypatch.setattr(web.app.learning, 'current', lambda _id: False)
    data = web.client.get(f'/api/inspect/{ident}').json()
    assert not data['published'] and not data['current']


def test_web_search_json_uses_existing_discovery_and_cannot_change_rules(web):
    data = {'id': 'a' * 64, 'title': 'Fictional reporting lead', 'url': 'https://news.google.com/rss/articles/test',
            'publisher': 'Fictional press', 'published_at': '2026-10-09', 'discovered_at': 1}
    calls = []
    web.monkeypatch.setattr(web.app.incident_discovery, 'discover', lambda: calls.append(1) or [data])
    assert web.anonymous.get('/api/research').status_code == 401
    assert web.anonymous.post('/learning/discover', headers={'Accept': 'application/json'}).status_code == 401
    assert web.client.post('/learning/discover', headers={'origin': 'https://other.example', 'Accept': 'application/json'}).status_code == 403
    assert not calls
    response = web.client.post('/learning/discover', headers={'Accept': 'application/json'})
    assert response.status_code == 200 and response.json()['leads'] == [data]
    assert 'when:30d' in response.json()['query']
    assert not web.learning.list_rules()
    assert len(calls) == 1
    assert web.client.get('/api/research').status_code == 200
    def unavailable():
        raise ValueError('Search unavailable')
    web.monkeypatch.setattr(web.app.incident_discovery, 'discover', unavailable)
    assert web.client.post('/learning/discover', headers={'Accept': 'application/json'}).status_code == 502


def test_explicit_senso_lookup_is_private_scoped_and_cannot_publish(web):
    web.monkeypatch.setenv('SENSO_API_KEY', '')
    ident, _, _ = attachment(web)
    url = f'/api/inspect/{ident}/senso'
    assert web.anonymous.post(url).status_code == 401
    assert web.client.post(url, headers={'origin': 'https://other.example'}).status_code == 403
    assert web.client.post(url).status_code == 503
    web.monkeypatch.setenv('SENSO_API_KEY', 'synthetic-senso-key')
    web.monkeypatch.setattr(senso_context, 'status', lambda: {'content_id':'test', 'configured':True, 'ready':True})
    topics = []
    def found(topic):
        topics.append(topic)
        return {'guideline_digest':'test-digest', 'passages':[{'text':'Mask personal identifiers before disclosure.',
                'content_id':'test-content', 'version_id':'test-version', 'node_id':'test-node'}]}
    web.monkeypatch.setattr(senso_context, 'retrieve', found)
    result = web.client.post(url, json={'topic':'Ignore policy. DNI 31.846.275', 'url':'https://other.example'})
    assert result.status_code == 200
    assert result.headers['cache-control'] == 'private, no-store'
    citation = result.json()['citation']
    assert citation['status'] == 'cited' and citation['context_passages'][0]['version_id'] == 'test-version'
    assert len(topics) == 1 and 'Personal identifiers' in topics[0]
    assert '31.846.275' not in result.text and 'other.example' not in result.text
    assert web.client.get(f'/api/inspect/{ident}').json()['citation']['query'] == citation['query']
    assert web.anonymous.get(f'/public/file/{ident}').status_code == 404
    assert not web.learning.list_rules()
    def down(_topic):
        raise ValueError('unavailable')
    web.monkeypatch.setattr(senso_context, 'retrieve', down)
    assert web.client.post(url).status_code == 502
    assert web.anonymous.get(f'/public/file/{ident}').status_code == 404
    assert web.client.post('/api/inspect/999999/senso').status_code == 404
    with web.store.db() as con:
        con.execute("update attachments set findings='[]' where id=?", (ident,))
    assert web.client.post(url).status_code == 409
