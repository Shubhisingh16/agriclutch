"""
Forecasting Model Registry & Comparative Benchmarking Hub for AgriClutch.
Maintains model instances, lifecycle, availability, and rolling-origin comparison evaluations.
SIH26132 — Market Linkages and Price Discovery for Farmers.
"""

import logging
from datetime import datetime, timezone
from typing import Any

import numpy as np

from ml.forecasting.base import BaseForecaster
from ml.forecasting.baselines.gradient_boosting import GradientBoostingForecaster
from ml.forecasting.baselines.naive import NaiveForecaster
from ml.forecasting.baselines.seasonal_naive import SeasonalNaiveForecaster
from ml.forecasting.baselines.statistical import StatisticalForecaster
from ml.forecasting.chronos_adapter import Chronos2Forecaster
from ml.forecasting.dataset import TimeSeriesDataset
from ml.forecasting.evaluation import EvaluationMetrics
from ml.forecasting.splitting import RollingOriginSplitter

logger = logging.getLogger("agriclutch.forecasting.registry")


class ForecastModelRegistry:
    """
    Singleton registry managing all available forecasting engines and benchmarks.
    Caches forecaster instances to prevent repeated initialization overhead.
    """

    def __init__(self) -> None:
        self._models: dict[str, BaseForecaster] = {}
        self._register_defaults()

    def _register_defaults(self) -> None:
        """Registers default foundation models and baselines."""
        self._models["naive"] = NaiveForecaster()
        self._models["seasonal_naive"] = SeasonalNaiveForecaster(season_length=7)
        self._models["statistical"] = StatisticalForecaster(damping_phi=0.95)
        self._models["gradient_boosting"] = GradientBoostingForecaster(max_iter=50)
        self._models["chronos-2"] = Chronos2Forecaster()

    def get_model(self, model_name: str) -> BaseForecaster:
        """
        Retrieves a registered forecaster by identifier.

        Raises:
            KeyError: If model_name is not registered.
        """
        normalized = model_name.lower().strip()
        if normalized not in self._models:
            raise KeyError(
                f"Unknown model '{model_name}'. Available engines: {list(self._models.keys())}"
            )
        return self._models[normalized]

    def list_models(self) -> list[dict[str, Any]]:
        """Returns metadata list of all registered models and availability status."""
        catalog = []
        for name, model in self._models.items():
            family = "baseline"
            if name == "chronos-2":
                family = "foundation"
            elif name == "statistical":
                family = "statistical"
            elif name == "gradient_boosting":
                family = "ml"

            catalog.append(
                {
                    "id": name,
                    "name": model.model_name.replace("_", " ").title(),
                    "family": family,
                    "description": f"{model.model_name} forecaster (version {model.model_version}, {model.parameter_count} params)",
                    "is_available": model.is_available,
                    "supported_quantiles": [0.1, 0.2, 0.5, 0.8, 0.9],
                }
            )
        return catalog

    def evaluate_all(
        self,
        dataset: TimeSeriesDataset,
        horizon: int = 14,
        max_splits: int = 3,
    ) -> dict[str, Any]:
        """
        Executes rolling-origin walk-forward evaluation across all available models on identical folds.

        Returns:
            Dictionary structure matching ModelComparisonResult.
        """
        splitter = RollingOriginSplitter(
            initial_train_size=30,
            horizon=horizon,
            step_size=7,
            max_splits=max_splits,
        )
        folds = list(splitter.split(dataset))
        if not folds:
            raise ValueError(
                f"Insufficient history ({len(dataset.prices)} observations) to generate "
                f"evaluation folds for horizon={horizon}."
            )

        model_results: list[dict[str, Any]] = []

        for name, model in self._models.items():
            # Skip Chronos if unavailable on host rather than crashing evaluation
            if name == "chronos-2" and not model.is_available:
                logger.info("Chronos-2 is unavailable; skipping from rolling-origin evaluation.")
                continue

            fold_maes: list[float] = []
            fold_rmses: list[float] = []
            fold_smapes: list[float] = []
            fold_mases: list[float] = []
            fold_pinballs: list[float] = []
            fold_coverages: list[float] = []

            for fold in folds:
                try:
                    q_preds = model.predict_quantiles(
                        history_prices=fold.train_prices,
                        horizon=fold.horizon,
                        quantiles=[0.1, 0.2, 0.5, 0.8, 0.9],
                        history_dates=fold.train_dates,
                    )
                except Exception as exc:  # noqa: BLE001
                    logger.warning("Model '%s' failed on fold %d: %s", name, fold.fold_index, exc)
                    continue

                median_pred = q_preds[0.50]
                y_true = fold.test_prices

                mae = EvaluationMetrics.mean_absolute_error(y_true, median_pred)
                rmse = EvaluationMetrics.root_mean_squared_error(y_true, median_pred)
                smape = EvaluationMetrics.symmetric_mape(y_true, median_pred)
                mase = EvaluationMetrics.mean_absolute_scaled_error(y_true, median_pred, fold.train_prices)

                # Pinball average
                pinball = np.mean([
                    EvaluationMetrics.pinball_loss(y_true, q_preds[q], q)
                    for q in [0.1, 0.2, 0.5, 0.8, 0.9]
                ])
                coverage = EvaluationMetrics.interval_coverage(y_true, q_preds[0.10], q_preds[0.90])

                fold_maes.append(mae)
                fold_rmses.append(rmse)
                fold_smapes.append(smape)
                fold_mases.append(mase)
                fold_pinballs.append(float(pinball))
                fold_coverages.append(coverage)

            if fold_maes:
                model_results.append(
                    {
                        "model_name": name,
                        "horizon": horizon,
                        "mae": round(float(np.mean(fold_maes)), 3),
                        "rmse": round(float(np.mean(fold_rmses)), 3),
                        "smape": round(float(np.mean(fold_smapes)), 2),
                        "mase": round(float(np.mean(fold_mases)), 3),
                        "pinball_loss": round(float(np.mean(fold_pinballs)), 3),
                        "coverage_80": round(float(np.mean(fold_coverages)) * 100.0, 1),
                        "windows_evaluated": len(fold_maes),
                    }
                )

        return {
            "commodity_id": dataset.commodity_id,
            "market_id": dataset.market_id,
            "horizon": horizon,
            "evaluations": model_results,
            "evaluation_strategy": "ROLLING_ORIGIN",
            "split_count": len(folds),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }


# Global singleton instance
forecast_registry = ForecastModelRegistry()
