# PHASE 2 — Audit DB Schema
**Date:** 2026-04-21
**Status:** ✅ COMPLETE (with findings)

---

## 1. Tables Inventory (21 tables)

| Table | Rows | Notes |
|---|---|---|
| users | 86 | Passwords bcrypt-hashed ✅ |
| students | 46 | |
| teachers | 28 | |
| parents | 12 | |
| topics | 53 | |
| units | 79 | |
| lessons | 101 | |
| exercises | 280 | |
| student_topic_progress | 33 | |
| sessions | 15 | FK: user_id ✅ |
| notifications | 2 | FK: user_id ✅ |
| achievements | 2 | |
| assignments | 0 | Empty |
| assignment_exercises | 0 | Empty |
| class_enrollments | 0 | Empty |
| classes | 3 | |
| parent_student_links | 0 | Empty |
| exercise_attempts | 1 | Single test attempt |
| student_assignments | 0 | Empty |
| leaderboard_cache | 0 | Empty |
| classroom_syncs | 0 | Empty |

**✅ FK Integrity:** Zero orphan rows across all tables.

---

## 2. Schema Per Table — Key Columns

### `users`
`id, email, password_hash, role (enum), created_at`
✅ No `username` column — auth is email-based only.

### `students`
`id, user_id (FK→users.id), display_name, created_at`
✅ Proper 1:1 with users via `user_id` FK.

### `teachers`
`id, user_id (FK→users.id), display_name, created_at`
✅ Same pattern as students.

### `parents`
`id, user_id (FK→users.id), created_at`
✅ Same pattern.

### `topics`
`id, slug, title, description, icon_name, parent_id (FK→self), created_at`
✅ Hierarchical topics supported via `parent_id`.

### `units`
`id, topic_id (FK→topics.id), slug, title, description, order_index`
✅ No `created_at` —minor observability gap.

### `lessons`
`id, unit_id (FK→units.id), title, content (TEXT), order_index`
✅ Has `content_type`? (Check in Phase 3 if column exists in model but not shown here)
✅ No `created_at`.

### `exercises`
`id, unit_id (FK→units.id), lesson_id (FK→lessons.id, NULLABLE), slug, title, exercise_type (enum), difficulty (enum), points_value, data (JSONB), hints (JSONB), is_anked, is_summative`
✅ JSONB for flexible data storage.
✅ `lesson_id` is nullable — allows exercises without a lesson (135 of them).

### `student_topic_progress`
`id, student_id (FK→students.id), topic_id (FK→topics.id), mastery_level, last_activity`
✅ Only 33 rows for 46 students — most students have zero recorded progress.

### `sessions`
`id, user_id (FK→users.id), token_hash, expires_at, created_at`
✅ Token-based sessions (not JWT for sessions table).

### `notifications`
`id, type, title, body, link, read (bool), created_at, user_id (FK→users.id)`
✅ `user_id` is nullable — notifications can exist without a user.

### `exercise_attempts`
`id, student_id (FK→students.id), exercise_id (FK→exercises.id), answer_json (JSONB), correct (bool), points_earned, xp_earned, time_spent_seconds, attempted_at, assignment_id (FK→assignments.id, NULLABLE)`
✅ Only 1 attempt recorded (from smoke test).

### `achievements`
`id, slug, title, description, icon_name, criteria_type, criteria_config`
✅ Achievements are global, not per-user (no FK to users).

---

## 3. ⚠️ CRITICAL: ExerciseType Enum Mismatch

**Python model** (`ExerciseType`):
```
multiple_choice, numeric, true_false, ordering, bar_model, word_problem
```

**PostgreSQL enum (`exercisetype`)**:
```
multiple_choice, numeric
```

**Impact:**
- 4 enum values in Python don't exist in DB: `true_false`, `ordering`, `bar_model`, `word_problem`
- If any code inserts an exercise with these types → `invalid input value for enum exercisetype` crash
- Current exercises: only `multiple_choice` (110) and `numeric` (170) ✅ working
- The `bar_model` and `word_problem` renderers exist in frontend but **no exercises use them**
- The `true_false` and `ordering` types have **no renderers** at all

**⚠️ CRITICAL — Action required:** Add missing values to DB enum.

