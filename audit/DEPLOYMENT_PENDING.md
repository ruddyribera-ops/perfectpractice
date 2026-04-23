# Phase 9 — Deployment — BLOCKED

**Status:** `railway login` expired — CLI returns "Unauthorized" on every command.
**What was verified:** docker compose up -d works locally, 9/9 integration tests pass.

**What to do when auth is restored:**
1. `railway login` — re-authenticate
2. `railway link` — connect to the Railway project
3. `railway up` — deploy from the `main` branch

---

## Railway Deployment Checklist

When `railway login` is re-established, run through this sequence:

### Pre-deploy
- [ ] `railway login` — re-authenticate CLI
- [ ] `railway link` — connect `C:/Users/Windows/math-platform` to Railway project
- [ ] Verify Railway project has PostgreSQL plugin (math_platform DB)
- [ ] Set env vars in Railway dashboard:
  - `DATABASE_URL` (PostgreSQL plugin provides this)
  - `REDIS_URL` (Redis plugin or `redis://redis:6379`)
  - `JWT_SECRET` (32+ char random string)
  - `JWT_REFRESH_SECRET` (32+ char random string)
- [ ] `NEXT_PUBLIC_API_URL` set to the Railway backend URL

### Deploy
- [ ] `railway up` from `C:/Users/Windows/math-platform` (detects Dockerfile in backend/ and frontend/)
- [ ] Note the Railway-provided URL for backend + frontend

### Post-deploy smoke test
- [ ] `powershell -File $HOME/.config/opencode/scripts/Verify-Deploy.ps1 -Url "<railway-backend-url>" -WaitSeconds 45`
- [ ] Smoke test: login as `student@test.com`, `profesor@test.com`, `padre@test.com`
- [ ] Verify `/api/health` returns 200
- [ ] Verify `/api/parents/me` returns `daily_activity`
- [ ] Verify thinking process endpoint works: `GET /api/students/46/thinking_process?exercise_id=535`

### Env vars to set in Railway dashboard

| Variable | Source | Notes |
|---|---|---|
| `DATABASE_URL` | Railway PostgreSQL plugin | Auto-provided |
| `REDIS_URL` | Railway Redis plugin or `redis://redis:6379` | |
| `JWT_SECRET` | Generate 32+ char random string | Required for auth |
| `JWT_REFRESH_SECRET` | Generate separate 32+ char random | Required for refresh tokens |
| `NEXT_PUBLIC_API_URL` | Railway backend URL | e.g. `https://math-platform-backend.up.railway.app` |
| `POSTGRES_DB` | `math_platform` | Must match plugin DB name |
| `POSTGRES_USER` | `postgres` | Default |
| `POSTGRES_PASSWORD` | Railway env | From plugin |

---

## Docker Image Structure

```
backend/Dockerfile         — python:3.12-slim + gunicorn (2 workers, 4 threads)
backend/Dockerfile.dev     — development with uvicorn --reload (NOT for production)
frontend/Dockerfile        — node:20-alpine multi-stage (deps → build → standalone)
docker-compose.yml         — postgres + redis + backend + frontend (dev stack)
```

## Production Deployment Notes

- **Backend uses gunicorn** (not uvicorn directly) for production stability
- **Frontend uses `standalone` output** from `next build` — no Node.js server needed at runtime
- **PostgreSQL and Redis** should use Railway's plugin system (persistent volumes)
- **No volume mounts in Railway** — all env vars, no `./backend:/app` mounts
- For Railway, the `Dockerfile.dev` is irrelevant — only `Dockerfile` is used
