"""
Unit Tests for AgriClutch Logistics Scenario Composer.
Verifies multi-stage pathways (Scenarios A through D), cumulative elapsed duration,
stage loss compounding, and transparent cost aggregation.
SIH26132 — Strengthening Market Linkages and Price Discovery for Farmers.
"""

from datetime import date, timedelta

import pytest

from ml.logistics import (
    Destination,
    LogisticsScenarioComposer,
    ProduceInput,
    StorageFacility,
    StorageType,
    TransportModeSpec,
)


@pytest.fixture
def sample_produce() -> ProduceInput:
    today = date(2026, 9, 15)
    return ProduceInput(
        produce_id="LOT_TEST_01",
        commodity_id="tomato",
        quantity_kg=2000.0,
        quality_grade="GRADE_A",
        origin_location="Kalka Farm",
        origin_latitude=30.8350,
        origin_longitude=76.9350,
        available_from=today,
        available_until=today + timedelta(days=10),
    )


@pytest.fixture
def sample_mode() -> TransportModeSpec:
    return TransportModeSpec(
        mode_id="DEMO_LCV_TATA_407",
        display_name="Light Commercial Vehicle (LCV)",
        vehicle_type="LCV",
        capacity_kg=2500.0,
        base_dispatch_fee=800.0,
        cost_per_km=25.0,
        speed_kmh=45.0,
    )


@pytest.fixture
def sample_destination() -> Destination:
    return Destination(
        destination_id="DEST_BUYER_PUNJAB",
        name="Punjab Fresh Mart",
        destination_type="BUYER",
        location="Mohali Sector 82",
        latitude=30.6800,
        longitude=76.7200,
    )


@pytest.fixture
def sample_cold_storage() -> StorageFacility:
    return StorageFacility(
        facility_id="DEMO_COLD_STORAGE_NORTH",
        name="Demo Northern Cold Chain Terminal",
        storage_type=StorageType.COLD,
        location="Zirakpur",
        capacity_kg=200000.0,
        available_capacity_kg=50000.0,
        cost_per_kg_day=0.25,
        min_duration_days=3,
        max_duration_days=90,
    )


def test_scenario_a_direct_buyer(
    sample_produce: ProduceInput,
    sample_destination: Destination,
    sample_mode: TransportModeSpec,
) -> None:
    scen = LogisticsScenarioComposer.build_scenario_a(
        produce=sample_produce,
        destination=sample_destination,
        transport_mode=sample_mode,
        road_distance_km=35.0,
    )
    assert scen.storage_duration_days == 0
    assert scen.storage_facility is None
    assert scen.total_elapsed_hours > 0
    assert scen.effective_delivered_quantity_kg <= sample_produce.quantity_kg
    assert scen.total_pathway_cost == scen.logistics_cost.total_cost
    assert scen.storage_cost == 0.0


def test_scenario_d_cold_storage_pathway(
    sample_produce: ProduceInput,
    sample_destination: Destination,
    sample_cold_storage: StorageFacility,
    sample_mode: TransportModeSpec,
) -> None:
    scen = LogisticsScenarioComposer.build_scenario_d(
        produce=sample_produce,
        destination=sample_destination,
        cold_storage_facility=sample_cold_storage,
        transport_mode=sample_mode,
        storage_duration_days=14,
        road_distance_km=40.0,
    )
    assert scen.storage_duration_days == 14
    assert scen.storage_facility is not None
    assert scen.storage_facility.storage_type == StorageType.COLD
    assert scen.storage_cost > 0.0
    assert scen.total_pathway_cost == scen.logistics_cost.total_cost + scen.storage_cost
    assert scen.perishability is not None
    assert scen.perishability.storage_type == StorageType.COLD
