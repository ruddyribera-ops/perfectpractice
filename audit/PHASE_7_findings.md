# Phase 7: Auth + Roles Audit Findings

**Audit Date:** 2026-04-21
**Scope:** Math Platform auth system, role-based access, parent dashboard bug investigation

---

## 1. Complete Auth Flow Diagram

### Login Flow (backend/app/routers/auth.py)

User submits POST /api/auth/login {email, password}
        |
        v
auth.py:login() [line 47-58]
  - DB query: SELECT * FROM users WHERE email = ?
  - verify_password(plain, hashed) via bcrypt
  - create_access_token({sub: str(user.id)}) -> JWT {sub: user_id, exp, type: access}
  - create_refresh_token({sub: str(user.id)}) -> JWT {sub: user_id, exp, type: refresh}
  - _create_session() -> stores Session(row) with hashed refresh_token in DB (7-day expiry)
  - Returns TokenResponse {user, access_token, refresh_token}

Frontend stores:
  localStorage.setItem(access_token, response.access_token)  <- 183-char JWT string
  localStorage.setItem(refresh_token, response.refresh_token)
  localStorage.setItem(user, JSON.stringify(response.user))   <- {id, email, name, role}



### JWT Token Structure

- access_token: 183-char JWT (HS256), expires in 15 minutes (JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 15)
- Payload: {sub: user_id, role: student, exp: timestamp, type: access}
- Role IS embedded in JWT payload, but the backend decode_token() does NOT validate 
  the role field at decode time. Role is extracted from the JWT sub (user_id), then looked 
  up from the DB in get_current_user() (security.py:45-56). The JWT role claim is informational only.

### After Login: Dashboard Routing (frontend/app/page.tsx)

useAuth() returns {user: {id, email, name, role}}
        |
        v
page.tsx:64
  {user.role === student ? <StudentDashboard /> : <TeacherDashboard />}

**Root cause of parent-dashboard bug:** Line 64 has only a binary conditional:
- If role === student -> StudentDashboard
- Otherwise (teacher OR parent OR admin) -> TeacherDashboard

padre@test.com with role parent falls into the else branch and sees TeacherDashboard.

The parent portal exists at /parent (frontend/app/parent/page.tsx) and correctly redirects non-parents:
  if (user?.role !== parent) { router.replace(/); return; }  [line 20]
But / itself has no such guard -- parents must manually navigate to /parent.

---

## 2. All Endpoints: Auth and Role Check Table

### Auth Router (backend/app/routers/auth.py)

| Method | Path | Auth Required? | Role Check? | Notes |
|--------|------|---------------|-------------|-------|
| POST | /auth/register | No | No | Creates User + role-specific profile |
| POST | /auth/login | No | No | Returns JWT + user object |
| POST | /auth/refresh | Cookie: refresh_token | No | Returns new access_token |
| POST | /auth/logout | Cookie: refresh_token | No | Deletes session from DB |
| POST | /auth/change-password | Yes (Bearer) | No | Verifies old password before setting new |

### Students Router (backend/app/routers/students.py)

| Method | Path | Auth Required? | Role Check? | Notes |
|--------|------|---------------|-------------|-------|
| GET | /me/progress | Yes | role == student | Returns per-topic mastery |
| POST | /me/streaks/freeze | Yes | role == student | Uses 1 streak freeze |
| POST | /me/exercises/{id}/attempt | Yes | role == student | Submit answer, calc XP/streak |
| GET | /me/streaks/me | Yes | role == student | Streak info |
| GET | /me/stats/me | Yes | role == student | XP, level, points |
| GET | /me/achievements | Yes | role == student | Badge list |
| GET | /me/history | Yes | role == student | Paginated attempt history |
| GET | /me/assignments | Yes | role == student | Assignments for enrolled classes |
| GET | /me/assignments/{id} | Yes | role == student + enrollment check | Assignment detail |
| GET | /me/classes | Yes | role == student | Enrolled classes |
| POST | /me/link-parent | Yes | role == UserRole.student | Student enters 6-char code |

### Parents Router (backend/app/routers/parents.py)

