import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { test } from '@e2e-dev/web';
import { expect } from 'e2e';

const sample = resolve('../fixtures/pdfs/fictional_patient.pdf');

test('Choosing a PDF starts analysis with no purchase fields', async ({ app, screen, browser }) => {
  await app.open('/office');
  await expect(screen.getByRole('heading', 'Drop PDFs here')).toBeVisible();
  await expect(screen.getByLabel('Procedure reference')).not.toBeVisible();
  await app.screenshot('file-first-upload');
  await screen.getByLabel('PDF files', { exact: true }).setInputFiles([sample]);
  await expect(browser).toHaveURL(/\/$/);
  await expect(browser.locator('#live-jobs')).toContainText('fictional_patient.pdf');
  await expect.poll(async () => {
    const snapshot = await browser.evaluate(async () => (await fetch('/api/workspace')).json());
    return snapshot.files.find((row: { filename: string }) => row.filename === 'fictional_patient.pdf')?.decision;
  }).toBe('withheld');
});

test('Dropping a PDF on the home page queues it without a submit button', async ({ app, browser }) => {
  await app.open('/');
  const filename = `drop-${Date.now()}.pdf`;
  const payload = { filename, bytes: Array.from(readFileSync(sample)) };
  await browser.evaluate(({filename, bytes}) => {
    const transfer = new DataTransfer();
    transfer.items.add(new File([new Uint8Array(bytes)], filename, {type: 'application/pdf'}));
    document.body.dispatchEvent(new DragEvent('dragenter', {bubbles: true, cancelable: true, dataTransfer: transfer}));
    document.body.dispatchEvent(new DragEvent('drop', {bubbles: true, cancelable: true, dataTransfer: transfer}));
  }, payload);
  await expect(browser).toHaveURL(/\/$/);
  await expect.poll(async () => {
    const snapshot = await browser.evaluate(async () => (await fetch('/api/workspace')).json());
    return snapshot.files.find((row: {filename: string}) => row.filename === filename)?.decision;
  }).toBe('withheld');
  const saved = await browser.evaluate(async () => (await fetch('/api/workspace')).json());
  const row = saved.files.find((row: {filename: string}) => row.filename === filename);
  expect((await fetch(new URL(`/public/file/${row.id}`, app.baseUrl))).status).toBe(404);
  await app.open(`/purchase/${row.purchase_id}`);
  // Private extracted hints are readable but never copied to public purchase fields.
  await browser.locator('.intake-details > summary').tap();
  await expect(browser.locator('.intake-details')).toContainText('TEST-PDF-2026-001');
});

test('An invalid drop shows an inline error and leaves the workspace unchanged', async ({ app, screen, browser }) => {
  await app.open('/office');
  const before = await browser.evaluate(async () => (await fetch('/api/workspace')).json());
  await browser.evaluate(() => {
    const transfer = new DataTransfer();
    transfer.items.add(new File(['not a PDF'], 'notes.txt', {type: 'text/plain'}));
    document.body.dispatchEvent(new DragEvent('drop', {bubbles: true, cancelable: true, dataTransfer: transfer}));
  });
  await expect(screen.getByRole('alert')).toContainText('Choose 1 to 8 non-empty PDF files.');
  const after = await browser.evaluate(async () => (await fetch('/api/workspace')).json());
  expect(after.counts.total).toBe(before.counts.total);
});

test('Activity shows processing until the verdict and refreshes the document list', async ({ app, browser }) => {
  let finished = false;
  const counts = () => ({processing: finished ? 0 : 1, published: finished ? 1 : 0, blocked: finished ? 0 : 1, waiting: 0, stale: 0});
  await browser.route('**/api/activity', async route => {
    await route.fulfill({json: {counts: counts(), waiting: [], feed: [], jobs: [{id: 1001, purchase_id: 1001,
      attachment_id: 1001, file: 'fictional-status.pdf', office: 'Test office', decision: finished ? 'cleaned' : 'withheld',
      done: finished, current: true, steps: [], started: Date.now()/1000}]}});
  });
  await browser.route('**/api/workspace', async route => {
    await route.fulfill({json: {counts: {total: 1, published: finished ? 1 : 0, review: 0, blocked: finished ? 0 : 1, stale: 0},
      files: [{id: 1001, purchase_id: 1001, filename: 'fictional-status.pdf', office: 'Test office', procedure: 'TEST-STATUS',
        decision: finished ? 'cleaned' : 'withheld', current: true, created_at: Date.now()/1000}]}});
  });
  await app.open('/');
  await expect(browser.locator('#live-jobs')).toContainText('Checking');
  await expect(browser.locator('#live-jobs')).not.toContainText('Kept internal');
  await expect(browser.locator('#document-workspace')).toContainText('Private');
  finished = true;
  await expect(browser.locator('#live-jobs')).toContainText('Published, cleaned');
  await expect(browser.locator('#document-workspace .workspace-chip')).toContainText('Published, cleaned');
});
