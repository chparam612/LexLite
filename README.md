# LEGAL AI — ASSISTANCE & ACCESS

> **Legal Disclaimer:**
> "This platform provides general legal information and document analysis for educational purposes. It does not provide legal advice, establish an attorney-client relationship, or replace consultation with a qualified legal professional."

LEGAL AI is an enterprise-grade, secure, and verifiable legal document analysis platform powered by Retrieval-Augmented Generation (RAG). It enables users to upload legal agreements, extract page-aware hierarchical clauses, search semantically and by exact keywords, synthesize grounded answers with high-speed LLM inference, and inspect claim-level verified citations grounded directly in the document text.

---

## Live Deployments & Demo

| Service | Environment | URL |
| :--- | :--- | :--- |
| **Web Application (SPA)** | Production (Vercel) | [https://lex-lite.vercel.app](https://lex-lite.vercel.app) |
| **REST Backend API** | Production (Render) | [https://legal-ai-backend-crc0.onrender.com](https://legal-ai-backend-crc0.onrender.com) |
| **API Interactive Docs** | Swagger UI | [https://legal-ai-backend-crc0.onrender.com/docs](https://legal-ai-backend-crc0.onrender.com/docs) |
| **Health Check Probe** | Production Status | [https://legal-ai-backend-crc0.onrender.com/health](https://legal-ai-backend-crc0.onrender.com/health) |
| **Live Evaluation Suite** | Judging Dashboard | [https://lex-lite.vercel.app/evaluation](https://lex-lite.vercel.app/evaluation) |

> **1-Click Demo Access**: On the live login page, click **"Instant Sign In as Demo Attorney"** to log in immediately as Sarah Jenkins, Esq., with pre-ingested agreements, verified chunk hierarchies, and pre-indexed 768-dimensional embeddings.

---

## Key Features

- **Multi-Tenant Document Management**: Secure PDF upload, SHA-256 checksum deduplication, and isolated tenant document ownership.
- **Legal-Aware Structural Parsing**: Automatic identification of Articles, Chapters, Sections, Subsections, Clauses, Definitions, Provisos, Exceptions, and Schedules.
- **Hybrid Retrieval (Dense + Sparse)**: Semantic similarity retrieval via PostgreSQL `pgvector` alongside Full-Text Search (BM25) fused via Reciprocal Rank Fusion (RRF).
- **Multi-Provider Resilient AI Architecture**:
  - **Primary Generation**: Groq (`llama-3.3-70b-versatile`) for low-latency legal synthesis.
  - **Fallback Generation**: Google Gemini (`gemini-flash-latest`) and local deterministic CPU inference (`LocalLLMProvider`).
  - **Embeddings**: 768-dimensional vectors (`models/text-embedding-004` / local sentence transformers).
- **Claim-Level Citation Verification**: Every answer claim is verified against actual document chunks and page numbers with entailment scoring to prevent hallucinations.
- **Performance & Trace Transparency**: Real-time breakdown of retrieval latency, generation latency, candidate chunk count, and verification status.
- **Defense in Depth**: React `ErrorBoundary` wrappers prevent unhandled runtime errors from breaking user workflows; XML context sandboxing prevents prompt injection.

---

## Technology Stack

- **Frontend**: React 18, Vite, TypeScript, Tailwind CSS, Lucide Icons, Axios.
- **Backend**: Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy 2.0, Alembic, PyMuPDF.
- **Database**: PostgreSQL 16 with `pgvector` extension and Full-Text Search (SQLite adapter for local/offline testing).
- **AI & RAG**:
  - Primary Provider: Groq (`llama-3.3-70b-versatile`)
  - Secondary / Fallback: Google Gemini (`gemini-flash-latest`) & Local LLM Provider
  - Embeddings: 768-dimensional embeddings (`models/text-embedding-004` / local sentence transformers)
- **Deployment & Hosting**:
  - Frontend SPA: Vercel
  - Backend API: Render Web Service (Docker container / Python 3.11)
  - Managed Database: Render PostgreSQL with `vector` extension enabled

---

## Project Structure

```
legal-ai-platform/
├── backend/            # FastAPI REST backend and worker pipelines
│   ├── app/            # Application core, api routers, models, schemas, services
│   └── tests/          # Comprehensive pytest test suite (140 tests)
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
- (Optional) PostgreSQL 16 with `pgvector` extension

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
# Run backend test suite (140 tests passing)
cd backend
pytest -v

# Run backend linting (0 flake8 errors against project configuration)
flake8 backend --config=backend/.flake8

# Run frontend type-check & production build (0 errors)
cd ../frontend
npm run type-check
npm run build
```

- **Backend Automated Tests**: 140 unit and integration tests passing (`140 passed`).
- **Code Style & Linting**: 0 flake8 errors (`flake8 backend --config=backend/.flake8`).
- **Frontend Type Safety**: Strict TypeScript type-checking passing with 0 errors (`tsc --noEmit`).
- **Live Component Evaluation**: 10 out of 10 applicable component judging tests pass with 100% pass rate (`POST /api/v1/evaluation/run`).

---

## Roadmap & Phase Status

| Phase | Description | Status |
| :--- | :--- | :---: |
| **Phase 1** | Foundation, Scaffolding, Core Config & Probes | **Complete** (8 tests) |
| **Phase 2** | Database Layer (17 Models, Dual-Mode pgvector/SQLite, Migrations) | **Complete** (6 tests) |
| **Phase 3** | Authentication & Authorization (Firebase / JWT, RBAC, Guards) | **Complete** (7 tests) |
| **Phase 4** | Document Upload & Storage (GCS / Local, Deduplication, UI Library) | **Complete** (12 tests) |
| **Phase 5** | Document Processing & Legal-Aware Chunking (PyMuPDF, OCR, Hierarchies) | **Complete** (6 tests) |
| **Phase 6** | Embeddings & Vector Storage (768-dim, Retry Backoff) | **Complete** (10 tests) |
| **Phase 7** | Basic RAG & Grounded Generation (XML Sandboxing, Chat UI) | **Complete** (10 tests) |
| **Phase 8** | Advanced Retrieval & RRF Reranking (Dense + Lexical BM25, Context Expansion) | **Complete** (10 tests) |
| **Phase 9** | Citation Verification & Security Audit (Entailment Scoring, OWASP Audit) | **Complete** (20 tests) |
| **Phase 10** | RAG Evaluation Suite, Groq Provider Tests, E2E Journey Tests | **Complete** (51 tests) |

**Total Automated Tests**: **140 Passing Tests**

---

## License

Apache 2.0. See [LICENSE](LICENSE) for details.