"""Serve a disposable, authenticated app for browser tests; never load deployment secrets."""
import argparse
import os
import tempfile
from pathlib import Path

import dotenv
import uvicorn

parser = argparse.ArgumentParser()
parser.add_argument('--port', type=int, required=True)
args = parser.parse_args()
for key in ('AKASHML_API_KEY', 'GUILD_WORKSPACE', 'GUILD_AGENT', 'GUILD_VERIFIER_AGENT', 'CLICKHOUSE_HOST', 'SENSO_API_KEY'):
    os.environ[key] = ''
os.environ['GATE_OPEN_DEMO'] = '0'
dotenv.load_dotenv = lambda *args, **kwargs: False
with tempfile.TemporaryDirectory(prefix='gate-browser-check-') as folder:
    os.environ['GATE_DB'] = str(Path(folder) / 'test.sqlite')
    uvicorn.run('gate.app:app', host='127.0.0.1', port=args.port)
