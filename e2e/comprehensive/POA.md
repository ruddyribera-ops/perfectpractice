# MathPlatform Full E2E Test Plan
# Multi-Phase Comprehensive Workflow Coverage

## GUARDRAILS
- MAX 8 TOOL CALLS PER SPECIALIST SESSION — phases chunked accordingly
- Each phase is standalone-verified before proceeding to next
- If a phase fails: stop, report what broke, wait for guidance
- NO refactoring — test only; any bugs found are documented, not fixed mid-test
- Playwright uses bundled Chromium at `C:/Users/Windows/AppData/Local/ms-playwright/chromium-1217/chrome-win64/chrome.exe`
- Base URL Railway: `https://lucid-serenity-production.up.railway.app`
- Base URL Frontend: `https://proactive-wisdom-production-cd0e.up.railway.app`

---

## PHASE 1: INFRASTRUCTURE SETUP
**Goal: Create all test data (teacher, 21 students, 3 parents, 1 class, assignments)**
**Tool: PowerShell API scripts against Railway backend**
**Exit gate: All 27 accounts created + enrolled + linked**

### Phase 1.1 — Create teacher account + class + invite code
- [ ] Register teacher: `profesor_e2e@test.com` / `test123`
- [ ] Login teacher → get JWT
- [ ] Create class "3ro Primaria A" via `POST /api/teachers/classes`
- [ ] Capture `invite_code`
- [ ] Verify class exists: `GET /api/teachers/classes`

### Phase 1.2 — Create 21 student accounts + enroll in class
- [ ] Register 21 students: `student_01@test.com` … `student_21@test.com` / `test123`
- [ ] Each student logs in → joins class via `POST /api/classes/join/{invite_code}`
- [ ] Verify enrollment: teacher `GET /api/teachers/classes/{id}/students` returns 21

### Phase 1.3 — Create 3 parent accounts + link to students
- [ ] Register 3 parents: `parent_01@test.com`, `parent_02@test.com`, `parent_03@test.com` / `test123`
- [ ] Parent 1 links to students 01-07: `POST /api/me/link-parent {link_code}` (parent generates code, student uses it)
- [ ] Parent 2 links to students 08-14
- [ ] Parent 3 links to students 15-21
- [ ] Verify links: `GET /api/parents/me` shows all linked students

### Phase 1.4 — Create teacher assignments
- [ ] Login as teacher
- [ ] Pick 3 exercises from topic picker: `GET /api/topics/picker/full`
- [ ] Create assignment "Tarea Números 1" with those 3 exercises: `POST /api/teachers/classes/{class_id}/assignments`
- [ ] Create a second assignment "Tarea Números 2" with 2 different exercises
- [ ] Verify: `GET /api/teachers/classes/{class_id}/assignments` returns 2

---

## PHASE 2: STUDENT WORKFLOW TESTS (Playwright)
**Goal: Every click path for a student verified**
**Tool: Playwright Chromium against Railway frontend**
**Exit gate: 15 student workflow tests all pass**

### Phase 2.1 — Core Dashboard
- [ ] `student_01@test.com` logs in → lands on `/`
- [ ] Dashboard shows: XP Total, Nivel, Racha, Hielos, Ejercicios cards
- [ ] Streak freeze alert shows if at risk
- [ ] XP progress bar renders
- [ ] "Continúa Aprendiendo" section has links to /topics and /me/history
- [ ] Achievements section (if any) renders
- [ ] "Mis Clases" section renders with enrolled class
- [ ] Language switcher (es-BO, en-US, fr, pt-BR) changes locale

### Phase 2.2 — Topics → Unit → Lesson → Exercise navigation
- [ ] Navigate to `/topics` → shows topic grid
- [ ] Click first topic → `/topics/{slug}` → shows topic detail with units
- [ ] Units have "Ver Lecciones" link → `/topics/{slug}?tab=units` (or navigate to unit)
- [ ] Unit page shows lessons list
- [ ] Click lesson → `/lessons/{id}` → shows lesson with exercise list
- [ ] Click exercise → `/exercises/{id}` → shows exercise UI

### Phase 2.3 — Exercise Submission Flow (FULL CYCLE)
- [ ] `/exercises/{id}` page loads with question
- [ ] Submit correct answer
- [ ] Result screen shows: correct/incorrect, explanation, XP earned, streak updated
- [ ] **CRITICAL: "Continuar" or "Siguiente" button exists → click it**
- [ ] What happens next? Verify: does it go to next exercise? Lesson summary? Dashboard?
- [ ] Repeat for incorrect answer → verify different feedback
- [ ] For multiple choice → verify options render and are selectable
- [ ] For bar model → verify interactive builder renders
- [ ] For word problem → verify text input renders

### Phase 2.4 — Post-Exercise Return Path (the key bug check)
- [ ] After completing ALL exercises in a lesson: where does the UI land?
- [ ] Is there a "Volver a Lecciones" or "Regresar" path?
- [ ] Can you navigate back to `/topics` from inside an exercise?
- [ ] Does the back button work correctly?
- [ ] Is there a breadcrumb navigation?

