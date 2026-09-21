# Groq Integration & Multi-Provider Architecture Report

## 1. Motivation & Executive Summary
- The user expressed interest in switching or adding **Groq** as an alternative to Google Gemini.
- Rather than ripping out Gemini or rewriting the entire backend, an enterprise-grade **Provider Abstraction** (`AIProvider`) was implemented.
- The platform now supports **Google Gemini**, **Groq Cloud**, and an **Offline Local Synthesis Fallback** with identical interfaces, strict JSON output adherence, citations extraction, and rate-limit handling.

---

## 2. Groq Provider Implementation Details

### A. Endpoint & Protocol
- **Endpoint**: `https://api.groq.com/openai/v1/chat/completions`
- **Protocol**: OpenAI-compatible REST API via `httpx.Client` (eliminating extra external binary dependencies).
- **Default Model**: `llama-3.3-70b-versatile` (State-of-the-art 70B parameter open-weights model).
- **Fast / High-Throughput Alternative**: `llama-3.1-8b-instant`.

### B. Prompt Engineering & System Instructions
The Groq provider uses the identical legal system prompt and context formulation as Gemini:
1. Grounded synthesis: Only factual assertions backed by supplied context chunks are permitted.
2. Direct inline citations: Every claim links to `[doc:chunk_id]`.
3. Strict JSON structure:
   ```json
   {
     "answer": "Grounded legal analysis...",
     "citations": [
       {
         "citation_id": "cite-001",
         "chunk_id": "chunk-rent-01",
         "document_id": "doc-lease-01",
         "source_title": "Residential Lease Agreement",
         "source_quote": "Monthly rent is $2,500.00 USD...",
         "heading_path": "Rent and Payments",
         "page_number": 2,
         "relevance_score": 0.95
       }
     ],
     "confidence_score": 0.95,
     "grounding_status": "fully_grounded",
     "hallucination_warning": false
   }
   ```

### C. Error Handling & Resiliency
- **429 Rate Limit**: Caught and surfaced as rate limit exception or seamlessly degraded to local deterministic synthesis.
- **401 Authentication Failure**: Clearly alerts invalid `GROQ_API_KEY`.
- **404 Model Not Found**: Gracefully handles model deprecations.
- **Timeout**: 15-second connect/read timeout prevents hung requests.
- **Fallback**: If Groq is unavailable, RAG falls back to local synthesis so the user is never stranded with an unhandled 500 error.

---

## 3. Comparison: Groq vs. Gemini

| Attribute | Groq Cloud | Google Gemini |
| :--- | :--- | :--- |
| **Primary Model** | `llama-3.3-70b-versatile` | `gemini-1.5-flash` |
| **Inference Speed** | Ultra-Fast (~250-500 tokens/sec via LPU) | Fast (~80-120 tokens/sec) |
| **API Protocol** | OpenAI-compatible REST (`/chat/completions`) | Google GenAI SDK REST |
| **Free Tier Quota** | Generous request rate on free tier | Subject to Google Cloud project quotas |
| **JSON Mode** | Supported (`response_format: {"type": "json_object"}`) | Supported (`response_mime_type: "application/json"`) |
| **Cost** | Free tier / Pay-as-you-go | Free tier / Pay-as-you-go |
| **Configuration** | `AI_PROVIDER=groq`<br>`GROQ_API_KEY=gsk_...` | `AI_PROVIDER=gemini`<br>`GEMINI_API_KEY=AIzaSy...` |

---

## 4. How to Switch Providers in Production
To switch to Groq on Render:
1. Set `AI_PROVIDER=groq`
2. Set `GROQ_API_KEY=gsk_your_key_here`
3. Set `GROQ_MODEL=llama-3.3-70b-versatile`

To switch back to Gemini:
1. Set `AI_PROVIDER=gemini`
2. Set `GEMINI_API_KEY=your_gemini_key`
3. Set `GEMINI_MODEL=gemini-1.5-flash`

No code deployment or schema migration is required.
