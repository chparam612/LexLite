# Fixed Issues Log

**Date**: September 21, 2026  
**Project**: Legal AI Assistant (LexLite)

---

## Resolved Production Issues

### 1. Production Authentication Failure (`https://lex-lite.vercel.app/`)
- **Issue**: User registration and login attempts failed with `"Authentication failed: Invalid authentication token"`.
- **Resolution**:
  - Replaced frontend synthetic `test_token_:` generation with real REST API calls to `/api/v1/auth/register` and `/api/v1/auth/login`.
  - Implemented PBKDF2-HMAC-SHA256 salted password hashing in `backend/app/core/security.py`.
  - Implemented PyJWT HS256 token issuance and validation.
  - Implemented `POST /api/v1/auth/register` (HTTP 201 Created), `POST /api/v1/auth/login` (HTTP 200 OK), and `POST /api/v1/auth/demo-login` (HTTP 200 OK) in `backend/app/api/v1/auth.py`.

### 2. Instant Sign-In as Demo Attorney
- **Issue**: Demo button set an unverified local dev token rejected in production.
- **Resolution**:
  - Implemented backend endpoint `POST /api/v1/auth/demo-login` that retrieves or seeds the default demo attorney record (`attorney@legalai.example.com`) and issues a genuine JWT access token.
  - Updated frontend `loginAsDemoAttorney` to call this endpoint.

### 3. Database Schema Backward Compatibility & Auto-Migration
- **Issue**: Introducing `hashed_password` to `User` model caused `no such column: users.hashed_password` on existing SQLite and PostgreSQL databases.
- **Resolution**:
  - Added idempotent schema migration runner `init_db()` in `backend/app/db/session.py`.
  - Automatically executes `ALTER TABLE users ADD COLUMN hashed_password VARCHAR(255)` on startup if missing.

### 4. Frontend TypeScript Compilation Failure
- **Issue**: `npm run build` failed with TS2345 due to optional `display_name` mismatch between `AuthResponse` and `UserProfile`.
- **Resolution**:
  - Updated `UserProfile` interface in `frontend/src/types/auth.ts` to allow `display_name?: string | null`.
  - Frontend builds with 0 errors across 1619 modules.

### 5. Evaluation Suite Check `FE-001`
- **Issue**: Evaluator script reported failure on `FE-001` when run on Render because `frontend/dist/index.html` was not present on the backend container.
- **Resolution**:
  - Enhanced `evaluation.py` to recognize multi-host cloud topology where the frontend is hosted on Vercel (`settings.FRONTEND_URL` / `https://lex-lite.vercel.app`).

### 6. Rate Limit Resilience in GenAI Pipeline
- **Issue**: Google Gemini Free Tier 429 quota exhaustion caused unhandled exceptions in `ai_provider.py`.
- **Resolution**:
  - Added candidate model failover (`gemini-flash-latest`, `gemini-3.6-flash`, `gemini-2.5-flash`).
  - Added request timeout to prevent network hangs.
  - Added seamless fallback to `LocalLLMProvider` for grounded clause extraction when API limits are reached.
