import { resolve } from 'node:path';
import { test } from '@e2e-dev/web';
import { expect } from 'e2e';

const sample = resolve('../fixtures/pdfs/inspection_purchase.pdf');

async function inspect(app: any, screen: any, browser: any) {
  await app.open('/office');
  await screen.getByLabel('PDF files', { exact: true }).setInputFiles([sample]);
  await expect(browser).toHaveURL(/\/$/);
  await expect.poll(async () => {
    const data = await browser.evaluate(async () => (await fetch('/api/workspace')).json());
    return data.files.find((file: any) => file.filename === 'inspection_purchase.pdf')?.id || 0;
  }).toBeGreaterThan(0);
  const data = await browser.evaluate(async () => (await fetch('/api/workspace')).json());
  const file = data.files.find((file: any) => file.filename === 'inspection_purchase.pdf');
  await app.open('/inspect/' + file.id);
  return file.id;
}

test('Inspect renders actual original and cleaned pages, changes and official sources', async ({app, screen, browser}) => {
  const id = await inspect(app, screen, browser);
  await expect(browser.locator('#ix-before')).toBeVisible();
  await expect(browser.locator('#ix-after')).toBeVisible();
  await expect(browser.locator('#ix-overlay .ix-region')).toHaveCount(2);
  await screen.getByRole('tab', 'Guidelines', {exact:true}).tap();
  await expect(browser.locator('#ix-sources')).toContainText('Ley 25.326');
  await screen.getByRole('tab', 'Process', {exact:true}).tap();
  await expect(browser.locator('#ix-manifest')).toContainText('DNI');
  await expect(browser.locator('#ix-public')).not.toBeVisible();
  expect((await fetch(new URL('/internal/preview/' + id + '/1', app.baseUrl))).status).toBe(401);
  expect((await fetch(new URL('/public/file/' + id, app.baseUrl))).status).toBe(404);
  await app.screenshot('inspector-desktop');
  await screen.getByRole('button', 'Next page').tap();
  await expect(browser.locator('#ix-page')).toContainText('Page 2 of 2');
  await expect(browser.locator('#ix-overlay .ix-region')).toHaveCount(0);
  await screen.getByRole('button', 'Previous page').tap();
  await expect(browser.locator('#ix-page')).toContainText('Page 1 of 2');
  await expect(browser.locator('#ix-overlay .ix-region')).toHaveCount(2);
  await screen.getByText('Show text changes', {exact:true}).tap();
  await expect(browser.locator('#ix-overlay')).not.toBeVisible();
});

test('Web research shows query, returned sources and failures without changing decisions', async ({app, screen, browser}) => {
  const id = await inspect(app, screen, browser);
  await screen.getByRole('tab', 'Web', {exact:true}).tap();
  await expect(browser.locator('#ix-query')).toContainText('when:30d');
  await browser.route('**/learning/discover', async route => route.fulfill({json:{query:'Argentina reporting when:30d', leads:[{
    id:'a'.repeat(64), title:'Fictional government report', publisher:'Fictional press', published_at:'2026-10-09',
    url:'https://news.google.com/rss/articles/fictional', discovered_at:1,
  }]}}));
  await screen.getByRole('button', 'Search reporting').tap();
  await expect(browser.locator('#ix-search-state')).toContainText('Found 1 reporting leads. No rules changed.');
  await expect(browser.locator('#ix-leads')).toContainText('Fictional press');
  await app.screenshot('inspector-web-research');
  await expect(browser.locator('#ix-leads a.ix-propose')).toHaveAttribute('href', /\/learning\?lead=a+#source-form/);
  await browser.route('**/learning/discover', async route => route.fulfill({status:502, json:{detail:'Search unavailable'}}));
  await screen.getByRole('button', 'Search reporting').tap();
  await expect(browser.locator('#ix-search-state')).toContainText('Reporting search unavailable');
  await expect(browser.locator('#ix-leads')).toContainText('Fictional government report');
  expect((await fetch(new URL('/public/file/' + id, app.baseUrl))).status).toBe(404);
});

test('Inspector stays usable on a phone with a missing cleaned page', async ({app, screen, browser}) => {
  await browser.setViewport({width:390, height:844});
  await inspect(app, screen, browser);
  await expect(browser.locator('#ix-before')).toBeVisible();
  expect(await browser.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await app.screenshot('inspector-mobile');
  await browser.route('**/internal/preview/**copy=cleaned*', async route => route.fulfill({status:503, body:'Unavailable'}));
  await screen.getByRole('button', 'Next page').tap();
  await expect(browser.locator('#ix-after-message')).toContainText('Preview unavailable');
  await expect(screen.getByRole('button', 'Refresh', {exact:true})).toBeVisible();
});

test('Senso exposes its query, cited passages and receipt with real loading and error states', async ({app, screen, browser}) => {
  const id = await inspect(app, screen, browser);
  await app.open('/inspect/' + id + '#senso');
  await expect(browser.locator('#ix-senso-connection')).toContainText('Not connected');
  await expect(screen.getByRole('button', 'Run lookup', {exact:true})).toBeDisabled();
  const document = await browser.evaluate(async () => (await fetch(location.pathname.replace('/inspect/', '/api/inspect/'))).json());
  document.senso = {configured:true, ready:true};
  await browser.route('**/api/inspect/' + id + '?*', async route => route.fulfill({json:document}));
  await screen.getByRole('button', 'Refresh', {exact:true}).tap();
  await expect(browser.locator('#ix-senso-connection')).toContainText('synced');
  const citation = {status:'cited', query:'Publication restrictions for: Personal identifiers', passages:1,
    latency_ms:143, content_id:'fictional-content', version_id:'fictional-version', guideline_digest:'fictional-digest',
    retrieved_at:1791543600, context_passages:[{text:'Mask private identifiers before publishing. <img src=x>'}]};
  await browser.route('**/api/inspect/' + id + '/senso', async route => {
    await new Promise(resolve => setTimeout(resolve, 300));
    await route.fulfill({json:{citation, senso:document.senso}});
  });
  await screen.getByRole('button', 'Run lookup', {exact:true}).tap();
  await expect(browser.locator('#ix-senso-state')).toContainText('Verifying');
  await expect(browser.locator('#ix-senso-state')).toContainText('1 passage retrieved · 143 ms');
  await expect(browser.locator('#ix-senso-query')).toContainText('Personal identifiers');
  await expect(browser.locator('#ix-senso')).toContainText('Mask private identifiers');
  await expect(browser.locator('#ix-senso img')).toHaveCount(0);
  await screen.getByText('Retrieval receipt', {exact:true}).tap();
  await expect(browser.locator('#ix-senso')).toContainText('fictional-version');
  await app.screenshot('inspector-senso');
  await browser.route('**/api/inspect/' + id + '/senso', async route => route.fulfill({status:502,json:{detail:'Senso unavailable. Retry lookup.'}}));
  await screen.getByRole('button', 'Run again', {exact:true}).tap();
  await expect(browser.locator('#ix-senso-state')).toContainText('Senso unavailable');
  await expect(browser.locator('#ix-senso')).toContainText('Mask private identifiers');
  expect((await fetch(new URL('/public/file/' + id, app.baseUrl))).status).toBe(404);
});
