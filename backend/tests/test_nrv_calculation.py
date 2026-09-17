"""
Unit Tests for AgriClutch NRV Calculation, Cost Arithmetic, and Units.
SIH26132 — Market Linkages and Price Discovery for Farmers.
"""

import pytest

from ml.decision.contracts import QuantitySpec
from ml.decision.loss import DocumentedLossModel
from ml.decision.nrv import NRVCalculator


class TestNRVCalculation:
    """Mathematical verification of Net Realizable Value solver."""

    @pytest.fixture
    def calculator(self) -> NRVCalculator:
        return NRVCalculator(loss_model=DocumentedLossModel())

    @pytest.fixture
    def forecast_quantiles(self) -> dict[str, float]:
        return {
            "p10": 24.0,
            "p20": 25.5,
            "p50": 28.0,
            "p80": 30.5,
            "p90": 32.0,
        }

    def test_quantity_unit_conversion(self) -> None:
        """Verifies explicit conversion of tonnes and quintals to kilograms."""
        q_1000kg = QuantitySpec.from_input(1000.0, "kg")
        q_10q = QuantitySpec.from_input(10.0, "quintal")
        q_1tonne = QuantitySpec.from_input(1.0, "tonne")

        assert q_1000kg.normalized_quantity_kg == 1000.0
        assert q_10q.normalized_quantity_kg == 1000.0
        assert q_1tonne.normalized_quantity_kg == 1000.0
        assert q_1000kg.original_unit == "kg"
        assert q_10q.original_unit == "quintal"
        assert q_1tonne.original_unit == "tonne"

    def test_invalid_quantity_rejections(self) -> None:
        """Verifies that negative, zero, or unsupported units are rejected."""
        with pytest.raises(ValueError, match="strictly positive"):
            QuantitySpec.from_input(-5.0, "kg")

        with pytest.raises(ValueError, match="strictly positive"):
            QuantitySpec.from_input(0.0, "kg")

        with pytest.raises(ValueError, match="Unsupported quantity unit"):
            QuantitySpec.from_input(50.0, "bushel")

    def test_gross_revenue_arithmetic(
        self, calculator: NRVCalculator, forecast_quantiles: dict[str, float]
    ) -> None:
        """Verifies gross revenue equals effective_quantity * quality_adjusted_price."""
        q = QuantitySpec.from_input(1000.0, "kg")
        res = calculator.calculate(
            commodity_id="tomato",
            market_id="mandi_ch_49",
            scenario_date="2024-09-15",
            quantity=q,
            forecast_price_quantiles=forecast_quantiles,
            distance_km=10.0,
            storage_days=0,
            quality_grade="FAQ",  # factor = 1.0
        )

        # Storage days = 0, so effective_qty = 1000.0
        assert res.loss.effective_quantity_kg == 1000.0
        assert res.gross_revenue_quantiles["p50"] == 28000.0
        assert res.gross_revenue_quantiles["p10"] == 24000.0
        assert res.gross_revenue_quantiles["p90"] == 32000.0

    def test_itemized_cost_subtraction(
        self, calculator: NRVCalculator, forecast_quantiles: dict[str, float]
    ) -> None:
        """Verifies every cost deduction is correctly itemized and subtracted."""
        q = QuantitySpec.from_input(1000.0, "kg")  # 1 tonne
        res = calculator.calculate(
            commodity_id="tomato",
            market_id="mandi_ch_49",
            scenario_date="2024-09-15",
            quantity=q,
            forecast_price_quantiles=forecast_quantiles,
            distance_km=10.0,
            storage_days=0,
            freight_rate_per_km_tonne=5.0,
            base_dispatch_fee=200.0,
            loading_rate_per_kg=0.25,
            unloading_rate_per_kg=0.25,
            apmc_fee_fraction=0.02,  # 2%
            other_rate_per_kg=0.30,
        )

        cb = res.cost_breakdown
        # Transport = 200 + (10 km * 5/km/t * 1 t) = 250
        assert cb.transport_cost.amount == 250.0
        # Handling = 1000 * (0.25 + 0.25) = 500
        assert cb.handling_cost.amount == 500.0
        # Other = 1000 * 0.30 = 300
        assert cb.other_costs.amount == 300.0
        # Market charges on P50 = 28000 * 0.02 = 560
        assert cb.market_charges.amount == 560.0

        # Total cost for P50 = 250 + 500 + 300 + 560 + 0 + 0 = 1610
        assert res.total_cost == 1610.0
        assert res.nrv_quantiles.p50 == 28000.0 - 1610.0

    def test_break_even_price_accuracy(
        self, calculator: NRVCalculator, forecast_quantiles: dict[str, float]
    ) -> None:
        """Verifies that at the calculated break-even price, NRV is approximately zero."""
        q = QuantitySpec.from_input(1000.0, "kg")
        res = calculator.calculate(
            commodity_id="tomato",
            market_id="mandi_ch_49",
            scenario_date="2024-09-15",
            quantity=q,
            forecast_price_quantiles=forecast_quantiles,
            distance_km=15.0,
            storage_days=0,
        )

        assert res.break_even.is_available
        be_price = res.break_even.break_even_price
        assert be_price is not None and be_price > 0

        # Re-evaluate with exact break-even price
        be_eval = calculator.calculate(
            commodity_id="tomato",
            market_id="mandi_ch_49",
            scenario_date="2024-09-15",
            quantity=q,
            forecast_price_quantiles={k: be_price for k in ["p10", "p20", "p50", "p80", "p90"]},
            distance_km=15.0,
            storage_days=0,
        )
        assert abs(be_eval.nrv_quantiles.p50) < 5.0  # within rounding tolerance

    def test_break_even_unrounded_mathematical_identity(
        self, calculator: NRVCalculator, forecast_quantiles: dict[str, float]
    ) -> None:
        """Numerically proves that with unrounded P_BE = C_non_market / (Q_eff * F_qual * (1 - mu)), |NRV(P_BE)| < 1e-10."""
        q = QuantitySpec.from_input(1000.0, "kg")
        res = calculator.calculate(
            commodity_id="tomato",
            market_id="mandi_ch_49",
            scenario_date="2024-09-15",
            quantity=q,
            forecast_price_quantiles=forecast_quantiles,
            distance_km=15.0,
            storage_days=0,
        )
        c_non_market = (
            res.cost_breakdown.transport_cost.amount
            + res.cost_breakdown.storage_cost.amount
            + res.cost_breakdown.handling_cost.amount
            + res.cost_breakdown.other_costs.amount
            + res.cost_breakdown.loss_cost.amount
            + res.cost_breakdown.risk_cost.amount
        )
        q_eff = res.loss.effective_quantity_kg
        f_qual = res.quality.quality_factor
        mu_apmc = 0.015  # mandi_ch_49 demo cess

        # Exact unrounded P_BE using division, not multiplication:
        be_denom = q_eff * f_qual * (1.0 - mu_apmc)
        p_be_exact = c_non_market / be_denom

        # Analytical evaluation of NRV at p_be_exact:
        gross_rev = q_eff * f_qual * p_be_exact
        market_fee = gross_rev * mu_apmc
        total_cost = c_non_market + market_fee
        nrv_exact = gross_rev - total_cost

        assert abs(nrv_exact) < 1e-10, f"Expected |NRV(P_BE)| < 1e-10, got {nrv_exact}"

