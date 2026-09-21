# Actionable User Requirements & Execution Guide

This document outlines all actions required from the user to operate, test with live AI, and deploy the LegalAssistant platform.

> [!IMPORTANT]
> **Strict Security Notice:** Never provide API keys, passwords, or secret tokens in chat or commit them into git repositories. Always populate them locally in your private `.env` file.

---

## Group A: Required Before Development

### Action A-1: Local Virtual Environment & Dependencies Setup
- **What you must do:** Verify and activate the Python virtual environment and Node.js dependencies on your development machine.
- **Why it is required:** The backend relies on FastAPI, PyMuPDF, FAISS, and Sentence-Transformers; the frontend requires Node.js v18+ and React packages.
- **Exact steps:**
  ```powershell
  # 1. Backend environment
  cd backend
  python -m venv venv
  .\venv\Scripts\Activate.ps1
  pip install -r requirements.txt

  # 2. Frontend environment
  cd ..\frontend
  npm install
  ```
- **Where to perform it:** Local PowerShell terminal in the repository root.
- **Expected result:** All Python dependencies installed in `backend/venv` and npm modules in `frontend/node_modules`.
- **Whether it costs money:** $0.00 (Completely free and open-source).
- **Whether a free alternative exists:** Not applicable (Already 100% free).
- **What happens if not completed:** Backend tests and development server cannot start.

---

## Group B: Required for Live AI Testing

### Action B-1: Obtain a Free Google Gemini API Key
- **What you must do:** Generate a free API key from Google AI Studio.
- **Why it is required:** The system utilizes a genuine Google Gemini LLM (`gemini-1.5-flash`) for synthesizing retrieved legal clauses into grounded answers. Without this key, retrieval and extraction work 100% locally, but the final LLM synthesis step returns a `503 Service Unavailable (Missing Gemini API key)`.
- **Exact steps:**
  1. Open a browser and visit [Google AI Studio](https://aistudio.google.com/).
  2. Sign in with your Google account.
  3. Click **"Get API key"** -> **"Create API key in new project"**.
  4. Copy the generated key.
  5. Open `backend/.env` (or copy from `.env.example` if it doesn't exist yet):
     ```bash
     GEMINI_API_KEY=YOUR_KEY_HERE
     AI_PROVIDER=gemini
     GEMINI_MODEL=gemini-1.5-flash
     ```
- **Where to perform it:** Google AI Studio web console, then locally in `backend/.env`.
- **Expected result:** Backend connects to Gemini Free Tier without error.
- **Whether it costs money:** $0.00 (Gemini 1.5 Flash offers 15 RPM / 1,500 RPD completely free with no credit card required).
- **Whether a free alternative exists:** The application also supports local dummy extraction and local embeddings; an open-source Ollama endpoint can be configured if fully offline LLM inference is required.
- **What happens if not completed:** The RAG retrieval pipeline extracts and ranks chunks, but dynamic answer generation fails gracefully with an explicit message indicating the missing API key.

---

## Group C: Required for Deployment

### Action C-1: Select Cloud Deployment Target
- **What you must do:** Choose between Render/Vercel (easiest zero-cost path) or Google Cloud Run (containerized enterprise path).
- **Why it is required:** Running locally does not provide an external public URL for remote judges or stakeholders.
- **Exact steps (Recommended: Render + Vercel free tier):**
  1. Push repository to your private or public GitHub account.
  2. **Backend on Render:**
     - Visit [render.com](https://render.com) and create a **Web Service**.
     - Connect your GitHub repository.
     - Root directory: `backend`.
     - Build command: `pip install -r requirements.txt`.
     - Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
     - Add Environment Variables: `GEMINI_API_KEY=YOUR_KEY_HERE`, `SECRET_KEY=YOUR_RANDOM_SECRET`.
  3. **Frontend on Vercel:**
     - Visit [vercel.com](https://vercel.com) and import the frontend folder.
     - Root directory: `frontend`.
     - Add Environment Variable: `VITE_API_BASE_URL=https://your-render-service.onrender.com`.
- **Where to perform it:** Render.com and Vercel.com dashboards.
- **Expected result:** Deployed HTTPS web interface accessible globally.
- **Whether it costs money:** $0.00 (Both platforms provide generous free tiers).
- **Whether a free alternative exists:** Docker Compose locally or Fly.io free allowance.
- **What happens if not completed:** The application remains accessible solely at `http://localhost:5173`.

---

## Group D: Required for Public Demo

### Action D-1: Ingest Demo Legal Document Before Demonstration
- **What you must do:** Upload the provided synthetic sample contract (`backend/app/demo_assets/sample_commercial_lease.pdf`) into the application.
- **Why it is required:** A clean, realistic legal agreement ensures judges can inspect real clause numbers (e.g., Section 4.2 Security Deposit, Section 11 Indemnification) without exposing confidential real-world contracts.
- **Exact steps:**
  1. Start backend: `uvicorn app.main:app --port 8000`
  2. Start frontend: `npm run dev`
  3. Navigate to `http://localhost:5173/register` and create an account (e.g. `demo@lexlite.ai`).
  4. Go to **Document Upload** and upload `sample_commercial_lease.pdf`.
  5. Wait for the progress indicator to reach `Status: Ready`.
- **Where to perform it:** Web browser interface.
- **Expected result:** Document appears in Document Library with status `Ready`, and chunks/embeddings are created in FAISS.
- **Whether it costs money:** $0.00.
- **Whether a free alternative exists:** Not applicable.
- **What happens if not completed:** You would need to spend 30-45 seconds of your 4-minute demo uploading a document from scratch.

---

## Group E: Optional Improvements

### Action E-1: Configure PostgreSQL for Multi-Instance Scaling
- **What you must do:** Replace SQLite with a managed PostgreSQL instance (e.g., Neon or Supabase free tier).
- **Why it is required:** SQLite locks during concurrent writes under heavy multi-tenant load.
- **Exact steps:**
  1. Create a free database at [neon.tech](https://neon.tech).
  2. In `backend/.env`, set `DATABASE_URL=postgresql+psycopg2://user:password@ep-xyz.neon.tech/neondb`.
- **Where to perform it:** Neon Console and `backend/.env`.
- **Expected result:** Concurrency scaling to thousands of simultaneous requests.
- **Whether it costs money:** $0.00 (Free tier provides 0.5 GB storage).
- **Whether a free alternative exists:** SQLite is already configured and working out-of-the-box.
- **What happens if not completed:** SQLite functions perfectly for local demos and single-instance deployments.
