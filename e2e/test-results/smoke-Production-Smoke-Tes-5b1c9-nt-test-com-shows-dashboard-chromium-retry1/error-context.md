# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: smoke.spec.ts >> Production Smoke Tests >> login as student@test.com shows dashboard
- Location: smoke.spec.ts:23:7

# Error details

```
TimeoutError: page.waitForURL: Timeout 10000ms exceeded.
=========================== logs ===========================
waiting for navigation until "load"
============================================================
```

# Page snapshot

```yaml
- generic [active] [ref=e1]:
  - generic [ref=e3]:
    - heading "Iniciar Sesión" [level=1] [ref=e4]
    - generic [ref=e5]: Failed to fetch
    - generic [ref=e6]:
      - generic [ref=e7]:
        - generic [ref=e8]: Correo electrónico
        - textbox [ref=e9]: student_01@test.com
      - generic [ref=e10]:
        - generic [ref=e11]: Contraseña
        - textbox [ref=e12]: test123
      - button "Iniciar Sesión" [ref=e13] [cursor=pointer]
    - paragraph [ref=e14]:
      - text: ¿No tienes cuenta?
      - link "Regístrate" [ref=e15] [cursor=pointer]:
        - /url: /register
  - alert [ref=e16]
```

# Test source

```ts
  1  | import { test, expect } from '@playwright/test';
  2  | 
  3  | const BACKEND_URL = process.env.BACKEND_URL || 'https://lucid-serenity-production.up.railway.app';
  4  | const FRONTEND_URL = process.env.FRONTEND_URL || 'https://proactive-wisdom-production-cd0e.up.railway.app';
  5  | 
  6  | test.describe('Production Smoke Tests', () => {
  7  | 
  8  |   test('backend /api/health returns 200', async ({ request }) => {
  9  |     const response = await request.get(`${BACKEND_URL}/api/health`);
  10 |     expect(response.status()).toBe(200);
  11 |     const body = await response.json();
  12 |     expect(body).toHaveProperty('status', 'healthy');
  13 |   });
  14 | 
  15 |   test('frontend loads and shows landing page', async ({ page }) => {
  16 |     await page.goto(FRONTEND_URL, { waitUntil: 'networkidle' });
  17 |     // Should show landing page for unauthenticated users
  18 |     await expect(page.getByText('Aprende Matemáticas Jugando')).toBeVisible({ timeout: 10000 });
  19 |     // Should have login link
  20 |     await expect(page.getByRole('link', { name: /Iniciar sesión/i })).toBeVisible();
  21 |   });
  22 | 
  23 |   test('login as student@test.com shows dashboard', async ({ page }) => {
  24 |     await page.goto(`${FRONTEND_URL}/login`, { waitUntil: 'networkidle' });
  25 |     await page.locator('input[type="email"]').fill('student_01@test.com');
  26 |     await page.locator('input[type="password"]').fill('test123');
  27 |     await page.locator('button[type="submit"]').click();
  28 |     // Student lands on / (root) not /student
> 29 |     await page.waitForURL(/^https:\/\/proactive-wisdom-production.*\/$/, { timeout: 10000 });
     |                ^ TimeoutError: page.waitForURL: Timeout 10000ms exceeded.
  30 |     // Dashboard should load (shows stats cards)
  31 |     await expect(page.getByText(/XP Total|Nivel|Racha|Ejercicios/i).first()).toBeVisible({ timeout: 10000 });
  32 |   });
  33 | 
  34 |   test('unauthenticated /api/me returns 401', async ({ request }) => {
  35 |     const response = await request.get(`${BACKEND_URL}/api/me/stats/me`);
  36 |     expect(response.status()).toBe(401);
  37 |   });
  38 | 
  39 | });
  40 | 
```