# Security & Compliance

## Security Principles

1. **Strict Tenant & Document Isolation (IDOR Defense)**:
   - User identity is always derived from the cryptographically verified Firebase JWT bearer token.
   - Any query fetching documents, chunks, conversations, or citations joins or filters on `owner_id = current_user.id`.
   - Never accept user IDs passed in request bodies or query parameters.

2. **Prompt Injection & Untrusted Data Sandboxing**:
   - Document chunks are injected into generation prompts enclosed within strict delimiter tags (e.g. `<document_evidence>...</document_evidence>`).
   - The system instructions explicitly direct the LLM to treat document text as untrusted raw evidence and ignore any system overrides or escape sequences contained within the documents.

3. **File Security & Upload Hardening**:
   - Magic byte verification (`%PDF-` header).
   - Filename sanitization against path traversal (e.g. `../../etc/passwd`).
   - File size limits (default 25 MB).
   - Files stored with random UUID keys and never executed.

4. **Zero Stack Trace & Secret Leakage**:
   - Global exception handlers catch unhandled errors and return generic, friendly JSON responses with a unique correlation ID.
   - Structured logger sanitizes sensitive tokens, API keys, and authorization headers.
