# MathPlatform E2E Bug Report

## Bug 1: POST /api/me/link-parent returns 500
**Severity:** High (parent linking is broken)
**Date:** 2026-04-25
**Environment:** Railway (lucid-serenity)
**Endpoint:** `POST /api/me/link-parent`

### Description
When a student tries to link to a parent account via `POST /api/me/link-parent {link_code: "..."}`, the server returns HTTP 500 Internal Server Error.

### Investigation
- `POST /api/parents/generate-code` works correctly (returns 200 with link_code)
- `POST /api/me/link-parent` with a valid code returns 500
- `GET /api/parents/me` shows previously linked students (linking worked in earlier attempts)
- The error might be related to duplicate linking attempts

### Possible Cause
The `parent_student_links` table might have duplicate or conflicting entries from previous test runs, causing a DB constraint violation.

### Workaround
Use direct DB cleanup to remove conflicting link records.

---

## Bug 2: [DESCRIBE HERE]

### Description

### Steps to Reproduce

### Expected Behavior

### Actual Behavior

### Severity
