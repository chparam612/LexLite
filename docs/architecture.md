# System Architecture

## Architecture Overview

```mermaid
graph TD
    Client[React Frontend] -->|HTTPS / Bearer JWT| Gateway[FastAPI Backend Gateway]
    Gateway --> Auth[Firebase Token Verification]
    Gateway --> RateLimit[Rate Limiting Middleware]
    Gateway --> Router[API v1 Routers]
    
    Router --> DocService[Document Ingestion Service]
    Router --> SearchService[Hybrid Search Service]
    Router --> ChatService[Chat & RAG Service]

    DocService --> Storage[(GCS / Local Storage)]
    DocService --> PyMuPDF[Page-by-Page PDF Extractor]
    DocService --> OCR[OCR Adapter]
    DocService --> Parser[Legal Structure Parser]
    DocService --> Chunker[Contextual Legal Chunker]
    Chunker --> Embeddings[Gemini Embeddings Service]
    Embeddings --> DB[(PostgreSQL + pgvector)]

    ChatService --> QueryNorm[Query Normalizer & Intent Classifier]
    QueryNorm --> DenseRetrieval[Dense Vector Retrieval]
    QueryNorm --> KeywordRetrieval[PostgreSQL Full-Text Search]
    DenseRetrieval --> RRF[Reciprocal Rank Fusion]
    KeywordRetrieval --> RRF
    RRF --> Rerank[Reranker Service]
    Rerank --> ContextAssembly[Context Window Assembly]
    ContextAssembly --> Gemini[Gemini LLM Generation]
    Gemini --> CitationVerifier[Claim-Level Citation Verifier]
    CitationVerifier --> Client
```

## Component Boundaries

1. **Presentation Layer (`frontend/`)**: Single-page application written in React with TypeScript and Tailwind CSS. Communicates solely via REST endpoints with JWT bearer authentication.
2. **API & Core Layer (`backend/app/core/`, `backend/app/api/`)**: Enforces authentication, authorization (owner isolation), schema validation via Pydantic, correlation tracking, and uniform error formatting.
3. **Domain & Retrieval Services (`backend/app/services/`)**: Independent, modular services handling document extraction, chunking, embeddings, hybrid retrieval, and LLM orchestration.
4. **Data Layer (`backend/app/db/`, `PostgreSQL`)**: Relational tables with pgvector extension for similarity search and GIN indexes for full-text search.
