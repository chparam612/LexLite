# Unresolved Issues & Environmental Constraints

## 1. External Infrastructure Dependencies

### A. Render Free Tier Spin-Down (Cold Starts)
- **Status**: External platform constraint (Render Free Web Service).
- **Behavior**: Services on the free plan spin down after 15 minutes of zero traffic. The initial request can take 30 to 50 seconds to complete while the container boots, loads PyTorch, and connects to the database.
- **Mitigation Implemented**: Frontend displays a friendly warming-up banner informing the user when a cold start is detected rather than timing out abruptly.
- **Recommended User Action**: Consider upgrading Render instance to a Starter ($7/mo) plan to eliminate cold starts for production demos.

### B. Third-Party Provider API Keys
- **Status**: Requires user credentials.
- **Behavior**:
  - `GROQ_API_KEY`: Required if setting `AI_PROVIDER=groq`.
  - `GEMINI_API_KEY`: Required if setting `AI_PROVIDER=gemini`.
- **Mitigation Implemented**: If neither key is provided, the platform automatically degrades to the built-in local deterministic synthesis engine with full citation and quote extraction ($0 cost, 0 external dependencies).

### C. Vercel Redeployment with Environment Variable
- **Status**: Requires user action in Vercel UI.
- **Behavior**: If `VITE_API_BASE_URL` was modified or previously missing on Vercel, a new deployment must be triggered for Vite to compile the variable into client JS.