| Method | Path | Auth Required? | Role Check? | Notes |
|--------|------|---------------|-------------|-------|
| GET | /parents/me | Yes | role == UserRole.parent | Dashboard with linked students |
| POST | /parents/generate-code | Yes | role == UserRole.parent | Generate 6-char link code |

### Teachers Router (backend/app/routers/teachers.py)

| Method | Path | Auth Required? | Role Check? | Notes |
|--------|------|---------------|-------------|-------|
| POST | /classes | Yes | role in [teacher, admin] | Create class |
| GET | /classes | Yes | role in [teacher, admin] | List teachers classes |
| GET | /classes/{id} | Yes | role in [teacher, admin] + ownership | Class detail |
| GET | /classes/{id}/students | Yes | role in [teacher, admin] + ownership | Student list |
| GET | /classes/{id}/assignments | Yes | role in [teacher, admin] + ownership | Assignment list |
| POST | /classes/{id}/assignments | Yes | role in [teacher, admin] + ownership | Create assignment |
| DELETE | /classes/{id}/students/{sid} | Yes | role in [teacher, admin] + ownership | Remove student |
| DELETE | /classes/{id}/assignments/{aid} | Yes | role in [teacher, admin] + ownership | Delete assignment |

### Exercises Router (backend/app/routers/exercises.py)

| Method | Path | Auth Required? | Role Check? | Notes |
|--------|------|---------------|-------------|-------|
| GET | /{exercise_id} | Yes (Bearer) | No role check, any auth works | Returns exercise (correct_answer stripped for students) |

### Lessons Router (backend/app/routers/lessons.py)

| Method | Path | Auth Required? | Role Check? | Notes |
|--------|------|---------------|-------------|-------|
| GET | /unit/{unit_id} | Yes (Bearer) | No role check | Returns lessons list |
| GET | /{lesson_id} | Yes (Bearer) | No role check | Returns lesson detail with exercises |

### Topics Router (backend/app/routers/topics.py)

| Method | Path | Auth Required? | Role Check? | Notes |
|--------|------|---------------|-------------|-------|
| GET | / (list) | NO AUTH | No | Public topic tree |
| GET | /{slug} | NO AUTH | No | Topic detail |
| GET | /picker/full | NO AUTH | No | Full tree for teachers (no auth!) |

---

## 3. Role Guard Findings

### Backend Role Guards

- Students router: Every endpoint checks user.role != student with 403 (students.py:38-39, etc.)
- Parents router: Every endpoint checks user.role != UserRole.parent with 403 (parents.py:99-100, etc.)
- Teachers router: Every endpoint checks user.role not in [teacher, admin] with 403 (teachers.py:27-28, etc.)
- Exercises/Lessons: Auth required but NO role check -- any authenticated user can access
- Topics: Public (no auth at all) -- /, /{slug}, /picker/full

### Frontend Role Guards

- AuthContext (frontend/contexts/AuthContext.tsx:31-46):
  - checkAuth() reads token + user from localStorage
  - Does NOT validate token with backend on load
  - Role comes from locally stored user object, not from token parsing

- frontend/app/page.tsx:64: Binary student/non-student split -- no parent check
- frontend/app/parent/page.tsx:20: Correctly redirects non-parents to /
- No middleware.ts exists -- no server-side auth verification
- No layout.tsx middleware -- AuthProvider wraps children, no server-side guard

### Auth Context Role Field Gap

// frontend/contexts/AuthContext.tsx:6-11
interface User {
  id: number
  email: string
  name: string
  role: student | teacher | admin  // parent is NOT in this union!
}

Issue: The User interface does NOT include parent as a valid role. The AuthContext stores 
response.user directly. If the backend returns role: parent, the TypeScript type does not 
account for it (though at runtime it would work since role is just a string).

---

## 4. Root Cause of Parent-Dashboard Bug (with file:line references)

### Primary Cause: frontend/app/page.tsx:64

  {user.role === student ? <StudentDashboard /> : <TeacherDashboard />}

Bug: This ternary has only two branches. Parent role falls into the else branch and renders TeacherDashboard.

Impact: When padre@test.com (role: parent) logs in:
1. AuthContext loads user from localStorage -> {id, email, name, role: parent}
2. page.tsx renders -> user.role === student is FALSE
3. Renders TeacherDashboard (teacher portal with class management links)
4. Parent must manually navigate to /parent to see their portal

