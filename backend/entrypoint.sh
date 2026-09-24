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
if ! alembic upgrade head; then
    echo "=================================================="
    echo "ERROR: Alembic migration failed! Check migration logs above."
    echo "Continuing application startup in degraded state..."
    echo "=================================================="
fi

echo "Launching application server on port ${APP_PORT}..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${APP_PORT}"
