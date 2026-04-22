# PHASE 5 — Audit Exercise Pipeline
**Date:** 2026-04-21
**Status:** ✅ COMPLETE

---

## 1. Exercise Types — Inventory

| Type | Frontend Renderer | Backend Scoring | Render Complete | Notes |
|---|---|---|---|---|
| `multiple_choice` | ✅ | ✅ | ✅ | 4-choice A/B/C/D buttons |
| `true_false` | ✅ | ✅ | ⚠️ | "Verdadero/Falso" buttons, but treated as string |
| `numeric` | ✅ | ✅ | ✅ | Text input, Enter to submit |
| `ordering` | ✅ | ⚠️ | ✅ | Drag/reorder + arrow buttons |
| `bar_model` | ✅ | ⚠️ | ✅ | Horizontal bar visualization + text input |
| `word_problem` | ✅ | ⚠️ | ✅ | Scenario card + question + text input |

---

## 2. Frontend Renderers — Complete Implementation

### Multiple Choice (✅)
- 4 option buttons (A–D labels) with visual selection state
- Selected → highlighted in primary color
- After submit → correct/incorrect coloring + disable
- `exercise.data.options` array

### True/False (✅)
- 2-button grid: "Verdadero" / "Falso"
- Maps to index 0/1 → sent as `'true'` or `'false'` string
- Visual feedback same as MC after submit

### Numeric (✅)
- Large centered text input
- `onKeyDown: Enter` triggers submit
- Disabled after result shown

### Ordering (✅)
- Shuffle + reorder UI with up/down arrow buttons
- Items stored as `orderedItems` string[]
- Submit sends `JSON.stringify(orderedItems)`
- ⚠️ Backend compares as string → JSON string vs correct answer string

### Bar Model (✅)
- `BarModelDisplay` component shows horizontal bars proportional to values
- Dark mode aware, colorful grade-based palette
- Question displayed above bars
- Total bar shown separately
- Text input below for student's numeric answer
- **Display data:** `data = {question, total, units: [{label, value}], type}`

### Word Problem (✅)
- `WordProblemDisplay` component with scenario card + question
- Collapsible hint toggle
- Optional answer preview
- Text input below for numeric answer
- **Display data:** `data = {scenario, question, answer, hint}`

---

## 3. ⚠️ CRITICAL: Backend Scoring — `word_problem` Always Wrong

**Root cause:** The `word_problem()` helper in `curriculum_seed.py` (lines 43–58) produces this data format:
```python
{
    "scenario": context,
    "question": f"{context} ¿Cuál es el resultado de {num1} {op_sym} {num2}?",
    "answer": answer,       # ← numeric value
    "explanation": f"{num1} {op_sym} {num2} = {answer}",
}
```

**No `correct_answer` field.** The backend's `submit_attempt` (students.py, line 149):
```python
correct_answer = exercise.data.get("correct_answer")
```

Returns `None` for all word_problem exercises. Then (line 159):
```python
correct = str(data.answer).strip().lower() == str(correct_answer).strip().lower() if correct_answer else False
```

Since `correct_answer` is `None` → `False` is returned. **Every single word_problem submission is marked incorrect regardless of the student's answer.**

**Impact:** Students never get correct feedback on word_problem exercises. Mastery never updates for word_problem topic progress. XP never awarded for these exercises.

---

## 4. ⚠️ CRITICAL: Backend Scoring — `bar_model` Data Mismatch

**The `bar_model_problem()` helper** (curriculum_seed.py, lines 27–40) produces:
```python
{
    "type": "bar_model",
    "segments": parts,     # list of segment values
    "total": total,        # total/target value
    "operation": operation,  # 'add'/'subtract'/'compare'
    "question": question,
}
```

**But the frontend `BarModelData` interface expects:**
```typescript
interface BarModelData {
    question: string
    total: string              // ← stored as STRING
    units: { label: string; value: number }[]
    type: string
}
```

The frontend `BarModelDisplay` uses `data.total` as a string and `data.units` as labeled values. But the backend `bar_model_problem()` helper returns `segments` (not `units`) and `total` as an integer.

**Two mismatches:**
1. **Field name:** `segments` vs `units`
2. **Type:** `total` as int vs string; `units` as list of {label, value} vs just values

Also: the backend's `bar_model_problem()` never sets `correct_answer`. Same `None` problem as word_problem — bar_model exercises will always mark as incorrect.

