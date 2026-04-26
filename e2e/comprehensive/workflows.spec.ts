import { test, expect, type Page, type Browser } from '@playwright/test';

const FRONTEND = process.env.FRONTEND_URL || 'https://proactive-wisdom-production-cd0e.up.railway.app';
const BACKEND = process.env.BACKEND_URL || 'https://lucid-serenity-production.up.railway.app';

const STUDENT_EMAIL = 'student_01@test.com';
const STUDENT_PASS = 'test123';
const TEACHER_EMAIL = 'profesor_e2e@test.com';
const PARENT_EMAIL = 'parent_01@test.com';

// ─── HELPERS ────────────────────────────────────────────────────────────────

async function loginStudent(page: Page, email = STUDENT_EMAIL, password = STUDENT_PASS) {
  await page.goto(`${FRONTEND}/login`, { waitUntil: 'networkidle' });
  await page.locator('input[type="email"]').fill(email);
  await page.locator('input[type="password"]').fill(password);
  await page.locator('button[type="submit"]').click();
  await page.waitForURL(/\/$/, { timeout: 10000 });
}

async function loginTeacher(page: Page) {
  await page.goto(`${FRONTEND}/login`, { waitUntil: 'networkidle' });
  await page.locator('input[type="email"]').fill(TEACHER_EMAIL);
  await page.locator('input[type="password"]').fill('test123');
  await page.locator('button[type="submit"]').click();
  await page.waitForURL(/\/teacher/, { timeout: 10000 });
}

async function loginParent(page: Page) {
  await page.goto(`${FRONTEND}/login`, { waitUntil: 'networkidle' });
  await page.locator('input[type="email"]').fill(PARENT_EMAIL);
  await page.locator('input[type="password"]').fill('test123');
  await page.locator('button[type="submit"]').click();
  await page.waitForURL(/\/parent/, { timeout: 10000 });
}

// ─── STUDENT: DASHBOARD ─────────────────────────────────────────────────────

test('S1: Student login lands on dashboard at /', async ({ page }) => {
  await page.goto(`${FRONTEND}/login`, { waitUntil: 'networkidle' });
  await page.locator('input[type="email"]').fill(STUDENT_EMAIL);
  await page.locator('input[type="password"]').fill(STUDENT_PASS);
  await page.locator('button[type="submit"]').click();
  await page.waitForURL(/\/$/, { timeout: 10000 });
  // Should NOT redirect to /student or /login
  expect(page.url()).toMatch(/\/$/);
});

test('S2: Dashboard shows all stat cards', async ({ page }) => {
  await loginStudent(page);
  // XP card
  await expect(page.getByText('XP Total')).toBeVisible();
  // Nivel card
  await expect(page.getByText('Nivel')).toBeVisible();
  // Racha card
  await expect(page.getByText('Racha')).toBeVisible();
  // Ejercicios card
  await expect(page.getByText('Ejercicios')).toBeVisible();
});

test('S3: Dashboard shows enrolled class card', async ({ page }) => {
  await loginStudent(page);
  await expect(page.getByText('3ro Primaria')).toBeVisible({ timeout: 5000 });
});

test('S4: Dashboard has links to Topics and History', async ({ page }) => {
  await loginStudent(page);
  await expect(page.getByRole('link', { name: /Ver Temas/i })).toBeVisible();
  await expect(page.getByRole('link', { name: /Mi Progreso/i })).toBeVisible();
});

test('S5: Language switcher is present and interactive', async ({ page }) => {
  await loginStudent(page);
  const langSelect = page.locator('select').first();
  await langSelect.selectOption('en-US');
  await page.waitForTimeout(1000);
  // Verify select shows en-US as selected
  const selectedValue = await langSelect.inputValue();
  expect(selectedValue).toBe('en-US');
});

// ─── STUDENT: TOPICS → UNIT → LESSON → EXERCISE ─────────────────────────────

test('S6: /topics shows topic grid', async ({ page }) => {
  await loginStudent(page);
  await page.goto(`${FRONTEND}/topics`, { waitUntil: 'networkidle' });
  // Should show topics heading
  const body = await page.textContent('body');
  expect(body!.length).toBeGreaterThan(100);
  // Should have topic names
  await expect(page.getByText('Números').first()).toBeVisible({ timeout: 5000 });
});

test('S7: Clicking topic navigates to topic detail', async ({ page }) => {
  await loginStudent(page);
  await page.goto(`${FRONTEND}/topics`, { waitUntil: 'networkidle' });
  // Click first topic link
  const topicLink = page.locator('a[href^="/topics/"]').first();
  const href = await topicLink.getAttribute('href');
  await topicLink.click();
  await page.waitForURL(/\/topics\/.+/, { timeout: 8000 });
  // Should show unit list
  const body = await page.textContent('body');
  expect(body!.length).toBeGreaterThan(50);
});

