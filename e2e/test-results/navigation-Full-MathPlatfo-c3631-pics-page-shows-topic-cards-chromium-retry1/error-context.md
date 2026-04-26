# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: navigation.spec.ts >> Full MathPlatform Navigation >> topics page shows topic cards
- Location: navigation.spec.ts:20:7

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
        - textbox [ref=e9]: student@test.com
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
  6  | test.describe('Full MathPlatform Navigation', () => {
  7  | 
  8  |   test('login and navigate to topics page', async ({ page }) => {
  9  |     await page.goto(`${FRONTEND_URL}/login`, { waitUntil: 'networkidle' });
  10 |     await page.locator('input[type="email"]').fill('student@test.com');
  11 |     await page.locator('input[type="password"]').fill('test123');
  12 |     await page.locator('button[type="submit"]').click();
  13 |     await page.waitForURL(/^https:\/\/proactive-wisdom-production.*\/$/, { timeout: 10000 });
  14 | 
  15 |     // Navigate to topics
  16 |     await page.goto(`${FRONTEND_URL}/topics`, { waitUntil: 'networkidle' });
  17 |     await expect(page.getByRole('heading', { name: /tema|topic/i })).toBeVisible({ timeout: 10000 });
  18 |   });
  19 | 
  20 |   test('topics page shows topic cards', async ({ page }) => {
  21 |     await page.goto(`${FRONTEND_URL}/login`, { waitUntil: 'networkidle' });
  22 |     await page.locator('input[type="email"]').fill('student@test.com');
  23 |     await page.locator('input[type="password"]').fill('test123');
  24 |     await page.locator('button[type="submit"]').click();
> 25 |     await page.waitForURL(/^https:\/\/proactive-wisdom-production.*\/$/, { timeout: 10000 });
     |                ^ TimeoutError: page.waitForURL: Timeout 10000ms exceeded.
  26 |     await page.goto(`${FRONTEND_URL}/topics`, { waitUntil: 'networkidle' });
  27 | 
  28 |     // Should see topic names
  29 |     const bodyText = await page.textContent('body');
  30 |     const hasTopics = bodyText && bodyText.includes('Números');
  31 |     expect(hasTopics).toBeTruthy();
  32 |   });
  33 | 
  34 |   test('login as teacher and check classes', async ({ page }) => {
  35 |     await page.goto(`${FRONTEND_URL}/login`, { waitUntil: 'networkidle' });
  36 |     await page.locator('input[type="email"]').fill('profesor@test.com');
  37 |     await page.locator('input[type="password"]').fill('test123');
  38 |     await page.locator('button[type="submit"]').click();
  39 |     await page.waitForURL(/teacher/, { timeout: 10000 });
  40 |     await expect(page.getByText(/docente|clase|panel/i).first()).toBeVisible({ timeout: 10000 });
  41 |   });
  42 | 
  43 | });
```