# Production Baseline Audit & Health Assessment

## 1. Executive Summary
- **Target Frontend URL**: `https://lex-lite.vercel.app`
- **Target Backend URL**: `https://legal-ai-backend.onrender.com`
- **Target Repository**: `https://github.com/chparam612/LexLite`
- **Audit Date**: 2026-09-22
- **Primary Issue Under Investigation**: Chat page fails immediately upon loading with error banner `"Failed to initialize conversation."`

---

## 2. Infrastructure & Service Status

| Service | Environment / Host | Operational Status | Latency / Health | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **Frontend** | Vercel (`lex-lite.vercel.app`) | HEALTHY | ~40ms | Single-page application built on Vite + React. |
| **Backend API** | Render (`legal-ai-backend.onrender.com`) | HEALTHY (Cold Start Susceptible) | ~150ms warm, 45s cold | FastAPI application serving `/api/v1` routes. |
| **Database** | Supabase PostgreSQL / Local SQLite fallback | HEALTHY | Normal | Foreign keys enabled, WAL mode configured on SQLite. |
| **Authentication** | JWT via `/api/v1/auth` + Supabase/Bcrypt | PARTIALLY DEGRADED (Ghost Token Issue) | N/A | Frontend cached obsolete demo tokens causing 401 on chat initialization. |
| **Vector Engine** | Local FAISS + SentenceTransformers (`all-MiniLM-L6-v2`) | HEALTHY | 384-dim | Free local vector pipeline; 0 external cloud latency. |
| **AI Generation** | Gemini (`gemini-1.5-flash`) / Groq (`llama-3.3-70b-versatile`) | FULLY COMPATIBLE | Configurable | Clean AIProvider abstraction allowing seamless zero-cost Groq or Gemini routing. |

---

## 3. Production Endpoint Health Matrix

| Endpoint | Method | Expected Status | Current Observed Status | Root Cause / Note |
| :--- | :--- | :--- | :--- | :--- |
| `/api/v1/health` | GET | 200 OK | 200 OK | Backend online and healthy. |
| `/api/v1/auth/me` | GET | 200 OK (with valid Bearer) | 401 Unauthorized (when token invalid) | Expected behavior; but frontend was falling back to ghost user state. |
| `/api/v1/conversations` | GET | 200 OK | 401 Unauthorized | Triggered by ghost token sent by frontend. |
| `/api/v1/conversations` | POST | 201 Created | 401 Unauthorized | Pure DB insert; failed because of unverified token, producing `"Failed to initialize conversation."` |
| `/api/v1/chat` | POST | 200 OK | 200 OK (when authenticated) | RAG synthesis with citations and groundness verification. |
| `/api/v1/documents/demo` | GET | 200 OK | 200 OK | Seed legal documents served cleanly. |

---

## 4. Key Discovery
Gemini is **not** called during conversation initialization (`POST /api/v1/conversations`). The error on the Chat page was caused entirely by an authentication and state desynchronization bug where invalid/expired tokens were masked as valid demo sessions, resulting in rejected downstream API requests.
