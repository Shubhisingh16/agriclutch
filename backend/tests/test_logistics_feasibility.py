"""
Unit Tests for AgriClutch Logistics Feasibility Evaluator.
Verifies multi-dimensional physical constraint evaluations: capacity, distance,
timing windows, and data sufficiency without ranking or recommendations.
SIH26132 — Strengthening Market Linkages and Price Discovery for Farmers.
"""

from datetime import date, timedelta

import pytest

from ml.logistics import (
    Destination,
    DistanceType,
    FeasibilityStatus,
    LogisticsFeasibilityEvaluator,
    ProduceInput,
    TransitTimeStatus,
    TransportModeSpec,
)


@pytest.fixture
def sample_produce() -> ProduceInput:
    today = date(2026, 9, 15)
    return ProduceInput(
        produce_id="LOT_FEAS_01",
        commodity_id="tomato",
        quantity_kg=3000.0,
        quality_grade="GRADE_A",
        origin_location="Kalka Farm",
        origin_latitude=30.8350,
        origin_longitude=76.9350,
        available_from=today,
        available_until=today + timedelta(days=5),
    )


def test_feasibility_over_capacity_partial(sample_produce: ProduceInput) -> None:
    # Vehicle capacity = 2500 kg < Produce 3000 kg
    lcv = TransportModeSpec(
        mode_id="DEMO_LCV_TATA_407",
        display_name="LCV",
        vehicle_type="LCV",
        capacity_kg=2500.0,
        base_dispatch_fee=800.0,
        cost_per_km=25.0,
        speed_kmh=45.0,
    )
    dest = Destination(
        destination_id="DEST_01",
        name="Test Dest",
        destination_type="BUYER",
        location="Mohali",
    )
    res = LogisticsFeasibilityEvaluator.evaluate(
        produce=sample_produce,
        destination=dest,
        transport_mode=lcv,
        distance_km=30.0,
        distance_type=DistanceType.ROAD_DISTANCE,
        transit_duration_hours=1.0,
        transit_time_status=TransitTimeStatus.CONFIGURED,
    )
    assert res.status == FeasibilityStatus.PARTIALLY_FEASIBLE
    assert res.transportable_quantity_kg == 2500.0
    assert res.untransportable_quantity_kg == 500.0


def test_feasibility_exceeding_max_acceptable_distance(sample_produce: ProduceInput) -> None:
    truck = TransportModeSpec(
        mode_id="DEMO_TRUCK",
        display_name="Truck",
        vehicle_type="HEAVY_TRUCK",
        capacity_kg=10000.0,
        base_dispatch_fee=2500.0,
        cost_per_km=55.0,
        speed_kmh=40.0,
    )
    dest_constrained = Destination(
        destination_id="DEST_NEAR",
        name="Local Mandi",
        destination_type="MANDI",
        location="Local Yard",
        max_acceptable_distance_km=50.0,
    )
    # Actual distance 80 km > max 50 km
    res = LogisticsFeasibilityEvaluator.evaluate(
        produce=sample_produce,
        destination=dest_constrained,
        transport_mode=truck,
        distance_km=80.0,
        distance_type=DistanceType.ROAD_DISTANCE,
        transit_duration_hours=2.0,
        transit_time_status=TransitTimeStatus.CONFIGURED,
    )
    assert res.status == FeasibilityStatus.INFEASIBLE
    assert any("exceeds destination max acceptable distance" in f for f in res.failed_constraints)


def test_feasibility_unknown_distance_insufficient_data(sample_produce: ProduceInput) -> None:
    lcv = TransportModeSpec(
        mode_id="DEMO_LCV",
        display_name="LCV",
        vehicle_type="LCV",
        capacity_kg=5000.0,
        base_dispatch_fee=800.0,
    )
    dest = Destination(
        destination_id="DEST_01",
        name="Test Dest",
        destination_type="BUYER",
        location="Unknown",
    )
    res = LogisticsFeasibilityEvaluator.evaluate(
        produce=sample_produce,
        destination=dest,
        transport_mode=lcv,
        distance_km=None,
        distance_type=DistanceType.UNKNOWN_DISTANCE,
        transit_duration_hours=None,
        transit_time_status=TransitTimeStatus.TRANSIT_TIME_UNAVAILABLE,
    )
    assert res.status == FeasibilityStatus.INSUFFICIENT_DATA