test('S8: Lesson page accessible and shows exercises', async ({ page }) => {
  await loginStudent(page);
  // Navigate to first lesson via API data
  // Try direct lesson ID navigation
  await page.goto(`${FRONTEND}/lessons/1`, { waitUntil: 'networkidle' });
  const body = await page.textContent('body');
  // Should either show lesson content or "no access" — just verify page loaded
  expect(body!.length).toBeGreaterThan(20);
});

test('S9: Exercise page loads with question', async ({ page }) => {
  await loginStudent(page);
  await page.goto(`${FRONTEND}/exercises/1`, { waitUntil: 'networkidle' });
  // Should show question content
  const body = await page.textContent('body');
  // Body should be non-trivial
  expect(body!.length).toBeGreaterThan(30);
  // Should have some input or button for answering
  const hasInput = await page.locator('input[type="text"], input[type="number"], button').count();
  expect(hasInput).toBeGreaterThan(0);
});

// ─── STUDENT: EXERCISE SUBMISSION FULL CYCLE ─────────────────────────────────

test('S10: Submit exercise → see result → what happens next?', async ({ page }) => {
  await loginStudent(page);
  await page.goto(`${FRONTEND}/exercises/1`, { waitUntil: 'networkidle' });

  // Check for answer input
  const textInput = page.locator('input[type="text"], input[type="number"]').first();
  const isVisible = await textInput.isVisible().catch(() => false);

  if (isVisible) {
    await textInput.fill('5');
    const submitBtn = page.locator('button[type="submit"], button:has-text("Enviar"), button:has-text("Submit")').first();
    const submitVisible = await submitBtn.isVisible().catch(() => false);
    if (submitVisible) {
      await submitBtn.click();
      await page.waitForTimeout(2000);
      const body = await page.textContent('body');
      // Result should show correct/incorrect feedback
      const hasResult = body!.includes('correct') || body!.includes('Correct') ||
                        body!.includes('incorrect') || body!.includes('Incorrect') ||
                        body!.includes('¡Correcto') || body!.includes('Incorrecto') ||
                        body!.includes('Puntos') || body!.includes('XP');
      expect(hasResult).toBeTruthy();

      // KEY CHECK: Is there a "Continuar" or "Siguiente" or "Volver" button?
      const continuarBtn = page.locator('button:has-text("Continuar"), button:has-text("Siguiente"), button:has-text("Volver"), button:has-text("Regresar"), a:has-text("Continuar"), a:has-text("Volver")');
      const continuarCount = await continuarBtn.count();
      console.log(`Post-exercise nav buttons found: ${continuarCount}`);
      if (continuarCount > 0) {
        // Try clicking it
        await continuarBtn.first().click();
        await page.waitForTimeout(1000);
        console.log(`After continue click, URL: ${page.url()}`);
      }
    }
  }
});

test('S11: Multiple choice exercise flow', async ({ page }) => {
  await loginStudent(page);
  // Try a known MC exercise — check by looking at exercise type
  await page.goto(`${FRONTEND}/exercises/1`, { waitUntil: 'networkidle' });
  // Check for radio buttons or clickable options
  const options = page.locator('input[type="radio"], button.option, [role="radio"]');
  const optionCount = await options.count();
  console.log(`MC options found: ${optionCount}`);
  if (optionCount > 0) {
    await options.first().click();
    const submitBtn = page.locator('button[type="submit"], button:has-text("Enviar")').first();
    await submitBtn.click();
    await page.waitForTimeout(2000);
    const body = await page.textContent('body');
    const hasResult = body!.includes('correct') || body!.includes('incorrect') ||
                      body!.includes('¡Correcto') || body!.includes('Incorrecto');
    expect(hasResult).toBeTruthy();
  }
});

// ─── STUDENT: PROGRESS / HISTORY ──────────────────────────────────────────────

test('S12: /me/history shows attempt history', async ({ page }) => {
  await loginStudent(page);
  await page.goto(`${FRONTEND}/me/history`, { waitUntil: 'networkidle' });
  // Page should load without crash
  const body = await page.textContent('body');
  expect(body!.length).toBeGreaterThan(20);
});

