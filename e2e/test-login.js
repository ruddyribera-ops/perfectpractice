const { chromium } = require('@playwright/test');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  await page.goto('https://proactive-wisdom-production-cd0e.up.railway.app/login', { timeout: 20000 });
  console.log('Title:', await page.title());

  // Try input[type=email] and input[type=password] instead
  const emailInput = page.locator('input[type="email"]');
  const passwordInput = page.locator('input[type="password"]');
  const submitBtn = page.locator('button[type="submit"]');

  await emailInput.fill('student@test.com', { timeout: 5000 });
  console.log('Filled email');
  await passwordInput.fill('test123', { timeout: 5000 });
  console.log('Filled password');
  await submitBtn.click();
  console.log('Clicked submit');

  await page.waitForURL('**/student**', { timeout: 15000 });
  console.log('Redirected to:', page.url());

  const bodyText = await page.textContent('body');
  console.log('Dashboard chars:', bodyText.length);
  console.log('PASS: login + redirect works end-to-end');

  await browser.close();
})().catch(e => console.error('FAIL:', e.message));