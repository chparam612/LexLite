# Free-First AI Setup & Cost Control Guide (Section 27)

This document provides complete instructions for setting up and operating Legal AI under a **Free-First, Zero-Billing** architecture. The application uses a real Generative AI model without incurring charges, requiring credit card commitments, or silently upgrading to paid services.

---

## 1. How to Create a Google AI Studio API Key (Free Tier)

Google provides free access to Gemini models via **Google AI Studio** without requiring Google Cloud billing:

1. Navigate to [aistudio.google.com](https://aistudio.google.com).
2. Sign in with any standard Google account (personal or workspace).
3. Click **"Get API key"** in the top navigation bar.
4. Click **"Create API key in new project"** (or select an existing non-billing project).
5. Copy your generated API key (starts with `AIzaSy...`).

> [!IMPORTANT]
> Do NOT attach a billing account or credit card in Google Cloud Console. Google AI Studio provides a free quota tier that operates completely independently of Cloud Billing.

---

## 2. Adding `GEMINI_API_KEY` to Your Local `.env`

Copy `.env.example` to `.env` in your project root:

```bash
cp .env.example .env
```

Add your key to `.env`:

```env
GEMINI_API_KEY=AIzaSyYourKeyHere...
AI_PROVIDER=gemini
GEMINI_MODEL=gemini-1.5-flash
ALLOW_PAID_AI_FALLBACK=false
```

---

## 3. Selecting a Free-Tier-Compatible Model

The default model is `gemini-1.5-flash`:
- **Model Identifier**: `gemini-1.5-flash`
- **Free Quota**: Included in Google AI Studio free tier.
- **Context Window**: 1,000,000 tokens (we enforce a tight 8,000 token limit to prevent latency).
- **Output Token Cap**: 800 tokens (`MAX_OUTPUT_TOKENS=800`).

---

## 4. Understanding & Checking Free Quotas

Free tier limits on Google AI Studio for `gemini-1.5-flash`:

| Metric | Free Tier Quota Limit |
|---|---|
| **Requests Per Minute (RPM)** | 15 RPM |
| **Requests Per Day (RPD)** | 1,500 RPD |
| **Tokens Per Minute (TPM)** | 1,000,000 TPM |
| **Input Context Budget** | 8,000 tokens (application enforced) |
| **Max Output Tokens** | 800 tokens (application enforced) |

You can monitor your live usage and remaining daily requests at [aistudio.google.com](https://aistudio.google.com) under **"Plan & Billing"** or the API dashboard.

---

## 5. How to Avoid Enabling Paid Billing

1. **Keep `ALLOW_PAID_AI_FALLBACK=false`**: The application will NEVER automatically switch to a paid API model or attempt billable fallback calls.
2. **Never Attach Payment Methods**: When prompted in Google Cloud Console to "Upgrade" or "Enable Billing", decline or close the modal.
3. **Audit Outgoing Calls**: All outgoing calls are explicitly directed to standard free-tier endpoints (`models/gemini-1.5-flash`).

---

## 6. How to Configure Local Free Embeddings

To completely eliminate external embedding API calls and avoid consuming Gemini rate limits on ingestion, the platform defaults to **local CPU embeddings**:

```env
EMBEDDING_PROVIDER=local
LOCAL_EMBEDDING_MODEL=all-MiniLM-L6-v2
```

- **Local Inference**: Runs on CPU using `sentence-transformers` or our built-in unit-normalized deterministic vector inference.
- **Dimensions**: 384 dimensions (or 768).
- **Cost**: $0.00, zero internet required.

If you ever wish to use Gemini embeddings instead, set:
```env
EMBEDDING_PROVIDER=gemini
GEMINI_EMBEDDING_MODEL=models/text-embedding-004
```

---

## 7. Running Without Google Cloud Billing

The application has a complete zero-cloud local development mode:
- **Database**: SQLite (`sqlite:///./legal_ai_dev.db`)
- **Vector Search**: FAISS or local cosine memory index (`VECTOR_STORE=faiss`)
- **File Storage**: Local filesystem (`STORAGE_MODE=local`, `./storage/uploads`)
- **Extraction**: PyMuPDF (`fitz`) and local Tesseract OCR

No Google Cloud services (Cloud Storage, Cloud SQL, Secret Manager) are required for local development or judging demonstrations.

---

## 8. What Happens When Free Quota Is Exhausted

If the 15 RPM or 1,500 RPD quota is reached, Google returns an HTTP 429 (`RESOURCE_EXHAUSTED`).

**Guaranteed Behavior**:
1. The system catches the 429 response.
2. It logs a safe redacted diagnostic message (never exposing the API key).
3. It displays the mandatory notification:
   > **"AI usage limit reached. Please wait for the quota to reset or configure another permitted model."**
4. The user's input and session are preserved so they can retry without losing their prompt.
5. **No paid request is ever made automatically.**

---

## 9. How to Replace Gemini with a Local Model in the Future

To switch from Gemini to a self-hosted local LLM (such as Llama 3 or Mistral via Ollama / vLLM):

1. Set `AI_PROVIDER=local_llm` in `.env`.
2. The `LocalLLMProvider` interface ([ai_provider.py](file:///backend/app/services/ai_provider.py)) handles local inference without cloud dependencies.

---

## 10. Environment Variables Reference

| Variable | Default Value | Description |
|---|---|---|
| `AI_PROVIDER` | `gemini` | Active AI provider (`gemini`, `local_llm`, `mock`) |
| `GEMINI_API_KEY` | *(empty / user-supplied)* | Google AI Studio API key |
| `GEMINI_MODEL` | `gemini-1.5-flash` | Free-tier Gemini generative model |
| `EMBEDDING_PROVIDER` | `local` | `local` (CPU/SentenceTransformers) or `gemini` |
| `LOCAL_EMBEDDING_MODEL`| `all-MiniLM-L6-v2` | Model identifier for local embeddings |
| `VECTOR_STORE` | `faiss` | Vector index (`faiss` or `pgvector`) |
| `DATABASE_MODE` | `sqlite` | Database engine (`sqlite` or `postgres`) |
| `STORAGE_MODE` | `local` | File storage backend (`local` or `gcs`) |
| `ALLOW_PAID_AI_FALLBACK`| `false` | **MUST BE FALSE** — never auto-upgrade |
| `MAX_OUTPUT_TOKENS` | `800` | Limits generation length for cost control |
| `MAX_CONTEXT_TOKENS` | `8000` | Limits retrieval context tokens sent to model |
