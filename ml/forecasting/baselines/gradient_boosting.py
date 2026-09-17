"""
Multi-Quantile Gradient Boosting Forecaster for AgriClutch.
Uses scikit-learn HistGradientBoostingRegressor trained at target quantiles with strictly past-lagged features.
SIH26132 — Market Linkages and Price Discovery for Farmers.
"""

from collections.abc import Sequence

import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor

from ml.forecasting.base import BaseForecaster
from ml.forecasting.features import PastFeatureExtractor


class GradientBoostingForecaster(BaseForecaster):
    """
    Multi-quantile Gradient Boosted Decision Tree Forecaster.
    Trains independent quantile regressors for q in {0.1, 0.2, 0.5, 0.8, 0.9}.
    Enforces monotonic rearrangement to eliminate quantile crossing.
    """

    def __init__(self, max_iter: int = 50, min_samples_leaf: int = 5) -> None:
        self.max_iter = max_iter
        self.min_samples_leaf = min_samples_leaf
        self._models: dict[float, HistGradientBoostingRegressor] = {}
        self.quantile_crossings_detected: int = 0

    @property
    def model_name(self) -> str:
        return "gradient_boosting"

    @property
    def model_version(self) -> str:
        return "HistGradientBoosting-Quantile (v1.0)"

    @property
    def parameter_count(self) -> str:
        return "~15K (ensemble trees)"

    @property
    def is_available(self) -> bool:
        return True

    def fit(
        self,
        history_prices: Sequence[float],
        history_dates: Sequence[str] | None = None,
    ) -> None:
        n = len(history_prices)
        if n < 30:
            raise ValueError(
                f"GradientBoostingForecaster requires at least 30 observations (found {n})."
            )

        # Build past-derived training matrix
        x_train, y = PastFeatureExtractor.build_training_dataset(
            history_prices, history_dates, max_lag=28
        )

        quantiles = [0.10, 0.20, 0.50, 0.80, 0.90]
        self._models = {}

        # Effective leaf size adjusted for small agricultural sets
        leaf_size = max(2, min(self.min_samples_leaf, len(x_train) // 5))

        for q in quantiles:
            model = HistGradientBoostingRegressor(
                loss="quantile",
                quantile=q,
                max_iter=self.max_iter,
                min_samples_leaf=leaf_size,
                random_state=42,
            )
            model.fit(x_train, y)
            self._models[q] = model

    def predict_quantiles(
        self,
        history_prices: Sequence[float],
        horizon: int = 14,
        quantiles: list[float] | None = None,
        history_dates: Sequence[str] | None = None,
    ) -> dict[float, list[float]]:
        self.fit(history_prices, history_dates)

        target_quantiles = sorted(quantiles or [0.10, 0.20, 0.50, 0.80, 0.90])
        results: dict[float, list[float]] = {q: [] for q in target_quantiles}

        # Multi-step autoregressive rollout
        # Simulated sequence starts with historical prices
        sim_history = list(history_prices)
        sim_dates = list(history_dates) if history_dates else None

        self.quantile_crossings_detected = 0

        for _h in range(horizon):
            curr_date_str = sim_dates[-1] if sim_dates else None
            feat = PastFeatureExtractor.extract_features_at_step(sim_history, curr_date_str)
            feat_arr = np.array([feat], dtype=np.float64)

            # Predict raw quantiles
            step_preds: dict[float, float] = {}
            for q in target_quantiles:
                model = self._models.get(q)
                if model is not None:
                    raw_val = float(model.predict(feat_arr)[0])
                else:
                    # Fallback to median model if specific quantile wasn't fitted
                    med_model = self._models[0.50]
                    raw_val = float(med_model.predict(feat_arr)[0])
                step_preds[q] = max(0.1, raw_val)

            # Quantile Crossing Validation & Isotonic Monotonic Rearrangement
            # (Chernozhukov, Fernandez-Val, Galichon, Econometrica 2010)
            raw_vals = [step_preds[q] for q in target_quantiles]
            if any(raw_vals[i] > raw_vals[i + 1] for i in range(len(raw_vals) - 1)):
                self.quantile_crossings_detected += 1
                sorted_vals = sorted(raw_vals)
                for idx, q in enumerate(target_quantiles):
                    step_preds[q] = sorted_vals[idx]

            for q in target_quantiles:
                results[q].append(round(step_preds[q], 2))

            # Autoregressively roll median forecast into simulated history for step h+1
            sim_history.append(step_preds[0.50])

        return results
