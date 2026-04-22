# Unique Platform Features — Perfect Practice Bolivia

## What Makes This Platform Different from Khan Academy

Khan Academy is a great generic platform. This platform is built specifically for Bolivian students, parents, and teachers — with the CPA (Concrete → Pictorial → Abstract) methodology and Singapore Math bar model as the core pedagogical engine.

---

## 1. Interactive Bar Model Construction (Phase 2)

**What it is:** A drag-and-drop bar model builder where students physically construct their understanding by placing labeled segments on a visual bar, not just typing an answer.

**Why it matters:** The bar model is the primary problem-solving tool in Singapore Math — it makes abstract relationships concrete. Most digital platforms show static bar diagrams. This platform lets students **build** them.

**How it works:**
- Student drags segments onto the bar or taps to place them
- Each segment has a label (e.g., "Manzanas", "Naranjas") and numeric value
- Total is shown visually on the bar
- Construction JSON is saved to `exercise_attempts.answer_json`
- Teacher sees the **replay** of the construction in the thinking process view

**Files:**
- `frontend/app/components/LessonVisuals.tsx` — `InteractiveBarModel` component
- `frontend/lib/api.ts` — `BarModelSegment` + `BarModelConstructionJSON` types
- `backend/app/routers/students.py` — stores construction in `answer_json`

---

## 2. Parent Daily Playbook (Phase 3)

**What it is:** Instead of a dashboard showing grades, the parent portal shows one **specific, hands-on activity** per day (rotating daily), designed for a Bolivian parent to do with their child using objects from home.

**Why it matters:** The platform's primary user is the **Bolivian parent who never learned math the Singapore way** and doesn't know how to help their child. Traditional dashboards leave them sidelined. This playbook gives them a concrete role.

**Activity examples (Grades 1–4):**
- Grade 1: "Carrera de Sumas" — use toy cars to practice addition
- Grade 2: "Multiplicación con Grupos" — arrange objects in rows/columns
- Grade 3: "Valor Posicional con Monedas" — use 1, 10, 100 centavo coins to understand place value
- Grade 4: "Fracciones con Frutas" — divide a real fruit to understand fractions

**How it works:**
- `parent_activities` table: 20 culturally-Bolivian activities, 5 per grade
- Daily selection: `day_index = (day_of_year - 1) % 5` — same activity for all students of that grade on the same day
- Parent marks activity complete → streak increments
- Streak unlocks `FAMILY_PARTICIPATION` badges at 3, 7, 30 days

**Files:**
- `backend/app/routers/parents.py` — `POST /parents/activities/{id}/complete`
- `backend/app/models/parent.py` — `ParentActivity` + `ParentActivityCompletion` ORM
- `frontend/app/parent/page.tsx` — daily activity card + complete button

---

## 3. Teacher Thinking Process View (Phase 4)

**What it is:** After a student completes a bar_model exercise, the teacher sees a **segment-by-segment animated replay** of how the student built the bar model — not just whether they got it right.

**Why it matters:** In Singapore Math pedagogy, the bar model IS the thinking process. If a student gets the answer right but builds the bar incorrectly, the teacher needs to see that. If they get it wrong, the replay shows exactly where the misunderstanding happened.

**How it works:**
- Every attempt stores `answer_json` with the full construction JSON
- Teacher clicks "Ver Proceso 🧠" on any bar_model exercise in assignment results
- `ThinkingProcessView` modal replays segment placement with CSS animations
- Per-attempt view: correct/incorrect, time spent, XP earned, timestamp

**Files:**
- `backend/app/routers/teachers.py` — `GET /students/{id}/thinking_process`
- `frontend/components/ThinkingProcessView.tsx` — animated replay component
- `backend/app/schemas/assignment.py` — `ExerciseResultItem` now includes `exercise_type`

---

## 4. Parent Engagement Streaks + Family Badges (Phase 5)

**What it is:** The parent's participation streak is tracked separately from the student's streak. When a parent completes a daily playbook activity with their child, the parent's streak increments — and after 3, 7, and 30 consecutive days, the **child** earns family participation badges.

**Why it matters:** In Bolivian family dynamics, the parent is the co-teacher. If the parent doesn't engage, the student doesn't have support at home. This feature makes the parent's involvement visible and rewarding.