---

## 4. ⚠️ MAJOR: 135 Exercises Without lesson_id (48% of all exercises)

```
Exercises WITHOUT lesson_id: 135  (IDs 357–636, the "old" curriculum)
Exercises WITH lesson_id: 145     (IDs 484–636, the "new" curriculum added in Phase 11)
Total: 280
```

**Root cause:** The old curriculum seed (pre-Phase 11) created exercises attached only to `unit_id`, not to a specific `lesson_id`. Only the new G1–G6 curriculum exercises (IDs 484+) have `lesson_id` set.

**Impact:**
- Student browsing by lesson works for the 145 exercises with lesson_id
- The 135 "old" exercises appear in topic/unit listings but have no associated lesson in the UI
- The lesson page (`GET /api/lessons/{id}`) won't show these exercises
- The "practice" flow that walks through lesson exercises will skip 135 exercises

**Verifying the split:**

| Set | lesson_id | unit_id | count |
|---|---|---|---|
| Old curriculum | NULL | set | 135 |
| New curriculum (G1-G6) | set | set | 145 |

**Both sets have `unit_id` set** — the difference is only `lesson_id`.

---

## 5. ⚠️ HIGH: 45 Lessons Without Any Exercises

Lessons with content but no exercises linked:

```
id=112 title=Contar hasta 20 unit_id=103
id=119 title=El triángulo unit_id=109
id=113 title=Mayor y menor unit_id=104
id=121 title=Decenas unit_id=111
id=115 title=Sumar con 10 unit_id=106
id=116 title=Restar hasta 5 unit_id=107
id=117 title=Restar desde 10 unit_id=108
... (and 38 more)
```

**Total: 45 lessons with no exercises.**

These are the lesson content shells with `:::tryit::: blocks` in them but no actual exercises seeded.

---

## 6. ⚠️ MEDIUM: student_topic_progress = 33 rows (46 students)

46 students exist but only 33 have any `student_topic_progress` record. This means:
- 13 students have never started any topic
- The `mastery_level` tracking is incomplete
- This might be expected for brand-new students — but worth tracking

---

## 7. ✅ Exercises FK Integrity

- `unit_id`: All exercises reference a valid unit (0 orphans)
- `lesson_id`: When set, references valid lesson (0 orphans)
- `assignment_id` in `exercise_attempts` can be NULL (optional) ✅

---

## 8. ✅ Parent-Stuent Links

0 invalid links. `parent_student_links` table is clean.

---

## 9. ✅ Sessions Integrity

0 orphan sessions. All sessions reference a valid user.

---

## 10. ✅ Notifications Integrity

2 notifications exist with valid `user_id`.

---

## 11. Indexes Present

Indexes detected for:
- `exercises.unit_id`
- `exercises.lesson_id`
- `units.topic_id`
- `lessons.unit_id`
- `sessions.user_id`
- `notifications.user_id`
- `student_topic_progress.student_id`
- `student_topic_progress.topic_id`
- `class_enrollments.student_id`
- `class_enrollments.class_id`

Full index list requires reading from `pg_indexes` (container filesystem).

---

## PHASE 2 — Completion Criteria

| Criteria | Status |
|---|---|
| All 21 tables inventoried with row counts | ✅ |
| Enum mismatch documented | ⚠️ CRITICAL |
| FK orphans = 0 | ✅ |
| Topics without units = 0 | ✅ |
| Units without lessons = 0 | ✅ |
| **Lessons without exercises = 45** | ⚠️ HIGH |
| **135 exercises without lesson_id** | ⚠️ MAJOR |
| Seed users with hashed passwords | ✅ |
| `PHASE_2_findings.md` written | ✅ |

---

## Open Items Carried Forward

| Severity | Issue | Phase |
|---|---|---|
| CRITICAL | ExerciseType enum missing 4 values in DB | Phase 3 |
| MAJOR | 135 exercises without lesson_id (can't be discovered via lesson flow) | Phase 3 |
| HIGH | 45 lessons with no exercises (content shells) | Phase 3/5 |
| MEDIUM | Only 33/46 students have any progress record | Phase 8 |
| LOW | `units`, `lessons` tables missing `created_at` (observability gap) | Phase 3 |
