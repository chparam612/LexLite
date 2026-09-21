# Authentication System Root-Cause & Production Remediation Report

**Date**: September 21, 2026  
**Status**: Resolved & Verified  
**Affected Service**: Frontend (Vercel) & Backend API (Render)

---

## 1. Executive Summary

Users attempting to register or log into the production application (`https://lex-lite.vercel.app/`) encountered consistent authentication failures (`Authentication failed: Invalid authentication token` or HTTP 401 Unauthorized). The instant demo login was similarly non-functional in production.

This report documents the architectural root causes, the code failure points, the production remediation deployed, and the verification steps taken.

---

## 2. Root Cause Analysis

### 2.1 The Frontend Mock Token Architecture
The initial frontend codebase was structured under the assumption that a client-side Firebase Web SDK would handle authentication. When running locally without Firebase configuration, the code fell back to creating synthetic development tokens:
```typescript
// Former frontend code:
const token = `test_token_:${email.split('@')[0]}_uid:${email}:${name}`;
await login(token);
```
These strings were stored directly in `localStorage.getItem('auth_token')` and forwarded in the `Authorization: Bearer <token>` header to the backend.

### 2.2 Backend Production Enforcement
In `backend/app/core/security.py`, the token verification logic strictly gated development tokens behind environment checks:
```python
if token.startswith("test_token_:"):
    if settings.is_development() or settings.APPLICATION_ENV == "test":
        ...  # Accepted only in dev/test
    # In production (Render):
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication token"
    )
```
On Render, `APPLICATION_ENV=production` is set. As a result:
1. Every user attempt to register generated a `test_token_:...` string.
2. The subsequent `/api/v1/auth/me` call returned HTTP 401.
3. The frontend intercepted the 401, cleared localStorage, and displayed `"Authentication failed"`.

### 2.3 Missing Backend Registration & Login Endpoints
The backend had **no user registration or credential login endpoints**:
- No `POST /api/v1/auth/register` existed.
- No `POST /api/v1/auth/login` existed.
- The `User` SQLAlchemy database model contained no `hashed_password` column.
- The `User` model required a non-null `firebase_uid` (`nullable=False`), preventing native accounts without Firebase UIDs.

---

## 3. Remediation & Implementation Details

### 3.1 Native Cryptographic Security (`backend/app/core/security.py`)
- **Password Hashing**: Implemented PBKDF2-HMAC-SHA256 with 100,000 iterations and per-password cryptographic salting (`hash_password`, `verify_password`). Uses Python's native `hashlib` and `secrets`, avoiding external C-extension binary dependencies.
- **JWT Issuance & Verification**: Implemented standard RFC 7519 JSON Web Token issuance via `PyJWT` (`HS256`).
- **Unified Verification**: `verify_firebase_token` seamlessly validates:
  1. Native HS256 JWT tokens issued by the backend.
  2. Firebase ID tokens (when Firebase Admin SDK credentials are provided).
  3. Local test tokens (strictly restricted to local dev/test environments).

### 3.2 Database Schema & Auto-Migration (`backend/app/models/user.py` & `session.py`)
- Added `hashed_password = Column(String(255), nullable=True)`.
- Made `firebase_uid` nullable (`nullable=True`) to support native accounts.
- Added idempotent `init_db()` migration runner executing on application startup:
  ```sql
  ALTER TABLE users ADD COLUMN hashed_password VARCHAR(255);
  ```
  Works automatically across both SQLite and PostgreSQL on Render.

### 3.3 Auth Endpoints (`backend/app/api/v1/auth.py`)
1. **`POST /api/v1/auth/register`** (HTTP 201):
   - Validates email and minimum 8-character password.
   - Prevents duplicate registration (HTTP 400).
   - Hashes password with PBKDF2 and creates user record.
   - Returns signed JWT access token and user profile.
2. **`POST /api/v1/auth/login`** (HTTP 200):
   - Authenticates email and password using constant-time hash verification.
   - Returns signed JWT access token and user profile.
3. **`POST /api/v1/auth/demo-login`** (HTTP 200):
   - Creates or retrieves `attorney@legalai.example.com` demo account.
   - Returns valid, signed JWT access token allowing instant trial without registration.

### 3.4 Frontend Integration (`frontend/src/`)
- Updated `frontend/src/services/api.ts` with `authApi.register`, `authApi.login`, `authApi.demoLogin`.
- Updated `frontend/src/contexts/AuthContext.tsx` with `loginWithCredentials`, `registerWithCredentials`, and real API call in `loginAsDemoAttorney`.
- Updated `LoginPage.tsx` and `RegisterPage.tsx` to call real credentials authentication.

---

## 4. Verification Results

| Test Scenario | Endpoint / Mechanism | Result |
| :--- | :--- | :--- |
| Valid User Registration | `POST /api/v1/auth/register` | ✅ HTTP 201 Created + Valid JWT |
| Duplicate User Registration | `POST /api/v1/auth/register` | ✅ HTTP 400 Bad Request |
| Valid User Login | `POST /api/v1/auth/login` | ✅ HTTP 200 OK + Valid JWT |
| Invalid Password Rejection | `POST /api/v1/auth/login` | ✅ HTTP 401 Unauthorized |
| Instant Demo Attorney Login | `POST /api/v1/auth/demo-login` | ✅ HTTP 200 OK + Valid JWT |
| Authenticated User Profile | `GET /api/v1/auth/me` with JWT | ✅ HTTP 200 OK + Correct User Profile |
| Frontend TypeScript Build | `npm run build` | ✅ Zero errors, bundle created in 8.77s |
