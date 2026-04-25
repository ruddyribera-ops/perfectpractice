# Production Smoke Tests

Playwright end-to-end tests that verify the production Railway deployment is healthy.

## URLs

| Service | URL |
|---------|-----|
| Frontend | `https://proactive-wisdom-production-cd0e.up.railway.app` |
| Backend | `https://lucid-serenity-production.up.railway.app` |

## Tests

| # | Test | What it checks |
|---|------|----------------|
| 1 | `backend /api/health returns 200` | Backend health endpoint is responding |
| 2 | `frontend loads and shows login page` | Frontend is reachable and renders login |
| 3 | `login as student@test.com redirects to dashboard` | Auth flow works end-to-end |
| 4 | `unauthenticated /api/me returns 401` | Protected endpoint rejects unauthenticated requests |

## Run Locally

### Prerequisites
- Node.js 18+
- npm install

### Setup
```bash
cd e2e
npm install
npx playwright install --with-deps chromium
```

### Run
```bash
npm run smoke
```

### Override URLs
```bash
FRONTEND_URL=https://custom-frontend.railway.app \
BACKEND_URL=https://custom-backend.railway.app \
npm run smoke
```

## Run Against Production (CI)

These tests also run in GitHub Actions as part of the CI pipeline after each deploy to `main`.

See `.github/workflows/ci.yml` for the job configuration.

## Why These Tests?

They verify the three things that most commonly break after a deploy:
1. **Backend is unreachable** — `/api/health` catches this in < 1s
2. **Frontend can't reach API** — auth test catches CORS/network misconfig
3. **Auth redirect broken** — login → dashboard flow catches broken JWT or middleware
