
"""TrendLens: bounded, explainable trend scoring functions."""

import math
from statistics import mean, pstdev


def compute_velocity(current_count: int, historical_avg: float) -> float:
    """Bounded relative growth in [-1, 1]."""
    if current_count < 0 or historical_avg < 0:
        raise ValueError("Counts and averages cannot be negative")
    if historical_avg == 0:
        return 1.0 if current_count > 0 else 0.0
    growth = (current_count - historical_avg) / historical_avg
    return max(-1.0, min(1.0, growth))


def compute_burst_score(current_count: int, historical_counts: list[int]) -> float:
    """Return a 0-to-1 burst score based on historical observations."""
    if current_count < 0 or any(x < 0 for x in historical_counts):
        raise ValueError("Counts cannot be negative")
    if len(historical_counts) < 2:
        return 0.0

    historical_mean = mean(historical_counts)
    historical_std = pstdev(historical_counts)
    if historical_std == 0:
        return 1.0 if current_count > historical_mean else 0.0

    z_score = (current_count - historical_mean) / historical_std
    return max(0.0, min(1.0, z_score / 3.0))


def compute_source_validation(sources_present: set) -> float:
    """Reward presence across distinct news outlets and sources (scaled to 4+ outlets)."""
    return min(1.0, len(sources_present) / 4.0)


def compute_sentiment_momentum(previous_avg: float, current_avg: float) -> float:
    """Magnitude of sentiment change, scaled to [0, 1]."""
    if not -1 <= previous_avg <= 1 or not -1 <= current_avg <= 1:
        raise ValueError("Sentiment averages must be between -1 and 1")
    return min(1.0, abs(current_avg - previous_avg) / 2.0)


DEFAULT_WEIGHTS = {
    "velocity": 0.40,
    "burst": 0.30,
    "source_validation": 0.20,
    "sentiment_momentum": 0.02,
    "entity_prominence": 0.08,
}


def compute_trend_score(
    velocity,
    burst,
    source_validation,
    sentiment_momentum,
    entity_prominence,
    weights: dict = None,
) -> float:
    """Return an experimental score from 0 to 100."""
    weights = weights or DEFAULT_WEIGHTS

    # Declining topics receive no positive velocity points.
    signals = {
        "velocity": max(0.0, min(1.0, float(velocity))),
        "burst": float(burst),
        "source_validation": float(source_validation),
        "sentiment_momentum": float(sentiment_momentum),
        "entity_prominence": float(entity_prominence),
    }

    if set(weights) != set(signals):
        raise ValueError("Weights must contain exactly the five signal names")
    if any(not math.isfinite(v) or not 0 <= v <= 1 for v in signals.values()):
        raise ValueError("Signals must be finite and within [0, 1]")

    clean_weights = {key: float(value) for key, value in weights.items()}
    if any(not math.isfinite(v) or v < 0 for v in clean_weights.values()):
        raise ValueError("Weights must be finite and non-negative")

    total = sum(clean_weights.values())
    if total <= 0:
        raise ValueError("At least one weight must be positive")

    score = sum(signals[k] * clean_weights[k] for k in signals) / total
    return round(score * 100, 2)
