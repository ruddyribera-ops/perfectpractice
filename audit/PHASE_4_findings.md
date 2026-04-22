# PHASE 4 — Audit Frontend Pages + Routing
**Date:** 2026-04-21
**Status:** ✅ COMPLETE

---

## 1. Page Inventory — All 22 Routes

| Route | File | Auth | Role Check |
|---|---|---|---|
| `/` | `page.tsx` | Optional | Student vs Teacher dashboard |
| `/login` | `login/page.tsx` | ❌ Public | — |
| `/register` | `register/page.tsx` | ❌ Public | — |
| `/topics` | `topics/page.tsx` | ✅ | None |
| `/topics/[slug]` | `topics/[slug]/page.tsx` | ✅ | None |
| `/units/[slug]` | `units/[slug]/page.tsx` | ✅ | None |
| `/learn/[slug]` | `learn/[slug]/page.tsx` | ✅ | None |
| `/lessons/[id]` | `lessons/[id]/page.tsx` | ✅ | Student only |
| `/exercises/[id]` | `exercises/[id]/page.tsx` | ✅ | Student only |
| `/me/history` | `me/history/page.tsx` | ✅ | — |
| `/me/assignments` | `me/assignments/page.tsx` | ✅ | — |
| `/me/assignments/[id]` | `me/assignments/[id]/page.tsx` | ✅ | — |
| `/me/classes` | `me/classes/page.tsx` | ✅ | — |
| `/me/notifications` | `me/notifications/page.tsx` | ✅ | — |
| `/leaderboard` | `leaderboard/page.tsx` | ✅ | — |
| `/teacher/page` | `teacher/page.tsx` | ✅ | — |
| `/teacher/classes` | `teacher/classes/page.tsx` | ✅ | — |
| `/teacher/classes/[id]` | `teacher/classes/[id]/page.tsx` | ✅ | — |
| `/teacher/classes/[id]/assignments/[id]/results` | `results/page.tsx` | ✅ | — |
| `/parent/page` | `parent/page.tsx` | ✅ | **Explicit parent role check** |

**Total: 22 routes across 3 role zones.**

---

## 2. Auth Guard Analysis

**No middleware.ts** — All auth is client-side via `useAuth()` context + per-page `useEffect` redirects.

**Observed pattern:**
```typescript
useEffect(() => {
  if (user?.role !== 'parent') { router.replace('/'); return; }
  fetchData()
}, [user, router])
```

**Problems with this pattern:**
1. Brief render for wrong-role users before redirect (UX issue)
2. API calls fire before role check completes (race condition possible)
3. No server-side protection — API returns 401, frontend handles it reactively

### Pages with Role Checks

| Page | Check Location | What Happens for Wrong Role |
|---|---|---|
| `/lessons/[id]` | `useEffect` line 20 | Redirect to `/` |
| `/exercises/[id]` | Unknown | Unknown |
| `/parent/page` | `useEffect` inside component | Redirect to `/` |
| `/` | Ternary: student → StudentDashboard else → TeacherDashboard | **PARENT SEES TEACHER DASHBOARD** |

---

## 3. ⚠️ CRITICAL: Parent Users See Teacher Dashboard at Home

**File:** `frontend/app/page.tsx`, line 64:
```typescript
{user.role === 'student' ? <StudentDashboard /> : <TeacherDashboard />}
```

**Impact:** When a parent logs in and visits `/`, they see `TeacherDashboard` because:
- `user.role === 'student'` → false (parent's role is "parent")
- Goes to `TeacherDashboard`
- TeacherDashboard shows "Mis Clases" and "Tabla de Posiciones" — features that don't make sense for a parent

**⚠️ CRITICAL — User-facing bug.** Parent should see a dedicated parent dashboard at root, OR be redirected to `/parent` automatically.

---

## 4. ⚠️ HIGH: Parent Portal — `completion_rate` Field Never Set

**File:** `frontend/app/parent/page.tsx`, lines 145–148:
```typescript
<span>{s.completion_rate}%</span>
<div style={{ width: `${s.completion_rate}%` ... />
```

**Backend schema** (`LinkedStudent` in `parents.py` lines 18–26):
```
id, name, grade, xp_total, current_streak, avg_mastery, exercises_completed
```

**No `completion_rate` field in backend response.** The field is always `undefined`.

**Result:**
- Display: blank text + CSS `width: undefined%` (renders as `width: undefined%` in browser)
- Visual glitch: progress bar appears at "undefined%"

---

## 5. ⚠️ MEDIUM: No `loading` State for Data Fetches

Many pages use:
```typescript
const [loading, setLoading] = useState(true)
useEffect(() => {
  fetchData().catch(...).finally(() => setLoading(false))
}, [...])
```

BUT the `catch` swallows the error and sets `setLoading(false)` — the error is logged to console but the user is never notified. If the API is down, the user just sees the page stuck in loading or showing empty data silently.

---

## 6. ✅ API Client (`lib/api.ts`) — Path Mapping Verification

All API calls use `${API_URL}/api${endpoint}` — the `/api` prefix is correct for all routers except the **teachers router which is at `/api/classes`** (not `/api/teachers/classes`).

**Key mappings verified:**

| ApiClient method | Endpoint called | Router | Status |
|---|---|---|---|
| `getClassDetail(id)` | `GET /api/classes/{id}` | teachers | ✅ |
| `getClassStudents(id)` | `GET /api/classes/{id}/students` | teachers | ✅ |
| `getParentDashboard()` | `GET /api/parents/me` | parents | ✅ |
| `generateParentLinkCode()` | `POST /api/parents/generate-code` | parents | ✅ |
| `getTopicPickerTree()` | `GET /api/topics/picker/full` | topics | ✅ |
| `submitAttempt(id, ...)` | `POST /api/me/exercises/{id}/attempt` | students | ✅ |

---

## 7. ✅ Login/Register — Token Storage

- Tokens stored in `localStorage` (`access_token`, `refresh_token`) ✅
- `login()` function stores both tokens before redirect ✅
- `logout()` clears both tokens ✅
- No HTTP-only cookie — tokens in localStorage (acceptable for SPA)

---

## 8. ✅ Exercise + Lesson Pages — Data Flow

**Lesson flow:** `/topics/[slug]` → topic detail with units → `/units/[slug]` → unit detail with lessons → `/lessons/[id]` → lesson with exercises → `/exercises/[id]` → single exercise

**Submit flow:** Exercise answer → `api.submitAttempt()` → backend scores → returns `AttemptResult` (correct/incorrect + XP + achievement) → frontend shows feedback ✅

---

## PHASE 4 — Completion Criteria

| Criteria | Status |
|---|---|
| All 22 routes mapped + auth requirement | ✅ |
| No missing middleware.ts (documented) | ✅ |
| Auth redirect for unauthenticated users | ⚠️ Client-side only |
| Role-based access enforced | ⚠️ TeacherDashboard for parent at root |
| API endpoint paths match backend | ✅ |
| Loading/error states | ⚠️ Errors swallowed silently |
| Parent portal completion_rate undefined | ⚠️ HIGH |
| `PHASE_4_findings.md` written | ✅ |

---

## Open Items Carried Forward

| Severity | Issue | Phase |
|---|---|---|
| CRITICAL | Parent sees teacher dashboard at `/` | Phase 7 |
| HIGH | Parent portal `completion_rate` undefined → undefined% CSS | Phase 4 → Phase 9 |
| MEDIUM | Errors swallowed silently in data fetches | Phase 4 (low priority) |
| MEDIUM | No server-side auth middleware | Phase 7 (awareness) |
| LOW | Brief render before role redirect | Phase 4 (low priority) |
