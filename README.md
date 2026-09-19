# LEGAL AI — ASSISTANCE & ACCESS

> **Legal Disclaimer:**
> "This platform provides general legal information and document analysis for educational purposes. It does not provide legal advice, establish an attorney-client relationship, or replace consultation with a qualified legal professional."

LEGAL AI is an enterprise-grade, secure, and verifiable legal document analysis platform powered by Retrieval-Augmented Generation (RAG). It enables users to upload legal agreements, extract page-aware hierarchical clauses, search semantically and by exact keywords, query documents using Google Gemini, and inspect claim-level verified citations grounded directly in the document text.

---

## Features

- **Multi-tenant Document Management**: Secure PDF upload, checksum deduplication, and isolated document ownership.
- **Legal-Aware Structural Parsing**: Automatic identification of Articles, Chapters, Sections, Subsections, Clauses, Definitions, Provisos, Exceptions, and Schedules.
- **Hybrid Retrieval (Dense + Keyword)**: Semantic similarity retrieval via `pgvector` alongside PostgreSQL Full-Text Search fused via Reciprocal Rank Fusion (RRF).
- **Claim-Level Citation Verification**: Every answer claim is verified against actual document chunks and page numbers to prevent hallucination.
- **Enterprise Security**: Untrusted document content sandboxing, strict prompt injection defense, CORS isolation, and Firebase token verification.
- **Modern Responsive Interface**: React 18, Vite, TypeScript, Tailwind CSS, and Lucide icons.

---

## Technology Stack

- **Frontend**: React, Vite, TypeScript, Tailwind CSS, Lucide Icons, TanStack Query, React Router DOM.
- **Backend**: Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy 2.0, Alembic, PyMuPDF.
- **Database**: PostgreSQL 16 with `pgvector` and Full-Text Search (with SQLite adapter for testing/local dev).
- **AI & RAG**: Google Gemini (`gemini-1.5-flash`, `text-embedding-004`).
- **Auth**: Firebase Authentication with backend token verification.

---

## Project Structure

```
legal-ai-platform/
├── backend/            # FastAPI REST backend and worker pipelines
│   ├── app/            # Application core, api routers, models, schemas, services
│   └── tests/          # Comprehensive pytest test suite
├── frontend/           # React + Vite + TypeScript web application
├── database/           # PostgreSQL init scripts and seeds
├── docs/               # Architecture, API, security, RAG, and testing documentation
├── infrastructure/     # Docker, GCP Cloud Run, and CI/CD manifests
├── docker-compose.yml  # Local multi-container development environment
└── Makefile            # Common development automation commands
```

---

## Quick Start (Local Development)

### 1. Prerequisites
- Python 3.11+
- Node.js 18+ and npm
- (Optional) Docker and Docker Compose for PostgreSQL + pgvector

### 2. Environment Setup
```bash
# Clone and prepare environment variables
cp .env.example .env
```

### 3. Backend Setup
```bash
cd backend
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
pytest -v
uvicorn app.main:app --reload --port 8000
```

### 4. Frontend Setup
```bash
cd ../frontend
npm install
npm run dev
```

Visit the app at `http://localhost:5173`.
Backend API interactive docs are at `http://localhost:8000/docs`.

---

## Testing & Quality Assurance

```bash
# Run backend tests with coverage (92 tests, 86% coverage)
cd backend
pytest -v --cov=app

# Run backend linting (0 flake8 errors)
flake8 backend --config=backend/.flake8

# Run frontend type-check & production build (0 errors)
cd ../frontend
npm run type-check
npm run build
```

---

## Roadmap & Phase Status

| Phase | Description | Status |
| :--- | :--- | :---: |
| **Phase 1** | Foundation, Scaffolding, Core Config & Probes | **Complete** (8 tests) |
| **Phase 2** | Database Layer (17 Models, Dual-Mode pgvector/SQLite, Migrations) | **Complete** (6 tests) |
| **Phase 3** | Authentication & Authorization (Firebase / JWT, RBAC, Guards) | **Complete** (7 tests) |
| **Phase 4** | Document Upload & Storage (GCS / Local, Deduplication, UI Library) | **Complete** (12 tests) |
| **Phase 5** | Document Processing & Legal-Aware Chunking (PyMuPDF, OCR, Hierarchies) | **Complete** (6 tests) |
| **Phase 6** | Embeddings & Vector Storage (Gemini 768-dim, Retry Backoff) | **Complete** (10 tests) |
| **Phase 7** | Basic RAG & Grounded Generation (XML Sandboxing, Chat UI) | **Complete** (10 tests) |
| **Phase 8** | Advanced Retrieval & RRF Reranking (Dense + Lexical BM25, Context Expansion) | **Complete** (10 tests) |
| **Phase 9** | Citation Verification & Security Audit (Entailment Scoring, OWASP Audit) | **Complete** (20 tests) |
| **Phase 10** | RAG Evaluation Suite, E2E Journey Tests, Settings & Final Polish | **Complete** (3 tests) |


## License

Apache 2.0. See [LICENSE](LICENSE) for details.