#!/bin/sh
set -e

APP_PORT="${PORT:-8000}"

echo "=================================================="
echo " Starting LEGAL AI Backend Service"
echo " Environment: ${APPLICATION_ENV:-production}"
echo " Port: ${APP_PORT}"
echo "=================================================="

# Apply database migrations
echo "Checking database schema migrations..."
alembic upgrade head || {
    echo "Warning: Alembic migration encountered an issue or schema is up-to-date. Continuing startup..."
}

echo "Launching application server on port ${APP_PORT}..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${APP_PORT}"
