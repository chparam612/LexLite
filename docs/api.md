# API Documentation

Base URL: `/api/v1`

## Health Endpoints
- `GET /health` - Returns service liveness (`{"status": "healthy"}`)
- `GET /ready` - Returns database and storage readiness status

## Authentication
- `GET /api/v1/auth/me` - Returns current user profile derived from verified Firebase token

## Documents
- `POST /api/v1/documents/upload` - Upload a legal PDF file (multipart/form-data)
- `GET /api/v1/documents` - List documents owned by the authenticated user
- `GET /api/v1/documents/{document_id}` - Get metadata and processing status
- `DELETE /api/v1/documents/{document_id}` - Delete document and all associated chunks/citations
- `POST /api/v1/documents/{document_id}/retry` - Retry a failed processing job
- `GET /api/v1/documents/{document_id}/status` - Check extraction & embedding progress

## Conversations & Chat
- `POST /api/v1/conversations` - Create a new conversation associated with documents
- `GET /api/v1/conversations` - List conversations for user
- `GET /api/v1/conversations/{conversation_id}` - Retrieve conversation messages and citations
- `DELETE /api/v1/conversations/{conversation_id}` - Delete conversation
- `POST /api/v1/conversations/{conversation_id}/messages` - Send a question and receive a grounded answer with citations

## Search
- `POST /api/v1/search` - Execute hybrid or keyword search across authorized documents
