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
  await expect(browser).toHaveURL(/\/live$/);
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
  await expect(browser).toHaveURL(/\/live$/);
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
