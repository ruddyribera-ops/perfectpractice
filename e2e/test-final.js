const { chromium } = require('@playwright/test');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  const results = [];

  try {
    // Test 1: backend health
    const r1 = await page.request.get('https://lucid-serenity-production.up.railway.app/api/health');
    const b1 = await r1.json();
    results.push({ test: 'backend /api/health', status: r1.status() === 200 && b1.status === 'healthy' ? 'PASS' : 'FAIL', detail: `${r1.status()} ${JSON.stringify(b1)}` });
  } catch(e) { results.push({ test: 'backend /api/health', status: 'FAIL', detail: e.message }); }

  try {
    // Test 2: unauthenticated /api/me -> 401
    const r2 = await page.request.get('https://lucid-serenity-production.up.railway.app/api/me/stats/me');
    results.push({ test: 'unauthenticated /api/me returns 401', status: r2.status() === 401 ? 'PASS' : 'FAIL', detail: `${r2.status()}` });
  } catch(e) { results.push({ test: 'unauthenticated /api/me returns 401', status: 'FAIL', detail: e.message }); }

  try {
    // Test 3: login + redirect to /student
    await page.goto('https://proactive-wisdom-production-cd0e.up.railway.app/login', { waitUntil: 'domcontentloaded', timeout: 15000 });
    await page.locator('input[type="email"]').fill('student@test.com');
    await page.locator('input[type="password"]').fill('test123');
    await page.locator('button[type="submit"]').click();
    await page.waitForURL('**/student**', { timeout: 15000 });
    results.push({ test: 'login redirects to /student dashboard', status: 'PASS', detail: page.url() });
  } catch(e) {
    results.push({ test: 'login redirects to /student dashboard', status: 'FAIL', detail: e.message.substring(0, 100) });
  }

  console.log('\n=== SMOKE TEST RESULTS ===');
  for (const r of results) {
    console.log(`[${r.status}] ${r.test} — ${r.detail}`);
  }
  const passed = results.filter(r => r.status === 'PASS').length;
  console.log(`\n${passed}/${results.length} passed`);

  await browser.close();
  process.exit(passed === results.length ? 0 : 1);
})();