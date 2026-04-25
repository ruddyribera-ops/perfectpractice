# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: smoke.spec.ts >> Production Smoke Tests >> login as student@test.com redirects to dashboard
- Location: smoke.spec.ts:24:7

# Error details

```
TimeoutError: page.waitForURL: Timeout 10000ms exceeded.
=========================== logs ===========================
waiting for navigation until "load"
  navigated to "https://proactive-wisdom-production-cd0e.up.railway.app/"
============================================================
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
          - link [ref=e8] [cursor=pointer]:
            - /url: /me/notifications
            - img [ref=e9]
          - combobox [ref=e12] [cursor=pointer]:
            - option "🇧🇴 Español" [selected]
            - option "🇺🇸 English"
            - option "🇫🇷 Français"
            - option "🇧🇷 Português"
          - button "🌙 Oscuro" [ref=e13] [cursor=pointer]
          - generic [ref=e14]: ¡Hola, Test!
          - button "Cerrar sesión" [ref=e15] [cursor=pointer]
    - main [ref=e16]:
      - generic [ref=e17]:
        - generic [ref=e18]:
          - generic [ref=e19]:
            - img [ref=e20]
            - generic [ref=e22]:
              - paragraph [ref=e23]: XP Total
              - paragraph [ref=e24]: "0"
          - generic [ref=e25]:
            - img [ref=e26]
            - generic [ref=e32]:
              - paragraph [ref=e33]: Nivel
              - paragraph [ref=e34]: "1"
          - generic [ref=e35]:
            - img [ref=e36]
            - generic [ref=e38]:
              - paragraph [ref=e39]: Racha
              - paragraph [ref=e40]: 0 días
          - generic [ref=e41]:
            - img [ref=e42]
            - generic [ref=e47]:
              - paragraph [ref=e48]: Hielos
              - paragraph [ref=e49]: "0"
          - generic [ref=e50]:
            - img [ref=e51]
            - generic [ref=e54]:
              - paragraph [ref=e55]: Ejercicios
              - paragraph [ref=e56]: "0"
        - generic [ref=e57]:
          - generic [ref=e58]:
            - generic [ref=e59]: Nivel 1
            - generic [ref=e60]: 100 XP para siguiente nivel
          - generic [ref=e63]: 0 XP
        - generic [ref=e64]:
          - heading "Continúa Aprendiendo" [level=2] [ref=e65]
          - generic [ref=e66]:
            - link "Ver Temas" [ref=e67] [cursor=pointer]:
              - /url: /topics
            - link "Mi Progreso" [ref=e68] [cursor=pointer]:
              - /url: /me/history
              - img [ref=e69]
              - text: Mi Progreso
        - generic [ref=e72]:
          - heading "📊 Mi Dominio por Tema" [level=2] [ref=e73]
          - generic [ref=e74]:
            - generic [ref=e76]:
              - generic [ref=e77]: Números hasta 100
              - generic [ref=e78]: 0%
            - generic [ref=e81]:
              - generic [ref=e82]: Suma y Resta hasta 20
              - generic [ref=e83]: 0%
            - generic [ref=e86]:
              - generic [ref=e87]: Formas Geométricas
              - generic [ref=e88]: 0%
            - generic [ref=e91]:
              - generic [ref=e92]: Medición
              - generic [ref=e93]: 0%
            - generic [ref=e96]:
              - generic [ref=e97]: Números hasta 1000
              - generic [ref=e98]: 0%
            - generic [ref=e101]:
              - generic [ref=e102]: Suma y Resta hasta 1000
              - generic [ref=e103]: 0%
        - navigation [ref=e105]:
          - link "🏠" [ref=e106] [cursor=pointer]:
            - /url: /
            - generic [ref=e107]: 🏠
          - link "📋" [ref=e108] [cursor=pointer]:
            - /url: /me/assignments
            - generic [ref=e109]: 📋
          - link "📊" [ref=e110] [cursor=pointer]:
            - /url: /me/history
            - generic [ref=e111]: 📊
          - link "🏆" [ref=e112] [cursor=pointer]:
            - /url: /leaderboard
            - generic [ref=e113]: 🏆
          - link "🔔" [ref=e114] [cursor=pointer]:
            - /url: /me/notifications
            - generic [ref=e115]: 🔔
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
  21 |     await expect(loginButton.or(page.getByRole('textbox', { name: /Correo electrónico/i }))).toBeVisible({ timeout: 10000 });
  22 |   });
  23 | 
  24 |   test('login as student@test.com redirects to dashboard', async ({ page }) => {
  25 |     await page.goto(`${FRONTEND_URL}/login`);
  26 |     await page.locator('input[type="email"]').fill('student@test.com');
  27 |     await page.locator('input[type="password"]').fill('test123');
  28 |     await page.locator('button[type="submit"]').click();
  29 |     // Should redirect somewhere under /student
> 30 |     await page.waitForURL(/\/student/, { timeout: 10000 });
     |                ^ TimeoutError: page.waitForURL: Timeout 10000ms exceeded.
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