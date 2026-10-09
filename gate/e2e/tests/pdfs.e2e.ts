import { readdirSync, readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { test } from '@e2e-dev/web';
import { expect } from 'e2e';

const fixtureDirectory = resolve('../fixtures/pdfs');
const files = readdirSync(fixtureDirectory).filter(name => name.endsWith('.pdf')).sort();

for (const filename of files) {
  test(`PDF stays private before review: ${filename}`, async ({ app, screen, browser }) => {
    const procedure = `QA-E2E-${Date.now()}-${filename}`;
    await app.open('/office');
    await expect(screen.getByRole('heading', 'Upload')).toBeVisible();
    await screen.getByLabel('Procedure reference').fill(procedure);
    await screen.getByLabel('Amount in ARS').fill('1');
    await screen.getByLabel('Item being purchased').fill('Fictional browser verification');
    await screen.getByLabel('Supporting attachments').setInputFiles([resolve(fixtureDirectory, filename)]);
    await screen.getByRole('button', 'Check files').tap();
    await expect(browser).toHaveURL(/\/purchase\/\d+$/);
    await expect(screen.getByRole('heading', filename)).toBeVisible();

    const id = await screen.getByRole('article').getAttribute('id');
    expect(id).toMatch(/^file-\d+$/);
    const attachmentId = id!.slice(5);
    const publicResponse = await fetch(new URL(`/public/file/${attachmentId}`, app.baseUrl));
    expect(publicResponse.status).toBe(404);
    const original = await fetch(new URL(`/internal/file/${attachmentId}`, app.baseUrl));
    expect(original.status).toBe(401);
    const snapshot = await browser.evaluate(async () => (await fetch('/api/workspace')).json());
    const stored = snapshot.files.find((row: { id: number }) => row.id === Number(attachmentId));
    expect(stored.filename).toBe(filename);
    expect(stored.procedure).toBe(procedure);
    expect(['hold', 'withheld']).toContain(stored.decision);
    if (['nota_pedido.pdf', 'justificacion_medica.pdf'].includes(filename)) expect(stored.decision).toBe('withheld');
    await app.screenshot(`private-${filename}`);
  });
}

for (const reviewPage of ['/review', '/live']) {
test(`an inspected benign PDF publishes with exact bytes via ${reviewPage}`, async ({ app, screen, browser }) => {
  const filename = 'especificacion_tecnica_silla.pdf';
  const procedure = `QA-E2E-REVIEW-${Date.now()}`;
  await app.open('/office');
  await screen.getByLabel('Procedure reference').fill(procedure);
  await screen.getByLabel('Amount in ARS').fill('1');
  await screen.getByLabel('Item being purchased').fill(procedure);
  await screen.getByLabel('Supporting attachments').setInputFiles([resolve(fixtureDirectory, filename)]);
  await screen.getByRole('button', 'Check files').tap();
  await expect(browser).toHaveURL(/\/purchase\/\d+$/);
  const purchaseUrl = await browser.url();
  const id = await screen.getByRole('article').getAttribute('id');
  const attachmentId = id!.slice(5);
  await app.open(reviewPage);
  const panel = browser.locator(reviewPage === '/review' ? 'details.review-panel' : 'details.live-review').filter({ hasText: procedure });
  await panel.getByRole('heading', filename).tap();
  await panel.getByLabel('Decision reason').fill('Inspected fictional equipment specification; no patient data.');
  const unsubscribe = await browser.onDialog('accept');
  await panel.getByRole('button', reviewPage === '/review' ? 'Publish original' : 'Approve publication ↗').tap();
  if (reviewPage === '/review') {
    await expect(screen.getByRole('cell', 'Inspected fictional equipment specification; no patient data.')).toBeVisible();
  } else {
    await expect(panel).toHaveCount(0);
  }
  await expect.poll(async () => (await fetch(new URL(`/public/file/${attachmentId}`, app.baseUrl))).status).toBe(200);
  await unsubscribe();
  const published = await fetch(new URL(`/public/file/${attachmentId}`, app.baseUrl));
  expect(published.status).toBe(200);
  expect(Buffer.from(await published.arrayBuffer()).equals(readFileSync(resolve(fixtureDirectory, filename)))).toBe(true);
  await app.open(purchaseUrl);
  await expect(screen.getByRole('link', 'Public PDF ↗')).toBeVisible();
});
}
