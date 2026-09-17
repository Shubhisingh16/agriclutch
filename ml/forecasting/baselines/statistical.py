"""
Statistical Forecaster for AgriClutch (Holt's Linear Exponential Smoothing with Damped Trend).
Constructs analytical level-trend updates and rigorous error-variance prediction intervals.
SIH26132 — Market Linkages and Price Discovery for Farmers.
"""

import math
from collections.abc import Sequence

import numpy as np
from scipy.optimize import minimize
from scipy.stats import norm

from ml.forecasting.base import BaseForecaster


class StatisticalForecaster(BaseForecaster):
    """
    Holt's Linear Exponential Smoothing with additive damped trend.
    Level: l[t] = alpha * y[t] + (1 - alpha) * (l[t-1] + phi * b[t-1])
    Trend: b[t] = beta * (l[t] - l[t-1]) + (1 - beta) * phi * b[t-1]
    Forecast: y_hat[t+h] = l[t] + sum_{i=1}^h (phi^i) * b[t]
    """

    def __init__(self, damping_phi: float = 0.95) -> None:
        self.damping_phi = damping_phi
        self.alpha: float = 0.3
        self.beta: float = 0.1
        self._level: float = 0.0
        self._trend: float = 0.0
        self._sigma_res: float = 1.0

    @property
    def model_name(self) -> str:
        return "statistical"

    @property
    def model_version(self) -> str:
        return f"Holt-Damped (phi={self.damping_phi})"

    @property
    def parameter_count(self) -> str:
        return "3 (alpha, beta, phi)"

    @property
    def is_available(self) -> bool:
        return True

    def _simulate(
        self,
        prices: np.ndarray,
        alpha: float,
        beta: float,
        phi: float,
    ) -> tuple[float, float, float, np.ndarray]:
        """Runs filter pass and computes one-step-ahead residuals."""
        n = len(prices)
        level = prices[0]
        b = (prices[1] - prices[0]) if n > 1 else 0.0
        residuals = np.zeros(n)

        for t in range(n):
            y_pred = level + phi * b
            residuals[t] = prices[t] - y_pred
            y_t = prices[t]
            new_level = alpha * y_t + (1 - alpha) * (level + phi * b)
            new_b = beta * (new_level - level) + (1 - beta) * phi * b
            level, b = new_level, new_b

        return level, b, float(np.mean(residuals[1:] ** 2)) if n > 1 else 0.0, residuals

    def fit(
        self,
        history_prices: Sequence[float],
        history_dates: Sequence[str] | None = None,
    ) -> None:
        if len(history_prices) < 3:
            raise ValueError("StatisticalForecaster requires at least 3 historical observations.")

        prices = np.array(history_prices, dtype=np.float64)

        # Optimize alpha and beta over bounds (0.01, 0.99)
        def loss_fn(params: np.ndarray) -> float:
            a, b = params[0], params[1]
            _, _, mse, _ = self._simulate(prices, a, b, self.damping_phi)
            return mse

        init_params = [0.3, 0.1]
        bounds = [(0.01, 0.99), (0.01, 0.99)]
        res = minimize(loss_fn, init_params, method="L-BFGS-B", bounds=bounds)

        self.alpha = float(res.x[0]) if res.success else 0.3
        self.beta = float(res.x[1]) if res.success else 0.1

        l_final, b_final, _, residuals = self._simulate(
            prices, self.alpha, self.beta, self.damping_phi
        )
        self._level = l_final
        self._trend = b_final
        self._sigma_res = max(0.1, float(np.std(residuals[1:])))

    def predict_quantiles(
        self,
        history_prices: Sequence[float],
        horizon: int = 14,
        quantiles: list[float] | None = None,
        history_dates: Sequence[str] | None = None,
    ) -> dict[float, list[float]]:
        self.fit(history_prices, history_dates)

        target_quantiles = quantiles or [0.10, 0.20, 0.50, 0.80, 0.90]
        results: dict[float, list[float]] = {q: [] for q in target_quantiles}

        phi = self.damping_phi
        # Precompute cumulative trend damping weights
        cum_phi = 0.0
        variance_multiplier = 0.0

        for h in range(1, horizon + 1):
            cum_phi += phi**h
            point_pred = self._level + cum_phi * self._trend

            # Error variance for damped Holt model grows over horizon
            weight_h = self.alpha + self.alpha * self.beta * cum_phi
            variance_multiplier += weight_h**2
            sigma_h = self._sigma_res * math.sqrt(1.0 + variance_multiplier)

            for q in target_quantiles:
                z = norm.ppf(q)
                pred = max(0.1, point_pred + z * sigma_h)
                results[q].append(round(pred, 2))

        return results
