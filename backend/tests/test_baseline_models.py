"""
Unit Tests for Agricultural Price Baseline Forecasters.
SIH26132 — Market Linkages and Price Discovery for Farmers.
"""

from ml.forecasting.baselines.gradient_boosting import GradientBoostingForecaster
from ml.forecasting.baselines.naive import NaiveForecaster
from ml.forecasting.baselines.seasonal_naive import SeasonalNaiveForecaster
from ml.forecasting.baselines.statistical import StatisticalForecaster


def test_naive_forecaster_contract_and_monotonicity() -> None:
    history = [25.0, 26.0, 25.5, 27.0, 28.0]
    model = NaiveForecaster()
    horizon = 7
    quantiles = [0.1, 0.2, 0.5, 0.8, 0.9]

    q_preds = model.predict_quantiles(history, horizon=horizon, quantiles=quantiles)

    # Point forecast equals latest observed price (28.0)
    for step in range(horizon):
        assert q_preds[0.5][step] == 28.0

        # Monotonicity check
        assert q_preds[0.1][step] <= q_preds[0.2][step]
        assert q_preds[0.2][step] <= q_preds[0.5][step]
        assert q_preds[0.5][step] <= q_preds[0.8][step]
        assert q_preds[0.8][step] <= q_preds[0.9][step]

    # Uncertainty increases over horizon
    spread_1 = q_preds[0.9][0] - q_preds[0.1][0]
    spread_7 = q_preds[0.9][6] - q_preds[0.1][6]
    assert spread_7 > spread_1


def test_seasonal_naive_forecaster() -> None:
    # 14 days of weekly seasonal pattern
    base_week = [25.0, 26.0, 27.0, 26.5, 28.0, 29.0, 25.5]
    history = base_week + base_week
    model = SeasonalNaiveForecaster(season_length=7)
    horizon = 7
    quantiles = [0.1, 0.2, 0.5, 0.8, 0.9]

    q_preds = model.predict_quantiles(history, horizon=horizon, quantiles=quantiles)

    # Day 0 should repeat day -7 (25.0)
    assert q_preds[0.5][0] == 25.0
    assert q_preds[0.5][1] == 26.0

    for step in range(horizon):
        assert q_preds[0.1][step] <= q_preds[0.5][step] <= q_preds[0.9][step]


def test_statistical_holt_forecaster() -> None:
    # Steady upward trending series
    history = [20.0 + i * 0.5 for i in range(35)]
    model = StatisticalForecaster(damping_phi=0.9)
    horizon = 10
    quantiles = [0.1, 0.2, 0.5, 0.8, 0.9]

    q_preds = model.predict_quantiles(history, horizon=horizon, quantiles=quantiles)

    assert len(q_preds[0.5]) == 10
    # Median should continue upward with damped trend
    assert q_preds[0.5][0] > history[-1]
    assert q_preds[0.5][-1] >= q_preds[0.5][0]

    for step in range(horizon):
        vals = [q_preds[q][step] for q in quantiles]
        assert vals == sorted(vals)


def test_gradient_boosting_forecaster_monotonic_rearrangement() -> None:
    # Synthetic series with noise
    import numpy as np
    np.random.seed(42)
    history = [float(25.0 + np.sin(i / 3.0) * 3.0 + (i % 5) * 0.4) for i in range(40)]
    dates = [f"2024-08-{i+1:02d}" for i in range(30)] + [f"2024-09-{i+1:02d}" for i in range(10)]

    model = GradientBoostingForecaster(max_iter=30)
    horizon = 7
    quantiles = [0.1, 0.2, 0.5, 0.8, 0.9]

    q_preds = model.predict_quantiles(history, horizon=horizon, quantiles=quantiles, history_dates=dates)

    assert len(q_preds[0.5]) == horizon
    for step in range(horizon):
        vals = [q_preds[q][step] for q in quantiles]
        # Verify strict non-decreasing quantile order
        for j in range(len(vals) - 1):
            assert vals[j] <= vals[j + 1] + 1e-6
