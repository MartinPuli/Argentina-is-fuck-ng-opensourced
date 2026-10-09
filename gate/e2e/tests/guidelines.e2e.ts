import { test } from '@e2e-dev/web';
import { expect } from 'e2e';

test('Reviewed guidelines and context states are accessible', async ({ app, screen }) => {
  await app.open('/guidelines');
  await expect(screen.getByRole('heading', 'Guidelines')).toBeVisible();
  await screen.getByText('Ley 25.326 — Personal data protection', { exact: true }).tap();
  await expect(screen.getByText('Personal data, including legal persons where applicable; health data is sensitive.', { exact: true })).toBeVisible();
  await app.open('/learning');
  await expect(screen.getByRole('heading', 'Rules', { exact: true })).toBeVisible();
  await expect(screen.getByRole('button', 'Find recent reports')).toBeVisible();
  await expect(screen.getByLabel('Use cited Senso guideline context')).toBeDisabled();
});
