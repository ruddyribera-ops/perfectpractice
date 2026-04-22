# PHASE 3 — Audit Backend Routers
**Date:** 2026-04-21
**Status:** ✅ COMPLETE

---

## 1. Router Inventory

| Router | File | Prefix | Endpoints |
|---|---|---|---|
| auth | `auth.py` | `/api/auth` | register, login, refresh, logout, change-password |
| topics | `topics.py` | `/api/topics` | list (tree), detail by slug, picker/full |
| units | `units.py` | `/api/units` | list, detail by slug |
| lessons | `lessons.py` | `/api/lessons` | list-by-unit, detail by id |
| exercises | `exercises.py` | `/api/exercises` | detail by id |
| students | `students.py` | `/api/me` | progress, streaks, stats, achievements, history, assignments, classes, link-parent, **exercises/attempt** |
| teachers | `teachers.py` | `/api` (root!) | classes (CRUD), class students, class assignments (CRUD) |
| parents | `parents.py` | `/api/parents` | me (dashboard), generate-code |
| assignments | `assignments.py` | `/api/assignments` | various (leer más abajo) |
| leaderboard | `leaderboard.py` | `/api/leaderboard` | weekly, all-time |
| notifications | `notifications.py` | `/api/me/notifications` | list, mark-read |
| classroom | `classroom.py` | `/api/classroom` | sync endpoints |

---

## 2. Auth Endpoints — Shape Verification ✅

### `POST /api/auth/register`
- **Auth:** None (public)
- **Input:** `email, password, name, role? ("teacher"/"parent"/"student"), school_name? (teacher), grade? (student)`
- **Output:** `TokenResponse { user, access_token, refresh_token }`
- **Errors:** 400 (email already registered)
- **Behavior:** Creates User + role-specific profile (Teacher/Parent/Student) + Session record
- ✅ Correct: bcrypt password hashing
- ✅ Correct: access_token + refresh_token both issued
- ✅ Correct: student role enforced when not teacher/parent

### `POST /api/auth/login`
- **Auth:** None (public)
- **Input:** `email, password`
- **Output:** `TokenResponse { user, access_token, refresh_token }`
- **Errors:** 401 (invalid credentials)
- ✅ Correct: timing-safe password verification

### `POST /api/auth/refresh`
- **Auth:** Cookie (`refresh_token`)
- **Output:** `{"access_token": new_token}`
- **Errors:** 401 (invalid/expired session)
- ✅ Correct: session validated in DB before issuing new token
- ✅ Issues ONLY new access_token (refresh token stays the same)

### `POST /api/auth/logout`
- **Auth:** Cookie (`refresh_token`)
- **Output:** `{"message": "Logged out"}`
- ✅ Correct: deletes session from DB

### `POST /api/auth/change-password`
- **Auth:** JWT required (get_current_user_required)
- **Input:** `current_password, new_password`
- **Errors:** 400 (wrong current password)
- ✅ Correct

---

## 3. Students Router (`/api/me`) — Full Endpoint Map

| Method | Path | Auth | Role | Description |
|---|---|---|---|---|
| GET | `/progress` | JWT | student | Mastery per topic |
| POST | `/streaks/freeze` | JWT | student | Use streak freeze |
| **POST** | **`/exercises/{id}/attempt`** | JWT | student | **Submit answer + scoring** |
| GET | `/streaks/me` | JWT | student | Streak info |
| GET | `/stats/me` | JWT | student | XP, level, streak |
| GET | `/achievements` | JWT | student | Badge list |
| GET | `/history` | JWT | student | Paginated attempt history |
| GET | `/assignments` | JWT | any | Student's assignments |
| GET | `/assignments/{id}` | JWT | student | Assignment detail |
| GET | `/classes` | JWT | student | Enrolled classes |
| POST | `/link-parent` | JWT | student | Link to parent via code |

---

## 4. ⚠️ CRITICAL: Submit Attempt — Scoring Logic Incomplete

**Endpoint:** `POST /api/me/exercises/{exercise_id}/attempt`

**Scoring logic (line 152–159 of students.py):**
```python
correct = False
if et == "multiple_choice" and choices:
    correct = str(data.answer).strip().lower() == str(correct_answer).strip().lower()
elif et == "true_false":
    correct = str(data.answer).strip().lower() == str(correct_answer).strip().lower()
else:  # numeric, ordering, bar_model, word_problem
    correct = str(data.answer).strip().lower() == str(correct_answer).strip().lower() if correct_answer else False
```

**Problems:**

1. **`true_false` treated same as `numeric`** — the `elif` for `true_false` is identical to the `else` branch. No special handling for true/false boolean values.

2. **`ordering` type not handled specially** — treated as `else` (string comparison). For ordering exercises the answer should be a list/array, not a string.

