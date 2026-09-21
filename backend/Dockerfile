FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for PyMuPDF and psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x /app/entrypoint.sh && \
    useradd -m -u 1000 appuser && \
    mkdir -p /app/storage/uploads && \
    chown -R appuser:appuser /app

USER appuser

ENV PYTHONUNBUFFERED=1
ENV PORT=8000

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]

