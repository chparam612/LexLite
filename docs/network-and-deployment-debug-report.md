# Network and Deployment Debug Report

**Date**: September 21, 2026  
**Status**: Analyzed & Documented  
**Services**: 
- Frontend: Vercel (`https://lex-lite.vercel.app/`)
- Backend: Render (`https://legal-ai-backend.onrender.com`)

---

## 1. Network Topology & Environment Variable Mapping

The application is deployed across two independent cloud providers:
1. **Frontend**: Hosted on Vercel as a static Single Page Application (SPA) built via Vite + React.
2. **Backend**: Hosted on Render as a Python FastAPI container/web service.

### Environment Variable Mapping
The user previously noted confusion regarding `VITE_API_URL` vs `VITE_API_BASE_URL`.

| Environment Variable | Service | Required Value | Purpose |
| :--- | :--- | :--- | :--- |
| `VITE_API_BASE_URL` | Vercel (Frontend) | `https://legal-ai-backend.onrender.com` | Configures Axios baseURL in `frontend/src/services/api.ts`. Vite only exposes variables prefixed with `VITE_` to client code. |
| `FRONTEND_URL` | Render (Backend) | `https://lex-lite.vercel.app` | Whitelists the production frontend in CORS middleware. |
| `APPLICATION_ENV` | Render (Backend) | `production` | Sets production operational mode. |
| `SECRET_KEY` | Render (Backend) | `[SECURE_RANDOM_HEX]` | Used for session & signing integrity. |
| `JWT_SECRET_KEY` | Render (Backend) | `[SECURE_RANDOM_HEX]` | Signs and verifies user JWT access tokens. |
| `GEMINI_API_KEY` | Render (Backend) | `AIzaSy...` | Powers Gemini GenAI extraction & query synthesis. |

---

## 2. Production Network Trace of the 401 Failure

Prior to remediation, the user flow encountered a fatal loop:

```
[Browser / Vercel]
       │
       ├─ 1. User submits login/register form
       ├─ 2. Frontend constructs synthetic token: "test_token_:user_uid:..."
       ├─ 3. GET https://legal-ai-backend.onrender.com/api/v1/auth/me
       │     Header: "Authorization: Bearer test_token_:..."
       ▼
[Render API Gateway]
       │
       ├─ 4. Passes request to FastAPI container
       ▼
[FastAPI Backend - security.py]
       │
       ├─ 5. Checks token prefix -> "test_token_:"
       ├─ 6. Inspects APPLICATION_ENV -> "production"
       ├─ 7. Fails check: test tokens forbidden in production!
       ├─ 8. Returns HTTP 401 Unauthorized: {"detail": "Invalid authentication token"}
       ▼
[Browser / Vercel]
       │
       ├─ 9. Axios interceptor intercepts 401
       ├─ 10. Removes 'auth_token' from localStorage
       ├─ 11. Dispatches 'auth:unauthorized' event
       └─ 12. Displays UI banner: "Authentication failed"
```

---

## 3. Post-Remediation Production Network Trace

With native JWT authentication deployed:

```
[Browser / Vercel]
       │
       ├─ 1. User enters Email & Password
       ├─ 2. POST https://legal-ai-backend.onrender.com/api/v1/auth/login
       │     Body: {"email": "...", "password": "..."}
       ▼
[Render API Backend]
       │
       ├─ 3. Queries user table for email
       ├─ 4. Verifies salted PBKDF2 hash using secrets.compare_digest
       ├─ 5. Issues HS256 JWT access token with 7-day expiration
       ├─ 6. Returns HTTP 200 OK: {"access_token": "eyJhbG...", "user": {...}}
       ▼
[Browser / Vercel]
       │
       ├─ 7. Saves real signed JWT into localStorage
       ├─ 8. Sets user state in AuthContext
       └─ 9. Seamlessly navigates to /dashboard
```

---

## 4. CORS & Cross-Origin Verification

In `backend/app/main.py`:
- `CORSMiddleware` explicitly allows `FRONTEND_URL` (`https://lex-lite.vercel.app`), `http://localhost:5173`, and any preview deployments via regex matching `https://.*\.vercel\.app`.
- `allow_credentials=True`, `allow_methods=["*"]`, `allow_headers=["*"]`.
- Options preflight requests receive `HTTP 200 OK` with proper CORS access headers.
