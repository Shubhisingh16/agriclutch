"""
Unit Tests for AgriClutch Economic Input Provenance and Fail-Closed Policy.
SIH26132 — Market Linkages and Price Discovery for Farmers.
"""

import pytest

from ml.decision.contracts import ProvenanceStatus, QuantitySpec
from ml.decision.loss import DocumentedLossModel, LossModelUnavailableError
from ml.decision.nrv import NRVCalculator


class TestNRVProvenance:
    """Verifies that all economic inputs are auditable and never silently fabricated."""

    @pytest.fixture
    def calculator(self) -> NRVCalculator:
        return NRVCalculator()

    def test_all_cost_items_carry_provenance(self, calculator: NRVCalculator) -> None:
        """Verifies every single deduction in the cost breakdown carries full provenance metadata."""
        q = QuantitySpec.from_input(1000.0, "kg")
        res = calculator.calculate(
            commodity_id="tomato",
            market_id="mandi_ch_49",
            scenario_date="2024-09-15",
            quantity=q,
            forecast_price_quantiles={"p10": 20.0, "p20": 22.0, "p50": 25.0, "p80": 28.0, "p90": 30.0},
            distance_km=10.0,
            storage_days=1,
            storage_type="ambient",
        )

        cb = res.cost_breakdown
        items = [
            cb.transport_cost,
            cb.storage_cost,
            cb.handling_cost,
            cb.market_charges,
            cb.other_costs,
            cb.loss_cost,
            cb.risk_cost,
        ]

        for item in items:
            assert item.provenance is not None
            assert item.provenance.source
            assert item.provenance.status in ProvenanceStatus
            assert item.provenance.effective_date
            assert item.provenance.is_demo is True  # Demo benchmark seed

    def test_loss_model_fails_closed_on_unknown_crop(self) -> None:
        """Verifies that attempting to calculate loss for an uncalibrated crop fails closed."""
        loss_model = DocumentedLossModel()
        with pytest.raises(LossModelUnavailableError) as exc_info:
            loss_model.estimate_loss(
                crop="unsupported_tropical_fruit",
                storage_type="ambient",
                storage_days=3,
                initial_quantity_kg=500.0,
            )
        assert "unsupported_tropical_fruit" in str(exc_info.value)
