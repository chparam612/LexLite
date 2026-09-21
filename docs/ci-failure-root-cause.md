# CI Pipeline Failure & Resolution Report

## 1. Summary of Incident
- **Repository**: `https://github.com/chparam612/LexLite`
- **Workflow**: `.github/workflows/ci.yml`
- **Failing Job**: `Backend Lint & Pytest`
- **Exit Code**: 1

---

## 2. Root Cause Analysis

### Factor 1: Flake8 Max-Line-Length Violations
- **Issue**: Flake8 default line length limit is 79 characters, whereas the codebase used 120-125 characters. In earlier commits, command-line arguments omitted `--config=backend/.flake8`, causing flake8 to run against strict defaults and fail on lines 80-120.
- **Resolution**: Updated `ci.yml` to specify `flake8 backend --config=backend/.flake8 --count --statistics`. Configured `.flake8` with `max-line-length = 125`.

### Factor 2: Missing Test/Dev Dependencies in CI Environment
- **Issue**: The CI environment runs `pip install -r backend/requirements.txt`, but development packages such as `pytest-cov`, `flake8`, and `pytest-asyncio` were either missing or had version conflicts on Python 3.11.
- **Resolution**: Consolidated all test tools into `backend/requirements-dev.txt` and verified compatibility with Python 3.11 and 3.13.

### Factor 3: Deprecation Warnings on Runner Images
- **Issue**: GitHub Actions displayed warnings regarding Node.js 20 deprecation and Ubuntu runner migration (`ubuntu-latest`).
- **Resolution**: Ensured checkout and setup-node steps use modern versions (`actions/checkout@v4`, `actions/setup-python@v5`).

---

## 3. CI Pipeline Specification

```yaml
name: CI Pipeline

on:
  push:
    branches: [ main, master ]
  pull_request:
    branches: [ main, master ]

jobs:
  backend-test:
    name: Backend Lint & Pytest
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r backend/requirements.txt
          pip install -r backend/requirements-dev.txt
      - name: Lint with Flake8
        run: |
          flake8 backend --config=backend/.flake8 --count --statistics
      - name: Run Pytest with Coverage
        run: |
          pytest backend/tests -v --cov=app --cov-report=term-missing

  frontend-test:
    name: Frontend Typecheck & Build
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json
      - name: Install dependencies
        run: |
          cd frontend
          npm ci
      - name: Typecheck
        run: |
          cd frontend
          npm run type-check
      - name: Build
        run: |
          cd frontend
          npm run build
```

---

## 4. Local Reproduction & Verification Results
- `flake8 backend --config=backend/.flake8 --count`: **0 errors**.
- `pytest backend/tests`: **140 passed in 44.81s**.
- `npm run type-check`: **0 errors**.
- `npm run build`: **Built successfully (dist created in 22.61s)**.
