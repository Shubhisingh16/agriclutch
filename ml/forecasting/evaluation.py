"""
Time-Series Evaluation Metrics Engine for AgriClutch.
Calculates point accuracy (MAE, RMSE, sMAPE, MASE) and quantile calibration (Pinball Loss, Coverage).
SIH26132 — Market Linkages and Price Discovery for Farmers.
"""

from collections.abc import Sequence

import numpy as np


class EvaluationMetrics:
    """Mathematical implementations of point and probabilistic forecast evaluation metrics."""

    @staticmethod
    def mean_absolute_error(y_true: Sequence[float], y_pred: Sequence[float]) -> float:
        """MAE in original units (INR/kg)."""
        yt = np.array(y_true, dtype=np.float64)
        yp = np.array(y_pred, dtype=np.float64)
        if len(yt) == 0:
            return 0.0
        return float(np.mean(np.abs(yt - yp)))

    @staticmethod
    def root_mean_squared_error(y_true: Sequence[float], y_pred: Sequence[float]) -> float:
        """RMSE in original units (INR/kg)."""
        yt = np.array(y_true, dtype=np.float64)
        yp = np.array(y_pred, dtype=np.float64)
        if len(yt) == 0:
            return 0.0
        return float(np.sqrt(np.mean((yt - yp) ** 2)))

    @staticmethod
    def symmetric_mape(y_true: Sequence[float], y_pred: Sequence[float]) -> float:
        """sMAPE bounded in [0%, 200%]."""
        yt = np.array(y_true, dtype=np.float64)
        yp = np.array(y_pred, dtype=np.float64)
        if len(yt) == 0:
            return 0.0
        denom = np.abs(yt) + np.abs(yp)
        # Avoid division by zero
        valid = denom > 1e-6
        if not np.any(valid):
            return 0.0
        smapes = 200.0 * np.abs(yt[valid] - yp[valid]) / denom[valid]
        return float(np.mean(smapes))

    @staticmethod
    def mean_absolute_scaled_error(
        y_true: Sequence[float],
        y_pred: Sequence[float],
        y_train: Sequence[float],
    ) -> float:
        """
        MASE relative to 1-step in-sample naive persistence.
        MASE < 1.0 indicates better performance than naive random walk.
        """
        mae = EvaluationMetrics.mean_absolute_error(y_true, y_pred)
        ytrain = np.array(y_train, dtype=np.float64)
        if len(ytrain) < 2:
            return 1.0

        naive_diffs = np.abs(np.diff(ytrain))
        scale = float(np.mean(naive_diffs))
        if scale < 1e-6:
            return 1.0
        return float(mae / scale)

    @staticmethod
    def pinball_loss(
        y_true: Sequence[float],
        y_pred_quantile: Sequence[float],
        quantile: float,
    ) -> float:
        """
        Pinball (quantile) loss for quantile level q in (0, 1).
        L_q(y, y_hat) = max(q * (y - y_hat), (1 - q) * (y_hat - y))
        """
        yt = np.array(y_true, dtype=np.float64)
        yp = np.array(y_pred_quantile, dtype=np.float64)
        if len(yt) == 0:
            return 0.0
        diff = yt - yp
        loss = np.maximum(quantile * diff, (quantile - 1.0) * diff)
        return float(np.mean(loss))

    @staticmethod
    def weighted_quantile_loss(
        y_true: Sequence[float],
        quantile_preds: dict[float, Sequence[float]],
    ) -> float:
        """Average weighted quantile loss across all evaluated quantiles."""
        yt = np.array(y_true, dtype=np.float64)
        sum_actuals = float(np.sum(np.abs(yt)))
        if sum_actuals < 1e-6 or len(quantile_preds) == 0:
            return 0.0

        total_loss = 0.0
        for q, preds in quantile_preds.items():
            total_loss += EvaluationMetrics.pinball_loss(y_true, preds, q) * len(y_true)

        avg_loss = total_loss / len(quantile_preds)
        return float(2.0 * avg_loss / sum_actuals)

    @staticmethod
    def interval_coverage(
        y_true: Sequence[float],
        lower_bound: Sequence[float],
        upper_bound: Sequence[float],
    ) -> float:
        """Percentage of actual values falling inside [lower_bound, upper_bound]."""
        yt = np.array(y_true, dtype=np.float64)
        lb = np.array(lower_bound, dtype=np.float64)
        ub = np.array(upper_bound, dtype=np.float64)
        if len(yt) == 0:
            return 0.0
        inside = (yt >= lb) & (yt <= ub)
        return float(np.mean(inside))