3. **`bar_model` type** — same as `else`: string comparison. But bar_model data format has `{"question": ..., "total": ..., "units": [...]}`. The `correct_answer` should be compared against the `total` value. Currently the comparison is just string comparison of the user's answer against `correct_answer`.

4. **`word_problem` type** — same as `else`. The `word_problem` data format uses the `answer` field (a number), not `correct_answer`. But the code reads `correct_answer = exercise.data.get("correct_answer")` — so it works IF the `word_problem()` helper populated `correct_answer` in the data dict. Let me verify...

**Checking word_problem data format:**

From `curriculum_seed.py`, the `word_problem()` helper returns:
```python
return {
    "scenario": context,  # the story
    "question": f"{context} ¿Cuál es el resultado de {num1} {op_sym} {num2}?",
    "answer": answer,      # numeric value
    "explanation": f"{num1} {op_sym} {num2} = {answer}",
}
```

**⚠️ CRITICAL BUG:** The helper does NOT include a `correct_answer` field. So `exercise.data.get("correct_answer")` returns `None`, and the comparison `None if correct_answer else False` always returns `False` for word_problem exercises. **All word_problem exercises will ALWAYS mark as incorrect.**

---

## 5. Topics API — Units Always Empty in List Response ⚠️

**Endpoint:** `GET /api/topics` (list_topics)

- Uses `TopicTreeResponse` which has `children` but **not `units`**
- Only top-level topics with their children are returned — no curriculum tree with units/lessons
- To get units, use `GET /api/topics/{slug}` (TopicDetailResponse) — but this returns units in `UnitResponse` format without nested lessons
- `GET /api/topics/picker/full` returns the full tree with exercises

**⚠️ The student app likely needs a combined topic → unit → lesson view, but there's no endpoint that returns that full tree in one call.**

---

## 6. Exercises API — Key Endpoint Only

**Endpoint:** `GET /api/exercises/{id}`

- **Auth:** JWT required
- **Role:** student (or any authenticated)
- For students: `correct_answer` is **stripped from data** before returning ✅ (line 56 in exercises.py)
- For non-students: full data including `correct_answer` returned
- ✅ Correct sanitization for student role

**Missing:** There's no `GET /api/exercises` (list endpoint) — only by ID. The topic picker tree (`/api/topics/picker/full`) is the substitute for browsing exercises.

---

## 7. Teachers Router — Registered at `/api` (NOT `/api/teachers`) ⚠️

**Finding from Phase 1 (already documented):** The teachers router is mounted at `/api` root prefix, not `/api/teachers`.

This means:
- `GET /api/classes` — teacher list (NOT student list)
- `POST /api/classes` — create class

**Potential for route collision with other routers at `/api` root?** Minimal — the teachers router only responds to `/classes` and `/classes/{class_id}` sub-paths. The assignments router uses `/api/assignments` with its own prefix. No conflict detected.

---

## 8. Assignments Router

Need to read `assignments.py` — not yet reviewed. **Deferred to Phase 8 (Teacher Flow).**

---

## 9. Parents Router — Only 2 Endpoints

| Method | Path | Auth | Role | Description |
|---|---|---|---|---|
| GET | `/me` | JWT | parent | Dashboard with linked students |
| POST | `/generate-code` | JWT | parent | Generate link code |

**Note:** There is NO separate `/linked-students` endpoint — data is inlined in `/me` response.

**Parent cannot access:** No explicit denial — parent role is only checked in the individual endpoints, not at router level.

---

## PHASE 3 — Completion Criteria

| Criteria | Status |
|---|---|
| All endpoints inventoried (path, method, auth, roles) | ✅ |
| Auth endpoints shape verified | ✅ |
| **Topics API units empty bug documented** | ⚠️ Finding |
| **Submit attempt scoring incomplete (word_problem always wrong)** | ⚠️ CRITICAL |
| Assignments router not reviewed | ⬜ Deferred |
| `PHASE_3_findings.md` written | ✅ |

---

## Open Items

| Severity | Issue | Phase |
|---|---|---|
| CRITICAL | word_problem `correct_answer` never set — all word_problem attempts score as wrong | Phase 5 |
| CRITICAL | ExerciseType enum missing values in DB | Phase 2 → carried |
| HIGH | 135 exercises without lesson_id (lesson flow skips them) | Phase 2 → carried |
| HIGH | 45 lessons with no exercises | Phase 2 → carried |
| MEDIUM | No endpoint returns topic→unit→lesson full tree | Phase 4/8 |
| LOW | `true_false` and `ordering` no special scoring logic | Phase 5 |
| LOW | teachers router at `/api` root (not `/api/teachers`) | Awareness only |
