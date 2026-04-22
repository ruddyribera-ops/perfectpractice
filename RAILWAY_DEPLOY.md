# ============================================
# Railway Deployment Environment Variables
# ============================================
# Copy these to Railway → Variables for each service

# ===================
# BACKEND (port 8000)
# ===================
BACKEND_SERVICE=math-platform-backend

# Database
DATABASE_URL=postgresql+asyncpg://USER:PASSWORD@HOST:5432/math_platform

# Redis
REDIS_URL=redis://USER:PASSWORD@HOST:6379

# JWT (use long random strings — generate with: openssl rand -base64 32)
JWT_SECRET=your-32-char-minimum-secret-here
JWT_REFRESH_SECRET=your-32-char-refresh-secret-here

# Google Classroom OAuth (optional)
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REDIRECT_URI=https://your-backend-domain.up.railway.app/api/classroom/oauth/callback

# ===================
# FRONTEND (port 3000)
# ===================
NEXT_PUBLIC_API_URL=https://your-backend-domain.up.railway.app

# ===================
# RAILWAY SERVICES SETUP
# ===================

# IMPORTANT: Railway spins up services as SEPARATE containers.
# You'll need TWO services:
#
# Service 1: Backend
#   Root Directory: /backend
#   Build Command: pip install -r requirements.txt
#   Start Command: gunicorn --bind 0.0.0.0:8000 --workers 2 --threads 4 app.main:app
#   Variables: DATABASE_URL, REDIS_URL, JWT_SECRET, JWT_REFRESH_SECRET
#             GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REDIRECT_URI
#
# Service 2: Frontend
#   Root Directory: /frontend
#   Build Command: npm install && npm run build
#   Start Command: npm start
#   Variables: NEXT_PUBLIC_API_URL=https://your-backend-domain.up.railway.app
#
# Service 3: PostgreSQL (use Railway's built-in postgres)
#   Add a PostgreSQL plugin → copy connection string to DATABASE_URL
#
# Service 4: Redis (use Railway's built-in redis)
#   Add a Redis plugin → copy connection string to REDIS_URL

# ===================
# HEALTH CHECK ENDPOINT
# ===================
# Add this to backend/app/main.py:
# @app.get("/health")
# async def health():
#     return {"status": "ok"}

# ===================
# DATABASE MIGRATION
# ===================
# After first deploy, run migrations inside Railway shell:
# python -m app.models.curriculum  # just imports — SQLAlchemy creates tables on startup if using Base.metadata.create_all
# Or use: alembic upgrade head       # if you have alembic set up