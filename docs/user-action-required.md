# User Action Required — Live Deployment & Environment Setup

## 1. Action Items for Render Dashboard (Backend)

1. Open your [Render Dashboard](https://dashboard.render.com).
2. Select your Web Service (`legal-ai-backend`).
3. Check the service URL displayed under your service name (confirmed live as: `https://legal-ai-backend-crc0.onrender.com`).
4. Click **Environment** in the left menu.
5. Verify and set the following exact keys (do NOT use outdated aliases):

| Key | Value | Reason |
| :--- | :--- | :--- |
| `CORS_ALLOWED_ORIGINS` | `*` *(or your Vercel URL)* | **CRITICAL**: The app reads `CORS_ALLOWED_ORIGINS` (not `BACKEND_CORS_ORIGINS`). |
| `JWT_SECRET_KEY` | *(Render auto-generates or paste 64-char hex)* | **CRITICAL**: The app reads `JWT_SECRET_KEY` (not `JWT_SECRET`). |
| `GEMINI_API_KEY` | `AIzaSy...` *(your Gemini key)* | Marked `sync: false` in `render.yaml`; must be supplied by you. |
| `GEMINI_MODEL` | `gemini-flash-latest` | Recommended free-tier Gemini model. |
| `DATABASE_MODE` | `postgres` | Sets database engine mode to PostgreSQL. |
| `VECTOR_STORE` | `pgvector` | Activates PostgreSQL pgvector persistence across cold starts. |
| `APPLICATION_ENV` | `production` | Enforces production mode and disables dev mocks. |

6. Check your **PostgreSQL Database** on Render:
   - On the Render Dashboard, check the database status for `legal-ai-postgres`.
   - **Note on Render Free Tier**: Free PostgreSQL databases expire 30 days after creation. If yours has expired or been suspended, click **New + -> PostgreSQL**, create a new free database named `legal-ai-postgres`, and update `DATABASE_URL` under your Web Service environment.
7. Click **Save Changes** (Render will automatically redeploy).

---

## 2. Action Items for Vercel Dashboard (Frontend)

1. Open your [Vercel Dashboard](https://vercel.com) and select the frontend project (`LexLite`).
2. Go to **Settings** -> **Environment Variables**.
3. Verify or set:
   - **Key**: `VITE_API_BASE_URL`
   - **Value**: `https://legal-ai-backend-crc0.onrender.com`
   - **Environments**: Production, Preview, Development.
   - *Ensure no trailing slash `/` and no `/api/v1` in the URL.*
4. **Trigger Redeploy**:
   - Go to the **Deployments** tab.
   - Click the `...` menu on the latest deployment -> **Redeploy**.
   - Make sure **"Redeploy with existing build cache"** is **UNCHECKED** so Vite rebuilds with the new environment variable.
