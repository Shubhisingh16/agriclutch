"""
AgriClutch Step 14: Decision API Endpoint Integration Tests.
Tests REST endpoints /api/v1/decision/optimize, /what-if, /sensitivity, /plans/{id}, and /configuration.
SIH26132 — Strengthening Market Linkages and Price Discovery for Farmers.
"""

from unittest.mock import AsyncMock

import pytest
from app.db.session import get_db
from app.main import app
from httpx import ASGITransport, AsyncClient


@pytest.fixture
def mock_db_session() -> AsyncMock:
    mock = AsyncMock()
    mock.execute = AsyncMock()
    mock.commit = AsyncMock()
    mock.rollback = AsyncMock()
    mock.flush = AsyncMock()
    mock.add = lambda x: None
    return mock


@pytest.mark.asyncio
async def test_optimize_plan_api(mock_db_session: AsyncMock) -> None:
    app.dependency_overrides[get_db] = lambda: mock_db_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "commodity_id": "tomato",
            "variety": "Standard",
            "quality_grade": "GRADE_A",
            "total_supply_kg": 2500.0,
            "decision_horizon_days": 7,
            "risk_preference": "RISK_AWARE",
            "liquidity_preference": "BALANCED",
        }
        resp = await client.post("/api/v1/decision/optimize", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["plan_id"].startswith("plan_")
        assert data["solver_status"] == "OPTIMAL"
        assert data["validation_status"] == "PASSED"
        assert data["total_allocated_kg"] > 0
        assert data["expected_total_nrv"] > 0
        assert len(data["allocations"]) > 0
        assert resp.headers.get("X-AgriClutch-Step") == "14"
        assert resp.headers.get("X-AgriClutch-DataSource") == "DEMO_DECISION"


@pytest.mark.asyncio
async def test_simulate_what_if_api(mock_db_session: AsyncMock) -> None:
    app.dependency_overrides[get_db] = lambda: mock_db_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "commodity_id": "tomato",
            "total_supply_kg": 2500.0,
            "transport_cost_multiplier": 1.25,
            "scenario_label": "High Freight Surge",
        }
        resp = await client.post("/api/v1/decision/what-if", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert "baseline_plan" in data
        assert "counterfactual_plan" in data
        assert "comparison" in data
        assert data["comparison"]["parameter_changed"] == "High Freight Surge"


@pytest.mark.asyncio
async def test_evaluate_sensitivity_api(mock_db_session: AsyncMock) -> None:
    app.dependency_overrides[get_db] = lambda: mock_db_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "commodity_id": "tomato",
            "total_supply_kg": 2000.0,
            "parameter_type": "TRANSPORT_COST",
            "sweep_multipliers": [0.8, 1.0, 1.2],
        }
        resp = await client.post("/api/v1/decision/sensitivity", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["points"]) == 3
        assert "interpretation" in data


@pytest.mark.asyncio
async def test_get_configuration_api() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/decision/configuration")
        assert resp.status_code == 200
        data = resp.json()
        assert data["solver"] == "SciPy-HiGHS-DualSimplex"
        assert "risk_weights" in data
        assert "liquidity_min_ratios" in data
