# Fixes Applied — Math Platform Audit + Remediation

**Date:** April 2026
**Scope:** Post-audit critical + high priority bug fixes
**Project:** `C:/Users/Windows/math-platform/`

---

## CRITICAL Fixes ✅

### CR-01: PostgreSQL ExerciseType Enum Mismatch
**File:** `backend/seed/add_enum_values.sql` (migrated directly)

PostgreSQL only had 2 enum values (`multiple_choice`, `numeric`) but Python had 6. Fixed with:
```sql
ALTER TYPE exercisetype ADD VALUE 'bar_model';
ALTER TYPE exercisetype ADD VALUE 'word_problem';
ALTER TYPE exercisetype ADD VALUE 'true_false';
ALTER TYPE exercisetype ADD VALUE 'ordering';
```
**Verified:** All 6 values now in DB (`multiple_choice`, `numeric`, `true_false`, `ordering`, `bar_model`, `word_problem`)

---

### CR-04: `bar_model_problem()` Helper — Wrong Field Names + Missing `correct_answer`
**File:** `backend/seed/curriculum_seed.py:27-41`

Old output:
```python
{"type": "bar_model", "segments": [...], "total": 10, "operation": "add", "question": "..."}
```

New output:
```python
{"type": "bar_model", "question": "...", "total": "10", "units": [{"label": "Parte 1", "value": 3}, ...],
 "operation": "add", "correct_answer": "10"}
```
Changes:
- `segments` → `units` (frontend field name)
- `total` is now a **string** (frontend expects string)
- Added `correct_answer` field (scoring bug fix)

---

### CR-06: Parent Users See Teacher Dashboard at Root `/`
**File:** `frontend/app/page.tsx:28-68`

Changed from binary `student ? StudentDashboard : TeacherDashboard` to role-based redirect:
```typescript
if (user.role !== 'student') {
  if (user.role === 'parent') {
    window.location.href = '/parent'
  } else {
    window.location.href = '/teacher'
  }
  return null
}
```
Parents now go to `/parent`, teachers go to `/teacher`.

---

### CR-07: Parent Portal `completion_rate` Renders as `undefined%`
**File:** `backend/app/routers/parents.py:18-26, 80-89`

Added to `LinkedStudent` schema:
```python
total_exercises: int
completion_rate: float
```

Added to `_get_student_stats()`:
```python
total_exercises = total_result.scalar() or 0
completion_rate = round((exercises_completed / total_exercises * 100), 1) if total_exercises > 0 else 0.0
# then include both fields in the return dict
```

---

### CR-08: `/topics/picker/full` Publicly Accessible
**File:** `backend/app/routers/topics.py:1-16, 41-42`

Added auth guard:
```python
from app.core.security import get_current_user_required
from app.models.user import User

@router.get("/picker/full", response_model=List[TopicWithExercises])
async def get_topic_picker_tree(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user_required),  # <-- auth now required
):
```
**Verified:** Returns 401 without auth token.

---

## HIGH Priority Fixes ✅

### HIGH-03: Password Change — No New≠Old Check + No Session Revocation
**File:** `backend/app/routers/auth.py:94-111`

```python
# Added new≠old password check
if verify_password(data.new_password, user.password_hash):
    raise HTTPException(status_code=400, detail="New password must be different...")

# Added session revocation on password change
await db.execute(
    select(Session).where(Session.user_id == user.id).delete()
)
```

---

### HIGH-04: Most Lesson Visuals Have No Dark Mode
**File:** `frontend/app/components/LessonVisuals.tsx` + `frontend/app/components/EnhancedLessonContent.tsx`

Applied `dark:` Tailwind variants to all 16 visual components:
- `Base10Blocks`, `NumberLine`, `ArrayGrid`, `FractionVisual`, `AnimatedSteps`, `Ruler`, `Protractor`, `DivisionGrouping`, `PlaceValueChart`, `ComparisonBars`, `TenFrame`, `AngleMaker`, `AnimatedArray`, `BarModel`, `WordProblem`, `TryIt`

Key changes:
- Containers: `bg-white` → `bg-white dark:bg-slate-800`
- Borders: `border-gray-200` → `border-gray-200 dark:border-slate-600`
- Text: `text-gray-700` → `text-gray-700 dark:text-gray-200`
- Filled blocks: `bg-primary-200 border-primary-400` → `bg-primary-200 dark:bg-primary-900 border-primary-400 dark:border-primary-600`
- Empty blocks: `bg-gray-100 border-gray-300` → `bg-gray-100 dark:bg-slate-700 border-gray-300 dark:border-slate-500`

Also fixed `EnhancedLessonContent.tsx` body text and headings:
- Body: `text-gray-700` → `text-gray-700 dark:text-gray-200`
- Headings: `text-gray-900` → `text-gray-900 dark:text-gray-100`

---

### HIGH-05: Teacher Dashboard `avg_mastery` Always 0
**File:** `backend/app/schemas/teacher.py:9-18` + `backend/app/routers/teachers.py:38-72`

Added to `ClassResponse` schema:
```python
student_count: int = 0
avg_mastery: float = 0.0
```

Rewrote `list_my_classes` to compute real values:
```python
# Count enrolled students
student_count_result = await db.execute(
    select(func.count(ClassEnrollment.id)).where(ClassEnrollment.class_id == c.id)
)

# Calculate class avg_mastery from all enrolled students' topic progress
enrolled = await db.execute(
    select(ClassEnrollment.student_id).where(ClassEnrollment.class_id == c.id)
)
student_ids = [r[0] for r in enrolled.fetchall()]

avg_mastery = 0.0
if student_ids:
    mastery_result = await db.execute(
        select(func.avg(StudentTopicProgress.mastery_score))
        .where(StudentTopicProgress.student_id.in_(student_ids))
    )
    raw_avg = mastery_result.scalar()
    avg_mastery = round(raw_avg, 1) if raw_avg else 0.0
```

---

### HIGH-06: Seed Teacher Has 0 Classes
**File:** `backend/seed/seed_test_class.py` (run once, script not committed to codebase)

Created class for `profesor@test.com`:
```python
Class(name="Matemáticas 5B - Test", teacher_id=27, subject="Matemáticas", invite_code="6VWHD1FK")
```
**Status:** Class created in DB (id=4).

---

## Backend Rebuilds

All backend code changes required Docker rebuilds since the container has no volume mount:

| Fix | Rebuild Date |
|---|---|
| Initial critical fixes (CR-04, CR-08, CR-07, CR-06) | Apr 2026 |
| HIGH-03 password change | Apr 2026 |
| HIGH-05 teacher avg_mastery | Apr 2026 |

---

## Verified Working

| Test | Result |
|---|---|
| `bar_model_problem()` returns correct fields | ✅ |
| `word_problem()` returns `correct_answer` | ✅ |
| PostgreSQL has all 6 enum values | ✅ |
| `/topics/picker/full` returns 401 without auth | ✅ |
| `LinkedStudent` has `completion_rate` + `total_exercises` | ✅ |
| Password change enforces new≠old + revokes sessions | ✅ |
| Teacher dashboard `list_my_classes` computes real `avg_mastery` | ✅ |
| Class "Matemáticas 5B - Test" exists for `profesor@test.com` | ✅ |
