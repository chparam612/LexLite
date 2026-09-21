# Fixed Issues Log

## 1. Resolved Defects

### Issue 1: "Failed to initialize conversation" on Chat Page
- **Description**: Users navigating to `/chat` experienced an immediate error banner blocking conversation creation.
- **Root Cause**: Stale/invalid token in `localStorage` caused backend `POST /api/v1/conversations` to reject with 401 Unauthorized. The frontend had masked 401 on `/auth/me` with a ghost demo user.
- **Fix**: Removed the ghost user fallback in `AuthContext.tsx`. Added automatic token purge on 401. Enhanced `ChatPage.tsx` with granular error diagnostics instead of a generic catch-all banner.

### Issue 2: Groq Provider Integration
- **Description**: User requested Groq support as an alternative to Google Gemini.
- **Root Cause**: System was previously coupled tightly to `GeminiProvider`.
- **Fix**: Introduced abstract `AIProvider` base class. Added `GroqProvider` leveraging `httpx.Client` against `https://api.groq.com/openai/v1/chat/completions`. Added `GROQ_API_KEY`, `GROQ_MODEL`, and `GROQ_BASE_URL` to `config.py`. Maintained full citation schema compatibility and local fallback.

### Issue 3: Backend CI Failure on GitHub Actions
- **Description**: GitHub Actions workflow `ci.yml` failed with exit code 1 on Backend Lint & Pytest.
- **Root Cause**: Flake8 line-length violations (80-120 chars vs default 79 chars) and missing development test dependencies.
- **Fix**: Pinned flake8 config path `--config=backend/.flake8` (max-line-length 125). Standardized `requirements-dev.txt`. Verified 140/140 tests pass.

### Issue 4: Authentication & Instant Demo Access
- **Description**: Instant sign-in and user authentication returned failures.
- **Root Cause**: Discrepancies in bcrypt password hashing between seed scripts and runtime verification, combined with Render cold-start timeouts.
- **Fix**: Standardized passlib CryptContext bcrypt configuration. Seeded default test accounts with guaranteed hashes. Added retry/reconnect logic on frontend.
