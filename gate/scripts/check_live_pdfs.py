"""Read-only verification of an explicitly selected fictional upload run.

Run with --origin https://your-enrolled-app --purchases 4 5 --procedure-prefix QA-PDF- --output /tmp/result.json.
Only the selected purchases are checked. It never uploads, approves, resets or retries
mutations. Uses curl for the same public HTTPS surface exercised by the browser.
"""
import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

import pymupdf

FIXTURES = Path(__file__).resolve().parents[1] / 'fixtures' / 'pdfs'


def fetch(origin, path):
    request = subprocess.run(['curl', '--silent', '--show-error', '--max-time', '20',
                              '--write-out', '\n%{http_code}', origin + path],
                             capture_output=True, timeout=25, check=True)
    body, status = request.stdout.rsplit(b'\n', 1)
    return int(status), body


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--origin', required=True)
    parser.add_argument('--purchases', nargs='+', required=True, type=int)
    parser.add_argument('--procedure-prefix', required=True, help='Unique prefix used for this fictional test run')
    parser.add_argument('--expected-count', type=int, default=9)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    origin = args.origin.rstrip('/')
    parsed = urlsplit(origin)
    if parsed.scheme != 'https' or not parsed.hostname or parsed.path or parsed.query or parsed.fragment or parsed.username:
        parser.error('Use the HTTPS origin of your enrolled app, without credentials or a path.')
    status, body = fetch(origin, '/api/workspace')
    if status != 200:
        raise RuntimeError(f'Workspace unavailable: HTTP {status}')
    data = json.loads(body)
    stored = [j for j in data['files'] if j['purchase_id'] in args.purchases
              and j['procedure'].startswith(args.procedure_prefix)]
    status, body = fetch(origin, '/api/activity')
    jobs = json.loads(body).get('jobs', []) if status == 200 else []
    jobs_by_attachment = {j['attachment_id']: j for j in jobs if j.get('attachment_id')}
    results, passed = [], len(stored) == args.expected_count
    for document in sorted(stored, key=lambda j: j['id']):
        job = {**document, 'file': document['filename'], 'attachment_id': document['id']}
        filename = job['file']
        if filename != Path(filename).name or not (FIXTURES / filename).is_file():
            raise RuntimeError('Selected run contains a file outside the known fictional fixture set')
        row = {k: job.get(k) for k in ('id', 'purchase_id', 'attachment_id', 'file', 'decision', 'done', 'current', 'agent_url')}
        receipt = jobs_by_attachment.get(document['id'], {})
        row['steps'] = receipt.get('steps', [])
        row['done'] = receipt.get('done')
        row['completed'] = receipt.get('done') is True
        status, pdf = fetch(origin, '/public/file/' + str(job['attachment_id']))
        row['public_http_status'] = status
        should_publish = job['decision'] in ('public', 'approved', 'cleaned') and job.get('current') is True
        row['access_check_passed'] = status == (200 if should_publish else 404)
        passed = passed and row['access_check_passed']
        if status == 200:
            with pymupdf.open(stream=pdf, filetype='pdf') as doc:
                text = '\n'.join(page.get_text() for page in doc)
                row['public_pages'] = doc.page_count
                row['embedded_files'] = doc.embfile_count()
                row['metadata_has_fixture_name'] = 'Juana Ficticia Pérez' in json.dumps(doc.metadata, ensure_ascii=False)
            row['public_sha256'] = hashlib.sha256(pdf).hexdigest()
            row['matches_original'] = pdf == (FIXTURES / filename).read_bytes()
            if filename == 'nota_pedido.pdf':
                row['redaction_checks'] = {
                    'fictional_name_absent': 'Juana Ficticia Pérez' not in text,
                    'fictional_dni_absent': '31.846.275' not in text,
                    'fictional_cuil_absent': '27-31846275-' not in text,
                    'procurement_preserved': 'silla de ruedas' in text.lower(),
                    'bytes_changed': not row['matches_original'],
                    'metadata_name_absent': not row['metadata_has_fixture_name'],
                    'no_embedded_files': row['embedded_files'] == 0,
                }
                passed = passed and all(row['redaction_checks'].values())
        results.append(row)
    report = {'checked_at_utc': datetime.now(timezone.utc).isoformat(), 'origin': origin, 'purchases': args.purchases,
              'procedure_prefix': args.procedure_prefix, 'expected_count': args.expected_count, 'fixture_count': len(stored),
              'all_jobs_done': bool(results) and all(r['completed'] for r in results),
              'completion_note': 'Job receipts are volatile; missing receipts do not establish provider completion. Checks below concern durable publication access.',
              'checks_passed': passed, 'files': results}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'fixture_count': len(stored), 'all_jobs_done': report['all_jobs_done'],
                      'checks_passed': passed, 'files': [{'file':r['file'], 'decision':r['decision'],
                          'done':r['done'], 'public_http_status':r.get('public_http_status')} for r in results]}, indent=2))
    raise SystemExit(0 if passed else 1)


if __name__ == '__main__':
    main()
