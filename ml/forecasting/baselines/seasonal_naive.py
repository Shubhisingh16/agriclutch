"""
Seasonal Naive Forecaster for AgriClutch.
Projects periodic seasonal cycles (default weekly m=7) with empirical seasonal residual variance.
SIH26132 — Market Linkages and Price Discovery for Farmers.
"""

import math
from collections.abc import Sequence

import numpy as np
from scipy.stats import norm

from ml.forecasting.base import BaseForecaster


class SeasonalNaiveForecaster(BaseForecaster):
    """
    Seasonal Naive baseline: y_hat[t+h] = y[t + h - m * ceil(h/m)].
    Requires at least 2 * m observations to validate cyclical alignment.
    """

    def __init__(self, season_length: int = 7) -> None:
        self.season_length = season_length
        self._history: list[float] = []
        self._sigma_seasonal: float = 1.0

    @property
    def model_name(self) -> str:
        return "seasonal_naive"

    @property
    def model_version(self) -> str:
        return f"1.0.0 (period={self.season_length})"

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
        m = self.season_length
        n = len(history_prices)
        if n < 2 * m:
            raise ValueError(
                f"SeasonalNaiveForecaster with period={m} requires at least "
                f"{2 * m} observations (found {n})."
            )

        self._history = [float(p) for p in history_prices]

        # Calculate seasonal residuals: y[t] - y[t-m]
        seasonal_diffs = [
            self._history[i] - self._history[i - m]
            for i in range(m, len(self._history))
        ]
        self._sigma_seasonal = max(0.1, float(np.std(seasonal_diffs)))

    def predict_quantiles(
        self,
        history_prices: Sequence[float],
        horizon: int = 14,
        quantiles: list[float] | None = None,
        history_dates: Sequence[str] | None = None,
    ) -> dict[float, list[float]]:
        self.fit(history_prices, history_dates)

        m = self.season_length
        target_quantiles = quantiles or [0.10, 0.20, 0.50, 0.80, 0.90]
        results: dict[float, list[float]] = {q: [] for q in target_quantiles}

        for h in range(1, horizon + 1):
            # Calculate seasonal index offset
            # When h=1..m, offset is -(m - (h - 1))
            k = (h - 1) % m
            cycle = math.ceil(h / m)
            seasonal_val = self._history[-m + k]

            sigma_h = self._sigma_seasonal * math.sqrt(cycle)

            for q in target_quantiles:
                z = norm.ppf(q)
                pred = max(0.1, seasonal_val + z * sigma_h)
                results[q].append(round(pred, 2))

        return results
