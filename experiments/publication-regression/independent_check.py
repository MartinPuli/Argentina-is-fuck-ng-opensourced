# SPDX-License-Identifier: MIT
"""Independent byte-level assertions over fresh loopback responses from run_case.

Run: PYTHONDONTWRITEBYTECODE=1 python3 -B independent_check.py
Uses orchestration/client transport only; never reads builder metrics/check_case.
"""
import base64
import hashlib
import json
import os
from pathlib import Path
import sys

os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
sys.dont_write_bytecode = True
from run_experiment import run_case

HERE = Path(__file__).resolve().parent


def hash_bytes(value):
    return hashlib.sha256(value).hexdigest()


def fixture():
    return {
        'case_id': 'independent-unicode-aliases-oct09',
        'fictional_data': True,
        'sources': [
            {'id': 'ind-public-ñ-731', 'source_path': 'original/aviso público.source',
             'classification': 'public', 'content': 'Aviso público ficticio: acción habilitada.\n',
             'artifact_paths': ['avisos/edición única.txt', 'aliases/public copy.txt', 'mirror/aviso.json']},
            {'id': 'ind-public-742', 'source_path': 'original/small.source',
             'classification': 'public', 'content': '{}\n',
             'artifact_paths': ['datos/resumen público.json']},
            {'id': 'ind-private-753', 'source_path': 'reservado/pequeño.source',
             'classification': 'private', 'content': 'SYNTHETIC_PRIVATE_SHORT_753\nñ\n',
             'private_marker': 'SYNTHETIC_PRIVATE_SHORT_753',
             'artifact_paths': ['cache/nombre público.css', 'media/última copia.bin']},
            {'id': 'ind-private-764', 'source_path': 'reservado/grande.source',
             'classification': 'private',
             'content': 'SYNTHETIC_PRIVATE_LONG_764\n' + ('dato ficticio de tamaño variable; ' * 73) + '\n',
             'private_marker': 'SYNTHETIC_PRIVATE_LONG_764',
             'artifact_paths': ['adjuntos/archivo número 764.dat']},
        ],
        'probe_paths': ['ausente/no existe.txt', 'other/未知.txt'],
    }


def main():
    data = fixture()
    policy = json.loads((HERE / 'lesson-policy.json').read_text())
    raw = run_case(data, policy)  # Creates four actual loopback servers and HTTP clients.
    private = {p: s['content'].encode() for s in data['sources']
               if s['classification'] == 'private' for p in s['artifact_paths']}
    public = {p: s['content'].encode() for s in data['sources']
              if s['classification'] == 'public' for p in s['artifact_paths']}
    known_private = [s for s in data['sources'] if s['classification'] == 'private']
    expected_paths = set(private) | set(public) | set(data['probe_paths'])
    first_public = next(s for s in data['sources'] if s['classification'] == 'public')
    checks = []
    observed = {}

    def check(name, value):
        checks.append({'name': name, 'passed': bool(value)})

    cases = {name: value['http']['observations'] for name, value in raw['conditions'].items()}
    cases['misclassification_counterexample'] = raw['misclassification_counterexample']['http']['observations']
    for name, items in cases.items():
        check(name + ': exact request path set', len(items) == len(expected_paths)
              and {item['path'] for item in items} == expected_paths)
        records = []
        for item in items:
            path, status = item['path'], item['status']
            body = base64.b64decode(item['body_base64'], validate=True)
            matches = [s['id'] for s in known_private
                       if s['private_marker'].encode() in body or s['content'].encode() in body]
            records.append({'path': path, 'status': status, 'body_bytes': len(body),
                            'body_sha256': hash_bytes(body), 'body_base64': item['body_base64'],
                            'independently_detected_private_ids': matches})
            if name in ('baseline', 'source_only_fix') and path in private:
                check(name + ': private exact bytes: ' + path, status == 200 and body == private[path])
            elif path in private:
                check(name + ': private path denied: ' + path, status == 404)
            if path in public:
                expected = public[path]
                if name == 'misclassification_counterexample' and path in first_public['artifact_paths']:
                    expected += known_private[0]['content'].encode()
                check(name + ': public exact bytes: ' + path, status == 200 and body == expected)
            if path in data['probe_paths']:
                check(name + ': missing path: ' + path, status == 404)
            if name == 'approved_release_gate':
                check(name + ': no known private bytes: ' + path, not matches)
        exposed = [r for r in records if r['independently_detected_private_ids']]
        if name in ('baseline', 'source_only_fix'):
            check(name + ': exact exposed set', {r['path'] for r in exposed} == set(private))
        if name == 'misclassification_counterexample':
            check(name + ': known private bytes exposed through public aliases',
                  {r['path'] for r in exposed} == set(first_public['artifact_paths']))
        observed[name] = {'requests': len(records), 'private_exposing_responses': len(exposed),
                          'observations': records}
    names = ['independent_check.py', 'publisher.py', 'serve_local.py', 'verify_http.py',
             'run_experiment.py', 'lesson-policy.json']
    result = {
        'schema_version': 1, 'experiment': 'independent-publication-byte-check',
        'license': 'CC-BY-4.0', 'network_scope': '127.0.0.1 only; real HTTP GETs',
        'independence': 'New fixture and byte-level oracle; reuses run_case and its HTTP transport. Does not call check_case or use reported metrics/private_matches/public_exact_success.',
        'limitations': 'One synthetic fixture; no production deployment, security proof, automatic learning, or prevention of false owner classifications.',
        'fixture': data, 'fixture_utf8_payload_bytes': {s['id']: len(s['content'].encode()) for s in data['sources']},
        'source_file_sha256': {name: hash_bytes((HERE / name).read_bytes()) for name in names},
        'conditions': observed, 'checks': checks,
        'checks_passed': sum(c['passed'] for c in checks), 'checks_total': len(checks),
        'all_passed': all(c['passed'] for c in checks),
    }
    (HERE / 'independent-check-results.json').write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps({'all_passed': result['all_passed'], 'checks_passed': result['checks_passed'],
                      'checks_total': result['checks_total'], 'conditions': {
                          name: {k: v for k, v in value.items() if k != 'observations'}
                          for name, value in observed.items()}}, indent=2))
    if not result['all_passed']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
