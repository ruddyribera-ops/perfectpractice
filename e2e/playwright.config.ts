import { defineConfig } from '@playwright/test';

export default defineConfig({
  testMatch: '**/e2e/**/*.spec.ts',
  use: {
    baseURL: process.env.FRONTEND_URL || 'https://proactive-wisdom-production-cd0e.up.railway.app',
    launchOptions: {
      executablePath: 'C:/Users/Windows/AppData/Local/ms-playwright/chromium-1217/chrome-win64/chrome.exe',
    },
  },
  timeout: 30000,
  retries: 1,
  reporter: [['list']],
  projects: [
    { name: 'chromium', use: { browserName: 'chromium' } },
  ],
});