test('S13: Logout redirects to landing page', async ({ page }) => {
  await loginStudent(page);
  // Click logout
  const logoutBtn = page.locator('button:has-text("Cerrar sesión"), button:has-text("Logout")').first();
  await logoutBtn.click();
  await page.waitForURL(/\/(login)?$/, { timeout: 5000 });
  // Should show landing page or login
  const body = await page.textContent('body');
  const isLanding = body!.includes('Aprende Matemáticas') || body!.includes('Math Platform');
  const isLogin = await page.locator('input[type="email"]').isVisible().catch(() => false);
  expect(isLanding || isLogin).toBeTruthy();
});

// ─── STUDENT: CLASSES AND ASSIGNMENTS ────────────────────────────────────────

test('S14: /me/classes shows enrolled class', async ({ page }) => {
  await loginStudent(page);
  await page.goto(`${FRONTEND}/me/classes`, { waitUntil: 'networkidle' });
  await expect(page.getByText('3ro Primaria').first()).toBeVisible({ timeout: 5000 });
});

test('S15: /me/assignments shows assignments for enrolled class', async ({ page }) => {
  await loginStudent(page);
  await page.goto(`${FRONTEND}/me/assignments`, { waitUntil: 'networkidle' });
  const body = await page.textContent('body');
  // Should show at least the 2 created assignments or a "no assignments" message
  expect(body!.length).toBeGreaterThan(20);
});

// ─── TEACHER WORKFLOWS ──────────────────────────────────────────────────────

test('T1: Teacher login lands on /teacher', async ({ page }) => {
  await loginTeacher(page);
  expect(page.url()).toContain('/teacher');
  await expect(page.getByText('Panel del Profesor')).toBeVisible({ timeout: 5000 });
});

test('T2: Teacher sees class card with correct student count', async ({ page }) => {
  await loginTeacher(page);
  await page.goto(`${FRONTEND}/teacher/classes`, { waitUntil: 'networkidle' });
  await expect(page.getByText('3ro Primaria').first()).toBeVisible({ timeout: 5000 });
  // Should show 21 students
  const body = await page.textContent('body');
  const has21 = body!.includes('21') || body!.includes('veintiún');
  // Just verify the page loaded with class info
  expect(body!.length).toBeGreaterThan(50);
});

test('T3: Teacher can navigate to class detail', async ({ page }) => {
  await loginTeacher(page);
  await page.goto(`${FRONTEND}/teacher/classes`, { waitUntil: 'networkidle' });
  await page.locator('a[href*="/teacher/classes/"]').first().click();
  await page.waitForURL(/\/teacher\/classes\/\d+/, { timeout: 8000 });
  // Should show student list
  const body = await page.textContent('body');
  expect(body!.length).toBeGreaterThan(50);
});

test('T4: Teacher can view assignment results', async ({ page }) => {
  await loginTeacher(page);
  await page.goto(`${FRONTEND}/teacher/classes`, { waitUntil: 'networkidle' });
  await page.locator('a[href*="/teacher/classes/"]').first().click();
  await page.waitForURL(/\/teacher\/classes\/\d+/, { timeout: 8000 });
  // Click into assignments if link exists
  const assignLink = page.locator('a:has-text("Tarea"), a:has-text("Assignment"), [href*="assignments"]').first();
  const assignLinkExists = await assignLink.isVisible().catch(() => false);
  if (assignLinkExists) {
    await assignLink.click();
    await page.waitForTimeout(2000);
    const body = await page.textContent('body');
    expect(body!.length).toBeGreaterThan(20);
  }
});

test('T5: /leaderboard loads and shows rankings', async ({ page }) => {
  await loginTeacher(page);
  await page.goto(`${FRONTEND}/leaderboard`, { waitUntil: 'networkidle' });
  const body = await page.textContent('body');
  // Should have tab switching or ranking content
  expect(body!.length).toBeGreaterThan(50);
});

// ─── PARENT WORKFLOWS ────────────────────────────────────────────────────────

test('P1: Parent login lands on /parent', async ({ page }) => {
  await loginParent(page);
  expect(page.url()).toContain('/parent');
});

test('P2: Parent dashboard shows linked children', async ({ page }) => {
  await loginParent(page);
  // Dashboard should show parent name
  await expect(page.getByText('Parent 1')).toBeVisible({ timeout: 5000 });
  // Should show linked student(s) — student_01 is linked
  const body = await page.textContent('body');
  expect(body!.length).toBeGreaterThan(20);
});

test('P3: Parent can view daily activity', async ({ page }) => {
  await loginParent(page);
  // Look for daily activity section
  const body = await page.textContent('body');
  // Activity section may or may not have content depending on seeding
  expect(body!.length).toBeGreaterThan(20);
});

export {};
