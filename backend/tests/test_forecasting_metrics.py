"""
Unit Tests for Agricultural Forecasting Evaluation Metrics.
Validates MAE, RMSE, sMAPE, MASE, Pinball Loss, and Interval Coverage against analytical vectors.
SIH26132 — Market Linkages and Price Discovery for Farmers.
"""

import pytest

from ml.forecasting.evaluation import EvaluationMetrics


def test_point_metrics_exact_values() -> None:
    y_true = [10.0, 20.0, 30.0]
    y_pred = [12.0, 18.0, 33.0]
    # Errors: [2.0, -2.0, 3.0]
    # MAE = (2 + 2 + 3) / 3 = 7/3 ~= 2.333
    # MSE = (4 + 4 + 9) / 3 = 17/3 ~= 5.667 -> RMSE ~= 2.380

    mae = EvaluationMetrics.mean_absolute_error(y_true, y_pred)
    rmse = EvaluationMetrics.root_mean_squared_error(y_true, y_pred)

    assert pytest.approx(mae, 0.001) == 7.0 / 3.0
    assert pytest.approx(rmse, 0.001) == (17.0 / 3.0) ** 0.5


def test_smape_bounded_percentage() -> None:
    y_true = [100.0, 50.0]
    y_pred = [100.0, 50.0]
    # Perfect forecast -> 0%
    assert EvaluationMetrics.symmetric_mape(y_true, y_pred) == 0.0

    # Max percentage is <= 200%
    y_zero = [0.0, 0.0]
    y_pos = [10.0, 10.0]
    smape_max = EvaluationMetrics.symmetric_mape(y_zero, y_pos)
    assert pytest.approx(smape_max, 0.1) == 200.0


def test_mase_scaled_relative_to_naive() -> None:
    train_history = [10.0, 12.0, 14.0, 16.0]  # daily diffs are all 2.0 -> mean abs diff = 2.0
    y_true = [18.0, 20.0]
    y_pred = [17.0, 19.0]  # errors are both 1.0 -> MAE = 1.0

    # MASE = 1.0 / 2.0 = 0.5
    mase = EvaluationMetrics.mean_absolute_scaled_error(y_true, y_pred, train_history)
    assert pytest.approx(mase, 0.001) == 0.5


def test_pinball_quantile_loss() -> None:
    y_true = [20.0]
    # Under-prediction (y > y_hat): loss = quantile * (y - y_hat)
    loss_under = EvaluationMetrics.pinball_loss(y_true, [10.0], quantile=0.8)
    assert pytest.approx(loss_under, 0.001) == 0.8 * 10.0

    # Over-prediction (y <= y_hat): loss = (1 - quantile) * (y_hat - y)
    loss_over = EvaluationMetrics.pinball_loss(y_true, [30.0], quantile=0.8)
    assert pytest.approx(loss_over, 0.001) == 0.2 * 10.0


def test_interval_coverage() -> None:
    y_true = [10.0, 20.0, 30.0, 40.0]
    q_low = [8.0, 18.0, 25.0, 50.0]   # 4th point is below q_low (out of bound)
    q_high = [12.0, 22.0, 35.0, 60.0]

    # Points 1, 2, 3 are inside [8,12], [18,22], [25,35]. Point 4 (40.0) is below 50.0.
    # Coverage = 3 / 4 = 0.75
    cov = EvaluationMetrics.interval_coverage(y_true, q_low, q_high)
    assert pytest.approx(cov, 0.01) == 0.75
