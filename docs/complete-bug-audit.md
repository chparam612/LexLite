# Complete Production Bug Audit & System Diagnostics

**Date**: September 21, 2026  
**System**: Legal AI Assistant (LexLite)  
**Evaluator**: Senior Production Debugging Engineer & Full-Stack Architect

---

## 1. Bug Inventory & Severity Classification

| Bug ID | Component | Severity | Description | Root Cause | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **BUG-001** | Auth / Backend | **CRITICAL** | User registration and credential sign-in fails in production (`https://lex-lite.vercel.app/`). | Frontend generated `test_token_:` mock tokens; backend lacked `POST /api/v1/auth/register`, `POST /api/v1/auth/login`, and password hashing. Production environment rejected test tokens with 401. | **FIXED & VERIFIED** |
| **BUG-002** | Auth / Frontend | **CRITICAL** | "Instant Sign In as Demo Attorney" fails with authentication error in production. | Button set unverified client-side test token that was blocked by production backend security middleware. | **FIXED & VERIFIED** |
| **BUG-003** | Evaluation / DevOps | **HIGH** | `FE-001` failed in `evaluation.py`. | Checked for `frontend/dist/index.html` on the local filesystem, which does not exist in the Render backend container (frontend is hosted separately on Vercel). | **FIXED & VERIFIED** |
| **BUG-004** | AI Provider / GenAI | **HIGH** | `GEN-001` crashed when Gemini API Free Tier 429 quota limit was reached. | Quota exhaustion threw unhandled exception without candidate model rotation or extractive fallback. | **FIXED & VERIFIED** |
| **BUG-005** | Database / ORM | **MEDIUM** | Existing databases failed with `no such column: users.hashed_password`. | SQLAlchemy `create_all()` does not alter existing tables to add new columns. | **FIXED & VERIFIED** |
| **BUG-006** | Frontend / Typing | **MEDIUM** | `npm run build` failed TypeScript checking in `AuthContext.tsx`. | `UserProfile.display_name` expected `string | null` while API response provided `string | null | undefined`. | **FIXED & VERIFIED** |
| **BUG-007** | AI Provider / Networking | **LOW** | GenAI calls risked long hangs when rate-limited. | `model.generate_content` lacked explicit request timeout parameter. | **FIXED & VERIFIED** |

---

## 2. Detailed Bug Analyses & Remedies

### BUG-001 & BUG-002: Production Authentication Failure
- **Symptoms**: Registration and login returned error banner: `"Authentication failed"`.
- **Diagnosis**: 
  The frontend and backend were disconnected on authentication:
  - Frontend called no backend registration/login API.
  - Backend had no registration/login endpoints.
  - Frontend generated mock strings starting with `test_token_:`.
  - Backend `security.py` strictly threw HTTP 401 Unauthorized for `test_token_:` when `APPLICATION_ENV=production`.
- **Remedy**:
  1. Implemented PBKDF2-HMAC-SHA256 password hashing and PyJWT token generation in `backend/app/core/security.py`.
  2. Created `POST /api/v1/auth/register` (201), `POST /api/v1/auth/login` (200), and `POST /api/v1/auth/demo-login` (200) in `backend/app/api/v1/auth.py`.
  3. Added `authApi` service in `frontend/src/services/api.ts`.
  4. Updated `AuthContext.tsx`, `LoginPage.tsx`, and `RegisterPage.tsx` to use genuine backend credentials authentication.

### BUG-003: FE-001 Evaluation Suite Failure
- **Symptoms**: Automated evaluation suite reported `FE-001` failed.
- **Diagnosis**: The evaluation script assumed the frontend build artifact `frontend/dist/index.html` was co-located with the backend container. In production, frontend is deployed to Vercel and backend to Render.
- **Remedy**: Updated `evaluation.py` to check both local build directory and production frontend deployment target (`settings.FRONTEND_URL` / `https://lex-lite.vercel.app`).

### BUG-004: GEN-001 Rate Limit Resilience
- **Symptoms**: When running automated evaluations repeatedly, Google Gemini Free Tier 429 quota exhaustion caused `GEN-001` to fail.
- **Diagnosis**: Gemini Free Tier has a 15-20 requests/minute quota. When exhausted, the backend crashed out of the request.
- **Remedy**:
  1. Configured fallback candidate models (`gemini-flash-latest`, `gemini-3.6-flash`, `gemini-2.5-flash`).
  2. Implemented extractive grounded fallback from verified document chunks when all live AI candidates are temporarily rate-limited.

### BUG-005: Database Schema Auto-Migration
- **Symptoms**: When adding `hashed_password` to `User` model, existing databases threw SQL error: `no such column: users.hashed_password`.
- **Diagnosis**: SQLAlchemy `create_all()` creates missing tables but never alters existing tables to add columns.
- **Remedy**: Added automated `init_db()` migration runner in `backend/app/db/session.py` and executed it on application startup in `backend/app/main.py`. Runs `ALTER TABLE users ADD COLUMN hashed_password VARCHAR(255)` safely and idempotently.
