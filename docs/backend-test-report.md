# Backend Pytest Execution & Coverage Report

**Date**: September 21, 2026  
**Execution Environment**: CI Emulation & Local Environment  
**Pytest Version**: 9.1.1  
**Python Version**: 3.11 / 3.13  
**Status**: 100% PASSED (130 / 130 Tests)

---

## 1. Test Suite Execution Summary

| Test Module | Domain | Tests | Passed | Failed | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `tests/test_advanced_retrieval.py` | Hybrid RRF Search, Reciprocal Fusion | 10 | 10 | 0 | **PASS** |
| `tests/test_ai_free_first.py` | Section 27 Free-First AI Architecture | 20 | 20 | 0 | **PASS** |
| `tests/test_audit_endpoints.py` | Governance, Cost & Model Diagnostics | 5 | 5 | 0 | **PASS** |
| `tests/test_auth.py` | Registration, Password Hashing, JWT & Identity | 12 | 12 | 0 | **PASS** |
| `tests/test_database.py` | SQLAlchemy Session Management & SQLite | 6 | 6 | 0 | **PASS** |
| `tests/test_demo_acceptance.py` | Section 26 DEMO-001 through DEMO-008 | 8 | 8 | 0 | **PASS** |
| `tests/test_e2e_journey.py` | Complete User Journey & Benchmark Evaluation | 3 | 3 | 0 | **PASS** |
| `tests/test_embedding.py` | Dense Vectors, FAISS Store, Normalization | 10 | 10 | 0 | **PASS** |
| `tests/test_foundation.py` | System Probes, CORS, Exception Middleware | 8 | 8 | 0 | **PASS** |
| `tests/test_processing.py` | PDF Parsing, Section Boundary Detection | 6 | 6 | 0 | **PASS** |
| `tests/test_rag.py` | Context Window Assembly & Claim Attribution | 10 | 10 | 0 | **PASS** |
| `tests/test_security_audit.py` | Token Tampering, SQL Injection, Auth Isolation | 10 | 10 | 0 | **PASS** |
| `tests/test_upload.py` | Safe File Handling, Mime Validation, Storage | 12 | 12 | 0 | **PASS** |
| `tests/test_verification.py` | Citation Quote Grounding & Page Mapping | 10 | 10 | 0 | **PASS** |
| **TOTAL** | **Full Backend Surface** | **130** | **130** | **0** | **100% PASS** |

---

## 2. Authentication Test Verification Matrix (`tests/test_auth.py`)

All 12 authentication integration tests executed and passed:

1. `test_a001_valid_token_accepted`: Verified tokens allow access to `/api/v1/auth/me`.
2. `test_a002_missing_token_returns_401`: Missing Authorization header returns HTTP 401.
3. `test_a003_invalid_token_returns_401`: Malformed or garbage tokens return HTTP 401.
4. `test_a004_expired_token_rejected`: Expired tokens return HTTP 401.
5. `test_a005_user_record_created_on_first_auth`: New user is automatically persisted in DB.
6. `test_a006_existing_user_record_reused`: Existing user records are reused without duplicates.
7. `test_a007_backend_identity_derived_from_token`: User identity derived strictly from verified token.
8. `test_a008_register_user_success`: Registering new credentials returns HTTP 201 + valid JWT.
9. `test_a009_register_duplicate_email_fails`: Registering an existing email returns HTTP 400.
10. `test_a010_login_user_success`: Valid login credentials return HTTP 200 + valid JWT.
11. `test_a011_login_invalid_password_fails`: Incorrect passwords return HTTP 401.
12. `test_a012_demo_login_success`: 1-click demo attorney login returns HTTP 200 + valid JWT.

---

## 3. Code Coverage Highlights

- **Overall Statement Coverage**: **80%** (2,191 of 2,753 statements executed).
- **Core Endpoints (`app/api/v1/auth.py`, `app/api/v1/chat.py`, `app/api/v1/system.py`)**: **100% Coverage**.
- **Data Models (`app/models/*`)**: **100% Coverage**.
- **Core Logging & Base**: **100% Coverage**.
