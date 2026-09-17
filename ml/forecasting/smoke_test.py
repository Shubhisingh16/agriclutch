"""Standalone executable smoke test for the AgriClutch Forecasting Subsystem.

Validates:
1. TimeSeriesDataset construction and data sufficiency gating (>= 30 points).
2. Naive, Seasonal Naive, Holt Statistical, and Gradient Boosting forecasters.
3. Quantile monotonicity (P10 <= P20 <= P50 <= P80 <= P90).
4. Chronos-2 adapter graceful execution or fail-closed ModelUnavailableError.
5. Rolling-origin evaluation and metric calculation.
"""

import sys
from datetime import date, timedelta
from typing import Any

import numpy as np

from ml.forecasting.baselines.gradient_boosting import GradientBoostingForecaster
from ml.forecasting.baselines.naive import NaiveForecaster
from ml.forecasting.baselines.seasonal_naive import SeasonalNaiveForecaster
from ml.forecasting.baselines.statistical import StatisticalForecaster
from ml.forecasting.chronos_adapter import Chronos2Forecaster, ModelUnavailableError
from ml.forecasting.dataset import TimeSeriesDataset
from ml.forecasting.registry import ForecastModelRegistry


def generate_synthetic_records(num_points: int = 60) -> list[dict[str, Any]]:
    """Generate deterministic synthetic mandi price records."""
    start_date = date(2024, 1, 1)
    records = []
    base_price = 28.5
    for i in range(num_points):
        d = start_date + timedelta(days=i)
        seasonal = 2.0 * np.sin(2 * np.pi * (i % 7) / 7)
        drift = 0.05 * i
        noise = ((i % 5) - 2) * 0.3
        p = round(float(base_price + seasonal + drift + noise), 2)
        records.append({
            "record_date": d.isoformat(),
            "normalized_modal_price": max(1.0, p),
            "arrival_tonnes": 15.0 + (i % 10),
            "source_record_id": f"rec_{i}",
        })
    return records


def run_smoke_test() -> int:
    print("==================================================")
    print("AGRICLUTCH STEP 10: FORECASTING SUBSYSTEM SMOKE TEST")
    print("==================================================")

    # 1. Dataset verification
    print("\n[1/6] Validating TimeSeriesDataset...")
    records_60 = generate_synthetic_records(60)
    dataset_60 = TimeSeriesDataset.from_records(
        records=records_60,
        commodity_id="tomato",
        market_id="mandi_dl_164",
    )
    is_suff, _count, msg = dataset_60.check_sufficiency(min_observations=30)
    assert is_suff, f"Expected sufficient, got: {msg}"
    print(f"  OK: 60-point dataset validated (origin={dataset_60.origin_date}, gaps={len(dataset_60.gaps)})")

    # 2. Insufficiency gating test
    print("\n[2/6] Validating Insufficient History Gating (< 30 observations)...")
    records_20 = generate_synthetic_records(20)
    dataset_20 = TimeSeriesDataset.from_records(
        records=records_20,
        commodity_id="tomato",
        market_id="mandi_dl_164",
    )
    is_suff_20, count_20, msg_20 = dataset_20.check_sufficiency(min_observations=30)
    assert not is_suff_20, "Expected insufficient for 20 records!"
    print(f"  OK: Correctly rejected short history ({count_20} records): {msg_20}")

    # 3. Test Baselines (Naive, Seasonal Naive, Statistical, Gradient Boosting)
    print("\n[3/6] Testing Baseline Forecasters with Horizon=14...")
    horizon = 14
    quantiles = [0.1, 0.2, 0.5, 0.8, 0.9]

    forecasters = [
        NaiveForecaster(),
        SeasonalNaiveForecaster(season_length=7),
        StatisticalForecaster(damping_phi=0.95),
        GradientBoostingForecaster(max_iter=50),
    ]

    for model in forecasters:
        q_preds = model.predict_quantiles(
            history_prices=dataset_60.prices,
            horizon=horizon,
            quantiles=quantiles,
            history_dates=dataset_60.dates,
        )
        assert 0.5 in q_preds, f"Missing median 0.5 in {model.model_name}"
        assert len(q_preds[0.5]) == horizon, f"{model.model_name} length mismatch"
        for q in quantiles:
            assert q in q_preds, f"Missing quantile {q} in {model.model_name}"
            assert len(q_preds[q]) == horizon, f"Quantile length mismatch in {model.model_name}"

        # Monotonicity check
        for step in range(horizon):
            q_vals = [q_preds[q][step] for q in sorted(quantiles)]
            for i in range(len(q_vals) - 1):
                assert q_vals[i] <= q_vals[i + 1] + 1e-6, (
                    f"Quantile crossing in {model.model_name} at step {step}: "
                    f"{q_vals[i]} > {q_vals[i+1]}"
                )

        print(f"  OK: {model.model_name} passed: step-0 median={q_preds[0.5][0]:.2f}, step-{horizon-1} median={q_preds[0.5][-1]:.2f}")

    # 4. Test Chronos-2 Adapter
    print("\n[4/6] Testing Chronos-2 Adapter...")
    chronos = Chronos2Forecaster()
    try:
        q_chronos = chronos.predict_quantiles(
            history_prices=dataset_60.prices,
            horizon=horizon,
            quantiles=quantiles,
            history_dates=dataset_60.dates,
        )
        print(f"  OK: Chronos-2 generated live inference: step-0 median={q_chronos[0.5][0]:.2f}")
    except ModelUnavailableError as e:
        print(f"  INFO: Chronos-2 weights unavailable locally/offline (fail-closed as expected): {e.detail}")

    # 5. Registry and Model Comparison
    print("\n[5/6] Testing Model Registry and Rolling-Origin Evaluation...")
    registry = ForecastModelRegistry()
    available_models = registry.list_models()
    print(f"  Registered models: {[m['id'] for m in available_models]}")

    eval_results = registry.evaluate_all(
        dataset=dataset_60,
        horizon=7,
        max_splits=2,
    )
    print(f"  Evaluated {len(eval_results['evaluations'])} models across rolling origins:")
    for metric in eval_results["evaluations"]:
        print(f"    - {metric['model_name']:20s}: MAE={metric['mae']:.3f}, RMSE={metric['rmse']:.3f}, sMAPE={metric['smape']:.2f}%, Coverage={metric['coverage_80']:.1f}%")

    print("\n[6/6] Smoke Test Summary")
    print("  ALL TESTS PASSED SUCCESSFULLY.")
    print("==================================================")
    return 0


if __name__ == "__main__":
    sys.exit(run_smoke_test())
