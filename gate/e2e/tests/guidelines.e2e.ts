import { test } from '@e2e-dev/web';
import { expect } from 'e2e';

test('Reviewed guidelines and context states are accessible', async ({ app, screen }) => {
  await app.open('/guidelines');
  await expect(screen.getByRole('heading', 'Guidelines')).toBeVisible();
  await screen.getByText('Ley 25.326 — Personal data protection', { exact: true }).tap();
  await expect(screen.getByText('Personal data, including legal persons where applicable; health data is sensitive.', { exact: true })).toBeVisible();
  await screen.getByText('AAIP Resolution 47/2018 — Personal-data security measures', { exact: true }).tap();
  await expect(screen.getByText('Articles 2–3; Annex I, sections A–H; Annex II', { exact: true })).toBeVisible();
  await screen.getByText('CERT-Ar — Annual computer security incident report, 2025', { exact: true }).tap();
  await expect(screen.getByText('Annual report: recorded incidents, State sector and incident categories', { exact: true })).toBeVisible();
  await app.open('/learning');
  await expect(screen.getByRole('heading', 'Rules', { exact: true })).toBeVisible();
  await expect(screen.getByRole('button', 'Find recent reports')).toBeVisible();
  await expect(screen.getByLabel('Use cited Senso guideline context')).toBeDisabled();
});
