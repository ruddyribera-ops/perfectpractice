# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: comprehensive\workflows.spec.ts >> S4: Dashboard has links to Topics and History
- Location: comprehensive\workflows.spec.ts:66:5

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
  1   | import { test, expect, type Page, type Browser } from '@playwright/test';
  2   | 
  3   | const FRONTEND = process.env.FRONTEND_URL || 'https://proactive-wisdom-production-cd0e.up.railway.app';
  4   | const BACKEND = process.env.BACKEND_URL || 'https://lucid-serenity-production.up.railway.app';
  5   | 
  6   | const STUDENT_EMAIL = 'student_01@test.com';
  7   | const STUDENT_PASS = 'test123';
  8   | const TEACHER_EMAIL = 'profesor_e2e@test.com';
  9   | const PARENT_EMAIL = 'parent_01@test.com';
  10  | 
  11  | // ─── HELPERS ────────────────────────────────────────────────────────────────
  12  | 
  13  | async function loginStudent(page: Page, email = STUDENT_EMAIL, password = STUDENT_PASS) {
  14  |   await page.goto(`${FRONTEND}/login`, { waitUntil: 'networkidle' });
  15  |   await page.locator('input[type="email"]').fill(email);
  16  |   await page.locator('input[type="password"]').fill(password);
  17  |   await page.locator('button[type="submit"]').click();
> 18  |   await page.waitForURL(/\/$/, { timeout: 10000 });
      |              ^ TimeoutError: page.waitForURL: Timeout 10000ms exceeded.
  19  | }
  20  | 
  21  | async function loginTeacher(page: Page) {
  22  |   await page.goto(`${FRONTEND}/login`, { waitUntil: 'networkidle' });
  23  |   await page.locator('input[type="email"]').fill(TEACHER_EMAIL);
  24  |   await page.locator('input[type="password"]').fill('test123');
  25  |   await page.locator('button[type="submit"]').click();
  26  |   await page.waitForURL(/\/teacher/, { timeout: 10000 });
  27  | }
  28  | 
  29  | async function loginParent(page: Page) {
  30  |   await page.goto(`${FRONTEND}/login`, { waitUntil: 'networkidle' });
  31  |   await page.locator('input[type="email"]').fill(PARENT_EMAIL);
  32  |   await page.locator('input[type="password"]').fill('test123');
  33  |   await page.locator('button[type="submit"]').click();
  34  |   await page.waitForURL(/\/parent/, { timeout: 10000 });
  35  | }
  36  | 
  37  | // ─── STUDENT: DASHBOARD ─────────────────────────────────────────────────────
  38  | 
  39  | test('S1: Student login lands on dashboard at /', async ({ page }) => {
  40  |   await page.goto(`${FRONTEND}/login`, { waitUntil: 'networkidle' });
  41  |   await page.locator('input[type="email"]').fill(STUDENT_EMAIL);
  42  |   await page.locator('input[type="password"]').fill(STUDENT_PASS);
  43  |   await page.locator('button[type="submit"]').click();
  44  |   await page.waitForURL(/\/$/, { timeout: 10000 });
  45  |   // Should NOT redirect to /student or /login
  46  |   expect(page.url()).toMatch(/\/$/);
  47  | });
  48  | 
  49  | test('S2: Dashboard shows all stat cards', async ({ page }) => {
  50  |   await loginStudent(page);
  51  |   // XP card
  52  |   await expect(page.getByText('XP Total')).toBeVisible();
  53  |   // Nivel card
  54  |   await expect(page.getByText('Nivel')).toBeVisible();
  55  |   // Racha card
  56  |   await expect(page.getByText('Racha')).toBeVisible();
  57  |   // Ejercicios card
  58  |   await expect(page.getByText('Ejercicios')).toBeVisible();
  59  | });
  60  | 
  61  | test('S3: Dashboard shows enrolled class card', async ({ page }) => {
  62  |   await loginStudent(page);
  63  |   await expect(page.getByText('3ro Primaria')).toBeVisible({ timeout: 5000 });
  64  | });
  65  | 
  66  | test('S4: Dashboard has links to Topics and History', async ({ page }) => {
  67  |   await loginStudent(page);
  68  |   await expect(page.getByRole('link', { name: /Ver Temas/i })).toBeVisible();
  69  |   await expect(page.getByRole('link', { name: /Mi Progreso/i })).toBeVisible();
  70  | });
  71  | 
  72  | test('S5: Language switcher is present and interactive', async ({ page }) => {
  73  |   await loginStudent(page);
  74  |   const langSelect = page.locator('select').first();
  75  |   await langSelect.selectOption('en-US');
  76  |   await page.waitForTimeout(1000);
  77  |   // Verify select shows en-US as selected
  78  |   const selectedValue = await langSelect.inputValue();
  79  |   expect(selectedValue).toBe('en-US');
  80  | });
  81  | 
  82  | // ─── STUDENT: TOPICS → UNIT → LESSON → EXERCISE ─────────────────────────────
  83  | 
  84  | test('S6: /topics shows topic grid', async ({ page }) => {
  85  |   await loginStudent(page);
  86  |   await page.goto(`${FRONTEND}/topics`, { waitUntil: 'networkidle' });
  87  |   // Should show topics heading
  88  |   const body = await page.textContent('body');
  89  |   expect(body!.length).toBeGreaterThan(100);
  90  |   // Should have topic names
  91  |   await expect(page.getByText('Números').first()).toBeVisible({ timeout: 5000 });
  92  | });
  93  | 
  94  | test('S7: Clicking topic navigates to topic detail', async ({ page }) => {
  95  |   await loginStudent(page);
  96  |   await page.goto(`${FRONTEND}/topics`, { waitUntil: 'networkidle' });
  97  |   // Click first topic link
  98  |   const topicLink = page.locator('a[href^="/topics/"]').first();
  99  |   const href = await topicLink.getAttribute('href');
  100 |   await topicLink.click();
  101 |   await page.waitForURL(/\/topics\/.+/, { timeout: 8000 });
  102 |   // Should show unit list
  103 |   const body = await page.textContent('body');
  104 |   expect(body!.length).toBeGreaterThan(50);
  105 | });
  106 | 
  107 | test('S8: Lesson page accessible and shows exercises', async ({ page }) => {
  108 |   await loginStudent(page);
  109 |   // Navigate to first lesson via API data
  110 |   // Try direct lesson ID navigation
  111 |   await page.goto(`${FRONTEND}/lessons/1`, { waitUntil: 'networkidle' });
  112 |   const body = await page.textContent('body');
  113 |   // Should either show lesson content or "no access" — just verify page loaded
  114 |   expect(body!.length).toBeGreaterThan(20);
  115 | });
  116 | 
  117 | test('S9: Exercise page loads with question', async ({ page }) => {
  118 |   await loginStudent(page);
```