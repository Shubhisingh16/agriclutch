"""
Integration Tests for AgriClutch Logistics, Storage & Perishability REST API Endpoints.
Verifies response schemas, demo headers, and data integrity.
SIH26132 — Strengthening Market Linkages and Price Discovery for Farmers.
"""

from unittest.mock import AsyncMock

import pytest
from app.db.session import get_db
from app.main import app
from httpx import ASGITransport, AsyncClient


@pytest.fixture
def mock_db_session() -> AsyncMock:
    return AsyncMock()


@pytest.mark.asyncio
async def test_list_transport_modes_api(mock_db_session: AsyncMock) -> None:
    app.dependency_overrides[get_db] = lambda: mock_db_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/logistics/modes")
        assert resp.status_code == 200
        assert resp.headers["X-AgriClutch-Step"] == "13"
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 4
        vehicle_types = [m["vehicle_type"] for m in data]
        assert "TRACTOR_TROLLEY" in vehicle_types
        assert "LCV" in vehicle_types
        assert "REEFER" in vehicle_types


@pytest.mark.asyncio
async def test_calculate_distance_api() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "origin_lat": 30.8350,
            "origin_lon": 76.9350,
            "dest_lat": 30.7050,
            "dest_lon": 76.7900,
            "speed_kmh": 40.0,
        }
        resp = await client.post("/api/v1/logistics/distance", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["distance_km"] > 0
        assert data["distance_type"] == "ESTIMATED_ROUTE_DISTANCE"
        assert data["straight_line_distance_km"] > 0
        assert data["circuity_factor"] == 1.25
        assert data["transit_duration_hours"] > 0


@pytest.mark.asyncio
async def test_evaluate_pathways_api(mock_db_session: AsyncMock) -> None:
    app.dependency_overrides[get_db] = lambda: mock_db_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "commodity_id": "tomato",
            "quantity_kg": 2500.0,
            "quality_grade": "GRADE_A",
            "origin_location": "Kalka Farm Gate",
            "origin_latitude": 30.8350,
            "origin_longitude": 76.9350,
            "available_from": "2026-09-15",
            "available_until": "2026-09-25",
            "storage_duration_days": 7,
        }
        resp = await client.post("/api/v1/logistics/evaluate", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert "lot_summary" in data
        assert "scenarios" in data
        assert len(data["scenarios"]) == 4  # Scenarios A, B, C, D
        assert data["economic_status"] == "DEMO_ASSUMPTION"


@pytest.mark.asyncio
async def test_storage_facilities_api(mock_db_session: AsyncMock) -> None:
    app.dependency_overrides[get_db] = lambda: mock_db_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/storage/facilities")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 4
        fac_ids = [f["id"] for f in data]
        assert "DEMO_COLD_STORAGE_NORTH" in fac_ids
        assert "DEMO_WAREHOUSE_MOHALI" in fac_ids

        # Availability
        avail_resp = await client.get("/api/v1/storage/facilities/DEMO_COLD_STORAGE_NORTH/availability")
        assert avail_resp.status_code == 200
        avail_data = avail_resp.json()
        assert avail_data["available_capacity_kg"] > 0
        assert avail_data["is_available"] is True


@pytest.mark.asyncio
async def test_perishability_api() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Models
        resp_models = await client.get("/api/v1/perishability/models")
        assert resp_models.status_code == 200
        models_data = resp_models.json()
        assert len(models_data) >= 6

        # Trajectory
        resp_traj = await client.get(
            "/api/v1/perishability/trajectory?commodity_id=tomato&storage_type=AMBIENT&initial_quantity_kg=1000&duration_days=5"
        )
        assert resp_traj.status_code == 200
        traj_data = resp_traj.json()
        assert traj_data["status"] == "CALCULATED"
        assert len(traj_data["trajectory"]) == 6
        assert traj_data["final_quantity_kg"] < 1000.0
