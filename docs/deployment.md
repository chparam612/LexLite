# Zero-Cost Cloud Deployment Guide: Render + Vercel

This guide explains how to deploy the entire Legal AI platform for free with **zero credit card requirements** using Render (FastAPI Backend + PostgreSQL) and Vercel (React Frontend).

---

## Architecture Overview

```
                  ┌──────────────────────────────┐
                  │    Vercel (React + Vite)     │
                  │   https://legal-ai.vercel.app│
                  └──────────────┬───────────────┘
                                 │ HTTPS REST API
                                 ▼
                  ┌──────────────────────────────┐
                  │      Render Web Service      │
                  │   FastAPI (Python 3.11)      │
                  │https://legal-ai-api.onrender.com
                  └──────────────┬───────────────┘
                                 │
                                 ▼
                  ┌──────────────────────────────┐
                  │ Render PostgreSQL / Supabase │
                  │  PostgreSQL with pgvector    │
                  └──────────────────────────────┘
```

---

## Option A: One-Click Render Blueprint (Recommended)

Render allows spinning up both the backend web service and PostgreSQL database automatically using our included [`render.yaml`](file:///render.yaml).

### Steps:
1. Push your latest code to your GitHub repository:
   ```bash
   git add .
   git commit -m "feat: complete demo requirements and deployment config"
   git push origin main
   ```
2. Log in to [Render.com](https://render.com) using your GitHub account.
3. In your Render Dashboard, click **New +** and select **Blueprint**.
4. Connect your GitHub repository (`LegalAssistant` or `LexLite`).
5. Render will automatically detect `render.yaml` and create:
   - **`legal-ai-postgres`**: Free PostgreSQL database.
   - **`legal-ai-backend`**: Free Python Web Service running FastAPI.
6. Under Environment Variables for `legal-ai-backend`:
   - Set `GEMINI_API_KEY` to your Google AI Studio key (free at [aistudio.google.com](https://aistudio.google.com)).
7. Click **Apply**.
8. Once deployed, copy your backend URL (e.g., `https://legal-ai-api.onrender.com`).

---

## Option B: Deploy Frontend to Vercel

Vercel provides free, instantaneous global hosting for Vite/React applications.

### Steps:
1. Log in to [Vercel.com](https://vercel.com) using your GitHub account.
2. Click **Add New...** -> **Project**.
3. Import your GitHub repository.
4. In the configuration screen:
   - **Framework Preset**: Vite
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
5. Under **Environment Variables**, add:
   - `VITE_API_BASE_URL`: Your Render backend URL (e.g., `https://legal-ai-api.onrender.com`).
6. Click **Deploy**.
7. In ~60 seconds, your site is live at `https://<your-project>.vercel.app`.

---

## Option C: Free Supabase PostgreSQL Database (Alternative)

If you prefer Supabase's hosted PostgreSQL with built-in `pgvector`:
1. Create a free project at [database.new](https://database.new) (Supabase).
2. Go to **Project Settings** -> **Database** and copy the **Connection string (URI)**.
3. In SQL Editor, run:
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```
4. In your Render backend settings, set `DATABASE_URL` to your Supabase connection URI.

---

## Verification After Deployment

1. Visit `https://<your-backend-url>/health` - should return `{"status": "healthy"}`.
2. Visit `https://<your-frontend-url>/evaluation` - executes the live 10-category automated verification suite.
3. Visit `https://<your-frontend-url>/demo` - 1-click synthetic rental agreement ingestion and testing for DEMO-001 through DEMO-008.
