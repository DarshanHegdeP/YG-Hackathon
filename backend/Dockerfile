# ============================================================
# Backend Dockerfile — FastAPI + Uvicorn (for Render)
# ============================================================
FROM python:3.11-slim AS base

# Prevent Python from writing .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# ---- Dependencies ----
FROM base AS deps
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ---- Application ----
FROM deps AS app

# Copy the entire backend application
COPY . .

# Create a directory for local file uploads (SQLite DB + evidence files)
RUN mkdir -p /app/storage_uploads

# Expose the port Render uses (default 10000, overridable via PORT env)
ENV PORT=10000
EXPOSE ${PORT}

# Run the seed script (creates tables + demo data if DB is empty),
# then start the uvicorn server.
# Render sets the PORT env var automatically.
CMD python -c "from app.db.seed import seed_database; seed_database()" && \
    uvicorn app.main:app \
        --host 0.0.0.0 \
        --port ${PORT} \
        --workers 1 \
        --log-level info