### Phase 2.5 — Progress, Achievements, History
- [ ] `/me/history` → shows attempt history list
- [ ] Attempt history shows: exercise name, topic, correct/incorrect, XP earned, date
- [ ] Achievements page reachable → `/me/achievements` (or from dashboard)
- [ ] Streak visible on dashboard
- [ ] Stats visible on dashboard

### Phase 2.6 — Classes and Assignments
- [ ] `/me/classes` → shows enrolled class
- [ ] Class card click → class detail with assignments
- [ ] Assignment card click → `/me/assignments/{id}` → shows exercise list with status
- [ ] Start assignment → first exercise loads
- [ ] Complete assignment exercises → result summary shows

### Phase 2.7 — Logout and Auth Edge Cases
- [ ] Logout → redirects to `/login` (landing page)
- [ ] Clear cookies/token → try to access `/` → should show landing page (not crash)
- [ ] Expired token → API returns 401 gracefully

---

## PHASE 3: TEACHER WORKFLOW TESTS (Playwright)
**Goal: Every click path for a teacher verified**
**Tool: Playwright Chromium against Railway frontend**
**Exit gate: 10 teacher workflow tests all pass**

### Phase 3.1 — Teacher Dashboard
- [ ] `profesor_e2e@test.com` logs in → lands on `/teacher`
- [ ] Dashboard shows: "Panel del Profesor", class count, "Mis Clases" link
- [ ] "Tabla de Posiciones" link visible

### Phase 3.2 — Class Management
- [ ] Navigate to `/teacher/classes`
- [ ] See class card "3ro Primaria A" with student count
- [ ] Click class → `/teacher/classes/{id}` → class detail
- [ ] Student list shows all 21 students with: name, email, grade, XP, streak, avg mastery
- [ ] Remove one student → confirm removal → student disappears from list
- [ ] Re-add student (use invite link flow) → student reappears

### Phase 3.3 — Assignment Creation Flow
- [ ] From class detail → "Crear Tarea" button
- [ ] Topic picker opens: `GET /api/topics/picker/full`
- [ ] Select exercises from topic picker
- [ ] Set due date
- [ ] Submit → assignment created → appears in class assignments list
- [ ] Assignment detail shows exercise list

### Phase 3.4 — Assignment Results
- [ ] Navigate to assignment results: `/teacher/classes/{id}/assignments/{assignment_id}/results`
- [ ] Results show: total students, completion rate, avg score
- [ ] Per-student results: name, score, completion rate, rank
- [ ] Click student → thinking process view: `/students/{student_id}/thinking_process?exercise_id=X`

### Phase 3.5 — Leaderboard
- [ ] `/leaderboard` loads
- [ ] Shows weekly, monthly, all-time tabs
- [ ] Student ranks visible with XP
- [ ] Teacher's own rank visible

---

## PHASE 4: PARENT WORKFLOW TESTS (Playwright)
**Goal: Every click path for a parent verified**
**Tool: Playwright Chromium against Railway frontend**
**Exit gate: 6 parent workflow tests all pass**

### Phase 4.1 — Parent Dashboard
- [ ] `parent_01@test.com` logs in → lands on `/parent`
- [ ] Dashboard shows: parent name, linked children list
- [ ] Each child shows: name, grade, XP, streak, avg mastery

### Phase 4.2 — Daily Activity
- [ ] Daily activity section shows today's suggested activity
- [ ] Activity has: title, description, difficulty, estimated time
- [ ] "Completar Actividad" button → confirmation

### Phase 4.3 — Child Progress Deep-Dive
- [ ] Click on linked child → expanded progress view
- [ ] Shows: exercises completed, mastery per topic, streak
- [ ] Activity history for this child

---

## PHASE 5: FULL 21-STUDENT PARALLEL SIMULATION
**Goal: Verify the class works at scale with 21 students all active**
**Tool: PowerShell parallel API simulation + Playwright spot-checks**

### Phase 5.1 — All 21 Students Submit Exercises
- [ ] Script: each of 21 students submits 3 exercise attempts
- [ ] Verify all 63 attempts return 200 and save correctly
- [ ] Verify streak updates for active students

### Phase 5.2 — Teacher Sees All Activity
- [ ] Teacher views class → all 21 students show non-zero XP
- [ ] Assignment results → all 21 students have submission records
- [ ] Leaderboard → 21 students ranked

### Phase 5.3 — Parent Dashboards Reflect Activity
- [ ] Parent 1 (students 01-07): all 7 children show updated XP/streak
- [ ] Parent 2 (students 08-14): same
- [ ] Parent 3 (students 15-21): same

---

## OUTPUTS
- All test scripts saved to `e2e/comprehensive/`
- Results logged to `e2e/comprehensive/results/`
- Bug report: `e2e/comprehensive/BUGS.md`