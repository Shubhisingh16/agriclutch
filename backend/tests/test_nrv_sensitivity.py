"""
Unit Tests for AgriClutch Sensitivity Engine.
SIH26132 — Market Linkages and Price Discovery for Farmers.
"""

import pytest

from ml.decision.contracts import QuantitySpec
from ml.decision.nrv import NRVCalculator
from ml.decision.sensitivity import SensitivityEngine


class TestNRVSensitivity:
    """Verifies orthogonal two-variable sensitivity grid calculation."""

    @pytest.fixture
    def sensitivity_engine(self) -> SensitivityEngine:
        return SensitivityEngine(NRVCalculator())

    def test_price_versus_transport_grid(
        self, sensitivity_engine: SensitivityEngine
    ) -> None:
        """Verifies 3x3 grid calculation for price vs transport."""
        q = QuantitySpec.from_input(1000.0, "kg")
        res = sensitivity_engine.generate_matrix(
            commodity_id="tomato",
            market_id="mandi_ch_49",
            scenario_date="2024-09-15",
            quantity=q,
            forecast_price_quantiles={"p10": 24.0, "p20": 25.5, "p50": 28.0, "p80": 30.5, "p90": 32.0},
            distance_km=10.0,
            variable_x="price",
            variable_y="transport",
        )

        assert res.variable_x == "price"
        assert res.variable_y == "transport"
        assert len(res.grid_nrv_p50) == 3
        assert len(res.grid_nrv_p50[0]) == 3

        # For a fixed transport row, higher price column must increase NRV
        for row in res.grid_nrv_p50:
            assert row[0] < row[1] < row[2]  # LOW price < BASE price < HIGH price
