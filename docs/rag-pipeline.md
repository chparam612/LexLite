# RAG Pipeline Specification

## 1. Document Extraction & Structure Detection
- PDFs are parsed page-by-page using PyMuPDF.
- Low-confidence or image-heavy pages are flagged for OCR processing.
- Regular expressions and structural heuristics parse legal hierarchies:
  - Articles (e.g. `ARTICLE I - DEFINITIONS`)
  - Sections & Subsections (e.g. `Section 2.1`, `2.1.1`)
  - Definitions (e.g. `"Confidential Information" means...`)
  - Schedules, Annexures, Exhibits, and Appendices.
  - Provisos and Exceptions (`provided that`, `unless`, `except as provided`).

## 2. Chunking
- Chunks target 300–700 tokens with 10–20% overlap.
- Clause integrity is preserved; exceptions are kept attached to their governing clauses.
- Each chunk prepends contextual breadcrumbs:
  ```
  Document: {title} | Jurisdiction: {jurisdiction} | Path: {heading_path}
  ```
- Citations reference only the exact original text, never the prepended context.

## 3. Hybrid Retrieval & RRF
- Dense vector retrieval via cosine distance `<=>` in pgvector (top 30).
- Keyword retrieval via PostgreSQL Full-Text Search `to_tsvector` / `websearch_to_tsquery` (top 30).
- Reciprocal Rank Fusion:
  $$RRF(d) = \sum_{m \in M} \frac{1}{60 + \text{rank}_m(d)}$$
- Candidate deduplication and optional reranking (top 10).

## 4. Grounded Generation & Citation Verification
- Gemini model receives prompt with retrieved chunks delineated by untrusted data boundaries.
- Structured JSON output returns answer, itemized claims with supporting chunk IDs, citations, and confidence.
- Verifier confirms citation quote exact substring presence in the referenced chunk and assigns verification status: `supported`, `partially_supported`, `unsupported`, or `contradicted`.
