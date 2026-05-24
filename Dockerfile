# ---- Build stage ----
FROM python:3.10-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ---- Runtime stage ----
FROM python:3.10-slim

LABEL maintainer="RAG System"
LABEL description="FastAPI RAG System Backend"

# Install runtime dependencies (libgomp for OpenMP used by some ML libs)
RUN apt-get update && \
    apt-get install -y --no-install-recommends libgomp1 curl && \
    rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r raguser && useradd -r -g raguser -d /app -s /sbin/nologin raguser

WORKDIR /app

# Copy installed Python packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY api/ api/
COPY ingestion/ ingestion/
COPY infrastructure/ infrastructure/

# Create logs directory
RUN mkdir -p logs && chown -R raguser:raguser /app

USER raguser

# Environment variables (can be overridden at runtime)
ENV API_HOST=0.0.0.0 \
    API_PORT=8000 \
    API_WORKERS=4 \
    API_RELOAD=false \
    PYTHONUNBUFFERED=1

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