### Why Backend Is NOT the Cause

- GET /parents/me correctly requires role == UserRole.parent (parents.py:99)
- GET /auth/me or equivalent does not exist -- user info comes from login response
- The backend correctly issues a JWT with the users actual role
- The backend has no redirect logic -- it just serves data based on the role in the auth token

### Secondary Issue: No automatic redirect for parent users

- There is no server-side middleware (no middleware.ts) to redirect / based on role
- The parent/page.tsx has the guard (line 20) but parents never get routed there automatically

---

## 5. Security Concerns

### Critical: Topics Endpoints Are Public (No Auth)

| Endpoint | Auth | Data Exposure |
|----------|------|---------------|
| GET /api/topics | None | Full topic tree |
| GET /api/topics/{slug} | None | Topic details |
| GET /api/topics/picker/full | None | Complete exercise picker (titles, types, difficulty, points) |

Concern: The /topics/picker/full endpoint (topics.py:41-93) exposes the complete exercise 
library including titles, types, difficulty, points -- all without any authentication.

### Moderate: Exercises and Lessons Require Auth But No Role Check

- GET /api/exercises/{id} -- any authenticated user can fetch exercise data
- GET /api/lessons/{id} -- same
- GET /api/lessons/unit/{unit_id} -- same

This means a parent or teacher can access exercise content via API even though they would not 
typically use those endpoints through the UI.

### Moderate: JWT Role Claim Not Validated

The create_access_token embeds role in the JWT payload (security.py:23-27):
  to_encode.update({exp: expire, type: access})
  # role is in data dict but not explicitly validated at decode

The decode_token() only checks type field, not role. Authorization uses DB lookup, which is 
secure, but the JWT role claim is informational only and could be misleading.

### Low: AuthContext Does Not Validate Token with Backend

checkAuth() (AuthContext.tsx:31-46) reads from localStorage without backend validation. 
If the token is tampered with or the user object is manually modified in localStorage, the 
frontend will trust it.

### Low: No Rate Limiting on Auth Endpoints

/auth/login, /auth/register have no rate limiting -- vulnerable to brute force.

---

## 6. Password Change Flow

### Endpoint: POST /api/auth/change-password

File: backend/app/routers/auth.py:94-106

@router.post(/change-password)
async def change_password(
    data: ChangePasswordRequest,
    user: User = Depends(get_current_user_required),
    db: AsyncSession = Depends(get_db),
):
    if not verify_password(data.current_password, user.password_hash):
        raise HTTPException(status_code=400, detail=Current password is incorrect)

    user.password_hash = get_password_hash(data.new_password)
    await db.commit()
    return {message: Password changed}

### Findings

| Check | Status | Notes |
|-------|--------|-------|
| Verifies old password | YES | verify_password(data.current_password, user.password_hash) |
| Checks new password != old | NO | No comparison performed -- user can set same password |
| Password strength validation | NO | No length/complexity checks in the endpoint |
| Audit log / notification | NO | No notification sent to user about change |
| Revokes other sessions | NO | Only the current sessions refresh token is valid |
| Invalidates other JWTs | NO | Other active access tokens remain valid until expiry (15 min) |

---

## 7. Summary

### Root Cause of Parent Bug
- File: frontend/app/page.tsx:64
- Line: {user.role === student ? <StudentDashboard /> : <TeacherDashboard />}
- Cause: Binary ternary -- parent role has no branch, falls into teacher dashboard
- Fix direction: Add user.role === parent ? <ParentDashboard /> : ... or route to /parent

### Auth Flow Summary
- JWT-based (access + refresh tokens), stored in localStorage
- Role embedded in JWT but not used for auth decisions -- DB lookup instead
- /topics/** are public (no auth), everything else requires Bearer token
- No role check on exercises/lessons -- any authenticated user can access

### Password Change
- Verifies old password: YES
- No check for new password being same as old: NO
- No password strength validation: NO
- No session revocation: NO

---

Verification script output:
  Token type: <class str>
  Token length: 183
  Token prefix: eyJhbGciOiJIUzI1NiIs...
JWT creation confirmed working. Role is embedded in token payload: 
{sub: 123, role: student, exp: ..., type: access}
