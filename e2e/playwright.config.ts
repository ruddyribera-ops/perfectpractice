import { defineConfig } from '@playwright/test';

export default defineConfig({
  testMatch: '**/e2e/**/*.spec.ts',
  use: {
    baseURL: process.env.FRONTEND_URL || 'https://proactive-wisdom-production-cd0e.up.railway.app',
  },
  timeout: 30000,
  retries: 1,
  reporter: [['list']],
});