---

## 5. ⚠️ HIGH: Ordering — Stringification Mismatch

Frontend sends: `JSON.stringify(orderedItems)` → e.g. `'["apple","banana","cherry"]'`

Backend compares as:
```python
correct = str(data.answer).strip().lower() == str(correct_answer).strip().lower()
```

If `correct_answer` is stored as a JSON array string in the DB, this would work. But the exercise data doesn't appear to have any ordering exercises — need to verify from DB.

---

## 6. ✅ Mastery Recalculation — First Attempt Only

**Lines 321–331 in students.py:**
```python
existing_correct = await db.execute(...)
if existing_correct.scalar_one_or_none() is None:
    progress_row.exercises_completed += 1
```

Only increments `exercises_completed` on first correct attempt. ✅ Correct.

**Weighted score formula** (lines 352–355):
- Last 5 correct attempts: weight=2
- Older correct attempts: weight=1
- Score = `(len(recent_five)*2 + len(older)*1) / (n*2) * 100`

⚠️ This means a student who gets 10 correct answers all in the last 5 attempts gets 100% mastery. But the formula normalizes by `n*2` where `n` is total attempts — so 5 recent correct = `(5*2 + 0*1) / (5*2) * 100 = 100%`. A student with 10 correct (5 recent, 5 older) gets `(5*2 + 5*1) / (10*2) * 100 = 75%`. **This is correct weighted behavior.**

---

## 7. ✅ Assignment Completion Check

**Lines 225–281 in students.py:** When `assignment_id` is provided:
1. Get all exercise IDs for the assignment
2. Count how many have at least one correct attempt for this student
3. If `correct_total >= len(exercise_ids)` → mark `StudentAssignment.completed_at`
4. Compute score = `(correct_count / total) * 100`
5. Create notification for teacher

**✅ Logic is correct.** Notifies teacher when assignment is fully completed by a student.

---

## 8. ⚠️ MEDIUM: Exercise Data — Answer Field Name Inconsistency

The `Exercise` model stores flexible `data (JSON)`:
- `numeric`: uses `correct_answer`, `question`, `explanation`
- `multiple_choice`: uses `choices` (array), `question`, `explanation`
- `word_problem` (seed helper): uses `scenario`, `question`, `answer`, `explanation` — **NO `correct_answer`**
- `bar_model` (seed helper): uses `type`, `segments`, `total`, `operation`, `question` — **NO `correct_answer`**

No enforced schema for `exercise.data`. The application relies on conventions.

---

## 9. ⚠️ MEDIUM: `true_false` Scoring — No Special Handling

The backend's `true_false` scoring (line 157) is identical to the `else` branch:
```python
elif et == "true_false":
    correct = str(data.answer).strip().lower() == str(correct_answer).strip().lower()
else:
    correct = str(data.answer).strip().lower() == str(correct_answer).strip().lower() if correct_answer else False
```

The frontend sends `'true'` or `'false'` strings. If `correct_answer` in DB is also `'true'`/`'false'` strings, it works. Otherwise:
- `true_false` data stored as `{"question": "...", "correct_answer": true}` (boolean) → backend compares string `'true'` vs string `'True'` → case sensitivity could cause issues.

The `str(True).lower()` = `'true'` vs `str('true').lower()` = `'true'` — this should actually work. But no special handling for boolean types exists.

---

## PHASE 5 — Completion Criteria

| Criteria | Status |
|---|---|
| All 6 exercise types have complete renderers | ✅ |
| `submit_attempt` handles all 6 types | ⚠️ word_problem + bar_model always wrong |
| Mastery recalculates correctly (first attempt only) | ✅ |
| Assignment completion check works | ✅ |
| `bar_model` frontend data format mismatch with backend | ⚠️ CRITICAL |
| `word_problem` missing `correct_answer` in data | ⚠️ CRITICAL |
| `PHASE_5_findings.md` written | ✅ |

---

## Open Items

| Severity | Issue | Fix |
|---|---|---|
| CRITICAL | word_problem: `correct_answer` missing → always wrong | Add `correct_answer` to word_problem helper |
| CRITICAL | bar_model: `correct_answer` missing + field name mismatch | Add `correct_answer` + rename `segments` → `units` |
| MEDIUM | true_false: no special boolean handling (but may work) | Verify correct_answer stored as string |
| LOW | exercise.data has no enforced schema — convention-only | Document schema or add validation |
