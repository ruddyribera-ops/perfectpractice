# Phase 8: Teacher Flow Audit

Audit Date: 2026-04-21
Working Directory: C:/Users/Windows/math-platform/
Read-only investigation - no files modified.

---

## 1. Teacher Endpoints Table

All endpoints from backend/app/routers/teachers.py and backend/app/routers/assignments.py:

| Method | Path | Auth | Role | Purpose |
|--------|------|------|------|---------|
| POST | /api/teachers/classes | JWT | teacher, admin | Create a new class |
| GET | /api/teachers/classes | JWT | teacher, admin | List all classes for the teacher |
| GET | /api/teachers/classes/{class_id} | JWT | teacher, admin | Get class detail |
| GET | /api/teachers/classes/{class_id}/students | JWT | teacher, admin | List enrolled students |
| GET | /api/teachers/classes/{class_id}/assignments | JWT | teacher, admin | List assignments |
| POST | /api/teachers/classes/{class_id}/assignments | JWT | teacher, admin | Create assignment |
| DELETE | /api/teachers/classes/{class_id}/students/{student_id} | JWT | teacher, admin | Remove student |
| DELETE | /api/teachers/classes/{class_id}/assignments/{assignment_id} | JWT | teacher, admin | Delete assignment |
| POST | /api/assignments | JWT | teacher, admin | Create standalone assignment |
| GET | /api/assignments/{assignment_id}/results | JWT | teacher, admin | Get assignment results |

The router prefix for teachers.py is /teachers, making these /api/teachers/classes/...

---

## 2. Class/Student Management Findings

### Seed Data Status

Query result for profesor@test.com:
Teacher: profesor@test.com, User ID: 90
Teacher profile ID: 27
Classes: 0

The seed teacher has zero classes. No students enrolled.

### How Students Are Associated with Teachers

- Teachers do NOT have direct teacher_id on students table.
- Students associated indirectly: Teacher -> Class -> ClassEnrollment -> Student
- A student enrolls via invite code (student-side endpoint, not audited).

### Class Creation Flow

1. Teacher creates class -> invite code generated (8-char token)
2. Teacher shares code manually (copy button in UI)
3. Students use code to enroll
4. Teacher views students via GET /teachers/classes/{class_id}/students

### Student Data Exposed to Teachers

GET /teachers/classes/{class_id}/students returns:
- student_id, name, email, grade
- points, level, current_streak
- avg_mastery (from StudentTopicProgress)
- enrolled_at, last_active
- exercises_completed

---

## 3. Topic Picker Findings

### topics/picker/full - PUBLIC (Confirmed)

File: backend/app/routers/topics.py lines 41-94

router.get picker-full (response_model=List[TopicWithExercises])
async def get_topic_picker_tree:

- NO AUTHENTICATION - no Depends(get_current_user_required)
- Returns full topic tree with all exercises
- Used by teacher frontend to pick exercises for assignments
- PUBLICLY ACCESSIBLE to anyone

### Response Schema

TopicWithExercises: id, slug, title, units[]
UnitWithExercises: id, title, slug, exercises[]
ExercisePickerItem: id, title, type, difficulty, points, lesson_title, unit_title

### How Teachers Assign

1. Teacher clicks Nueva Tarea in class detail
2. Modal fetches topics/picker/full (public, no auth)
3. Teacher checks exercises to assign
4. Sets title, description, due_date
5. Submit -> POST /teachers/classes/{class_id}/assignments with exercise_ids

Key: Assignments are at EXERCISE level, not topic/unit. Teachers pick individual exercises.

---

## 4. Assignment Tracking Findings

### DB State (Fresh Seed)

| Table | Row Count |
|-------|-----------|
| assignments | 0 |
| student_assignments | 0 |
| student_topic_progress | 5 rows (student_id=40, topics 68-70, all mastery=0.0) |

### How Assignments Work

1. POST /teachers/classes/{class_id}/assignments -> Assignment + AssignmentExercise rows
2. Notification sent to all enrolled students (new_assignment type)
3. Student sees in /me/assignments with per-exercise status
4. Completion: all exercises >= 1 correct attempt -> completed_at set
5. Teacher views results via GET /assignments/{id}/results

### Completion Logic

submit_attempt: if all assignment exercises have correct attempt, mark completed.

---

## 5. Unit-level vs Topic-level Assignments

Phase 3 finding: Units empty in TopicTreeResponse - verified still true.

- TopicTreeResponse (GET /api/topics) does NOT include exercises
- TopicWithExercises (GET /topics/picker/full) includes exercises at exercise level only
- NO topic-level or unit-level assignment
- Assignment model has no topic_id or unit_id - only class_id and exercise_ids

---

## 6. Teacher Dashboard Frontend Findings

### Teacher Dashboard (page.tsx)
- Fetches /api/classes
- Shows: total classes, total students, avg mastery
- Quick actions: Mis Clases, Crear Tarea, Google Classroom, Leaderboard

### Class List (classes/page.tsx)
- Lists classes with invite codes
- Nueva Clase button with inline create form
- Shows student count and assignment count

### Class Detail (classes/[id]/page.tsx)
- Two tabs: Students and Assignments
- Students: name, grade, XP/level, streak, mastery bar, last active, exercises
- Assignments: list with due dates, Ver resultados link
- Nueva Tarea button -> modal with exercise picker

### Google Classroom (classroom/page.tsx)
- Shows connection status
- Can link courses to local classes
- Sync options when creating assignments

---

## 7. Gaps, Bugs, and Concerns

### Bug: Hardcoded Class IDs in Google Classroom UI
frontend/app/teacher/classroom/page.tsx lines 168-170
Hardcoded option values - should fetch from /me/classes instead.

### Bug: Teacher Dashboard avg_mastery Calculation Wrong
frontend/app/teacher/page.tsx line 19
Uses c.avg_mastery but ClassResponse has no avg_mastery field. Always 0.

### Security: Topic Picker Publicly Accessible
GET /topics/picker/full requires NO authentication.
Exposes all exercise data to anyone.

### Security: Assignment Results Not Authorization-Checked
GET /api/assignments/{id}/results only checks role=teacher/admin.
Does NOT verify teacher owns the class. Any teacher can view any result.

### Missing: No Topic-Level or Unit-Level Assignment
Teachers can only assign individual exercises.

### Empty State: Zero Classes, Zero Assignments
Seed teacher has 0 classes, 0 assignments.

---

## 8. Summary

| Area | Status |
|------|--------|
| Teacher endpoints (auth+role) | All JWT + teacher/admin |
| Class creation flow | Working, invite codes |
| Student enrollment | Manual code sharing |
| Topic picker | PUBLIC - security concern |
| Exercise assignment | Working |
| Assignment results | Per-student breakdown |
| Unit/Topic assignment | Not implemented |
| Dashboard avg_mastery | Bug - always 0 |
| Google Classroom | Hardcoded IDs |
| Assignment auth | Any teacher can see any |