**Badges:**
- 🏠 `familia-participa-3` — 3 consecutive days of parent completing activities
- 🏠 `familia-participa-7` — 7 consecutive days
- 🏠 `familia-unida-30` — 30 consecutive days

**Files:**
- `backend/app/routers/students.py` — `_check_achievements` + `family_participation_*` triggers
- `backend/app/routers/parents.py` — streak logic in `complete_activity`
- `backend/app/models/user.py` — `Student.parent_participation_streak`

---

## 5. Top Helper Peer Recognition (Phase 6)

**What it is:** Students earn XP and badges not just for getting answers right, but for **helping their peers**. When a student receives help from a classmate, they mark it — and the helper earns credit toward a `top-helper` badge after helping 3+ unique peers in one week.

**Why it matters:** In a classroom, the best way to learn something is to teach it. This feature creates a social incentive for peer teaching without requiring the teacher to facilitate every interaction.

**How it works:**
- Student submits attempt with optional `helped_peer_id: int`
- `POST /me/helps/{attempt_id}` marks that an attempt received peer help
- `_count_helped_peers_this_week()` counts unique helped peers
- Badge `top-helper` awarded when count >= 3

**Files:**
- `backend/app/models/progress.py` — `ExerciseAttempt.helped_peer_id` column
- `backend/app/routers/students.py` — `mark_helped_received` endpoint + `top_helper` trigger
- `frontend/lib/api.ts` — `markHelpedReceived()` method

---

## 6. Culturally Bolivian Content (Phase 1)

**What it is:** All lesson content, word problems, and activities use Bolivian contexts — La Paz prices, Bolivianos (Bs), local food, cultural references. No "Alice bought apples in a generic store."

**Why it matters:** A student in La Paz connects with "una trufa de La Paz a Bs. 5" far more than "an apple at $0.50". Cultural relevance drives engagement and makes math meaningful.

**Content examples:**
- Word problems reference Bolivian foods, school supplies, market prices
- Parent activities use real objects found in Bolivian homes (coins, fruits, toys)
- Emoji usage kept for visual engagement without breaking rendering

**Files:**
- `backend/seed/curriculum_seed.py` — all content in Spanish with Bolivian contexts
- `audit/PHASE1_CONTENT_CLEANUP.md` — documentation of content audit

---

## 7. Curriculum De-duplication (Phase 0)

**What it was:** The seed data had 7 duplicate topics and 1 duplicate unit, causing students to see the same content twice.

**What changed:** All duplicates consolidated, FK references remapped, order indexes re-sequenced.

**Result:** 45 topics / 78 units / 101 lessons / 280 exercises — no duplication.

---

## Architecture Notes

### API Path Conventions
- Teacher endpoints for students: `/api/students/{id}/...` (NOT `/api/teachers/students/...`)
- Students (me): `/api/me/...`
- Parents: `/api/parents/...`
- Assignments: `/api/assignments/{id}/results`
- Classes: `/api/classes/...`

### Bar Model Data Flow
```
Frontend: InteractiveBarModel (drag segments)
    ↓ onChange(segs, numericAnswer)
Exercise Page: constructs BarModelConstructionJSON
    ↓ POST /api/me/exercises/{id}/attempt {answer: "5", ...}
Backend: stores construction in exercise_attempts.answer_json
    ↓ GET /api/students/{id}/thinking_process?exercise_id=X
Teacher: replay in ThinkingProcessView modal
```

### Parent Streak Data Flow
```
Parent opens /parent dashboard
    ↓ GET /api/parents/me (daily activity computed by day_of_year % 5)
Parent clicks "Completé esta actividad"
    ↓ POST /api/parents/activities/{id}/complete {student_id: X}
Backend: records completion + increments student.parent_participation_streak
    ↓ calls _check_achievements(db, student)
Student earns FAMILY_PARTICIPATION badge at 3/7/30 days
```

---

## What's NOT Implemented Yet (Phases 9–10)

| Phase | Status |
|---|---|
| Phase 9 — Railway Deployment + Verify-Deploy.ps1 | TODO |
| Phase 10 — KPI Monitoring Framework | TODO |

---

*Document generated after Phase 7 integration testing.*
*Last updated: 2026-04-22*
