"""Statistical failure prediction — pure domain logic (ML-ready feature vector)."""

from dataclasses import dataclass
from statistics import mean, pstdev

from src.domain.factory.machine import Machine
from src.domain.prediction.enums import PredictionType
from src.domain.simulation.metric_snapshot import MetricSnapshot


@dataclass(frozen=True)
class AnomalyScore:
    score: float
    features: dict[str, float]


@dataclass(frozen=True)
class FailurePredictionResult:
    prediction_type: PredictionType
    confidence: float
    features: dict[str, object]
    anomaly_score: float


class FailurePredictor:
    """Heuristic predictor using trend analysis — architecture ready for sklearn models."""

    ANOMALY_THRESHOLD = 0.7
    CONFIDENCE_THRESHOLD = 0.8
    MIN_SAMPLES = 5

    def compute_anomaly_score(
        self, machine: Machine, metrics_history: list[MetricSnapshot]
    ) -> AnomalyScore | None:
        if len(metrics_history) < self.MIN_SAMPLES:
            return None

        temps = [m.temperature for m in metrics_history]
        vibs = [m.vibration for m in metrics_history]
        powers = [m.power_consumption for m in metrics_history]
        rates = [m.production_rate for m in metrics_history]

        temp_mean = mean(temps)
        vib_mean = mean(vibs)
        power_mean = mean(powers)
        rate_mean = mean(rates)

        temp_trend = (temps[-1] - temps[0]) / max(len(temps), 1)
        vib_trend = (vibs[-1] - vibs[0]) / max(len(vibs), 1)
        vib_std = pstdev(vibs) if len(vibs) > 1 else 0.0

        nominal = machine.nominal_production_rate
        temp_score = min(1.0, max(0.0, (temp_mean - 45.0) / 50.0))
        vib_score = min(1.0, max(0.0, (vib_mean - 1.5) / 10.0))
        trend_score = min(1.0, max(0.0, (temp_trend + vib_trend) / 5.0))
        rate_score = min(1.0, max(0.0, 1.0 - rate_mean / nominal))
        volatility_score = min(1.0, vib_std / 3.0)

        score = (
            0.3 * temp_score
            + 0.25 * vib_score
            + 0.2 * trend_score
            + 0.15 * rate_score
            + 0.1 * volatility_score
        )
        score = min(1.0, max(0.0, score + machine.failure_rate * 0.2))

        features = {
            "temp_mean": round(temp_mean, 2),
            "vib_mean": round(vib_mean, 2),
            "power_mean": round(power_mean, 2),
            "rate_mean": round(rate_mean, 2),
            "temp_trend": round(temp_trend, 3),
            "vib_trend": round(vib_trend, 3),
            "vib_std": round(vib_std, 3),
        }
        return AnomalyScore(score=round(score, 4), features=features)

    def predict(
        self, machine: Machine, metrics_history: list[MetricSnapshot]
    ) -> FailurePredictionResult | None:
        anomaly = self.compute_anomaly_score(machine, metrics_history)
        if anomaly is None or anomaly.score < self.ANOMALY_THRESHOLD:
            return None

        confidence = min(0.95, anomaly.score + 0.1)
        if confidence < self.CONFIDENCE_THRESHOLD:
            return None

        prediction_type = (
            PredictionType.FAILURE_WITHIN_24H
            if confidence >= 0.85
            else PredictionType.DEGRADATION_TREND
        )

        features: dict[str, object] = dict(anomaly.features)
        features["anomaly_score"] = anomaly.score

        return FailurePredictionResult(
            prediction_type=prediction_type,
            confidence=round(confidence, 4),
            features=features,
            anomaly_score=anomaly.score,
        )
