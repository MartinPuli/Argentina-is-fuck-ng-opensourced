"""Check actual fixture uploads and publication boundaries in an isolated offline app.

Run from the repository root: gate/.venv/bin/python gate/scripts/check_pdfs.py
No provider credentials, external calls, existing databases or invented model answers.
"""
import hashlib
import json
import os
import secrets
import tempfile
from pathlib import Path

import dotenv
from fastapi.testclient import TestClient

FIXTURES = Path(__file__).resolve().parents[1] / 'fixtures' / 'pdfs'
EXPECTED = {'justificacion_medica.pdf': 'withheld', 'nota_pedido.pdf': 'withheld'}


def main():
    with tempfile.TemporaryDirectory(prefix='gate-pdf-check-') as folder:
        for name in ('AKASHML_API_KEY', 'GUILD_WORKSPACE', 'GUILD_AGENT', 'CLICKHOUSE_HOST'):
            os.environ[name] = ''
        os.environ['GATE_OPEN_DEMO'] = '0'
        os.environ['GATE_STAFF_USERNAME'] = 'pdf-checker'
        os.environ['GATE_STAFF_PASSWORD'] = secrets.token_urlsafe(24)
        os.environ['GATE_DB'] = str(Path(folder) / 'check.sqlite')
        # app.py must not load a deployment's .env and silently enable external calls.
        dotenv.load_dotenv = lambda *args, **kwargs: False
        from gate import app, store
        auth = (os.environ['GATE_STAFF_USERNAME'], os.environ['GATE_STAFF_PASSWORD'])
        results = []
        with TestClient(app.app, headers={'Origin': 'http://testserver'}) as client:
            client.auth = auth
            with TestClient(app.app) as anonymous:
                for pdf in sorted(FIXTURES.glob('*.pdf')):
                    original = pdf.read_bytes()
                    submitted = client.post('/office', data={
                        'office': 'Fictional verification office', 'procedure': 'QA-PDF-OFFLINE',
                        'item': 'Fictional procurement test', 'amount': '1',
                    }, files=[('files', (pdf.name, original, 'application/pdf'))], follow_redirects=False)
                    if submitted.status_code != 303:
                        raise RuntimeError(f'{pdf.name}: upload returned {submitted.status_code}')
                    with store.db() as con:
                        row = con.execute('select * from attachments order by id desc limit 1').fetchone()
                    expected = EXPECTED.get(pdf.name, 'hold')
                    if row['decision'] not in ('hold', 'withheld') or (pdf.name in EXPECTED and row['decision'] != expected):
                        raise RuntimeError(f'{pdf.name}: expected {expected}, got {row["decision"]}')
                    public = anonymous.get(f'/public/file/{row["id"]}')
                    internal = anonymous.get(f'/internal/file/{row["id"]}')
                    if public.status_code != 404 or internal.status_code != 401:
                        raise RuntimeError(f'{pdf.name}: access boundary failed')
                    result = {
                        'file': pdf.name, 'sha256': hashlib.sha256(original).hexdigest(),
                        'upload_status': submitted.status_code, 'decision': row['decision'],
                        'public_before_review': public.status_code, 'anonymous_original': internal.status_code,
                        'finding_types': sorted({f['kind'] for f in json.loads(row['findings'])}),
                        'cleaned_candidate_available': bool(row['public_pdf']),
                    }
                    # Exercise an actual human-review transition only for the inspected benign fixture.
                    if pdf.name == 'especificacion_tecnica_silla.pdf':
                        approved = client.post(f'/review/{row["id"]}', data={
                            'action': 'approve',
                            'note': 'Inspected the fictional equipment specification. No patient details in the fixture.',
                        }, follow_redirects=False)
                        published = anonymous.get(f'/public/file/{row["id"]}')
                        if approved.status_code != 303 or published.status_code != 200 or published.content != original:
                            raise RuntimeError('Benign reviewed file did not publish with its exact bytes')
                        result['reviewed_benign_public_status'] = published.status_code
                        result['reviewed_benign_bytes_match'] = True
                    results.append(result)
        print(json.dumps({'mode': 'offline_no_provider_mocks', 'sponsor_execution': False,
                          'fixture_count': len(results), 'checks_passed': True, 'files': results}, indent=2))


if __name__ == '__main__':
    main()
