# syntax=docker/dockerfile:1
# QueryMind MCP — production Dockerfile (multi-stage)
# Build stage: install dependencies and compile where needed.
FROM python:3.13-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# System deps for building psycopg2/bcrypt wheels (minimal).
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
RUN pip install --upgrade pip && pip install -e ".[test,dev]"

# Runtime stage: minimal image, non-root user.
FROM python:3.13-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    QUERYMIND_ENV=production

WORKDIR /app

# Only libpq for psycopg2 at runtime.
RUN apt-get update && apt-get install -y --no-install-recommends libpq5 curl \
    && rm -rf /var/lib/apt/lists/ \
    && groupadd -r querymind && useradd -r -g querymind -d /app -s /sbin/nologin querymind

COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY ./src ./src
COPY ./alembic ./alembic
COPY ./pyproject.toml ./

RUN chown -R querymind:querymind /app

USER querymind

# Health endpoint: FastAPI /healthz or MCP stdio check.
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://127.0.0.1:8000/healthz || exit 1

EXPOSE 8000

CMD ["python", "-m", "querymind.mcp.transports"]
