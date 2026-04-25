const { chromium } = require('@playwright/test');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  // Capture ALL network requests
  const apiCalls = [];
  page.on('request', r => {
    if (r.url().includes('/api/')) apiCalls.push({ method: r.method(), url: r.url() });
  });
  page.on('response', r => {
    if (r.url().includes('/api/')) apiCalls.push({ url: r.url(), status: r.status() });
  });
  page.on('console', m => console.log(`[${m.type()}] ${m.text().substring(0, 150)}`));

  await page.goto('https://proactive-wisdom-production-cd0e.up.railway.app/login', {
    waitUntil: 'networkidle',
    timeout: 15000
  });

  console.log('\n--- Login form fill ---');
  await page.locator('input[type="email"]').fill('student@test.com');
  await page.locator('input[type="password"]').fill('test123');
  console.log('Filled credentials');

  console.log('\n--- Click submit ---');
  await page.locator('button[type="submit"]').click();
  console.log('Clicked, waiting 8s...');
  await page.waitForTimeout(8000);

  console.log('\n--- Final state ---');
  console.log('URL:', page.url());
  console.log('API calls made:', JSON.stringify(apiCalls, null, 2));

  await browser.close();
})().catch(e => console.error('FAIL:', e.message));