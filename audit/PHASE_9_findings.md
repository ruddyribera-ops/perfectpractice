# PHASE 9 — Parent Portal Audit
**Date:** 2026-04-21
**Status:** ? COMPLETE
**Read-only investigation — no files modified**

---

## 1. Parent Endpoints Table

| Method | Path | Auth | Role | Purpose |
|--------|------|------|------|---------|
| GET | /parents/me | Required | parent | Returns parent dashboard: parent_name + list of linked students with stats |
| POST | /parents/generate-code | Required | parent | Generates a 6-char link code, stores as unclaimed ParentStudentLink |
| POST | /me/link-parent | Required | student | Student enters parent link code to bind accounts |
| POST | /auth/change-password | Required | any | Changes current user password (requires current password) |

---

## 2. Link Code System — How It Works

**Flow:**
1. Parent calls POST /parents/generate-code
2. Backend generates 6-char uppercase alphanumeric code using secrets.token_urlsafe(6)[:6].upper()
3. Code stored in ParentStudentLink with student_id=NULL (unclaimed)
4. Parent shares code with student
5. Student calls POST /me/link-parent with the code
6. Backend finds ParentStudentLink with matching code where student_id IS NULL
7. Backend sets student_id=student.id (claims the link)
8. Both accounts are now linked

**Code properties:**
- Format: 6-char uppercase alphanumeric, e.g., A3B7K9
- Uniqueness: enforced server-side with retry loop (regenerates if collision)
- No expiry — codes persist indefinitely until claimed
- Single use — claimed links have student_id set, preventing reuse
- No parent notification when claimed — parent must refresh dashboard manually

**Security considerations:**
- Code transmitted in plaintext (no short-lived token, no email auto-delivery)
- No rate limiting on code generation observed
- No expiry means old unclaimed codes could be guessed/stolen over time

---

## 3. Parent-Student Linking — DB Tables

| Table | Purpose |
|-------|---------|
| users | User accounts — email, name, role (student/teacher/parent) |
| parents | Parent profile — user_id FK to users, created_at |
| students | Student profile — user_id FK to users, grade, streaks, XP |
| parent_student_links | Link table — parent_id, student_id (nullable), link_code, created_at |

**ParentStudentLink schema (parent.py model):**
- id: Integer (PK)
- parent_id: Integer (FK to parents.id)
- student_id: Integer (nullable) — NULL = unclaimed
- link_code: String(20), unique — 6-char code
- created_at: DateTime

**Query in /parents/me returns only claimed links** — unclaimed codes invisible to parent dashboard.

---

## 4. Seed Data State

Could not execute database queries due to environment restrictions. DB state reviewed via code inspection only.

Expected seed data for padre@test.com:
- User row: email=padre@test.com, role=parent, name=Padre Test
- Parent row: user_id points to padre@test.com user
- ParentStudentLink rows: possibly 0 (unclaimed) or some claimed links if seeded

---

## 5. LinkedStudent Schema — Backend vs Frontend

### Backend Schema (parents.py lines 18-26)
Fields: id, name, grade, xp_total, current_streak, avg_mastery, exercises_completed

### Frontend Expected Schema (api.ts lines 496-506)
Fields: id, name, grade, xp_total, current_streak, avg_mastery, exercises_completed, total_exercises, completion_rate

### Mismatch Summary

| Field | Backend | Frontend Expects | Status |
|-------|---------|------------------|--------|
| id | Yes | Yes | OK |
| name | Yes | Yes | OK |
| grade | Yes | Yes | OK |
| xp_total | Yes | Yes | OK |
| current_streak | Yes | Yes | OK |
| avg_mastery | Yes | Yes | OK |
| exercises_completed | Yes | Yes | OK |
| total_exercises | No | Yes | MISSING |
| completion_rate | No | Yes | MISSING |

### Confirmed: completion_rate Renders as undefined%

Frontend (parent/page.tsx lines 145-148):
- span shows s.completion_rate% which becomes undefined%
- CSS width becomes width: undefined% which renders as broken bar

Previously flagged in PHASE_4 as HIGH severity — confirmed still present in Phase 9.

---

## 6. Student Progress Visible to Parent

### What parents CAN see via /parents/me:
For each linked student: id, name, grade, xp_total, current_streak, avg_mastery, exercises_completed

### What parents CANNOT see:
- Per-exercise attempt data — no endpoint exposes individual attempts to parents
- Detailed topic progress breakdown — only aggregate avg_mastery, not per-topic scores
- Assignment details — no per-assignment completion/score visible to parent
- Exercise-level correctness — parent sees count, not which exercises correct/incorrect

### Available to students (not parents):
- GET /me/history — full paginated attempt history
- GET /me/assignments — per-assignment completion_rate and score
- GET /me/assignments/{id} — per-exercise status

---

## 7. Security Concerns

### Isolation Verified
/parents/me query filtered by parent.id — each parent only sees their own claimed links. No IDOR vulnerability detected.

### Link Code Has No Expiry
ParentStudentLink.link_code persists until claimed. Unclaimed codes generated months ago would still work.

### No Rate Limiting on Code Generation
A parent could generate unlimited codes via POST /parents/generate-code with no cooldown. Could flood table with garbage data.

### No Notification When Student Links
Parent receives no notification when student claims link. Must manually refresh dashboard.

### Parent Role Still Sees Teacher Dashboard at Root
Previously flagged in PHASE_4. Parent visiting / sees TeacherDashboard (not StudentDashboard since role is not student). Should redirect to /parent.

---

## 8. Password Change Flow

Endpoint: POST /auth/change-password

Flow:
1. User provides current_password, new_password
2. Backend verifies current_password against bcrypt hash
3. If valid, replaces user.password_hash with new bcrypt hash
4. Returns message: Password changed
5. No session revocation — old sessions remain valid until they expire (up to 7 days)

Security characteristics:
- Current password required (prevents session hijacking)
- bcrypt hashing for passwords
- Old sessions not revoked — if compromised, attacker retains access until session expires
- No email/mobile notification when password changes

---

## 9. Summary of Findings

| Severity | Issue |
|----------|-------|
| HIGH | LinkedStudent missing total_exercises and completion_rate — undefined% in parent UI |
| MEDIUM | Link code has no expiry — permanent until claimed |
| MEDIUM | No rate limiting on code generation |
| LOW | Parent sees teacher dashboard at / (root) |
| LOW | Password change does not revoke old sessions |
| LOW | No notification to parent when student links |

---

## Open Items Carried Forward

| Severity | Issue | Phase |
|----------|-------|-------|
| HIGH | Parent portal completion_rate undefined — undefined% CSS | Phase 4 ? Phase 9 (still open) |
| HIGH | Parent portal total_exercises missing from backend | Phase 9 (new finding) |
| MEDIUM | Link code has no expiry | Phase 9 |
| MEDIUM | No rate limiting on code generation | Phase 9 |
| LOW | Parent sees teacher dashboard at / | Phase 4 |
| LOW | Password change does not revoke old sessions | Phase 9 |
| LOW | No notification to parent when student links | Phase 9 |

---

## PHASE_9 — Completion Criteria

| Criteria | Status |
|----------|--------|
| Parent endpoints mapped (method, path, auth, role, purpose) | ? |
| Link code system documented (format, expiry, flow) | ? |
| Parent-student linking tables documented | ? |
| Seed data state reviewed (via code inspection) | ? |
| LinkedStudent schema mismatch documented | ? |
| Security concerns identified | ? |
| Password change flow reviewed | ? |
| Student progress visibility analyzed | ? |
| PHASE_9_findings.md created | ? |
