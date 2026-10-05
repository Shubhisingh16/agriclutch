"""
AgriClutch Logistics + Storage + Perishability 15-Stage Smoke Test.
Verifies all mathematical models, physical constraints, and contract integrity.
Strictly verifies ZERO recommendation or ranking leakage.
Run with: python -m ml.logistics.smoke_test
"""

import math
from datetime import date, timedelta

from ml.logistics import (
    Destination,
    DistanceEngine,
    DistanceType,
    EconomicStatus,
    FeasibilityStatus,
    LogisticsCostEngine,
    LogisticsFeasibilityEvaluator,
    LogisticsScenarioComposer,
    PerishabilityEngine,
    ProduceInput,
    ProvenanceStatus,
    StorageEngine,
    StorageFacility,
    StorageType,
    TransitTimeStatus,
    TransportModeSpec,
)


def run_15_stage_smoke_test() -> None:
    print("=" * 70)
    print("AGRICLUTCH STEP 13 -- LOGISTICS & STORAGE 15-STAGE SMOKE TEST")
    print("=" * 70)

    # ----------------------------------------------------
    # Stage 1: Contracts instantiation and to_dict() serialization
    # ----------------------------------------------------
    print("[Stage 1] Verifying Contracts & Serialization...")
    today = date(2026, 9, 15)
    produce = ProduceInput(
        produce_id="LOT_SMOKE_01",
        commodity_id="tomato",
        quantity_kg=2500.0,
        quality_grade="GRADE_A",
        origin_location="Kalka Farm Gate",
        available_from=today,
        available_until=today + timedelta(days=5),
        origin_latitude=30.8350,
        origin_longitude=76.9350,
        initial_quality_factor=1.0,
    )
    p_dict = produce.to_dict()
    assert p_dict["produce_id"] == "LOT_SMOKE_01"
    assert p_dict["quantity_kg"] == 2500.0
    print("  [PASS] Stage 1 Passed: ProduceInput instantiated and serialized.")

    # ----------------------------------------------------
    # Stage 2: Geodesic Haversine calculation
    # ----------------------------------------------------
    print("[Stage 2] Verifying Geodesic Haversine Calculation...")
    # Distance between Kalka (30.8350, 76.9350) and Chandigarh APMC (30.7050, 76.7900)
    dist = DistanceEngine.haversine_distance(30.8350, 76.9350, 30.7050, 76.7900)
    assert 18.0 <= dist <= 25.0, f"Unexpected distance: {dist} km"
    # Same point distance must be 0
    zero_dist = DistanceEngine.haversine_distance(30.8350, 76.9350, 30.8350, 76.9350)
    assert zero_dist == 0.0
    print(f"  [PASS] Stage 2 Passed: Haversine distance Kalka to Chandigarh = {dist:.2f} km.")

    # ----------------------------------------------------
    # Stage 3: Road distance vs straight-line distance resolution
    # ----------------------------------------------------
    print("[Stage 3] Verifying Road vs Straight-Line Distance Resolution...")
    dist_road, d_type_road = DistanceEngine.resolve_route_distance(
        30.8350, 76.9350, 30.7050, 76.7900, road_distance_km=28.5
    )
    assert dist_road == 28.5
    assert d_type_road == DistanceType.ROAD_DISTANCE

    dist_sl, d_type_sl = DistanceEngine.resolve_route_distance(
        30.8350, 76.9350, 30.7050, 76.7900, road_distance_km=None
    )
    assert dist_sl is not None and dist_sl > 0
    assert d_type_sl == DistanceType.STRAIGHT_LINE_DISTANCE
    print("  [PASS] Stage 3 Passed: Distance resolution correctly differentiates road vs straight-line.")

    # ----------------------------------------------------
    # Stage 4: Coordinate out-of-range rejection
    # ----------------------------------------------------
    print("[Stage 4] Verifying Coordinate Validation...")
    try:
        DistanceEngine.haversine_distance(95.0, 76.9, 30.7, 76.7)
        raise AssertionError("Should have rejected invalid latitude 95.0")
    except ValueError:
        pass
    try:
        DistanceEngine.haversine_distance(30.7, 195.0, 30.7, 76.7)
        raise AssertionError("Should have rejected invalid longitude 195.0")
    except ValueError:
        pass
    print("  [PASS] Stage 4 Passed: Out-of-bounds coordinates strictly rejected.")

    # ----------------------------------------------------
    # Stage 5: Transit time calculation and speed edge cases
    # ----------------------------------------------------
    print("[Stage 5] Verifying Transit Time Calculation...")
    transit_h, t_status = DistanceEngine.calculate_transit_time(distance_km=100.0, speed_kmh=50.0)
    assert transit_h == 2.0
    assert t_status == TransitTimeStatus.CONFIGURED

    transit_none, t_none_status = DistanceEngine.calculate_transit_time(distance_km=100.0, speed_kmh=None)
    assert transit_none is None
    assert t_none_status == TransitTimeStatus.TRANSIT_TIME_UNAVAILABLE
    print("  [PASS] Stage 5 Passed: Transit duration evaluated with explicit status.")

    # ----------------------------------------------------
    # Stage 6: Cost decomposition into components
    # ----------------------------------------------------
    print("[Stage 6] Verifying Logistics Cost Decomposition...")
    lcv = TransportModeSpec(
        mode_id="DEMO_LCV_TATA_407",
        display_name="Light Commercial Vehicle (LCV)",
        vehicle_type="LCV",
        capacity_kg=2500.0,
        base_dispatch_fee=800.0,
        cost_per_km=25.0,
        speed_kmh=45.0,
    )
    cost_breakdown = LogisticsCostEngine.calculate_cost_breakdown(
        transport_mode=lcv,
        quantity_kg=2000.0,  # 20 quintals
        distance_km=40.0,
        loading_fee_per_quintal=12.0,  # 20 * 12 = 240
        unloading_fee_per_quintal=10.0,  # 20 * 10 = 200
        extra_handling_fee=150.0,
        is_demo=True,
    )
    # Expected:
    # Base: 800
    # Transport (Distance): 40 * 25 = 1000
    # Loading: 20 * 12 = 240
    # Unloading: 20 * 10 = 200
    # Extra Handling: 150
    # Total = 800 + 1000 + 240 + 200 + 150 = 2390
    assert math.isclose(cost_breakdown.transport_cost, 1800.0, rel_tol=1e-3), f"Transport cost: {cost_breakdown.transport_cost}"
    assert math.isclose(cost_breakdown.loading_cost, 240.0, rel_tol=1e-3)
    assert math.isclose(cost_breakdown.unloading_cost, 200.0, rel_tol=1e-3)
    assert math.isclose(cost_breakdown.handling_cost, 150.0, rel_tol=1e-3)
    assert math.isclose(cost_breakdown.total_cost, 2390.0, rel_tol=1e-3)
    assert cost_breakdown.economic_status == EconomicStatus.DEMO_ASSUMPTION
    print("  [PASS] Stage 6 Passed: Cost arithmetic additive and provenance verified.")

    # ----------------------------------------------------
    # Stage 7: Zero-distance & Zero-handling edge cases
    # ----------------------------------------------------
    print("[Stage 7] Verifying Zero Distance & Minimal Fee Edge Cases...")
    cost_zero = LogisticsCostEngine.calculate_cost_breakdown(
        transport_mode=lcv,
        quantity_kg=1000.0,
        distance_km=0.0,
        loading_fee_per_quintal=0.0,
        unloading_fee_per_quintal=0.0,
        extra_handling_fee=0.0,
    )
    assert math.isclose(cost_zero.transport_cost, 800.0, rel_tol=1e-3)
    assert cost_zero.loading_cost == 0.0
    assert cost_zero.unloading_cost == 0.0
    assert cost_zero.total_cost == 800.0
    print("  [PASS] Stage 7 Passed: Zero distance and fee edges handled properly.")

    # ----------------------------------------------------
    # Stage 8: Storage capacity partition into stored vs unstored
    # ----------------------------------------------------
    print("[Stage 8] Verifying Storage Capacity Allocation...")
    storage_fac = StorageFacility(
        facility_id="DEMO_WAREHOUSE_MOHALI",
        name="Mohali Demo Warehouse",
        storage_type=StorageType.VENTILATED,
        location="Mohali",
        capacity_kg=50000.0,
        available_capacity_kg=1500.0,  # Only 1500 kg available
        cost_per_kg_day=0.15,
        min_duration_days=2,
        max_duration_days=60,
    )
    storage_eval = StorageEngine.evaluate_storage(
        facility=storage_fac,
        requested_quantity_kg=2500.0,
        requested_duration_days=10,
    )
    assert storage_eval.stored_quantity_kg == 1500.0
    assert storage_eval.unstored_quantity_kg == 1000.0
    assert storage_eval.status == FeasibilityStatus.PARTIALLY_FEASIBLE
    assert math.isclose(storage_eval.storage_cost, 1500.0 * 10 * 0.15, rel_tol=1e-3)
    print("  [PASS] Stage 8 Passed: Partial storage capacity partitioned without rounding away shortfall.")

    # ----------------------------------------------------
    # Stage 9: Storage duration bounds checking
    # ----------------------------------------------------
    print("[Stage 9] Verifying Storage Duration Bounds...")
    storage_eval_over = StorageEngine.evaluate_storage(
        facility=storage_fac,
        requested_quantity_kg=1000.0,
        requested_duration_days=70,  # Exceeds max 60
    )
    assert storage_eval_over.status == FeasibilityStatus.INFEASIBLE
    assert any("exceeds facility maximum" in w for w in storage_eval_over.warnings)
    print("  [PASS] Stage 9 Passed: Storage duration limits strictly enforced.")

    # ----------------------------------------------------
    # Stage 10: Decoupled perishability exponential equations
    # ----------------------------------------------------
    print("[Stage 10] Verifying Decoupled Perishability Equations...")
    # Formula: S(t) = exp(-delta * t), F(t) = F0 * exp(-beta * t)
    s_val = PerishabilityEngine.calculate_decay_survival(decay_parameter_delta=0.035, days=5)
    expected_s = math.exp(-0.035 * 5)
    assert math.isclose(s_val, expected_s, rel_tol=1e-5)

    q_val = PerishabilityEngine.calculate_quality_factor(
        initial_quality_factor=1.0, quality_decay_beta=0.050, days=5
    )
    expected_q = 1.0 * math.exp(-0.050 * 5)
    assert math.isclose(q_val, expected_q, rel_tol=1e-5)
    print(f"  [PASS] Stage 10 Passed: S(5) = {s_val:.4f}, F_qual(5) = {q_val:.4f} strictly match equations.")

    # ----------------------------------------------------
    # Stage 11: Trajectory generation for benchmark commodities
    # ----------------------------------------------------
    print("[Stage 11] Verifying Commodity Trajectory Generation...")
    for crop in ["tomato", "onion", "potato"]:
        traj_ambient = PerishabilityEngine.calculate_trajectory(
            commodity_id=crop,
            storage_type=StorageType.AMBIENT,
            initial_quantity_kg=1000.0,
            duration_days=7,
        )
        assert traj_ambient.status == "CALCULATED"
        assert len(traj_ambient.trajectory) == 8  # Day 0 to 7
        assert traj_ambient.final_quantity_kg < 1000.0
        assert traj_ambient.final_quality_factor < 1.0

        traj_cold = PerishabilityEngine.calculate_trajectory(
            commodity_id=crop,
            storage_type=StorageType.COLD,
            initial_quantity_kg=1000.0,
            duration_days=7,
        )
        assert traj_cold.final_quantity_kg > traj_ambient.final_quantity_kg  # Cold preserves better
    print("  [PASS] Stage 11 Passed: Trajectories verified for Tomato, Onion, Potato in Ambient and Cold.")

    # ----------------------------------------------------
    # Stage 12: Unsupported crop fail-closed behavior
    # ----------------------------------------------------
    print("[Stage 12] Verifying Unsupported Commodity Fail-Closed Behavior...")
    traj_unknown = PerishabilityEngine.calculate_trajectory(
        commodity_id="exotic_dragonfruit",
        storage_type=StorageType.AMBIENT,
        initial_quantity_kg=500.0,
        duration_days=5,
    )
    assert traj_unknown.status == "LOSS_MODEL_UNAVAILABLE"
    assert traj_unknown.model_spec is None
    assert traj_unknown.final_quantity_kg == 500.0  # Zero unmodeled decay claimed
    assert traj_unknown.provenance.status == ProvenanceStatus.UNAVAILABLE
    print("  [PASS] Stage 12 Passed: Unknown commodity cleanly defaults to LOSS_MODEL_UNAVAILABLE.")

    # ----------------------------------------------------
    # Stage 13: Multi-stage scenarios composition
    # ----------------------------------------------------
    print("[Stage 13] Verifying Multi-Stage Scenario Composition (A, B, C, D)...")
    dest_buyer = Destination(
        destination_id="DEMO_BUYER_PUNJAB_RETAIL",
        name="Punjab Fresh Mart Hub",
        destination_type="BUYER",
        location="Mohali Sector 82",
        latitude=30.6800,
        longitude=76.7200,
    )
    dest_mandi = Destination(
        destination_id="MANDI_CHD_APMC",
        name="Chandigarh APMC Yard",
        destination_type="MANDI",
        location="Sector 26, Chandigarh",
        latitude=30.7250,
        longitude=76.8000,
    )
    cold_storage = StorageFacility(
        facility_id="DEMO_COLD_STORAGE_NORTH",
        name="Demo Northern Cold Chain Terminal",
        storage_type=StorageType.COLD,
        location="Zirakpur",
        capacity_kg=200000.0,
        available_capacity_kg=50000.0,
        cost_per_kg_day=0.25,
        latitude=30.6400,
        longitude=76.8200,
        min_duration_days=3,
        max_duration_days=90,
    )

    scen_a = LogisticsScenarioComposer.build_scenario_a(
        produce=produce,
        destination=dest_buyer,
        transport_mode=lcv,
        road_distance_km=32.0,
    )
    scen_b = LogisticsScenarioComposer.build_scenario_b(
        produce=produce,
        destination=dest_buyer,
        storage_facility=storage_fac,
        transport_mode=lcv,
        storage_duration_days=7,
        road_distance_km=35.0,
    )
    scen_c = LogisticsScenarioComposer.build_scenario_c(
        produce=produce,
        mandi_destination=dest_mandi,
        transport_mode=lcv,
        road_distance_km=22.0,
    )
    scen_d = LogisticsScenarioComposer.build_scenario_d(
        produce=produce,
        destination=dest_buyer,
        cold_storage_facility=cold_storage,
        transport_mode=lcv,
        storage_duration_days=14,
        road_distance_km=40.0,
    )

    assert scen_a.storage_duration_days == 0
    assert scen_a.total_elapsed_hours > 0
    assert scen_b.storage_duration_days == 7
    assert scen_b.storage_cost > 0
    assert scen_c.storage_facility is None
    assert scen_d.storage_facility is not None
    assert scen_d.storage_facility.storage_type == StorageType.COLD
    print("  [PASS] Stage 13 Passed: Scenarios A, B, C, D composed with physical elapsed hours and costs.")

    # ----------------------------------------------------
    # Stage 14: Logistics feasibility evaluation
    # ----------------------------------------------------
    print("[Stage 14] Verifying Logistics Feasibility Evaluator...")
    # Over-capacity vehicle test
    tractor = TransportModeSpec(
        mode_id="DEMO_TRACTOR",
        display_name="Tractor Trolley",
        vehicle_type="TRACTOR_TROLLEY",
        capacity_kg=1500.0,  # 1500 kg < produce 2500 kg
        base_dispatch_fee=500.0,
        cost_per_km=18.0,
        speed_kmh=25.0,
    )
    feas_partial = LogisticsFeasibilityEvaluator.evaluate(
        produce=produce,
        destination=dest_buyer,
        transport_mode=tractor,
        distance_km=30.0,
        distance_type=DistanceType.ROAD_DISTANCE,
        transit_duration_hours=1.2,
        transit_time_status=TransitTimeStatus.CONFIGURED,
    )
    assert feas_partial.status == FeasibilityStatus.PARTIALLY_FEASIBLE
    assert feas_partial.transportable_quantity_kg == 1500.0
    assert feas_partial.untransportable_quantity_kg == 1000.0
    print("  [PASS] Stage 14 Passed: Feasibility evaluator detects capacity shortfalls correctly.")

    # ----------------------------------------------------
    # Stage 15: Strict Recommendation-Leakage Audit
    # ----------------------------------------------------
    print("[Stage 15] Verifying Strict Absence of Recommendation Leakage...")
    forbidden_terms = [
        "winner",
        "rank",
        "ranking",
        "recommended",
        "recommended_action",
        "recommended_buyer",
        "recommended_market",
        "best",
        "is_best",
        "optimal",
        "score",
        "score_total",
        "sell",
        "hold",
    ]
    # Check scenario dict
    scen_dict = scen_a.to_dict()
    for term in forbidden_terms:
        assert term not in scen_dict, f"Recommendation term '{term}' leaked into scenario contract!"
        assert f"is_{term}" not in scen_dict, f"Recommendation term 'is_{term}' leaked into scenario contract!"

    # Check feasibility dict
    feas_dict = feas_partial.to_dict()
    for term in forbidden_terms:
        assert term not in feas_dict, f"Recommendation term '{term}' leaked into feasibility contract!"

    print("  [PASS] Stage 15 Passed: Zero recommendation or ranking terms leaked into Step 13 contracts.")
    print("=" * 70)
    print("ALL 15 SMOKE TEST STAGES PASSED SUCCESSFULLY!")
    print("=" * 70)


if __name__ == "__main__":
    run_15_stage_smoke_test()
