# Unresolved Issues & External Dependencies Log

**Date**: September 21, 2026  
**Project**: Legal AI Assistant (LexLite)

---

## Current Status Overview

All application-level software defects, authentication failures, database schema incompatibilities, and frontend build issues have been **100% resolved and verified** in code.

The items below document external dependencies that require user credential ownership or manual external dashboard actions.

---

## 1. External Infrastructure Dependencies

### DEP-001: Google Cloud Run Billing Account Activation
- **Status**: **BLOCKED (Requires User Action)**
- **Description**: Deployment to Google Cloud Run requires an active Google Cloud Billing Account linked to the GCP project.
- **Impact**: Automatic deployment to Cloud Run via CLI or Cloud Build cannot proceed without active billing.
- **Mitigation**: The application is already containerized and successfully deployed to **Render** (`https://legal-ai-backend.onrender.com`) for the backend and **Vercel** (`https://lex-lite.vercel.app`) for the frontend. If Google Cloud Run is specifically needed, the user must attach a valid billing account in Google Cloud Console.

### DEP-002: Remote Repository Synchronization (Git Push)
- **Status**: **PENDING USER ACTION**
- **Description**: The verified code fixes reside on the local branch `main`.
- **Impact**: Render and Vercel build pipelines are triggered on git pushes to `chparam612/LexLite`.
- **Required Action**: Run `git push origin main` in the terminal to trigger automatic production redeployments.

---

## 2. No Codebase Blockers Remaining

- **Backend Unit Tests**: Passing.
- **Frontend TypeScript / Vite Build**: Passing (0 errors).
- **Authentication System**: Fully self-contained with zero external third-party auth dependencies required.
- **AI / Grounding Pipeline**: Operates with Google Gemini and seamlessly degrades to local grounded clause extraction if Gemini Free Tier limits are exhausted.
