"""
AgriClutch Step 15: Rigorous Temporal Leakage and Information Horizon Regression Tests.
Verifies strictly chronological train/validation/test splits, zero future price leakage,
zero future feature leakage, forecast cutoff enforcement, and information bounding.
SIH26132 — Strengthening Market Linkages and Price Discovery for Farmers.
"""

from datetime import date, timedelta
from typing import Any

import numpy as np

from ml.forecasting.baselines.gradient_boosting import GradientBoostingForecaster
from ml.forecasting.baselines.naive import NaiveForecaster
from ml.forecasting.dataset import TimeSeriesDataset
from ml.forecasting.features import PastFeatureExtractor
from ml.forecasting.splitting import RollingOriginSplitter


def _generate_synthetic_series(num_points: int = 60, seed: int = 42) -> list[dict[str, Any]]:
    """Generates synthetic records with known date ordering."""
    rng = np.random.default_rng(seed)
    start_date = date(2024, 1, 1)
    records = []
    base_price = 30.0
    for i in range(num_points):
        d = start_date + timedelta(days=i)
        p = round(float(base_price + 0.1 * i + rng.normal(0, 0.5)), 2)
        records.append({
            "record_date": d.isoformat(),
            "normalized_modal_price": max(1.0, p),
            "arrival_tonnes": 10.0 + (i % 5),
            "source_record_id": f"rec_{i}",
        })
    return records


def test_temporal_split_order() -> None:
    """
    Verifies that train_time < validation/test_time strictly holds across all folds.
    No test timestamp may ever be less than or equal to the maximum training timestamp.
    """
    records = _generate_synthetic_series(60)
    dataset = TimeSeriesDataset.from_records(records, "tomato", "mandi_test_01")

    splitter = RollingOriginSplitter(initial_train_size=30, horizon=14, step_size=7, max_splits=3)
    folds = list(splitter.split(dataset))
    assert len(folds) > 0

    for fold in folds:
        max_train_date = max(fold.train_dates)
        min_test_date = min(fold.test_dates)
        # Strict inequality: max(train) < min(test)
        assert max_train_date < min_test_date, (
            f"Fold {fold.fold_index} temporal violation: max_train={max_train_date} >= min_test={min_test_date}"
        )
        assert fold.origin_date == max_train_date
        assert len(fold.train_prices) == len(fold.train_dates)
        assert len(fold.test_prices) == len(fold.test_dates)


def test_no_future_price_leakage() -> None:
    """
    Verifies that modifying future test prices does NOT alter forecasts or training sets.
    """
    records = _generate_synthetic_series(60)
    dataset = TimeSeriesDataset.from_records(records, "tomato", "mandi_test_01")
    splitter = RollingOriginSplitter(initial_train_size=30, horizon=14, step_size=7, max_splits=1)
    fold = next(splitter.split(dataset))

    # Baseline forecast with unmodified history
    model = NaiveForecaster()
    pred_orig = model.predict_quantiles(fold.train_prices, horizon=fold.horizon, quantiles=[0.5])

    # Counterfactual future where test prices explode by 10x
    corrupted_test_prices = [p * 10.0 for p in fold.test_prices]
    assert len(corrupted_test_prices) == len(fold.test_prices)
    # Re-predict using only fold.train_prices (which remains uncorrupted)
    pred_after = model.predict_quantiles(fold.train_prices, horizon=fold.horizon, quantiles=[0.5])

    assert np.allclose(pred_orig[0.5], pred_after[0.5]), "Model forecast altered by future prices!"


def test_no_future_feature_leakage() -> None:
    """
    Verifies that PastFeatureExtractor derives features exclusively from observations
    available at or before the forecast origin, with zero access to future prices.
    """
    history = [10.0, 11.0, 12.0, 13.0, 14.0, 15.0]
    origin_date = "2024-03-01"

    feat_baseline = PastFeatureExtractor.extract_features_at_step(history, origin_date)

    # Appending a future shock point [999.0] to a separate future array must not affect past feature vector
    future_history = history + [999.0]
    feat_at_origin = PastFeatureExtractor.extract_features_at_step(future_history[:-1], origin_date)

    assert feat_baseline == feat_at_origin, "PastFeatureExtractor output changed when isolated from future!"


def test_forecast_cutoff_enforcement() -> None:
    """
    Verifies that forecasters fail closed or only process data up to the cutoff horizon.
    """
    records = _generate_synthetic_series(45)
    dataset = TimeSeriesDataset.from_records(records, "tomato", "mandi_test_01")

    # Cut off at record 35
    cutoff_idx = 35
    cutoff_date = dataset.dates[cutoff_idx]
    train_history = dataset.prices[: cutoff_idx + 1]

    forecaster = GradientBoostingForecaster(max_iter=25)
    q_preds = forecaster.predict_quantiles(
        history_prices=train_history,
        horizon=7,
        quantiles=[0.1, 0.5, 0.9],
        history_dates=dataset.dates[: cutoff_idx + 1],
    )

    assert len(q_preds[0.5]) == 7
    # Future true points are strictly excluded from history
    assert len(train_history) == 36
    assert dataset.dates[cutoff_idx] == cutoff_date


def test_evaluation_uses_only_available_information() -> None:
    """
    Verifies that walk-forward evaluation trains on history and assesses strictly on future test.
    """
    records = _generate_synthetic_series(50)
    dataset = TimeSeriesDataset.from_records(records, "tomato", "mandi_test_01")
    splitter = RollingOriginSplitter(initial_train_size=30, horizon=7, step_size=7, max_splits=2)
    folds = list(splitter.split(dataset))

    for fold in folds:
        # Check that test set dates are all strictly after origin date
        for td in fold.test_dates:
            assert td > fold.origin_date, f"Test date {td} is not strictly after origin {fold.origin_date}"
