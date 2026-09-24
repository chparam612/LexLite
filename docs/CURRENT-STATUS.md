# LexLite System Status & Canonical Ground Truth

**Date:** 2026-09-24  
**Repository:** LexLite / LegalAssistant (`chparam612/LexLite`)  
**Status:** In active deployment & verification  

---

## 1. Verified Architecture & Service Identification

Through direct inspection of Git history, curl probes, and Render service mapping in this session, the following facts have been verified:

| Service / Resource | Identifier / Hostname | Status | Verified Technical Reality |
| :--- | :--- | :--- | :--- |
| **Backend API** | `srv-daols88473hc73cto6g0` / `https://legal-ai-backend-crc0.onrender.com` | **In Deployment** | Confirmed that `srv-daols88473hc73cto6g0` is the single live Render service for `legal-ai-backend-crc0.onrender.com`. There is no separate orphaned service to delete. |
| **Backend Database** | `legal-ai-postgres` | **Managed PostgreSQL** | PostgreSQL 16 with `pgvector` extension configured via `render.yaml`. |
| **Frontend Application** | Vercel Hosting (`vite build`) | **Ready for Vercel Redeploy** | Configured with `VITE_API_BASE_URL=https://legal-ai-backend-crc0.onrender.com`. |

---

## 2. Root Cause Analysis: Why Old Code Was Served

Direct testing of `https://legal-ai-backend-crc0.onrender.com` initially returned:
- `GET /health` -> `{"status":"healthy","environment":"development",...}`
- `POST /api/v1/auth/demo-login` -> `HTTP 404 Not Found`
- `GET /openapi.json` -> routes registered matched commit `af3e5cb` (Mon Sep 21), lacking `/auth/login`, `/auth/register`, and `/auth/demo-login`.

**Root Cause Confirmed**:
- In the Render Dashboard settings for service `srv-daols88473hc73cto6g0`, the **Root Directory** was left empty instead of being set to `backend`.
- Because the repository files reside in `backend/` (`backend/requirements.txt`, `backend/app/`, `backend/alembic.ini`), builds attempted from repo root failed.
- On Render, when a new deployment **fails**, Render **refuses to switch live traffic to the failed build**. Instead, it silently continues serving the last build that succeeded (`af3e5cb`).
- This caused the service to appear alive while actually running 3-day-old code.

---

## 3. Required Render Service Configuration

In Render Dashboard -> `srv-daols88473hc73cto6g0`:

### Settings (`/settings`)
- **Root Directory**: `backend`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `(alembic upgrade head || true) && uvicorn app.main:app --host 0.0.0.0 --port $PORT`

*(Or if Root Directory is left empty: Build Command: `cd backend && pip install -r requirements.txt`; Start Command: `cd backend && (alembic upgrade head || true) && uvicorn app.main:app --host 0.0.0.0 --port $PORT`)*

### Environment Variables (`/env`)
- `APPLICATION_ENV` = `production`
- `ENVIRONMENT` = `production`
- `CORS_ALLOWED_ORIGINS` = `*`
- `STORAGE_BACKEND` = `local`
- `LOCAL_STORAGE_DIR` = `./storage/uploads`
- `PYTHON_VERSION` = `3.11.9`
- `DATABASE_URL` = *(linked to `legal-ai-postgres` connection string)*

---

## 4. Frontend & Vercel Configuration Instruction

`frontend/.env` and `frontend/.env.example` have both been locked to:
```env
VITE_API_BASE_URL=https://legal-ai-backend-crc0.onrender.com
```

### Action Required in Vercel:
> Set `VITE_API_BASE_URL` to `https://legal-ai-backend-crc0.onrender.com` in Vercel → Settings → Environment Variables, for Production/Preview/Development, then redeploy without build cache.

---

## 5. Verification Probes (Raw Curl Logs)

### Baseline (Prior to Clean Deploy):
```http
HTTP/1.1 200 OK
Date: Thu, 24 Sep 2026 04:37:49 GMT
Content-Type: application/json
Transfer-Encoding: chunked
Connection: keep-alive
rndr-id: 69c861a6-f206-4b40
Server: cloudflare
x-correlation-id: 0e78cd80-8bba-4423-986f-fefd08de5967
x-process-time-ms: 3.04
x-render-origin-server: uvicorn

{"status":"healthy","app_name":"LEGAL AI — ASSISTANCE & ACCESS","version":"0.1.0","environment":"development","timestamp":"2026-09-24T04:37:49.538652+00:00"}
```

```http
HTTP/1.1 404 Not Found
Date: Thu, 24 Sep 2026 04:37:55 GMT
Content-Type: application/json
Transfer-Encoding: chunked
Connection: keep-alive
rndr-id: 415964a0-244c-40f9
Server: cloudflare

{"detail":"Not Found"}
```

### Post-Deploy Verification Commands (Execute Once Deploy Finishes):
```bash
curl -i https://legal-ai-backend-crc0.onrender.com/health
curl -i -X POST https://legal-ai-backend-crc0.onrender.com/api/v1/auth/demo-login
```
**Expected Results Once Live**:
- `/health`: `"environment": "production"`
- `/api/v1/auth/demo-login`: HTTP `200 OK` with JSON `{ "access_token": "...", "token_type": "bearer", "user": { ... } }`

---

## 6. Documentation & Obsolete Files Cleanup

- Removed obsolete conflicting deployment doc `docs/deployment-readiness.md` which declared outdated environment variable names (`ENV`, `SECRET_KEY`, `CORS_ORIGINS`).
- Cleaned up prior root-cause speculation documents from `/docs`.
- Verified canonical environment variable naming across the repository:
  - `CORS_ALLOWED_ORIGINS` (canonical; fallback `BACKEND_CORS_ORIGINS` supported via Pydantic `AliasChoices`)
  - `JWT_SECRET_KEY` (canonical; fallback `JWT_SECRET` supported via Pydantic `AliasChoices`)
  - `APPLICATION_ENV` (canonical; fallback `ENVIRONMENT` synced in `config.py`)
