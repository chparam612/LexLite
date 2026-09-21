# Production Environment Variable Audit & Configuration Guide

## 1. Overview
This guide details every required and optional environment variable across the Frontend (Vercel) and Backend (Render/Cloud).

---

## 2. Frontend Environment Variables (Vercel)

| Variable Name | Required? | Example Value | Description |
| :--- | :--- | :--- | :--- |
| `VITE_API_BASE_URL` | **REQUIRED** | `https://legal-ai-backend.onrender.com` | Base URL of the deployed FastAPI backend. Note: Do NOT append trailing slash or `/api/v1`. |

> **IMPORTANT**: In Vite, environment variables MUST begin with `VITE_` to be embedded into the client bundle at build time. After setting `VITE_API_BASE_URL` on Vercel, trigger a **Redeploy** (without cache).

---

## 3. Backend Environment Variables (Render)

| Variable Name | Required? | Default / Example Value | Description |
| :--- | :--- | :--- | :--- |
| `ENVIRONMENT` | Optional | `production` | Operational mode (`production` or `development`). |
| `BACKEND_CORS_ORIGINS` | **REQUIRED** | `["https://lex-lite.vercel.app","http://localhost:5173"]` | JSON array or comma-separated list of allowed origins. |
| `DATABASE_URL` | Optional | `postgresql://user:pass@host:5432/db` | Database connection string. Falls back to SQLite if unset. |
| `JWT_SECRET` | **REQUIRED** | `random-secure-64-character-string` | Secret key used for signing JWT access tokens. |
| `JWT_ALGORITHM` | Optional | `HS256` | Algorithm for token signing. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Optional | `1440` | Token expiration period (24 hours). |
| `AI_PROVIDER` | **REQUIRED** | `groq` (or `gemini`) | Active LLM generation provider. |
| `GROQ_API_KEY` | Optional / Recommended | `gsk_...` | Groq API Key (required if `AI_PROVIDER=groq`). |
| `GROQ_MODEL` | Optional | `llama-3.3-70b-versatile` | Groq model name (`llama-3.3-70b-versatile` or `llama-3.1-8b-instant`). |
| `GROQ_BASE_URL` | Optional | `https://api.groq.com/openai/v1` | Groq OpenAI-compatible REST endpoint. |
| `GEMINI_API_KEY` | Optional | `AIzaSy...` | Google Gemini API Key (required if `AI_PROVIDER=gemini`). |
| `GEMINI_MODEL` | Optional | `gemini-1.5-flash` | Gemini model name. |

---

## 4. Verification Checklist for Render
1. Navigate to **Render Dashboard** -> Select Backend Web Service -> **Environment**.
2. Verify `BACKEND_CORS_ORIGINS` includes `https://lex-lite.vercel.app`.
3. Verify `AI_PROVIDER` is set to `groq` or `gemini`.
4. If using Groq: ensure `GROQ_API_KEY` is pasted and `GROQ_MODEL=llama-3.3-70b-versatile`.
5. If using Gemini: ensure `GEMINI_API_KEY` is pasted and `GEMINI_MODEL=gemini-1.5-flash`.
6. Verify `JWT_SECRET` is defined.
7. Click **Save Changes** (Render will automatically redeploy).
