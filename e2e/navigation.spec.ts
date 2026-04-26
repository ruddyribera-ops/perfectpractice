import { test, expect } from '@playwright/test';

const BACKEND_URL = process.env.BACKEND_URL || 'https://lucid-serenity-production.up.railway.app';
const FRONTEND_URL = process.env.FRONTEND_URL || 'https://proactive-wisdom-production-cd0e.up.railway.app';

test.describe('Full MathPlatform Navigation', () => {

  test('login and navigate to topics page', async ({ page }) => {
    await page.goto(`${FRONTEND_URL}/login`, { waitUntil: 'networkidle' });
    await page.locator('input[type="email"]').fill('student@test.com');
    await page.locator('input[type="password"]').fill('test123');
    await page.locator('button[type="submit"]').click();
    await page.waitForURL(/^https:\/\/proactive-wisdom-production.*\/$/, { timeout: 10000 });

    // Navigate to topics
    await page.goto(`${FRONTEND_URL}/topics`, { waitUntil: 'networkidle' });
    await expect(page.getByRole('heading', { name: /tema|topic/i })).toBeVisible({ timeout: 10000 });
  });

  test('topics page shows topic cards', async ({ page }) => {
    await page.goto(`${FRONTEND_URL}/login`, { waitUntil: 'networkidle' });
    await page.locator('input[type="email"]').fill('student@test.com');
    await page.locator('input[type="password"]').fill('test123');
    await page.locator('button[type="submit"]').click();
    await page.waitForURL(/^https:\/\/proactive-wisdom-production.*\/$/, { timeout: 10000 });
    await page.goto(`${FRONTEND_URL}/topics`, { waitUntil: 'networkidle' });

    // Should see topic names
    const bodyText = await page.textContent('body');
    const hasTopics = bodyText && bodyText.includes('Números');
    expect(hasTopics).toBeTruthy();
  });

  test('login as teacher and check classes', async ({ page }) => {
    await page.goto(`${FRONTEND_URL}/login`, { waitUntil: 'networkidle' });
    await page.locator('input[type="email"]').fill('profesor@test.com');
    await page.locator('input[type="password"]').fill('test123');
    await page.locator('button[type="submit"]').click();
    await page.waitForURL(/teacher/, { timeout: 10000 });
    await expect(page.getByText(/docente|clase|panel/i).first()).toBeVisible({ timeout: 10000 });
  });

});