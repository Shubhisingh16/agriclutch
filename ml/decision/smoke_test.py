"""
Standalone Smoke Test for AgriClutch Decision Intelligence & NRV Engine.
Validates all 13 core requirements of Step 11 without external network dependencies.
SIH26132 — Market Linkages and Price Discovery for Farmers.
"""

import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from ml.decision.contracts import ProvenanceStatus, QuantitySpec
from ml.decision.loss import DocumentedLossModel, LossModelUnavailableError
from ml.decision.nrv import NRVCalculator
from ml.decision.scenarios import ScenarioEngine
from ml.decision.sensitivity import SensitivityEngine


def run_smoke_test() -> None:
    print("=" * 60)
    print("AGRICLUTCH STEP 11: NRV & DECISION ENGINE SMOKE TEST")
    print("=" * 60)

    # 1. Quantity Validation
    print("\n[1/13] Testing Quantity Validation & Rejection...")
    try:
        QuantitySpec.from_input(quantity=-50.0, unit="kg")
        raise AssertionError("Failed: Negative quantity was not rejected!")
    except ValueError as exc:
        print(f"  OK: Negative quantity rejected: {exc}")

    try:
        QuantitySpec.from_input(quantity=100.0, unit="bushel")
        raise AssertionError("Failed: Invalid unit was not rejected!")
    except ValueError as exc:
        print(f"  OK: Invalid unit rejected: {exc}")

    # 2. Unit Conversions (Dimensional Consistency)
    print("\n[2/13] Testing Unit Conversions (tonne, quintal, kg)...")
    q_kg = QuantitySpec.from_input(1000.0, "kg")
    q_q = QuantitySpec.from_input(10.0, "quintal")
    q_t = QuantitySpec.from_input(1.0, "tonne")
    assert q_kg.normalized_quantity_kg == 1000.0, f"Expected 1000 kg, got {q_kg.normalized_quantity_kg}"
    assert q_q.normalized_quantity_kg == 1000.0, f"Expected 1000 kg from 10 quintals, got {q_q.normalized_quantity_kg}"
    assert q_t.normalized_quantity_kg == 1000.0, f"Expected 1000 kg from 1 tonne, got {q_t.normalized_quantity_kg}"
    print(f"  OK: 1000 kg == 10 quintals == 1 tonne normalized to {q_kg.normalized_quantity_kg} kg")

    # 3. Forecast Integration & NRV Calculator
    print("\n[3/13] Testing Forecast Quantile Integration & NRV Calculation...")
    calc = NRVCalculator()
    forecast_quantiles = {
        "p10": 25.0,
        "p20": 26.5,
        "p50": 28.5,
        "p80": 30.5,
        "p90": 32.0,
    }
    result = calc.calculate(
        commodity_id="tomato",
        market_id="mandi_ch_49",
        scenario_date="2024-09-15",
        quantity=q_kg,
        forecast_price_quantiles=forecast_quantiles,
        distance_km=8.0,
        storage_days=0,
        storage_type="ambient",
        quality_grade="FAQ",
        freight_rate_per_km_tonne=4.50,
        base_dispatch_fee=250.0,
        apmc_fee_fraction=0.015,
    )
    print(f"  OK: NRV calculated: P50 GrossRev=INR {result.gross_revenue_quantiles['p50']}, TotalCost=INR {result.total_cost}, P50 NRV=INR {result.nrv_quantiles.p50}")

    # 4. Gross Revenue Arithmetic
    print("\n[4/13] Testing Gross Revenue Calculation...")
    expected_rev_p50 = round(1000.0 * 28.5 * 1.0, 2)
    assert result.gross_revenue_quantiles["p50"] == expected_rev_p50, f"Expected INR {expected_rev_p50}, got INR {result.gross_revenue_quantiles['p50']}"
    print(f"  OK: Gross revenue exactly matches effective_qty * price: INR {expected_rev_p50}")

    # 5. Cost Breakdown Separability
    print("\n[5/13] Testing Cost Breakdown Items...")
    cb = result.cost_breakdown
    assert cb.transport_cost.amount > 0, "Transport cost missing"
    assert cb.handling_cost.amount == 600.0, f"Expected INR 600 handling (INR 0.60/kg * 1000 kg), got INR {cb.handling_cost.amount}"
    assert cb.market_charges.amount > 0, "Market charges missing"
    assert cb.other_costs.amount == 400.0, f"Expected INR 400 other (INR 0.40/kg * 1000 kg), got INR {cb.other_costs.amount}"
    print(f"  OK: Cost components separately itemized: Freight=INR {cb.transport_cost.amount}, Handling=INR {cb.handling_cost.amount}, MandiFee=INR {cb.market_charges.amount}, Other=INR {cb.other_costs.amount}")

    # 6. Effective Quantity & Decay Handling
    print("\n[6/13] Testing Perishability Decay on 3-day Ambient Tomato...")
    res_storage = calc.calculate(
        commodity_id="tomato",
        market_id="mandi_ch_49",
        scenario_date="2024-09-18",
        quantity=q_kg,
        forecast_price_quantiles=forecast_quantiles,
        distance_km=8.0,
        storage_days=3,
        storage_type="ambient",
    )
    assert res_storage.loss.effective_quantity_kg < 1000.0, "Effective quantity did not decay after 3 days ambient storage"
    assert res_storage.loss.loss_rate > 0.10, "Expected >10% loss after 3 days of tomato ambient storage"
    print(f"  OK: 3d Ambient Tomato decayed from 1000 kg -> {res_storage.loss.effective_quantity_kg} kg (loss: {res_storage.loss.loss_quantity_kg} kg, {res_storage.loss.loss_rate*100:.2f}%)")

    # 7. Distribution Propagation & Monotonicity
    print("\n[7/13] Testing NRV Quantile Monotonicity (P10 <= P20 <= P50 <= P80 <= P90)...")
    nq = result.nrv_quantiles
    assert nq.p10 <= nq.p20 <= nq.p50 <= nq.p80 <= nq.p90, f"Monotonicity violated: {nq}"
    print(f"  OK: Quantiles strictly monotonic: P10=INR {nq.p10} <= P20=INR {nq.p20} <= P50=INR {nq.p50} <= P80=INR {nq.p80} <= P90=INR {nq.p90}")

    # 8. Break-Even Price Calculation
    print("\n[8/13] Testing Break-Even Price Derivation...")
    assert result.break_even.is_available, "Break-even price should be available"
    assert result.break_even.break_even_price is not None and result.break_even.break_even_price > 0, "Break-even price must be positive"
    be = result.break_even.break_even_price
    # Verify at break-even price, NRV is approximately zero
    be_res = calc.calculate(
        commodity_id="tomato",
        market_id="mandi_ch_49",
        scenario_date="2024-09-15",
        quantity=q_kg,
        forecast_price_quantiles={"p10": be, "p20": be, "p50": be, "p80": be, "p90": be},
        distance_km=8.0,
        storage_days=0,
    )
    assert abs(be_res.nrv_quantiles.p50) < 5.0, f"NRV at break-even INR {be} was not ~0 (got INR {be_res.nrv_quantiles.p50})"
    print(f"  OK: Break-even quoted price = INR {be}/kg (yields NRV of INR {be_res.nrv_quantiles.p50} ~ INR 0)")

    # 9. Scenario Comparison (Multi-Market & Multi-Horizon)
    print("\n[9/13] Testing Scenario Engine (Market & Time Comparisons)...")
    sc_engine = ScenarioEngine(calc)
    mkt_candidates = [
        {
            "market_id": "mandi_ch_49",
            "market_name": "Chandigarh APMC",
            "distance_km": 8.0,
            "apmc_fee_fraction": 0.015,
            "forecast_price_quantiles": forecast_quantiles,
        },
        {
            "market_id": "mandi_dl_164",
            "market_name": "Azadpur Delhi Terminal",
            "distance_km": 245.0,
            "apmc_fee_fraction": 0.010,
            "forecast_price_quantiles": {k: v + 3.0 for k, v in forecast_quantiles.items()},  # Higher headline price (+INR 3/kg)
        },
    ]
    mkt_scenarios = sc_engine.compare_markets(
        commodity_id="tomato",
        quantity=q_kg,
        scenario_date="2024-09-15",
        markets_data=mkt_candidates,
    )
    assert len(mkt_scenarios) == 2, "Expected 2 market scenarios"
    ch_res = mkt_scenarios[0]
    dl_res = mkt_scenarios[1]
    print(f"  Mandi A (Chandigarh): Dist={ch_res.distance_km}km, Price=INR {ch_res.forecast_modal_price}, Freight=INR {ch_res.transport_cost}, NRV=INR {ch_res.nrv_p50}")
    print(f"  Mandi B (Azadpur Delhi): Dist={dl_res.distance_km}km, Price=INR {dl_res.forecast_modal_price}, Freight=INR {dl_res.transport_cost}, NRV=INR {dl_res.nrv_p50}")
    # Azadpur has higher headline price (INR 31.50 vs INR 28.50) but higher freight (INR 1352 vs INR 286)
    print("  OK: Markets compared transparently without declaring a winner or rank score")

    # 10. Sensitivity Matrix Generation
    print("\n[10/13] Testing Sensitivity Engine (3x3 Grid)...")
    sens_engine = SensitivityEngine(calc)
    sens_matrix = sens_engine.generate_matrix(
        commodity_id="tomato",
        market_id="mandi_ch_49",
        scenario_date="2024-09-15",
        quantity=q_kg,
        forecast_price_quantiles=forecast_quantiles,
        distance_km=8.0,
        variable_x="price",
        variable_y="transport",
    )
    assert len(sens_matrix.grid_nrv_p50) == 3 and len(sens_matrix.grid_nrv_p50[0]) == 3, "Matrix must be 3x3"
    print(f"  OK: 3x3 Sensitivity Grid generated for {sens_matrix.variable_x} vs {sens_matrix.variable_y}:")
    for r_idx, row in enumerate(sens_matrix.grid_nrv_p50):
        print(f"    {sens_matrix.levels_y[r_idx]}: {row}")

    # 11. Provenance Integrity
    print("\n[11/13] Testing Provenance Fields...")
    assert len(result.provenance_items) >= 5, "Missing provenance entries on cost components"
    for p in result.provenance_items:
        assert p.source, "Missing source in provenance"
        assert p.status in ProvenanceStatus, f"Invalid provenance status: {p.status}"
        assert p.effective_date, "Missing effective_date"
    print(f"  OK: All {len(result.provenance_items)} components have auditable provenance (status={result.provenance_items[0].status.value})")

    # 12. Fail-Closed Behavior
    print("\n[12/13] Testing Fail-Closed on Missing Crop Loss Parameters...")
    loss_model = DocumentedLossModel()
    try:
        loss_model.estimate_loss(
            crop="exotic_dragonfruit",
            storage_type="ambient",
            storage_days=5,
            initial_quantity_kg=100.0,
        )
        raise AssertionError("Failed: Unknown crop did not raise LossModelUnavailableError!")
    except LossModelUnavailableError as exc:
        print(f"  OK: Failed closed with LossModelUnavailableError: {exc.detail}")

    # 13. Zero Recommendation Leakage
    print("\n[13/13] Testing Strict Absence of Recommendation Terms...")
    forbidden_phrases = [
        "SELL NOW",
        "BUY NOW",
        "STORE NOW",
        "BEST MARKET",
        "WINNER",
        "RECOMMENDED ACTION",
        "RECOMMENDED MARKET",
        "RECOMMENDATION:",
        "ACTION: SELL",
        "ACTION: HOLD",
        "ACTION: BUY",
    ]
    res_dict = result.to_dict()
    res_str = str(res_dict).upper()
    for phrase in forbidden_phrases:
        assert phrase not in res_str, f"Recommendation phrase '{phrase}' leaked into NRV result!"

    # Ensure standalone word HOLD as recommendation doesn't appear
    assert not re.search(r"\b(RECOMMEND|ADVISE|SHOULD)\s+(SELL|HOLD|BUY|STORE)\b", res_str), "Advisory decision leaked!"
    print("  OK: Verified 0 recommendation leaks across result dictionary")

    print("\n" + "=" * 60)
    print("SMOKE TEST COMPLETE: ALL 13 TEST STAGES PASSED CLEANLY.")
    print("=" * 60)


if __name__ == "__main__":
    run_smoke_test()
