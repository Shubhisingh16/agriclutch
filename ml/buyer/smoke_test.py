"""
AgriClutch Step 12: Buyer Matching & Demand Aggregation Standalone Smoke Test.
Verifies all 16 algorithmic stages, mathematical consistency, and recommendation-leakage guards.
SIH26132 — Strengthening Market Linkages and Price Discovery for Farmers.
"""

import sys
from datetime import date, timedelta
from pathlib import Path

# Ensure repository root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from ml.buyer.aggregation import DemandAggregationEngine
from ml.buyer.compatibility import CompatibilityEngine, calculate_haversine_distance
from ml.buyer.contracts import (
    BuyerDemand,
    BuyerProfile,
    BuyerRequirement,
    BuyerTransactionRecord,
    BuyerType,
    DeliveryMode,
    DistanceStatus,
    DistributionStatus,
    FarmerSupply,
    PaymentTerms,
    PriceBasis,
    ProvenanceStatus,
    QuantityMatchStatus,
    ReliabilityStatus,
    TemporalOverlapStatus,
)
from ml.buyer.reliability import BuyerReliabilityEngine


def run_smoke_test() -> None:
    print("=" * 60)
    print("AGRICLUTCH STEP 12: BUYER MATCHING & DEMAND SMOKE TEST")
    print("=" * 60)

    # [1/16] Buyer Profile Creation
    print("\n[1/16] Testing Buyer Profile Creation...")
    buyer = BuyerProfile(
        buyer_id="b_retail_01",
        display_name="Demo TriCity Fresh Retail",
        buyer_type=BuyerType.RETAILER,
        location="Chandigarh Sector 26",
        latitude=30.7333,
        longitude=76.7794,
        active_status=True,
    )
    assert buyer.buyer_id == "b_retail_01"
    assert buyer.buyer_type == BuyerType.RETAILER
    print("  OK: Buyer profile instantiated with valid attributes and coordinates.")

    # [2/16] Buyer Requirement Creation
    print("\n[2/16] Testing Buyer Requirement Creation...")
    today = date(2026, 10, 1)
    req = BuyerRequirement(
        requirement_id="req_tom_01",
        buyer_id=buyer.buyer_id,
        commodity_id="tomato",
        minimum_quantity_kg=500.0,
        maximum_quantity_kg=3000.0,
        preferred_quality_grade="Grade_A",
        acceptable_quality_range=["Grade_A", "FAQ"],
        required_from=today,
        required_until=today + timedelta(days=7),
        delivery_mode=DeliveryMode.BUYER_PREMISES,
        delivery_location="Chandigarh Hub",
        delivery_latitude=30.7333,
        delivery_longitude=76.7794,
        price_basis=PriceBasis.FIXED_QUOTE,
        quoted_price=29.50,
        payment_terms=PaymentTerms.NET_3_DAYS,
    )
    assert req.commodity_id == "tomato"
    assert req.quoted_price == 29.50
    print("  OK: Buyer requirement created with bounded quantity [500kg, 3000kg] and quote.")

    # [3/16] Supply Lot Creation
    print("\n[3/16] Testing Supply Creation...")
    supply = FarmerSupply(
        supply_id="sup_fpo_001",
        farmer_or_fpo_reference="FPO-PATIALA-01",
        commodity_id="tomato",
        quantity_kg=2000.0,
        quality_grade="Grade_A",
        available_from=today,
        available_until=today + timedelta(days=5),
        origin_location="Patiala Cluster",
        origin_latitude=30.3398,
        origin_longitude=76.3869,
    )
    assert supply.quantity_kg == 2000.0
    print("  OK: FarmerSupply created with 2000kg Grade A tomato.")

    # [4/16] Commodity Matching
    print("\n[4/16] Testing Commodity Matching...")
    compat_engine = CompatibilityEngine()
    c_match, _ = compat_engine.evaluate_commodity("tomato", "tomato")
    assert c_match, "Tomato should match tomato"
    c_mismatch, _ = compat_engine.evaluate_commodity("tomato", "potato")
    assert not c_mismatch, "Tomato should not match potato"
    print("  OK: Commodity predicate verifies exact match and flags mismatch.")

    # [5/16] Quantity Matching
    print("\n[5/16] Testing Quantity Matching Logic...")
    # Supply = 2000kg, Req = [500, 3000] -> Full absorption of supply
    q_stat, compat_q, un_s, un_d, _ = compat_engine.evaluate_quantity(2000.0, 500.0, 3000.0)
    assert q_stat == QuantityMatchStatus.PARTIAL_MATCH
    assert compat_q == 2000.0
    assert un_s == 0.0
    assert un_d == 1000.0

    # Supply = 4000kg, Req = [500, 3000] -> Max capacity reached
    _, compat_q2, un_s2, un_d2, _ = compat_engine.evaluate_quantity(4000.0, 500.0, 3000.0)
    assert compat_q2 == 3000.0
    assert un_s2 == 1000.0
    assert un_d2 == 0.0

    # Supply = 300kg, Req = [500, 3000] -> Below minimum
    q_stat3, compat_q3, _, _, _ = compat_engine.evaluate_quantity(300.0, 500.0, 3000.0)
    assert q_stat3 == QuantityMatchStatus.INSUFFICIENT_SUPPLY
    assert compat_q3 == 0.0
    print("  OK: Quantity matching accurately evaluates absorption, capacity limits, and batch minimums.")

    # [6/16] Quality Matching
    print("\n[6/16] Testing Quality Matching...")
    q_match, _ = compat_engine.evaluate_quality("Grade_A", "Grade_A", ["Grade_A", "FAQ"])
    assert q_match
    q_match2, _ = compat_engine.evaluate_quality("FAQ", "Grade_A", ["Grade_A", "FAQ"])
    assert q_match2
    q_mismatch, _ = compat_engine.evaluate_quality("Grade_B", "Grade_A", ["Grade_A", "FAQ"])
    assert not q_mismatch
    print("  OK: Quality matching supports preferred grades, acceptable grade ranges, and rejects undergrades.")

    # [7/16] Temporal Matching
    print("\n[7/16] Testing Temporal Overlap...")
    # Supply [0, 5] within Req [0, 7] -> Full overlap for supply
    t_match, t_stat, _ = compat_engine.evaluate_temporal(
        today, today + timedelta(days=5), today, today + timedelta(days=7), reference_date=today
    )
    assert t_match and t_stat == TemporalOverlapStatus.FULL_OVERLAP

    # Supply [0, 5] with Req [2, 7] -> Partial overlap (starts day 2)
    t_part_match, t_part_stat, _ = compat_engine.evaluate_temporal(
        today, today + timedelta(days=5), today + timedelta(days=2), today + timedelta(days=7), reference_date=today
    )
    assert t_part_match and t_part_stat == TemporalOverlapStatus.PARTIAL_OVERLAP

    # Expired requirement test
    past_date = today - timedelta(days=10)
    t_exp_match, t_exp_stat, _ = compat_engine.evaluate_temporal(
        today, today + timedelta(days=5), past_date - timedelta(days=5), past_date, reference_date=today
    )
    assert not t_exp_match and t_exp_stat == TemporalOverlapStatus.EXPIRED_REQUIREMENT
    print("  OK: Temporal logic verifies interval intersection and detects expired requirements.")

    # [8/16] Geographic Measurement
    print("\n[8/16] Testing Geographic Measurement (Haversine)...")
    dist_km, dist_stat = calculate_haversine_distance(
        supply.origin_latitude, supply.origin_longitude, req.delivery_latitude, req.delivery_longitude
    )
    assert dist_km is not None and 50.0 < dist_km < 80.0
    assert dist_stat == DistanceStatus.DISTANCE_GEODESIC

    _, dist_unavail = calculate_haversine_distance(None, None, 30.73, 76.77)
    assert dist_unavail == DistanceStatus.DISTANCE_UNAVAILABLE
    print(f"  OK: Geodesic distance calculated: {dist_km:.1f} km (Status: {dist_stat.value}).")

    # [9/16] Commercial Terms Representation
    print("\n[9/16] Testing Commercial Terms Representation...")
    assert req.price_basis == PriceBasis.FIXED_QUOTE
    assert req.quoted_price == 29.50
    assert req.price_unit == "INR_PER_KG"
    assert req.payment_terms == PaymentTerms.NET_3_DAYS
    print("  OK: Commercial terms represented with explicit units and payment horizons.")

    # [10/16] Demand Aggregation
    print("\n[10/16] Testing Demand Aggregation...")
    demands = [
        BuyerDemand(
            demand_id="d1",
            buyer_id="b1",
            commodity_id="tomato",
            quantity_kg=1000.0,
            quality_requirement="Grade_A",
            date_window_start=today,
            date_window_end=today + timedelta(days=7),
            location="Chandigarh",
        ),
        BuyerDemand(
            demand_id="d2",
            buyer_id="b2",
            commodity_id="tomato",
            quantity_kg=2500.0,
            quality_requirement="FAQ",
            date_window_start=today,
            date_window_end=today + timedelta(days=7),
            location="Panchkula",
        ),
        BuyerDemand(
            demand_id="d3",
            buyer_id="b3",
            commodity_id="tomato",
            quantity_kg=1500.0,
            quality_requirement="Grade_A",
            date_window_start=today,
            date_window_end=today + timedelta(days=7),
            location="Chandigarh",
        ),
    ]
    agg_res = DemandAggregationEngine.aggregate(demands, "tomato")
    assert agg_res.total_demand_kg == 5000.0
    assert agg_res.buyer_count == 3
    assert agg_res.demand_by_quality["Grade_A"] == 2500.0
    assert agg_res.demand_by_quality["FAQ"] == 2500.0
    assert agg_res.hhi_concentration is not None and agg_res.hhi_concentration > 0
    print(f"  OK: Aggregated demand: {agg_res.total_demand_kg:.1f} kg across {agg_res.buyer_count} buyers (HHI: {agg_res.hhi_concentration:.1f}).")

    # [11/16] Reliability Calculation with Sufficient History (N >= 3)
    print("\n[11/16] Testing Reliability Metrics (N >= 3)...")
    transactions = [
        BuyerTransactionRecord(
            transaction_id="tx_1",
            buyer_id="b_reliable",
            commodity_id="tomato",
            order_date=today - timedelta(days=30),
            agreed_quantity_kg=1000.0,
            delivered_quantity_kg=1000.0,
            agreed_price_per_kg=28.0,
            fulfillment_status="FULFILLED",
            payment_status="PAID_ON_TIME",
            agreed_payment_due_date=today - timedelta(days=23),
            actual_payment_date=today - timedelta(days=23),
            dispute_status=False,
        ),
        BuyerTransactionRecord(
            transaction_id="tx_2",
            buyer_id="b_reliable",
            commodity_id="tomato",
            order_date=today - timedelta(days=20),
            agreed_quantity_kg=1500.0,
            delivered_quantity_kg=1500.0,
            agreed_price_per_kg=28.5,
            fulfillment_status="FULFILLED",
            payment_status="PAID_LATE",
            agreed_payment_due_date=today - timedelta(days=13),
            actual_payment_date=today - timedelta(days=11),  # 2 days late
            dispute_status=False,
        ),
        BuyerTransactionRecord(
            transaction_id="tx_3",
            buyer_id="b_reliable",
            commodity_id="tomato",
            order_date=today - timedelta(days=10),
            agreed_quantity_kg=2000.0,
            delivered_quantity_kg=2000.0,
            agreed_price_per_kg=29.0,
            fulfillment_status="FULFILLED",
            payment_status="PAID_ON_TIME",
            agreed_payment_due_date=today - timedelta(days=3),
            actual_payment_date=today - timedelta(days=3),
            dispute_status=False,
        ),
    ]
    rel_metrics = BuyerReliabilityEngine.calculate("b_reliable", transactions)
    assert rel_metrics.status == ReliabilityStatus.CALCULATED
    assert rel_metrics.sample_size == 3
    assert rel_metrics.fulfillment_rate == 1.0
    assert rel_metrics.cancellation_rate == 0.0
    assert rel_metrics.average_payment_delay_days is not None and abs(rel_metrics.average_payment_delay_days - (2.0 / 3.0)) < 1e-4
    print(f"  OK: Empirical reliability calculated: FR={rel_metrics.fulfillment_rate:.2f}, Avg Delay={rel_metrics.average_payment_delay_days:.2f} days.")

    # [12/16] Insufficient History Handling
    print("\n[12/16] Testing Insufficient History Handling (N < 3 and N = 0)...")
    few_txs = transactions[:2]  # N = 2
    rel_few = BuyerReliabilityEngine.calculate("b_reliable", few_txs)
    assert rel_few.status == ReliabilityStatus.INSUFFICIENT_HISTORY
    assert rel_few.fulfillment_rate is None, "Should not emit fulfillment rate for N < 3"

    rel_zero = BuyerReliabilityEngine.calculate("b_unknown", [])
    assert rel_zero.status == ReliabilityStatus.UNAVAILABLE
    assert rel_zero.fulfillment_rate is None
    print("  OK: Insufficient sample size (N < 3) safely triggers INSUFFICIENT_HISTORY; N = 0 triggers UNAVAILABLE.")

    # [13/16] Provenance Propagation
    print("\n[13/16] Testing Provenance Propagation...")
    match_result = compat_engine.match(supply, req, reference_date=today)
    assert match_result.provenance.status == ProvenanceStatus.DEMO
    assert match_result.provenance.is_demo is True
    print("  OK: Provenance status DEMO correctly propagated through compatibility evaluation.")

    # [14/16] Demo Mode Disclosure
    print("\n[14/16] Testing Demo Mode Disclosure...")
    assert match_result.provenance.is_demo is True
    dict_res = match_result.to_dict()
    assert dict_res["provenance"]["status"] == "DEMO"
    assert dict_res["provenance"]["is_demo"] is True
    print("  OK: Serialization explicitly tags demo fixtures with is_demo: True.")

    # [15/16] Demand Distribution Sufficiency Gating
    print("\n[15/16] Testing Demand Distribution Sufficiency...")
    dist_valid = DemandAggregationEngine.calculate_distribution(demands, "tomato")
    assert dist_valid.status == DistributionStatus.VALID
    assert dist_valid.min_kg == 1000.0
    assert dist_valid.max_kg == 2500.0
    assert dist_valid.median_kg == 1500.0

    dist_under = DemandAggregationEngine.calculate_distribution(demands[:2], "tomato")
    assert dist_under.status == DistributionStatus.INSUFFICIENT_DATA
    assert dist_under.median_kg is None
    print("  OK: Distribution calculation gates on N >= 3; returns INSUFFICIENT_DATA for N = 2.")

    # [16/16] Recommendation-Leakage Guard
    print("\n[16/16] Testing Strict Absence of Recommendation Terms...")
    forbidden_terms = [
        "SELL NOW",
        "SELL",
        "HOLD",
        "BUY",
        "BEST BUYER",
        "BEST MARKET",
        "WINNER",
        "RECOMMENDED BUYER",
        "RECOMMENDED MARKET",
        "RECOMMENDED ACTION",
        "OPTIMAL BUYER",
        "OPTIMAL SELLING PLAN",
    ]
    res_str = str(dict_res).upper()
    for term in forbidden_terms:
        # Check that forbidden recommendation terms do not appear as decisions
        assert term not in dict_res, f"Forbidden key '{term}' found in CompatibilityResult dictionary"
        assert f"'{term}'" not in res_str, f"Forbidden term '{term}' found in serialized output"
    print("  OK: Zero recommendation advice or ranking terms present in compatibility output.")

    print("\n" + "=" * 60)
    print("STEP 12 SMOKE TEST COMPLETE: ALL 16 STAGES PASSED CLEANLY.")
    print("=" * 60)


if __name__ == "__main__":
    run_smoke_test()
