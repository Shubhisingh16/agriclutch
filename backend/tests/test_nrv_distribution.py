"""
Unit Tests for AgriClutch NRV Distribution Propagation and Monotonicity.
SIH26132 — Market Linkages and Price Discovery for Farmers.
"""

import pytest

from ml.decision.contracts import QuantitySpec
from ml.decision.nrv import NRVCalculator


class TestNRVDistribution:
    """Verifies that price distribution quantiles propagate monotonically into NRV."""

    @pytest.fixture
    def calculator(self) -> NRVCalculator:
        return NRVCalculator()

    @pytest.fixture
    def forecast_quantiles(self) -> dict[str, float]:
        return {
            "p10": 22.0,
            "p20": 24.5,
            "p50": 27.0,
            "p80": 29.5,
            "p90": 32.5,
        }

    def test_nrv_quantile_monotonicity(
        self, calculator: NRVCalculator, forecast_quantiles: dict[str, float]
    ) -> None:
        """Asserts P10 <= P20 <= P50 <= P80 <= P90 strictly holds for NRV."""
        q = QuantitySpec.from_input(1500.0, "kg")
        res = calculator.calculate(
            commodity_id="tomato",
            market_id="mandi_ch_49",
            scenario_date="2024-09-15",
            quantity=q,
            forecast_price_quantiles=forecast_quantiles,
            distance_km=12.0,
            storage_days=2,
            storage_type="ambient",
        )

        nq = res.nrv_quantiles
        assert nq.p10 <= nq.p20 <= nq.p50 <= nq.p80 <= nq.p90, (
            f"Monotonicity violated in NRV: P10={nq.p10}, P20={nq.p20}, P50={nq.p50}, P80={nq.p80}, P90={nq.p90}"
        )

        n_per_kg = res.nrv_per_kg_quantiles
        assert n_per_kg.p10 <= n_per_kg.p20 <= n_per_kg.p50 <= n_per_kg.p80 <= n_per_kg.p90

    def test_scenario_risk_bounding(
        self, calculator: NRVCalculator, forecast_quantiles: dict[str, float]
    ) -> None:
        """Verifies Conservative <= Expected <= Optimistic realization hierarchy."""
        q = QuantitySpec.from_input(1000.0, "kg")

        exp_res = calculator.calculate(
            commodity_id="onion",
            market_id="mandi_ch_49",
            scenario_date="2024-09-15",
            quantity=q,
            forecast_price_quantiles=forecast_quantiles,
            distance_km=25.0,
            scenario_type="EXPECTED",
        )

        cons_res = calculator.calculate(
            commodity_id="onion",
            market_id="mandi_ch_49",
            scenario_date="2024-09-15",
            quantity=q,
            forecast_price_quantiles=forecast_quantiles,
            distance_km=25.0,
            scenario_type="CONSERVATIVE",
        )

        opt_res = calculator.calculate(
            commodity_id="onion",
            market_id="mandi_ch_49",
            scenario_date="2024-09-15",
            quantity=q,
            forecast_price_quantiles=forecast_quantiles,
            distance_km=25.0,
            scenario_type="OPTIMISTIC",
        )

        # Conservative applies downside P10 price + cost stress; Optimistic applies P90 + cost efficiency
        assert cons_res.nrv_quantiles.p10 < exp_res.nrv_quantiles.p50 < opt_res.nrv_quantiles.p90
        assert cons_res.total_cost >= exp_res.total_cost
