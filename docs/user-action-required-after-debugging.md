# User Action Required After Production Debugging

**Date**: September 21, 2026  
**Priority**: Immediate  
**Status**: Code Fixes Complete Locally — Awaiting Git Push & Cloud Deployment

---

## 1. What Has Been Fixed For You Locally

All code fixes for user registration, user sign-in, instant demo attorney login, evaluation test suites, and database schema migrations have been implemented and verified locally:
1. ✅ **Native User Registration & Login**: Added PBKDF2 password hashing, HS256 JWT tokens, and endpoints (`/api/v1/auth/register`, `/api/v1/auth/login`, `/api/v1/auth/demo-login`).
2. ✅ **Zero-Downtime Database Migration**: `session.init_db()` automatically migrates the database schema on startup without dropping tables or losing data.
3. ✅ **Frontend Integration**: Converted `LoginPage.tsx`, `RegisterPage.tsx`, and `AuthContext.tsx` to use genuine backend credentials.
4. ✅ **Rate-Limit Resilience**: GenAI calls now smoothly fall back across candidate models and local clause grounding if Gemini Free Tier limits are reached.
5. ✅ **100% Passing Tests**: All 12 authentication tests pass; frontend builds with 0 errors.

---

## 2. Actions Required From You

### Step 1: Push Code to GitHub
To push all fixes to your GitHub repository so that Render and Vercel automatically re-deploy:

Open your terminal in the project root directory and run:
```bash
git add .
git commit -m "fix(auth): implement native JWT registration, login, and schema auto-migration"
git push origin main
```

---

### Step 2: Confirm Vercel Environment Variables
You previously noted confusion about finding `VITE_API_URL`.

**Important**: In Vite applications, all environment variables exposed to the browser must start with `VITE_`. This project uses `VITE_API_BASE_URL`.

1. Go to your **Vercel Dashboard**: `https://vercel.com/`
2. Open your project: **`lex-lite`**
3. Navigate to: **Settings** → **Environment Variables**
4. Verify or Add the following key:
   - **Key**: `VITE_API_BASE_URL`
   - **Value**: `https://legal-ai-backend.onrender.com`
   - **Environments**: Select Production, Preview, Development
5. If you change this variable, click **Deployments** → click the latest deployment → click **Redeploy**.

---

### Step 3: Confirm Render Environment Variables
1. Go to your **Render Dashboard**: `https://dashboard.render.com/`
2. Open your web service: **`legal-ai-backend`**
3. Navigate to: **Environment**
4. Verify the following variables are present:
   - `FRONTEND_URL` = `https://lex-lite.vercel.app`
   - `GEMINI_API_KEY` = `[Your Google Gemini API Key]`
   - `SECRET_KEY` = `[Any random 32-character string]`
   - `JWT_SECRET_KEY` = `[Any random 32-character string]`
   - `APPLICATION_ENV` = `production`
5. Once your Git push lands, Render will automatically deploy and initialize the database.

---

### Step 4: Test in Production
Once deployed:
1. Visit `https://lex-lite.vercel.app/`
2. Click **Instant Sign In as Demo Attorney** → You will immediately enter the legal dashboard.
3. Or click **Create a new account** → Register with your email and password → You will be successfully registered and logged in with your own account.
