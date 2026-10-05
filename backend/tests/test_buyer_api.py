"""
Integration Tests for AgriClutch Buyer REST API Endpoints.
Verifies response schemas, filtering, demo headers, fail-closed database mode,
and zero recommendation leakage.
SIH26132 — Strengthening Market Linkages and Price Discovery for Farmers.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from app.config import settings
from app.db.session import get_db
from app.main import app
from httpx import ASGITransport, AsyncClient


@pytest.fixture
def mock_db_session() -> AsyncMock:
    return AsyncMock()


@pytest.mark.asyncio
async def test_list_buyers_demo_mode(mock_db_session: AsyncMock) -> None:
    """Verifies listing registered buyers in demo mode with appropriate headers."""
    app.dependency_overrides[get_db] = lambda: mock_db_session
    original_mode = settings.DATA_MODE
    settings.DATA_MODE = "demo"

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/v1/buyers")
            assert resp.status_code == 200
            assert resp.headers["X-AgriClutch-Data-Mode"] == "DEMO"
            assert resp.headers["X-AgriClutch-DataSource"] == "DEMO_BENCHMARK_SEED"

            data = resp.json()
            assert isinstance(data, list)
            assert len(data) >= 6

            buyer_ids = [b["id"] for b in data]
            assert "buyer_wholesaler_ch" in buyer_ids
            assert "buyer_processor_delhi" in buyer_ids

            # Test filtering by buyer_type
            resp_type = await client.get("/api/v1/buyers", params={"buyer_type": "processor"})
            assert resp_type.status_code == 200
            data_type = resp_type.json()
            assert all(b["buyer_type"] == "processor" for b in data_type)

    finally:
        settings.DATA_MODE = original_mode
        app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_get_buyer_detail_and_404(mock_db_session: AsyncMock) -> None:
    """Verifies single buyer profile retrieval and 404 for nonexistent ID."""
    app.dependency_overrides[get_db] = lambda: mock_db_session
    original_mode = settings.DATA_MODE
    settings.DATA_MODE = "demo"

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/v1/buyers/buyer_wholesaler_ch")
            assert resp.status_code == 200
            data = resp.json()
            assert data["id"] == "buyer_wholesaler_ch"
            assert data["provenance_status"] == "DEMO"
            assert data["is_demo"] is True

            # 404 for unknown buyer
            resp_404 = await client.get("/api/v1/buyers/nonexistent_buyer")
            assert resp_404.status_code == 404
    finally:
        settings.DATA_MODE = original_mode
        app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_buyer_requirements_and_demands(mock_db_session: AsyncMock) -> None:
    """Verifies procurement requirements and active demands endpoints."""
    app.dependency_overrides[get_db] = lambda: mock_db_session
    original_mode = settings.DATA_MODE
    settings.DATA_MODE = "demo"

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp_req = await client.get("/api/v1/buyers/buyer_wholesaler_ch/requirements")
            assert resp_req.status_code == 200
            reqs = resp_req.json()
            assert len(reqs) >= 1
            assert reqs[0]["buyer_id"] == "buyer_wholesaler_ch"

            resp_dem = await client.get("/api/v1/buyers/buyer_wholesaler_ch/demand")
            assert resp_dem.status_code == 200
            dems = resp_dem.json()
            assert len(dems) >= 1
            assert dems[0]["buyer_id"] == "buyer_wholesaler_ch"
    finally:
        settings.DATA_MODE = original_mode
        app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_buyer_reliability_endpoint(mock_db_session: AsyncMock) -> None:
    """Verifies empirical reliability calculation with statistical gating (N >= 3)."""
    app.dependency_overrides[get_db] = lambda: mock_db_session
    original_mode = settings.DATA_MODE
    settings.DATA_MODE = "demo"

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/v1/buyers/buyer_wholesaler_ch/reliability")
            assert resp.status_code == 200
            data = resp.json()
            assert data["buyer_id"] == "buyer_wholesaler_ch"
            assert data["status"] == "CALCULATED"
            assert data["sample_size"] >= 3
            assert data["fulfillment_rate"] is not None
            assert 0.0 <= data["fulfillment_rate"] <= 1.0
            assert data["cancellation_rate"] is not None
            assert data["dispute_rate"] is not None
    finally:
        settings.DATA_MODE = original_mode
        app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_buyer_matching_post_and_get(mock_db_session: AsyncMock) -> None:
    """Verifies buyer matching POST and GET endpoints."""
    app.dependency_overrides[get_db] = lambda: mock_db_session
    original_mode = settings.DATA_MODE
    settings.DATA_MODE = "demo"

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # POST with supply lot
            supply_payload = {
                "id": "lot_test_01",
                "commodity_id": "tomato",
                "variety": "Hybrid Red",
                "quantity_kg": 2500.0,
                "quality_grade": "GRADE_A",
                "available_from": "2024-09-15",
                "available_until": "2024-09-22",
                "origin_location": "Mohali Rural Farmgate",
                "origin_latitude": 30.6970,
                "origin_longitude": 76.6948,
            }
            resp_post = await client.post("/api/v1/buyer-matching", json=supply_payload)
            assert resp_post.status_code == 200
            data_post = resp_post.json()
            assert data_post["supply_id"] == "lot_test_01"
            assert data_post["commodity_id"] == "tomato"
            assert data_post["matches_evaluated"] > 0
            assert isinstance(data_post["matches"], list)

            # GET convenience endpoint
            resp_get = await client.get(
                "/api/v1/buyer-matching",
                params={"commodity_id": "tomato", "quantity_kg": 2000.0, "quality_grade": "GRADE_A"},
            )
            assert resp_get.status_code == 200
            data_get = resp_get.json()
            assert data_get["matches_evaluated"] > 0

            # Sample supplies
            resp_sample = await client.get("/api/v1/buyer-matching/sample-supplies")
            assert resp_sample.status_code == 200
            samples = resp_sample.json()
            assert len(samples) >= 2
    finally:
        settings.DATA_MODE = original_mode
        app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_demand_aggregation_endpoints(mock_db_session: AsyncMock) -> None:
    """Verifies regional demand aggregate, distribution, and concentration endpoints."""
    app.dependency_overrides[get_db] = lambda: mock_db_session
    original_mode = settings.DATA_MODE
    settings.DATA_MODE = "demo"

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp_agg = await client.get("/api/v1/demand/aggregate", params={"commodity_id": "tomato"})
            assert resp_agg.status_code == 200
            data_agg = resp_agg.json()
            assert data_agg["commodity_id"] == "tomato"
            assert data_agg["total_demand_kg"] > 0
            assert data_agg["buyer_count"] >= 1
            assert data_agg["hhi_concentration"] is not None

            resp_dist = await client.get("/api/v1/demand/distribution", params={"commodity_id": "tomato"})
            assert resp_dist.status_code == 200
            data_dist = resp_dist.json()
            assert data_dist["commodity_id"] == "tomato"
            assert data_dist["sample_size"] >= 3
            assert data_dist["status"] == "VALID"
            assert data_dist["median_kg"] is not None

    finally:
        settings.DATA_MODE = original_mode
        app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_fail_closed_database_mode() -> None:
    """Verifies that database mode with no DB session or unseeded DB raises 503."""
    original_mode = settings.DATA_MODE
    settings.DATA_MODE = "database"

    # Mock DB that returns empty results
    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = []
    mock_result.scalars.return_value = mock_scalars
    mock_db.execute.return_value = mock_result

    app.dependency_overrides[get_db] = lambda: mock_db

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/v1/buyers")
            assert resp.status_code == 503
            assert "BUYER_DATA_UNAVAILABLE" in resp.json()["detail"]
    finally:
        settings.DATA_MODE = original_mode
        app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_zero_recommendation_leakage_in_all_endpoints(mock_db_session: AsyncMock) -> None:
    """
    CRITICAL SIH26132 GOVERNANCE TEST:
    Ensures that NO response from ANY buyer/matching/demand endpoint contains
    recommendations, winning badges, or optimization advice.
    """
    forbidden_tokens = [
        "SELL NOW",
        "HOLD PRODUCE",
        "RECOMMENDED BUYER",
        "OPTIMAL SELLING PLAN",
        "BEST BUYER",
        "WINNER",
    ]

    app.dependency_overrides[get_db] = lambda: mock_db_session
    original_mode = settings.DATA_MODE
    settings.DATA_MODE = "demo"

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            endpoints = [
                "/api/v1/buyers",
                "/api/v1/buyers/buyer_wholesaler_ch",
                "/api/v1/buyers/buyer_wholesaler_ch/requirements",
                "/api/v1/buyers/buyer_wholesaler_ch/demand",
                "/api/v1/buyers/buyer_wholesaler_ch/reliability",
                "/api/v1/buyer-matching?commodity_id=tomato",
                "/api/v1/demand/aggregate?commodity_id=tomato",
                "/api/v1/demand/distribution?commodity_id=tomato",
            ]

            for ep in endpoints:
                resp = await client.get(ep)
                assert resp.status_code == 200
                content_str = resp.text.upper()
                for token in forbidden_tokens:
                    assert token not in content_str, f"Forbidden recommendation token '{token}' in {ep}"
    finally:
        settings.DATA_MODE = original_mode
        app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_route_safety_sample_supplies_not_captured_by_dynamic_id(mock_db_session: AsyncMock) -> None:
    """
    REGRESSION TEST (Requirement 5):
    Verifies that the static route GET /api/v1/buyer-matching/sample-supplies
    is NOT captured by the dynamic route GET /api/v1/buyer-matching/{supply_id}.
    It must resolve to the sample-supplies list handler, not treat supply_id = 'sample-supplies'.
    """
    app.dependency_overrides[get_db] = lambda: mock_db_session
    original_mode = settings.DATA_MODE
    settings.DATA_MODE = "demo"

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 1. Static endpoint /sample-supplies must return 200 and a JSON list
            resp_static = await client.get("/api/v1/buyer-matching/sample-supplies")
            assert resp_static.status_code == 200
            data_static = resp_static.json()
            assert isinstance(data_static, list), "Expected list response from /sample-supplies"
            assert len(data_static) >= 2
            sample_ids = [s["id"] for s in data_static]
            assert "supply_demo_tomato_01" in sample_ids

            # 2. Dynamic endpoint /{supply_id} with known sample ID returns single object
            resp_dynamic = await client.get("/api/v1/buyer-matching/supply_demo_tomato_01")
            assert resp_dynamic.status_code == 200
            data_dynamic = resp_dynamic.json()
            assert isinstance(data_dynamic, dict)
            assert data_dynamic["id"] == "supply_demo_tomato_01"

            # 3. Dynamic endpoint /{supply_id} with nonexistent ID returns 404
            resp_404 = await client.get("/api/v1/buyer-matching/nonexistent_supply_xyz")
            assert resp_404.status_code == 404
    finally:
        settings.DATA_MODE = original_mode
        app.dependency_overrides.pop(get_db, None)

