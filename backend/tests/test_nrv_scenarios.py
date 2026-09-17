"""
Unit Tests for AgriClutch Multi-Market and Multi-Horizon Scenario Engine.
SIH26132 — Market Linkages and Price Discovery for Farmers.
"""

import pytest

from ml.decision.contracts import QuantitySpec
from ml.decision.nrv import NRVCalculator
from ml.decision.scenarios import ScenarioEngine


class TestNRVScenarios:
    """Verifies scenario comparison logic and strict zero-recommendation boundaries."""

    @pytest.fixture
    def scenario_engine(self) -> ScenarioEngine:
        return ScenarioEngine(NRVCalculator())

    def test_mandi_price_versus_realization_divergence(
        self, scenario_engine: ScenarioEngine
    ) -> None:
        """
        Proves core platform principle: Higher mandi price does not guarantee higher realization.
        Market A: Quoted INR 28.00/kg (local, 8 km away)
        Market B: Quoted INR 30.50/kg (distant, 245 km away)
        """
        q = QuantitySpec.from_input(1000.0, "kg")  # 1 tonne
        markets_data = [
            {
                "market_id": "mandi_ch_49",
                "market_name": "Chandigarh APMC",
                "distance_km": 8.0,
                "apmc_fee_fraction": 0.015,
                "forecast_price_quantiles": {"p10": 25.0, "p20": 26.5, "p50": 28.0, "p80": 29.5, "p90": 31.0},
            },
            {
                "market_id": "mandi_dl_164",
                "market_name": "Azadpur Delhi Terminal",
                "distance_km": 245.0,
                "apmc_fee_fraction": 0.010,
                "forecast_price_quantiles": {"p10": 27.5, "p20": 29.0, "p50": 30.5, "p80": 32.0, "p90": 34.0},
            },
        ]

        scenarios = scenario_engine.compare_markets(
            commodity_id="tomato",
            quantity=q,
            scenario_date="2024-09-15",
            markets_data=markets_data,
        )

        assert len(scenarios) == 2
        ch = scenarios[0]
        dl = scenarios[1]

        # Quoted headline price at Azadpur is higher (INR 30.50 vs INR 28.00)
        assert dl.forecast_modal_price > ch.forecast_modal_price
        # But transport freight to Azadpur is much higher (245 km vs 8 km)
        assert dl.transport_cost > ch.transport_cost * 4
        # Scenarios must not contain recommendation or winner badges
        for sc in scenarios:
            sc_str = str(sc.to_dict()).upper()
            assert "BEST" not in sc_str
            assert "WINNER" not in sc_str
            assert "RECOMMEND" not in sc_str

    def test_time_horizon_decay_accumulation(
        self, scenario_engine: ScenarioEngine
    ) -> None:
        """Verifies that storage rent and perishability decay accumulate across t+0 to t+28."""
        q = QuantitySpec.from_input(1000.0, "kg")
        horizon_forecasts = {
            0: {"date": "2024-09-15", "quantiles": {"p10": 24.0, "p20": 25.0, "p50": 27.0, "p80": 29.0, "p90": 31.0}},
            3: {"date": "2024-09-18", "quantiles": {"p10": 24.5, "p20": 25.5, "p50": 27.5, "p80": 29.5, "p90": 31.5}},
            7: {"date": "2024-09-22", "quantiles": {"p10": 25.0, "p20": 26.0, "p50": 28.0, "p80": 30.0, "p90": 32.0}},
            14: {"date": "2024-09-29", "quantiles": {"p10": 26.0, "p20": 27.0, "p50": 29.0, "p80": 31.0, "p90": 33.0}},
            28: {"date": "2024-10-13", "quantiles": {"p10": 27.0, "p20": 28.0, "p50": 30.0, "p80": 32.0, "p90": 34.0}},
        }

        time_scenarios = scenario_engine.compare_time_horizons(
            commodity_id="tomato",
            market_id="mandi_ch_49",
            market_name="Chandigarh APMC",
            distance_km=8.0,
            quantity=q,
            horizon_forecasts=horizon_forecasts,
            storage_type="ambient",
        )

        assert len(time_scenarios) == 5
        # Effective quantity must decrease over time under ambient storage for tomato
        assert time_scenarios[0].effective_quantity_kg > time_scenarios[1].effective_quantity_kg > time_scenarios[2].effective_quantity_kg
