# Production Authentication Root Cause & Architecture Audit

## 1. System Overview
Authentication in the LexLite platform is designed to support dual operation:
1. **Production Mode**: JWT Bearer authentication backed by PostgreSQL / Supabase, validating hashed passwords (bcrypt) and signing tokens with `JWT_SECRET`.
2. **Demo / Quick Evaluation Mode**: Seeded demo accounts (`demo@lexlite.internal` / `demopassword123`) or local bypass when unconfigured.

---

## 2. Root Cause Audit of Authentication Failures

### Root Cause A: Cold-Start Timeout on Render Backend
- **Symptom**: User clicks "Sign In" or "Register"; spinner spins for 30–50 seconds before failing with a network error or 504 Gateway Timeout.
- **Underlying Mechanism**: Render free instances spin down after 15 minutes of inactivity. The first HTTP request triggers container spin-up, Python environment initialization, PyTorch/SentenceTransformers loading, and database connection pooling.
- **Frontend Impact**: Vite/Axios default request timeouts were tripping before the server finished warming up.
- **Fix**: Implemented health check pinging and backend wake-up retry logic with user-friendly warming notices.

### Root Cause B: Ghost Token / Inconsistent LocalStorage State
- **Symptom**: User appears logged in on the navbar, but all API actions (Chat, Upload, List Documents) fail with 401.
- **Underlying Mechanism**: `AuthContext.tsx` previously caught `/api/v1/auth/me` errors and assigned a fake client-side user object without validating the stored token. The Axios interceptor attached the stale token to all subsequent requests.
- **Fix**: Removed fake client-side fallback in production. When `/api/v1/auth/me` returns 401, the invalid token is purged from `localStorage`, state is reset, and the user is redirected to sign-in.

### Root Cause C: Password Hashing Discrepancy
- **Symptom**: Seeded demo credentials failed password verification on fresh databases.
- **Underlying Mechanism**: `bcrypt` cost factor variations and salt generation discrepancies between manual script seeds and runtime `passlib` handlers.
- **Fix**: Standardized `verify_password` and `get_password_hash` using `passlib.context.CryptContext(schemes=["bcrypt"], deprecated="auto")`. Seed scripts now dynamically verify password validity at startup.

---

## 3. Authentication Verification Matrix

| Test ID | Scenario | Input | Expected Result | Verified Result |
| :--- | :--- | :--- | :--- | :--- |
| AUTH-001 | User Registration | New email + strong password | 201 Created + User record | PASS |
| AUTH-002 | Duplicate Registration | Existing email | 400 Bad Request ("Email already registered") | PASS |
| AUTH-003 | User Sign-In | Valid credentials | 200 OK + JWT access_token | PASS |
| AUTH-004 | Bad Password | Valid email + incorrect password | 401 Unauthorized | PASS |
| AUTH-005 | Token Verification | Valid Bearer token to `/auth/me` | 200 OK + User profile | PASS |
| AUTH-006 | Expired Token | Expired Bearer token | 401 Unauthorized + Client purge | PASS |
| AUTH-007 | Instant Demo Login | Click "Try Demo Account" | Real authenticated session issued | PASS |

---

## 4. Production Credentials for Manual Testing
- **Email**: `demo@lexlite.internal`
- **Password**: `demopassword123`
- **Role**: `attorney`
- **Token Type**: Bearer JWT
