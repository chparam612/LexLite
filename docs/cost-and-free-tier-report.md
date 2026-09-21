# Cost Analysis & Free-Tier Operational Audit

**System:** LegalAssistant / LexLite  
**Architecture Principle:** Free-First / Zero Mandatory Ongoing Operational Cost  
**Audit Date:** 2026-09-21

---

## 1. Executive Cost Summary

The entire LegalAssistant platform has been engineered to operate with **$0.00 monthly cost** for development, evaluation, and hackathon demonstrations. Every architectural layer—from document ingestion and embeddings to vector indexing and LLM generation—uses either local offline compute or generous non-billing free-tier allocations.

| Component | Technology Used | Cost | Billing / Credit Card Required |
| :--- | :--- | :--- | :--- |
| **Document Ingestion** | PyMuPDF (`fitz`) | $0.00 | No (Open source local library) |
| **OCR Fallback** | Tesseract OCR | $0.00 | No (Open source local engine) |
| **Text Embeddings** | `sentence-transformers/all-MiniLM-L6-v2` | $0.00 | No (Runs locally in CPU memory) |
| **Vector Storage** | FAISS (`faiss-cpu`) | $0.00 | No (Local file system index) |
| **Keyword Search** | `rank-bm25` | $0.00 | No (Local in-memory index) |
| **Database** | SQLite 3 / Neon PostgreSQL Free Tier | $0.00 | No |
| **File Storage** | Local Disk Sandboxed Directory | $0.00 | No |
| **LLM Generation** | Google Gemini API (`gemini-1.5-flash`) | $0.00 | **No credit card required** |
| **Frontend & Web UI** | React / Vite / Tailwind | $0.00 | No |
| **Cloud Hosting** | Render (Backend) + Vercel (Frontend) | $0.00 | No (Free tiers) |
| **TOTAL PROJECT OPERATING COST** | | **$0.00 / mo** | |

---

## 2. Component-by-Component Service Analysis

### 1. Document Extraction
- **Service Name:** PyMuPDF (`fitz`)
- **Purpose:** Extracts digital text, structural layout, and page coordinates from PDF files.
- **Free Availability:** Fully free open-source library.
- **Possible Limits:** Host CPU and memory during large PDF uploads.
- **API Key Required:** No.
- **Billing Required:** No.
- **Current Project Usage:** Active in `backend/app/services/extraction_service.py`.
- **Alternative Free Option:** `pypdf` or `pdfplumber`.

### 2. OCR Engine
- **Service Name:** Tesseract OCR / `pytesseract`
- **Purpose:** Converts scanned raster images inside PDFs into searchable text.
- **Free Availability:** Fully open source.
- **Possible Limits:** Host CPU processing speed on high-DPI scans.
- **API Key Required:** No.
- **Billing Required:** No.
- **Current Project Usage:** Integrated as fallback when extracted digital text character count is below threshold.
- **Alternative Free Option:** EasyOCR.

### 3. Dense Embeddings
- **Service Name:** Sentence-Transformers (`all-MiniLM-L6-v2`)
- **Purpose:** Generates 384-dimensional dense semantic vectors for text chunks.
- **Free Availability:** Runs locally on CPU/GPU via Hugging Face PyTorch weights.
- **Possible Limits:** Local memory (~200MB RAM model footprint).
- **API Key Required:** No.
- **Billing Required:** No.
- **Current Project Usage:** Primary embedding provider in `backend/app/services/embedding_provider.py`.
- **Alternative Paid Option (Avoided):** OpenAI `text-embedding-3-small` (avoided to eliminate API charges).

### 4. Vector Store
- **Service Name:** FAISS (`faiss-cpu` by Meta Research)
- **Purpose:** Indexing and sub-millisecond similarity search over chunk vectors.
- **Free Availability:** Fully open source.
- **Possible Limits:** Scalability bounded by server RAM (thousands of documents per gigabyte).
- **API Key Required:** No.
- **Billing Required:** No.
- **Current Project Usage:** Primary vector store in `backend/app/services/retrieval_service.py`.
- **Alternative Paid Option (Avoided):** Pinecone, Weaviate Cloud, or Qdrant Cloud.

### 5. Primary Generative LLM
- **Service Name:** Google Gemini API (`gemini-1.5-flash`)
- **Purpose:** Grounded synthesis of retrieved clauses, citation formatting, and conversational Q&A.
- **Free Availability:** Google AI Studio Free Tier.
- **Possible Limits:**
  - **15 Requests Per Minute (RPM)**
  - **1,500 Requests Per Day (RPD)**
  - **1,000,000 Tokens Per Minute (TPM)**
- **API Key Required:** Yes (Generated in Google AI Studio).
- **Billing Required:** **No.** A credit card is NOT required to generate or use a Gemini Free Tier key.
- **Current Project Usage:** Integrated via official `google.generativeai` SDK in `backend/app/services/ai_provider.py`.
- **Alternative Local Option:** Ollama (e.g. `llama3:8b` or `mistral:7b`) for 100% air-gapped deployments.

---

## 3. Accidental Paid Dependencies Audit

A search across all dependencies (`requirements.txt`, `package.json`, environment variables) verified:
- **Zero Paid AI APIs:** No OpenAI, Anthropic, or Cohere paid endpoints are hardcoded or automatically invoked.
- **Zero Paid Vector DBs:** No calls to Pinecone or external managed indexes.
- **Zero Paid Cloud Storage:** No mandatory AWS S3 buckets or Google Cloud Storage billing accounts required.
- **Zero Paid Auth:** Auth is handled in-house with standard bcrypt + JWT tokens (no Auth0, Clerk, or Okta subscriptions).
- **Zero Silent Paid Fallback:** If the Gemini API key reaches its rate limit or is unset, the system explicitly returns a structured error rather than quietly routing queries to a metered paid provider.
