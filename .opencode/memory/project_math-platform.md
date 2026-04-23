# Math Platform — Production State

## Deploy URLs
- **Backend**: `https://perfectpractice-production.up.railway.app`
- **Railway Project**: `https://railway.app/project/a8c01475-fd4c-4f2a-8512-2c0abd1dba0f`

## Seed Users (all password: `test123`)
- `student@test.com` — student role
- `profesor@test.com` — teacher role
- `padre@test.com` — parent role

## Database
- Railway PostgreSQL: `postgres.railway.internal:5432/math_platform`
- Local Docker: same credentials via `DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/math_platform`

## Known Issues
1. **Railway stale image**: Railway's public URL serves `[]` for `/api/topics` while `docker exec curl localhost:8000/api/topics` returns 45 topics. Railway is routing to an older Docker image that doesn't have the `topics` router registered. The container `math-platform-backend-1` itself also appears to be from an older build (health shows `version: 1.0.0` despite pushes of `1.0.1` and `1.0.2`). **Fix: manual redeploy from Railway dashboard.**

2. **Railway CLI token invalid**: `railway login --token` rejected. CLI auth is broken in this environment.

3. **Playwright EACCESS**: Chrome cannot be launched inside OpenCode MCP on Windows. Defender/scan blocking. Fix: run as Administrator and add exclusions, or use Python httpx for testing instead.

## Verified Working (inside container)
- `/api/health` → `{"status":"healthy","version":"1.0.0"}`
- `/api/auth/login` → 200 for all 3 seed users
- `/api/topics` (from inside container via localhost:8000) → 45 topics ✅
- Database: 48 topics, 78 units, 101 lessons, 280 exercises

## Verified NOT Working (Railway public URL)
- `/api/topics` → `[]` (empty array, should be 45 topics)
- `/api/units` → 404

## Code Fixes Pushed
- `cb003e8`: make curriculum seed idempotent (skip existing units/lessons/exercises)
- `df10071`: bump backend version to 1.0.2
- `afa6a06`: fix all TypeScript build errors + directory reorganization