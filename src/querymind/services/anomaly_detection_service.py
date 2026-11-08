"""Machine learning anomaly detection for database metrics.

Combines interpretable statistical baselines (rolling mean/stddev, Z-score,
EWMA) with an Isolation Forest experiment. Statistical alerts remain
available even if ML inference fails.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import math
import statistics

try:  # scikit-learn is optional; degrade gracefully when unavailable
    from sklearn.ensemble import IsolationForest
    from sklearn.preprocessing import StandardScaler

    _HAS_SKLEARN = True
except Exception:  # noqa: BLE001
    IsolationForest = None  # type: ignore
    StandardScaler = None  # type: ignore
    _HAS_SKLEARN = False


@dataclass
class MetricObservation:
    """A single metric observation."""

    metric: str
    value: float
    timestamp: str  # ISO 8601 UTC
    database: str = "default"
    source: str = "collector"
    dimensions: dict = field(default_factory=dict)


@dataclass
class AnomalyEvent:
    """A detected anomaly event."""

    event_id: str
    database: str
    metric: str
    observed_value: float
    expected_baseline: float
    anomaly_score: float
    severity: str  # informational | low | medium | high | critical
    detection_algorithm: str  # statistical | isolation_forest
    timestamp: str
    explanation: str
    supporting_observations: list = field(default_factory=list)
    model_version: Optional[str] = None


class StatisticalBaseline:
    """Rolling statistical baseline for a single metric."""

    def __init__(self, *, window_size: int = 50, min_observations: int = 10) -> None:
        self.window_size = window_size
        self.min_observations = min_observations
        self._values: list[float] = []
        self._timestamps: list[str] = []

    def add(self, value: float, timestamp: str) -> None:
        self._values.append(value)
        self._timestamps.append(timestamp)
        if len(self._values) > self.window_size:
            self._values = self._values[-self.window_size:]
            self._timestamps = self._timestamps[-self.window_size:]

    def z_score(self, value: float) -> Optional[float]:
        if len(self._values) < self.min_observations:
            return None
        mean = statistics.mean(self._values)
        stdev = statistics.pstdev(self._values)
        if stdev == 0:
            return 0.0
        return (value - mean) / stdev

    def ewma(self, value: float, alpha: float = 0.3) -> Optional[float]:
        if not self._values:
            return value
        prev = self._values[-1]
        return alpha * value + (1 - alpha) * prev

    def expected(self) -> Optional[float]:
        if not self._values:
            return None
        return statistics.mean(self._values)

    def stddev(self) -> Optional[float]:
        if len(self._values) < 2:
            return None
        return statistics.pstdev(self._values)

    def has_baseline(self) -> bool:
        return len(self._values) >= self.min_observations


class AnomalyDetector:
    """Detects anomalies using statistical baselines and Isolation Forest."""

    def __init__(
        self,
        *,
        z_score_threshold: float = 3.0,
        contamination: float = 0.1,
        random_state: int = 42,
    ) -> None:
        self.z_score_threshold = z_score_threshold
        self.contamination = contamination
        self.random_state = random_state
        self._baselines: dict[str, StatisticalBaseline] = {}
        self._model = None
        self._model_version = "isolation_forest_v1"
        self._trained = False

    def _baseline_for(self, metric: str) -> StatisticalBaseline:
        if metric not in self._baselines:
            self._baselines[metric] = StatisticalBaseline()
        return self._baselines[metric]

    def observe(self, observation: MetricObservation) -> None:
        self._baseline_for(observation.metric).add(observation.value, observation.timestamp)

    def detect_statistical(self, observation: MetricObservation) -> Optional[AnomalyEvent]:
        """Z-score based detection. Returns None when baseline is insufficient."""
        baseline = self._baseline_for(observation.metric)
        if not baseline.has_baseline():
            return None

        z = baseline.z_score(observation.value)
        if z is None:
            return None

        abs_z = abs(z)
        if abs_z < self.z_score_threshold:
            return None

        severity = self._severity_from_z(abs_z)
        expected = baseline.expected() or 0.0
        score = min(abs_z / self.z_score_threshold, 5.0)

        return AnomalyEvent(
            event_id=f"stat_{observation.metric}_{observation.timestamp}",
            database=observation.database,
            metric=observation.metric,
            observed_value=observation.value,
            expected_baseline=expected,
            anomaly_score=score,
            severity=severity,
            detection_algorithm="statistical",
            timestamp=observation.timestamp,
            explanation=(
                f"{observation.metric} is {observation.value:.2f} vs baseline "
                f"{expected:.2f} (|z|={abs_z:.2f})."
            ),
            supporting_observations=list(baseline._values[-5:]),
        )

    def train_isolation_forest(self, features: list[list[float]]) -> bool:
        """Train Isolation Forest on a 2D feature matrix. Returns True on success."""
        if not _HAS_SKLEARN:
            return False
        if len(features) < 10:
            return False
        X = StandardScaler().fit_transform(features)
        self._model = IsolationForest(
            contamination=self.contamination,
            random_state=self.random_state,
        )
        self._model.fit(X)
        self._trained = True
        return True

    def detect_isolation_forest(
        self, observation: MetricObservation, feature_vector: list[float]
    ) -> Optional[AnomalyEvent]:
        """Run Isolation Forest inference on a single observation."""
        if not _HAS_SKLEARN or self._model is None:
            return None
        X = StandardScaler().fit_transform([feature_vector])
        score = self._model.decision_function(X)[0]  # higher = more normal
        prediction = self._model.predict(X)[0]  # -1 = anomaly
        if prediction != -1:
            return None

        anomaly_score = abs(float(score))
        severity = "medium" if anomaly_score > 0.5 else "low"
        baseline = self._baseline_for(observation.metric).expected() or 0.0

        return AnomalyEvent(
            event_id=f"ml_{observation.metric}_{observation.timestamp}",
            database=observation.database,
            metric=observation.metric,
            observed_value=observation.value,
            expected_baseline=baseline,
            anomaly_score=round(anomaly_score, 4),
            severity=severity,
            detection_algorithm="isolation_forest",
            timestamp=observation.timestamp,
            explanation=(
                f"Isolation Forest flagged {observation.metric}={observation.value:.2f} "
                f"as anomalous (score={anomaly_score:.4f})."
            ),
            model_version=self._model_version,
        )

    def detect(self, observation: MetricObservation, feature_vector=None) -> list[AnomalyEvent]:
        """Run all detectors and return events."""
        events = []
        stat = self.detect_statistical(observation)
        if stat:
            events.append(stat)
        if feature_vector is not None:
            ml = self.detect_isolation_forest(observation, feature_vector)
            if ml:
                events.append(ml)
        return events

    @staticmethod
    def _severity_from_z(abs_z: float) -> str:
        if abs_z >= 5.0:
            return "critical"
        if abs_z >= 4.0:
            return "high"
        if abs_z >= 3.5:
            return "medium"
        return "low"

    @property
    def model_trained(self) -> bool:
        return self._trained

    @property
    def sklearn_available(self) -> bool:
        return _HAS_SKLEARN

    @property
    def model_version(self) -> str:
        return self._model_version
