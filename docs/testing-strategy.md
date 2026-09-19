# Testing Strategy & Test Matrix

## Overview
This document defines the comprehensive testing strategy for the LEGAL AI — ASSISTANCE & ACCESS platform. Testing is required across foundation, authentication, file validation, document extraction, legal structure parsing, embeddings, retrieval, generation, citation verification, APIs, security, processing jobs, and UI.

---

## Testing Layers

1. **Unit Tests**:
   - Validation logic (file size, MIME types, magic numbers, checksums).
   - Text parsing & legal structural regex / state machines (Articles, Sections, Clauses, Definitions).
   - Reciprocal Rank Fusion calculations.
   - Pydantic schema validation.
   - Claim extraction and verification string matching.

2. **Integration Tests**:
   - Database model persistence & relationships (SQLAlchemy).
   - FastAPI endpoint integration via `httpx.AsyncClient` / `TestClient`.
   - Health and Readiness checks.
   - Storage service operations (Local / Cloud Storage adapters).

3. **Security & Authorization Tests**:
   - IDOR prevention: User A attempting to fetch/delete User B's documents, conversations, or citations.
   - Path traversal prevention.
   - Prompt injection resilience.
   - Missing / expired / forged JWT token rejection.

4. **Frontend Tests**:
   - Type validation via TypeScript compiler (`tsc --noEmit`).
   - Component rendering, form validation, and routing.
   - Production bundle compilation via Vite.

---

## Test Cases Matrix

| Test ID | Category | Description | Target Component |
|---|---|---|---|
| TEST-F001 | Foundation | Backend health endpoint returns HTTP 200 | `api/v1/health.py` |
| TEST-F002 | Foundation | Readiness endpoint correctly reports DB availability | `api/v1/health.py` |
| TEST-F003 | Foundation | Application starts with valid environment variables | `core/config.py` |
| TEST-F004 | Foundation | Application fails safely when required config is missing | `core/config.py` |
| TEST-F005 | Foundation | Database connection can be established | `db/session.py` |
| TEST-F006 | Foundation | Database migration runs successfully on a clean database | Alembic |
| TEST-F007 | Foundation | Database migration can be rolled back where supported | Alembic |
| TEST-F008 | Foundation | Frontend builds successfully | Vite build |
| TEST-F009 | Foundation | Frontend TypeScript type-check passes | `tsc` |
| TEST-F010 | Foundation | Backend linting and formatting checks pass | flake8/ruff |
| TEST-A001 | Auth | Valid Firebase token is accepted | `core/security.py` |
| TEST-A002 | Auth | Missing authentication token returns HTTP 401 | `api/deps.py` |
| TEST-A003 | Auth | Invalid token returns HTTP 401 | `core/security.py` |
| TEST-A004 | Auth | Expired token is rejected | `core/security.py` |
| TEST-A005 | Auth | User record is created after first valid authentication | `services/auth_service.py` |
| TEST-A006 | Auth | Existing user record is reused instead of duplicated | `services/auth_service.py` |
| TEST-A007 | Auth | Backend identity is derived from the verified token | `api/deps.py` |
| TEST-A008 | Auth | Frontend redirects unauthenticated users to login | React Router ProtectedRoute |
| TEST-A009 | Auth | Authenticated users can access protected routes | React Router ProtectedRoute |
| TEST-A010 | Auth | Logout clears the local authentication state | `AuthContext` |
| TEST-FV001| File Val | Valid PDF is accepted | `services/document_service.py` |
| TEST-FV002| File Val | Non-PDF file is rejected | `services/document_service.py` |
| TEST-FV003| File Val | Incorrect MIME type is rejected or safely inspected | `services/document_service.py` |
| TEST-FV004| File Val | Empty file is rejected | `services/document_service.py` |
| TEST-FV005| File Val | Corrupted PDF is handled gracefully | `services/extraction_service.py` |
| TEST-FV006| File Val | File exceeding size limit is rejected | `services/document_service.py` |
| TEST-FV007| File Val | Filename containing path traversal is sanitized | `utils/file_utils.py` |
| TEST-FV008| File Val | Filename containing special characters is handled safely | `utils/file_utils.py` |
| TEST-FV009| File Val | Duplicate file checksum is detected | `services/document_service.py` |
| TEST-FV010| File Val | Uploaded file is never executed as code | Storage & permissions |
| TEST-FV011| File Val | Unsupported file extension is rejected | `services/document_service.py` |
| TEST-FV012| File Val | Upload without authentication is rejected | `api/v1/documents.py` |
| TEST-SEC001| Security | User A cannot retrieve User B's document | `services/document_service.py` |
| TEST-SEC002| Security | User A cannot retrieve User B's conversation | `services/chat_service.py` |
| TEST-SEC003| Security | User A cannot access User B's citations | `services/citation_service.py` |
| TEST-SEC004| Security | User A cannot delete User B's document | `services/document_service.py` |
| TEST-SEC005| Security | Frontend-supplied user ID is ignored for authorization | `api/deps.py` |
| TEST-SEC007| Security | Path traversal attempts are blocked | `services/storage_service.py` |
| TEST-SEC009| Security | Prompt injection inside document text does not override system instructions | RAG generation system prompt |
| TEST-SEC011| Security | Secrets are not present in logs | `core/logging.py` |

---

## Test Execution Commands

```bash
# Run all backend tests with coverage
pytest backend/tests -v --cov=backend/app

# Run only security tests
pytest backend/tests/test_security.py -v

# Run foundation tests
pytest backend/tests/test_foundation.py -v

# Run frontend tests and type checks
cd frontend && npm run type-check && npm test
```
