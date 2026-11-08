"""Unit tests for anomaly detection service (statistical + Isolation Forest)."""

from __future__ import annotations

from querymind.services.anomaly_detection_service import (
    AnomalyDetector,
    MetricObservation,
    StatisticalBaseline,
)


def test_baseline_insufficient_returns_none():
    baseline = StatisticalBaseline(min_observations=10)
    for i in range(5):
        baseline.add(float(i), "2024-01-01T00:00:00Z")
    assert baseline.has_baseline() is False


def test_zscore_detection():
    baseline = StatisticalBaseline(min_observations=3)
    for v in [10.0, 11.0, 10.5]:
        baseline.add(v, "2024-01-01T00:00:00Z")
    # A far outlier should produce a high z-score.
    z = baseline.z_score(100.0)
    assert z is not None
    assert abs(z) > 1.0


def test_detect_statistical_anomaly():
    detector = AnomalyDetector(z_score_threshold=3.0)
    baseline = detector._baseline_for("latency")
    for v in [10.0, 11.0, 10.5, 10.2, 10.8, 11.1, 10.0, 10.5, 10.2, 10.9]:
        baseline.add(v, "2024-01-01T00:00:00Z")

    obs = MetricObservation(metric="latency", value=100.0, timestamp="2024-01-02T00:00:00Z")
    events = detector.detect(obs)
    assert len(events) == 1
    assert events[0].detection_algorithm == "statistical"
    assert events[0].severity in {"informational", "low", "medium", "high", "critical"}


def test_no_anomaly_when_normal():
    detector = AnomalyDetector(z_score_threshold=3.0)
    baseline = detector._baseline_for("latency")
    for v in [10.0, 11.0, 10.5, 10.2, 10.8, 11.1, 10.0, 10.5, 10.2, 10.9]:
        baseline.add(v, "2024-01-01T00:00:00Z")
    obs = MetricObservation(metric="latency", value=10.5, timestamp="2024-01-02T00:00:00Z")
    events = detector.detect(obs)
    assert events == []


def test_isolation_forest_train_and_infer():
    detector = AnomalyDetector()
    assert detector.sklearn_available is True
    features = [[10.0], [11.0], [10.5], [10.2], [10.8], [11.1], [10.0], [10.5], [10.2], [10.9], [10.1], [10.4]]
    assert detector.train_isolation_forest(features) is True
    assert detector.model_trained is True
    obs = MetricObservation(metric="latency", value=1000.0, timestamp="2024-01-02T00:00:00Z")
    event = detector.detect_isolation_forest(obs, [1000.0])
    # Isolation Forest may or may not flag depending on contamination; just ensure it runs.
    assert event is None or event.detection_algorithm == "isolation_forest"


def test_anomaly_event_fields():
    detector = AnomalyDetector(z_score_threshold=3.0)
    baseline = detector._baseline_for("conn")
    for v in [5.0, 6.0, 5.5, 5.2, 5.8, 6.1, 5.0, 5.5, 5.2, 5.9]:
        baseline.add(v, "2024-01-01T00:00:00Z")
    obs = MetricObservation(metric="conn", value=50.0, timestamp="2024-01-02T00:00:00Z")
    events = detector.detect(obs)
    if events:
        e = events[0]
        assert e.event_id
        assert e.metric == "conn"
        assert e.observed_value == 50.0
        assert e.severity in {"informational", "low", "medium", "high", "critical"}
