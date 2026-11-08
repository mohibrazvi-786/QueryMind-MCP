# Anomaly Detection — QueryMind MCP

Database anomaly detection combining statistical baselines and machine learning.

## Metric ingestion (`services/anomaly_detection_service.py`)
`MetricObservation` captures metric name, value, UTC timestamp, database,
source, and dimensions. Observations are added via `AnomalyDetector.observe()`.

## Statistical baseline engine (`StatisticalBaseline`)
Per-metric rolling baseline with:
- Rolling average / standard deviation.
- Z-score anomaly scoring.
- Exponential weighted moving average (EWMA).
- Configurable `z_score_threshold` (default 3.0).
- Minimum observation requirement before baselining.
- Graceful handling of missing values, zero variance, insufficient data.

## ML anomaly detection (`Isolation Forest`)
`AnomalyDetector.train_isolation_forest(features)` trains a scikit-learn
`IsolationForest` (configurable contamination, reproducible random state,
feature scaling). `detect_isolation_forest(...)` runs inference.

Statistical alerts remain available even if ML inference or scikit-learn is
unavailable.

## Anomaly event (`AnomalyEvent`)
Structured event containing event ID, database, metric, observed value,
expected baseline, anomaly score, severity (informational/low/medium/high/
critical), detection algorithm, timestamp, explanation, supporting
observations, and model version. Severity follows documented Z-score rules,
not LLM judgment.

## Evaluation
Reproducible synthetic workloads (normal sequences + injected spikes) used to
compute precision/recall/F1. Results recorded in `tests/evaluation/`.

## Status

Implemented and unit-tested (statistical detection + Isolation Forest with
scikit-learn). Live metric collection against a real PostgreSQL target
requires provisioning (see `docs/POSTGRESQL_INTEGRATION_CHECKLIST.md`).
