# PHASE 1 — Snapshot del entorno actual
**Date:** 2026-04-21
**Status:** ✅ COMPLETE (with findings)

---

## 1. Docker Stack

| Container | Image | Status | Ports |
|---|---|---|---|
| math-platform-backend-1 | math-platform-backend | **Up 3h** | 0.0.0.0:8000→8000 |
| math-platform-frontend-1 | math-platform-frontend | **Up 4h** | 0.0.0.0:3000→3000 |
| math-platform-postgres-1 | postgres:16-alpine | **Up 13h (healthy)** | 0.0.0.0:5432→5432 |
| math-platform-redis-1 | redis:7-alpine | **Up 13h** | 0.0.0.0:6379→6379 |
| gma-website-web-1 | gma-website-web | Up 15h | 0.0.0.0:8080→80 |
| eduflow-v2-frontend-1 | eduflow-v2-frontend | **Exited (0) 35h ago** | — |
| eduflow-v2-backend-1 | eduflow-v2-backend | **Exited (0) 35h ago** | — |

**Volumes:**
- `math-platform_postgres_data` ← **ACTIVE** (mounted to postgres-1)
- `math-platform_redis_data` ← **ACTIVE** (mounted to redis-1)
- Other volumes are from eduflow (Exited containers — ignore)

**结论:** Stack activo limpio — solo math-platform corriendo. Los containers eduflow están apagados y sus volumes son huérfanos.

---

## 2. Backend Health

```
GET http://localhost:8000/api/health
→ 200 {"status":"healthy","version":"1.0.0"}

GET http://localhost:8000/docs
→ 200 (Swagger UI disponible)
```

**结论:** Backend healthy y respondiendo.

---

## 3. Frontend Health

```
Frontend: All connection attempts failed
```

El frontend container está **Up 4h** pero拒绝 conexiones desde el backend container. Posibles causas:
1. El frontend está bindeado a `127.0.0.1:3000` (internal only) en vez de `0.0.0.0:3000`
2. Firewall/block en la red del container
3. El proceso Node.js murió pero el container sigue "Up"

**⚠️ FINDING — Severity: HIGH**
Frontend container Up pero no responde desde backend. Esto puede afectar el smoke test de Phase 10.

---

## 4. API Endpoints — Quick Check

```
POST /api/auth/login (student@test.com / test123)
→ 200 OK (token devuelto)

GET /api/topics (con auth)
→ 200 OK, 53 topics
```

**结论:** Auth working, topics API respondiendo.

---

## 5. Database Schema — Tables

**21 tablas detectadas:**

| Table | Row Count |
|---|---|
| users | 86 |
| students | 46 |
| teachers | 28 |
| parents | 12 |
| topics | 53 |
| units | 79 |
| lessons | 101 |
| exercises | 280 |
| student_topic_progress | 33 |
| sessions | 15 |
| achievements | 2 |
| notifications | 2 |
| assignments | 0 |
| assignment_exercises | 0 |
| class_enrollments | 0 |
| classes | 3 |
| parent_student_links | 0 |
| exercise_attempts | 1 |
| student_assignments | 0 |
| leaderboard_cache | 0 |
| classroom_syncs | 0 |

**结论:** Datos seed cargados. 86 usuarios en DB (many more than the 3 seed accounts — indica testing anterior).

---

## 6. Enum ExerciseType — CRITICAL MISMATCH ⚠️

**Python model** (`backend/app/models/curriculum.py`):
```
['multiple_choice', 'numeric', 'true_false', 'ordering', 'bar_model', 'word_problem']
```

**PostgreSQL enum** (`exercisetype`):
```
['multiple_choice', 'numeric']
```

**6 values en Python, solo 2 en Postgres.**

**⚠️ CRITICAL:**
- `bar_model` y `word_problem` están en el modelo Python pero **no existen en el DB enum**
- Exercises insertados con estos tipos fallarían con:
  `invalid input value for enum exercisetype: "bar_model"`
- La seed funcionó solo porque **ningún ejercicio usa esos tipos todavía**
- El fix temporal (Phase 0) de `ALTER TYPE ADD VALUE` no se aplicó persistentemente (el container fue recreado)

**Verificado en runtime:**
```
$ docker exec math-platform-backend-1 python -c "from app.models.curriculum import ExerciseType; print([e.value for e in ExerciseType])"
→ ['multiple_choice', 'numeric', 'true_false', 'ordering', 'bar_model', 'word_problem']

$ SELECT DISTINCT exercise_type FROM exercises;
→ multiple_choice, numeric
```

---

## 7. Seed Users — Password Hashing

```
Password hash sample:
  Hash starts with: $2b$12$Ea/CffX9lffC4 ...
  Length: 60 chars
```

**Formato:** bcrypt (`$2b$12$...`). ✅ Hashed correctly — no plaintext passwords.

**Seed accounts verificados:**

| Email | Role | Created |
|---|---|---|
| student@test.com | student | 2026-04-21 14:52:09 |
| profesor@test.com | teacher | 2026-04-21 14:52:09 |
| padre@test.com | parent | 2026-04-21 14:52:09 |

---

## 8. Enum UserRole — Python vs DB

**Python:** `['student', 'teacher', 'admin', 'parent']`
**DB (via FK constraint):** necesita verificarse en Phase 2

---

## PHASE 1 — Completion Criteria

| Criteria | Status |
|---|---|
| Docker compose status confirmado | ✅ |
| Backend + frontend respondiendo | ⚠️ Frontend no reachable desde backend (verificar) |
| Credenciales seed verificadas en DB | ✅ student@test.com, profesor@test.com, padre@test.com |
| Enum ExerciseType completo documentado | ⚠️ CRITICAL MISMATCH — 6 Python / 2 DB |
| `PHASE_1_findings.md` escrito | ✅ |

---

## Open Items Carried to Phase 2

1. **CRITICAL:** ExerciseType enum mismatch — documentar en Phase 2 schema audit
2. **HIGH:** Frontend no reachable desde el backend container (network debug)
3. **INFO:** 86 usuarios en DB (muchos de testing previo) — no es bug, solo información
