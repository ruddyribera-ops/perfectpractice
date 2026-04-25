# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: smoke.spec.ts >> Production Smoke Tests >> frontend loads and shows login page
- Location: smoke.spec.ts:15:7

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: getByRole('button', { name: /Iniciar Sesión/i }).or(getByRole('textbox', { name: /Correo electrónico/i }))
Expected: visible
Timeout: 10000ms
Error: element(s) not found

Call log:
  - Expect "toBeVisible" with timeout 10000ms
  - waiting for getByRole('button', { name: /Iniciar Sesión/i }).or(getByRole('textbox', { name: /Correo electrónico/i }))

```

# Page snapshot

```yaml
- generic [active] [ref=e1]:
  - alert [ref=e2]
  - generic [ref=e3]:
    - banner [ref=e4]:
      - navigation [ref=e5]:
        - heading "Math Platform" [level=1] [ref=e6]
        - generic [ref=e7]:
          - link "Iniciar sesión" [ref=e8] [cursor=pointer]:
            - /url: /login
          - link "Registrarse" [ref=e9] [cursor=pointer]:
            - /url: /register
    - main [ref=e10]:
      - generic [ref=e12]:
        - heading "Aprende Matemáticas Jugando" [level=2] [ref=e13]
        - paragraph [ref=e14]: La plataforma educativa que hace las matemáticas divertidas para estudiantes bolivianos
        - link "¡Comienza Ahora!" [ref=e15] [cursor=pointer]:
          - /url: /register
      - generic [ref=e17]:
        - heading "Características" [level=3] [ref=e18]
        - generic [ref=e19]:
          - generic [ref=e20]:
            - img [ref=e22]
            - heading "Contenido Khan Academy" [level=4] [ref=e25]
            - paragraph [ref=e26]: Currículo completo de matemáticas para grados 1-6 basado en Khan Academy
          - generic [ref=e27]:
            - img [ref=e29]
            - heading "Gamificación" [level=4] [ref=e35]
            - paragraph [ref=e36]: Gana puntos, sube de nivel y desbloquea logros mientras aprendes
          - generic [ref=e37]:
            - img [ref=e39]
            - heading "Para Docentes" [level=4] [ref=e44]
            - paragraph [ref=e45]: Crea clases, asigna tareas y sigue el progreso de tus estudiantes
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
  15 |   test('frontend loads and shows login page', async ({ page }) => {
  16 |     await page.goto(FRONTEND_URL, { waitUntil: 'domcontentloaded' });
  17 |     // Should land on login page (no redirect to /student yet)
  18 |     await expect(page).toHaveTitle(/./);
  19 |     // Check a login-related element is visible
  20 |     const loginButton = page.getByRole('button', { name: /Iniciar Sesión/i });
> 21 |     await expect(loginButton.or(page.getByRole('textbox', { name: /Correo electrónico/i }))).toBeVisible({ timeout: 10000 });
     |                                                                                              ^ Error: expect(locator).toBeVisible() failed
  22 |   });
  23 | 
  24 |   test('login as student@test.com redirects to dashboard', async ({ page }) => {
  25 |     await page.goto(`${FRONTEND_URL}/login`);
  26 |     await page.locator('input[type="email"]').fill('student@test.com');
  27 |     await page.locator('input[type="password"]').fill('test123');
  28 |     await page.locator('button[type="submit"]').click();
  29 |     // Should redirect somewhere under /student
  30 |     await page.waitForURL(/\/student/, { timeout: 10000 });
  31 |     // Dashboard should show something meaningful
  32 |     await expect(page.getByText(/estudiante|student|xp|progreso|puntos/i).or(page.locator('body'))).toBeVisible({ timeout: 5000 });
  33 |   });
  34 | 
  35 |   test('unauthenticated /api/me returns 401', async ({ request }) => {
  36 |     const response = await request.get(`${BACKEND_URL}/api/me/stats/me`);
  37 |     expect(response.status()).toBe(401);
  38 |   });
  39 | 
  40 | });
  41 | 
```