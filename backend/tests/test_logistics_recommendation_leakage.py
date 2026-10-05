"""
Strict Recommendation-Leakage Audit Tests for Step 13.
Verifies that Step 13 remains purely factual and never outputs recommendations,
rankings, scores, or winner selections.
SIH26132 — Strengthening Market Linkages and Price Discovery for Farmers.
"""

from datetime import date, timedelta

import pytest
from app.main import app
from httpx import ASGITransport, AsyncClient

from ml.logistics import (
    Destination,
    DistanceType,
    LogisticsFeasibilityEvaluator,
    LogisticsScenarioComposer,
    ProduceInput,
    TransitTimeStatus,
    TransportModeSpec,
)

FORBIDDEN_RECOMMENDATION_TERMS = [
    "best_route",
    "preferred_route",
    "selected_route",
    "optimal_route",
    "recommended_route",
    "winner",
    "rank",
    "rank_score",
    "priority_score",
    "recommendation_score",
    "is_best",
    "is_preferred",
    "is_selected",
    "ranking",
    "recommended",
    "recommended_action",
    "recommended_buyer",
    "recommended_market",
    "best",
    "optimal",
    "score",
    "score_total",
    "sell",
    "hold",
]


def test_scenario_contract_no_recommendation_fields() -> None:
    today = date(2026, 9, 15)
    produce = ProduceInput(
        produce_id="LOT_AUDIT_01",
        commodity_id="tomato",
        quantity_kg=2000.0,
        quality_grade="GRADE_A",
        origin_location="Kalka Farm",
        origin_latitude=30.8350,
        origin_longitude=76.9350,
        available_from=today,
        available_until=today + timedelta(days=5),
    )
    dest = Destination(
        destination_id="DEST_AUDIT",
        name="Test Dest",
        destination_type="BUYER",
        location="Mohali",
        latitude=30.6800,
        longitude=76.7200,
    )
    mode = TransportModeSpec(
        mode_id="DEMO_LCV",
        display_name="LCV",
        vehicle_type="LCV",
        capacity_kg=2500.0,
        base_dispatch_fee=800.0,
        cost_per_km=25.0,
        speed_kmh=45.0,
    )

    scenario = LogisticsScenarioComposer.build_scenario_a(
        produce=produce,
        destination=dest,
        transport_mode=mode,
        road_distance_km=30.0,
    )

    scen_dict = scenario.to_dict()
    for term in FORBIDDEN_RECOMMENDATION_TERMS:
        assert term not in scen_dict, f"Forbidden term '{term}' leaked into scenario dictionary"
        assert f"is_{term}" not in scen_dict, f"Forbidden term 'is_{term}' leaked into scenario dictionary"


def test_feasibility_contract_no_recommendation_fields() -> None:
    today = date(2026, 9, 15)
    produce = ProduceInput(
        produce_id="LOT_AUDIT_02",
        commodity_id="onion",
        quantity_kg=1500.0,
        quality_grade="GRADE_A",
        origin_location="Panchkula",
        available_from=today,
        available_until=today + timedelta(days=7),
    )
    dest = Destination(
        destination_id="DEST_AUDIT_2",
        name="Test Mandi",
        destination_type="MANDI",
        location="Chandigarh",
    )
    mode = TransportModeSpec(
        mode_id="DEMO_TRACTOR",
        display_name="Tractor",
        vehicle_type="TRACTOR_TROLLEY",
        capacity_kg=2000.0,
        base_dispatch_fee=500.0,
    )

    feas = LogisticsFeasibilityEvaluator.evaluate(
        produce=produce,
        destination=dest,
        transport_mode=mode,
        distance_km=20.0,
        distance_type=DistanceType.ROAD_DISTANCE,
        transit_duration_hours=0.8,
        transit_time_status=TransitTimeStatus.CONFIGURED,
    )

    feas_dict = feas.to_dict()
    for term in FORBIDDEN_RECOMMENDATION_TERMS:
        assert term not in feas_dict, f"Forbidden term '{term}' leaked into feasibility dictionary"


@pytest.mark.asyncio
async def test_api_evaluate_response_no_recommendation_fields() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "commodity_id": "tomato",
            "quantity_kg": 2000.0,
            "quality_grade": "GRADE_A",
            "origin_location": "Kalka Farm Gate",
            "available_from": "2026-09-15",
            "available_until": "2026-09-25",
        }
        resp = await client.post("/api/v1/logistics/evaluate", json=payload)
        assert resp.status_code == 200
        data = resp.json()

        for term in FORBIDDEN_RECOMMENDATION_TERMS:
            assert term not in data, f"Forbidden term '{term}' leaked in evaluate response root"

        for sc in data.get("scenarios", []):
            for term in FORBIDDEN_RECOMMENDATION_TERMS:
                assert term not in sc, f"Forbidden term '{term}' leaked in scenario item"
