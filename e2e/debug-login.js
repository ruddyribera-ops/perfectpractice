const { chromium } = require('@playwright/test');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  page.on('console', m => {
    if (m.type() === 'error') console.log('BROWSER ERR:', m.text());
  });
  page.on('requestfailed', r => console.log('REQ FAIL:', r.url(), r.failure().errorText));

  await page.goto('https://proactive-wisdom-production-cd0e.up.railway.app/login', {
    waitUntil: 'domcontentloaded',
    timeout: 15000
  });

  console.log('URL after load:', page.url());
  console.log('Title:', await page.title());

  await page.locator('input[type="email"]').fill('student@test.com');
  await page.locator('input[type="password"]').fill('test123');
  await page.locator('button[type="submit"]').click();

  await page.waitForTimeout(5000);
  console.log('URL after submit:', page.url());

  const body = await page.textContent('body');
  console.log('Body preview:', body.substring(0, 300));

  await browser.close();
})().catch(e => console.error('FAIL:', e.message));