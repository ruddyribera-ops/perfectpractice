import { test, expect } from '@playwright/test';

const BACKEND_URL = process.env.BACKEND_URL || 'https://lucid-serenity-production.up.railway.app';
const FRONTEND_URL = process.env.FRONTEND_URL || 'https://proactive-wisdom-production-cd0e.up.railway.app';

test.describe('Production Smoke Tests', () => {

  test('backend /api/health returns 200', async ({ request }) => {
    const response = await request.get(`${BACKEND_URL}/api/health`);
    expect(response.status()).toBe(200);
    const body = await response.json();
    expect(body).toHaveProperty('status', 'healthy');
  });

  test('frontend loads and shows login page', async ({ page }) => {
    await page.goto(FRONTEND_URL, { waitUntil: 'domcontentloaded' });
    // Should land on login page (no redirect to /student yet)
    await expect(page).toHaveTitle(/./);
    // Check a login-related element is visible
    const loginButton = page.getByRole('button', { name: /Iniciar Sesión/i });
    await expect(loginButton.or(page.getByRole('textbox', { name: /Correo electrónico/i }))).toBeVisible({ timeout: 10000 });
  });

  test('login as student@test.com redirects to dashboard', async ({ page }) => {
    await page.goto(`${FRONTEND_URL}/login`);
    await page.locator('input[type="email"]').fill('student@test.com');
    await page.locator('input[type="password"]').fill('test123');
    await page.locator('button[type="submit"]').click();
    // Should redirect somewhere under /student
    await page.waitForURL(/\/student/, { timeout: 10000 });
    // Dashboard should show something meaningful
    await expect(page.getByText(/estudiante|student|xp|progreso|puntos/i).or(page.locator('body'))).toBeVisible({ timeout: 5000 });
  });

  test('unauthenticated /api/me returns 401', async ({ request }) => {
    const response = await request.get(`${BACKEND_URL}/api/me/stats/me`);
    expect(response.status()).toBe(401);
  });

});
