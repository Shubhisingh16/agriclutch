"""
Naive Persistence Forecaster for AgriClutch.
Projects the latest observed price with residual variance scaling over horizon h.
SIH26132 — Market Linkages and Price Discovery for Farmers.
"""

import math
from collections.abc import Sequence

import numpy as np
from scipy.stats import norm

from ml.forecasting.base import BaseForecaster


class NaiveForecaster(BaseForecaster):
    """
    Naive Persistence baseline: y_hat[t+h] = y[t].
    Uncertainty grows as sigma_h = sigma_diff * sqrt(h) based on historical daily price volatility.
    """

    def __init__(self) -> None:
        self._last_price: float | None = None
        self._sigma_diff: float = 1.0

    @property
    def model_name(self) -> str:
        return "naive"

    @property
    def model_version(self) -> str:
        return "1.0.0"

    @property
    def parameter_count(self) -> str:
        return "0"

    @property
    def is_available(self) -> bool:
        return True

    def fit(
        self,
        history_prices: Sequence[float],
        history_dates: Sequence[str] | None = None,
    ) -> None:
        if len(history_prices) == 0:
            raise ValueError("Cannot fit NaiveForecaster on empty history.")

        self._last_price = float(history_prices[-1])
        if len(history_prices) > 1:
            diffs = np.diff(np.array(history_prices, dtype=np.float64))
            self._sigma_diff = max(0.1, float(np.std(diffs)))
        else:
            self._sigma_diff = 1.0

    def predict_quantiles(
        self,
        history_prices: Sequence[float],
        horizon: int = 14,
        quantiles: list[float] | None = None,
        history_dates: Sequence[str] | None = None,
    ) -> dict[float, list[float]]:
        if len(history_prices) == 0:
            raise ValueError("History cannot be empty.")

        self.fit(history_prices, history_dates)
        assert self._last_price is not None

        target_quantiles = quantiles or [0.10, 0.20, 0.50, 0.80, 0.90]
        results: dict[float, list[float]] = {q: [] for q in target_quantiles}

        for h in range(1, horizon + 1):
            sigma_h = self._sigma_diff * math.sqrt(h)
            for q in target_quantiles:
                z = norm.ppf(q)
                pred = max(0.1, self._last_price + z * sigma_h)
                results[q].append(round(pred, 2))

        return results
