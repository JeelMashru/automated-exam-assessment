"""
Unit tests for Benchmark calculations, MAE, RMSE, Pearson Correlation, and Repeatability.
"""

import pytest
from core.benchmark import BenchmarkEngine


def test_agreement_metrics_calculation():
    human = [9.0, 7.5, 5.5, 3.5, 2.0]
    ai = [8.75, 8.0, 5.5, 3.5, 2.0]

    metrics = BenchmarkEngine.calculate_agreement_metrics(human, ai, max_marks=10.0, tolerance=1.0)

    assert metrics["n"] == 5
    assert metrics["mae"] >= 0.0
    assert metrics["rmse"] >= metrics["mae"]
    assert metrics["correlation"] > 0.95  # Highly correlated
    assert metrics["tolerance_agreement_pct"] == 100.0


def test_repeatability_metrics():
    # Deterministic run
    scores = [8.5, 8.5, 8.5]
    metrics = BenchmarkEngine.calculate_repeatability_metrics(scores)

    assert metrics["runs"] == 3
    assert metrics["mean"] == 8.5
    assert metrics["std_dev"] == 0.0
    assert metrics["score_range"] == 0.0
    assert metrics["is_stable"] is True
