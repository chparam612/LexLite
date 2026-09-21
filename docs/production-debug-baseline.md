# Production Debugging Baseline & System Inventory

**Audit Date:** 2026-09-21  
**Project:** LegalAssistant / LexLite  
**Repository:** `https://github.com/chparam612/LexLite.git`  
**Current Branch:** `main` (Up to date with `origin/main`)  
**Deployment URLs:**
- **Frontend (Vercel):** `https://lex-lite.vercel.app/`
- **Backend (Render):** `https://legal-ai-backend.onrender.com` (or user's Render service)

---

## 1. Technology Inventory

| Layer | Technology | Version | Purpose |
| :--- | :--- | :--- | :--- |
| **Frontend Framework** | React + Vite + TypeScript | React 18/19, Vite 5.4 | Single Page Application (SPA) |
| **UI & Styling** | Tailwind CSS, Lucide React | 3.4.x | Design system, responsive legal UI |
| **Backend Framework** | FastAPI + Uvicorn | FastAPI 0.111.0 | REST API, async document processing |
| **Database ORM** | SQLAlchemy 2.0 + Alembic | SQLAlchemy 2.0.30 | Multi-tenant schema, SQLite (dev) / PostgreSQL (prod) |
| **Authentication** | Dual: Native JWT + Firebase Adapter | PyJWT 2.8.0, Firebase Admin 6.5.0 | User registration, login, token verification |
| **Document Processing** | PyMuPDF (`fitz`), PyPDF | PyMuPDF 1.24.0 | Page-by-page PDF extraction |
| **Embeddings** | Sentence-Transformers / Local CPU | `all-MiniLM-L6-v2` (384-dim) | Zero-cost dense semantic vectors |
| **Vector Store** | FAISS CPU (`faiss-cpu`) | 1.7.4+ | Fast cosine similarity index |
| **Generative LLM** | Google Gemini API (`google.generativeai`) | `gemini-flash-latest` | Grounded answer generation, citation binding |
| **Frontend Hosting** | Vercel | Production | Global CDN Edge network |
| **Backend Hosting** | Render | Production Free Tier | Containerized Python web service |

---

## 2. Environment Variables Baseline

| Variable Name | Context | Expected Format | Status in Production |
| :--- | :--- | :--- | :--- |
| `VITE_API_BASE_URL` | Frontend (Vercel) | `https://your-backend.onrender.com` | **REQUIRES USER ACTION** (Must point to active Render backend) |
| `GEMINI_API_KEY` | Backend (Render) | `AIzaSy...` or `AQ...` | **PRESENT** (Tested & Verified with live Gemini API) |
| `GEMINI_MODEL` | Backend (Render) | `gemini-flash-latest` | **PRESENT** |
| `DATABASE_URL` | Backend (Render) | `sqlite:///./legal_ai_dev.db` or PostgreSQL | **PRESENT** |
| `STORAGE_BACKEND` | Backend (Render) | `local` | **PRESENT** |
| `LOCAL_STORAGE_DIR` | Backend (Render) | `./storage/uploads` | **PRESENT** |
| `CORS_ALLOWED_ORIGINS` | Backend (Render) | `*` or JSON list | **PRESENT** (Configured for Vercel) |
| `JWT_SECRET_KEY` | Backend (Render) | Random 64-char string | **PRESENT** (Auto-generated in `render.yaml`) |

---

## 3. Reproduction & Known Production Failures

### Bug 1: User Registration Fails
- **Symptom:** User enters Name, Email, Password on `/register` and clicks "Create Account", but registration fails or returns an error.
- **Root Cause Identified:** The backend was originally structured around external Firebase authentication tokens and lacked native `POST /api/v1/auth/register` endpoints. The `User` database model lacked a `hashed_password` column, meaning passwords were never stored or verified.

### Bug 2: User Sign-in Fails ("Authentication Failed")
- **Symptom:** User submits email + password on `/login`, but receives "Authentication failed".
- **Root Cause Identified:** 
  1. The frontend generated an ephemeral development token string (`test_token_:...`), which the backend rejected in production (`APPLICATION_ENV=production`).
  2. The backend lacked a native `POST /api/v1/auth/login` endpoint to verify passwords against salted database hashes.

### Bug 3: Evaluation Suite Failures on Vercel
- **Symptom:** `GEN-001` and `FE-001` displayed `FAIL` on `https://lex-lite.vercel.app/evaluation`.
- **Root Cause Identified:**
  - `GEN-001`: Hit Google Gemini Free Tier 15 RPM rate-limit cooldown without a graceful local grounding fallback.
  - `FE-001`: Looked for `frontend/dist/index.html` on the Render backend container's filesystem instead of recognizing that the frontend is hosted separately on Vercel.

---

## 4. Risky Areas (Must Preserve Working Functionality)

1. **RAG Vector Search & FAISS:** Working with 100% test pass rate (`test_retrieval.py`, `test_chunking.py`). Do not touch embedding dimensions or index serialization logic.
2. **Gemini Generative Provider:** Configured for `gemini-flash-latest` with structured JSON output. Must retain claim quote verification.
3. **Multi-tenant Document Ownership:** All document reads and chats must continue enforcing `user_id == current_user.id`.
