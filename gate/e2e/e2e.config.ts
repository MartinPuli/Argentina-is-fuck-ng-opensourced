import { randomBytes } from 'node:crypto';
import type { E2EConfig } from 'e2e';
import { secrets } from 'e2e';
import { web } from '@e2e-dev/web';

// One random credential per run, shared only with the disposable local server.
process.env.GATE_STAFF_USERNAME ||= 'browser-checker';
process.env.GATE_STAFF_PASSWORD ||= randomBytes(24).toString('hex');

export default {
  projectId: 'publication-gate-pdfs',
  tests: 'tests/**/*.e2e.ts',
  workers: 1,
  retries: 0,
  trace: 'on',
  reporters: ['list', 'markdown', 'junit'],
  secrets: { staffPassword: process.env.GATE_STAFF_PASSWORD },
  targets: [{
    name: 'chromium',
    engine: web({ basicAuth: { username: process.env.GATE_STAFF_USERNAME, password: secrets.get('staffPassword') } }),
    app: {
      url: 'http://127.0.0.1:0',
      readyUrl: 'http://127.0.0.1:{port}/public',
      environment: 'test',
      command: {
        executable: '../.venv/bin/python',
        args: ['start_app.py', '--port', '{port}'],
        env: { GATE_STAFF_USERNAME: process.env.GATE_STAFF_USERNAME, GATE_STAFF_PASSWORD: process.env.GATE_STAFF_PASSWORD },
        log: '.e2e/app.log',
      },
    },
  }],
} satisfies E2EConfig;
