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

  test('frontend loads and shows landing page', async ({ page }) => {
    await page.goto(FRONTEND_URL, { waitUntil: 'networkidle' });
    // Should show landing page for unauthenticated users
    await expect(page.getByText('Aprende Matemáticas Jugando')).toBeVisible({ timeout: 10000 });
    // Should have login link
    await expect(page.getByRole('link', { name: /Iniciar sesión/i })).toBeVisible();
  });

  test('login as student@test.com shows dashboard', async ({ page }) => {
    await page.goto(`${FRONTEND_URL}/login`, { waitUntil: 'networkidle' });
    await page.locator('input[type="email"]').fill('student@test.com');
    await page.locator('input[type="password"]').fill('test123');
    await page.locator('button[type="submit"]').click();
    // Student lands on / (root) not /student
    await page.waitForURL(/^https:\/\/proactive-wisdom-production.*\/$/, { timeout: 10000 });
    // Dashboard should load (shows stats cards)
    await expect(page.getByText(/Math Platform|XP Total|Nivel|Racha|Ejercicios/i)).toBeVisible({ timeout: 10000 });
  });

  test('unauthenticated /api/me returns 401', async ({ request }) => {
    const response = await request.get(`${BACKEND_URL}/api/me/stats/me`);
    expect(response.status()).toBe(401);
  });

});
