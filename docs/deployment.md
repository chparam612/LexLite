# Deployment Guide

## Target Deployment: Google Cloud Run & Cloud SQL

### Architecture
- **Web & API Backend**: Containerized FastAPI service on Cloud Run.
- **Database**: Cloud SQL for PostgreSQL 16 with `pgvector` extension enabled.
- **Frontend**: Cloud Run or Firebase Hosting / Cloud Storage CDN.
- **Storage**: Google Cloud Storage bucket for encrypted PDF document persistence.
- **Secrets**: Google Cloud Secret Manager for Gemini API key, Firebase credentials, and DB passwords.

### Local Deployment
```bash
# Start PostgreSQL with pgvector
docker-compose up -d postgres

# Run backend
cd backend
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Run frontend
cd frontend
npm run dev
```

### Production Container Build
```bash
# Build backend
docker build -t gcr.io/$PROJECT_ID/legal-ai-backend:latest ./backend

# Build frontend
docker build -t gcr.io/$PROJECT_ID/legal-ai-frontend:latest ./frontend
```
