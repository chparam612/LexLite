# User Action Required — Configuration & Deployment Checklist

## 1. Action Items for Vercel (Frontend)
1. Navigate to **Vercel Dashboard** -> Project `LexLite` (or `lex-lite`).
2. Go to **Settings** -> **Environment Variables**.
3. Verify or add:
   - **Key**: `VITE_API_BASE_URL`
   - **Value**: `https://legal-ai-backend.onrender.com`
   - **Environments**: Production, Preview, Development.
4. **Trigger Redeploy**:
   - Go to **Deployments** tab.
   - Click the three dots on the latest deployment -> **Redeploy**.
   - Ensure "Redeploy with existing build cache" is **unchecked** so new environment variables are baked in.

---

## 2. Action Items for Render (Backend)
1. Navigate to **Render Dashboard** -> Your Web Service (`legal-ai-backend`).
2. Go to **Environment**.
3. Verify or configure the following variables:
   - `BACKEND_CORS_ORIGINS`: `["https://lex-lite.vercel.app","http://localhost:5173"]`
   - `JWT_SECRET`: A secure random string.
   - `AI_PROVIDER`: `groq` (recommended for fastest speed) or `gemini`.
   - If using Groq:
     - `GROQ_API_KEY`: Paste your Groq API key (`gsk_...` from [Groq Console](https://console.groq.com/keys)).
     - `GROQ_MODEL`: `llama-3.3-70b-versatile`
   - If using Gemini:
     - `GEMINI_API_KEY`: Paste your Google AI Studio key (`AIzaSy...`).
     - `GEMINI_MODEL`: `gemini-1.5-flash`
4. Click **Save Changes**. Render will trigger an automatic restart and build.

---

## 3. Git Push & CI Verification
1. Commit the local changes:
   ```bash
   git add .
   git commit -m "fix(prod): resolve conversation init, add Groq provider, and fix CI"
   git push origin main
   ```
2. Check the GitHub Actions tab at `https://github.com/chparam612/LexLite/actions` to confirm both:
   - `Backend Lint & Pytest` -> **PASSED**
   - `Frontend Typecheck & Build` -> **PASSED**
