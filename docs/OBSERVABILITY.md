# Observability — QueryMind MCP

## Logging

Structured JSON logging via `structlog` (`src/querymind/core/logging.py`).
Logs include level, ISO-8601 timestamp, and tracebacks.

## Correlation IDs

Audit records carry a `correlation_id` to trace a request across tools and
services.

## Health / readiness endpoints

The FastAPI backend exposes health endpoints (e.g. `/healthz`) used by
Docker health checks and load balancers.

## Metrics

No sensitive SQL parameters or credentials are collected in telemetry.
Metrics that may be emitted:
- Database connection monitoring
- MCP request counts/latency
- SQL execution duration
- RAG retrieval metrics
- Anomaly detection metrics

OpenTelemetry and Prometheus integration may be added where justified by the
architecture; they are not required in v1.

## What is not collected

- Passwords, tokens, API keys, raw credentials
- Sensitive SQL parameter values
- Unrestricted customer records
