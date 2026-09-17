"""
Unit and Integration Tests for AgriClutch Net Realizable Value (NRV) REST API Endpoints.
SIH26132 — Market Linkages and Price Discovery for Farmers.
"""

from unittest.mock import AsyncMock

import pytest
from app.config import settings
from app.db.session import get_db
from app.main import app
from httpx import ASGITransport, AsyncClient


@pytest.fixture
def mock_db_session() -> AsyncMock:
    return AsyncMock()


@pytest.mark.asyncio
async def test_get_nrv_endpoint_demo_mode(mock_db_session: AsyncMock) -> None:
    """Verifies GET /api/v1/nrv returns valid NRV response with itemized costs and headers."""
    app.dependency_overrides[get_db] = lambda: mock_db_session
    original_mode = settings.DATA_MODE
    settings.DATA_MODE = "demo"

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get(
                "/api/v1/nrv",
                params={
                    "commodity_id": "tomato",
                    "market_id": "mandi_ch_49",
                    "quantity": 1000.0,
                    "unit": "kg",
                    "storage_days": 0,
                    "forecast_model": "gradient_boosting",
                },
            )

            assert resp.status_code == 200
            data = resp.json()

            assert data["commodity_id"] == "tomato"
            assert data["market_id"] == "mandi_ch_49"
            assert data["status"] == "VALID"
            assert data["disclaimer"] == "Model estimate — not a guaranteed price or transaction quote."

            # Verify quantity normalization
            assert data["quantity"]["normalized_quantity_kg"] == 1000.0
            assert data["quantity"]["original_unit"] == "kg"

            # Verify costs
            cb = data["cost_breakdown"]
            assert cb["transport_cost"]["amount"] > 0
            assert cb["handling_cost"]["amount"] == 600.0
            assert cb["other_costs"]["amount"] == 400.0
            assert cb["total_cost"] == data["total_cost"]

            # Verify NRV quantiles monotonicity
            nq = data["nrv_quantiles"]
            assert nq["p10"] <= nq["p20"] <= nq["p50"] <= nq["p80"] <= nq["p90"]

            # Verify headers
            assert resp.headers["x-agriclutch-data-mode"] == "DEMO"
            assert resp.headers["x-agriclutch-datasource"] == "DEMO_BENCHMARK_SEED"
    finally:
        settings.DATA_MODE = original_mode
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_nrv_invalid_inputs(mock_db_session: AsyncMock) -> None:
    """Verifies that invalid quantity or unit returns HTTP 400."""
    app.dependency_overrides[get_db] = lambda: mock_db_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Negative quantity
        resp_neg = await client.get(
            "/api/v1/nrv",
            params={
                "commodity_id": "tomato",
                "market_id": "mandi_ch_49",
                "quantity": -50.0,
            },
        )
        assert resp_neg.status_code in [400, 422]

        # Unsupported unit
        resp_unit = await client.get(
            "/api/v1/nrv",
            params={
                "commodity_id": "tomato",
                "market_id": "mandi_ch_49",
                "quantity": 100.0,
                "unit": "bushel",
            },
        )
        assert resp_unit.status_code == 400
        assert "INVALID_QUANTITY" in resp_unit.json()["detail"]


@pytest.mark.asyncio
async def test_get_nrv_markets_comparison_endpoint(mock_db_session: AsyncMock) -> None:
    """Verifies GET /api/v1/nrv/markets returns multi-mandi scenarios without ranking."""
    app.dependency_overrides[get_db] = lambda: mock_db_session
    original_mode = settings.DATA_MODE
    settings.DATA_MODE = "demo"

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get(
                "/api/v1/nrv/markets",
                params={"commodity_id": "tomato", "quantity": 1000.0},
            )

            assert resp.status_code == 200
            data = resp.json()
            assert "scenarios" in data
            assert len(data["scenarios"]) >= 3

            # Zero recommendation check
            forbidden_labels = ["RECOMMENDED MARKET", "RECOMMENDED ACTION", "BEST MARKET", "WINNER", "ACTION: SELL", "ACTION: HOLD"]
            data_str = str(data).upper()
            for label in forbidden_labels:
                assert label not in data_str, f"Forbidden label '{label}' found in response!"
            assert "recommendation" not in [k.lower() for sc in data["scenarios"] for k in sc.keys()]
    finally:
        settings.DATA_MODE = original_mode
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_nrv_times_comparison_endpoint(mock_db_session: AsyncMock) -> None:
    """Verifies GET /api/v1/nrv/times returns holding scenarios."""
    app.dependency_overrides[get_db] = lambda: mock_db_session
    original_mode = settings.DATA_MODE
    settings.DATA_MODE = "demo"

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get(
                "/api/v1/nrv/times",
                params={"commodity_id": "tomato", "market_id": "mandi_ch_49", "quantity": 1000.0},
            )

            assert resp.status_code == 200
            data = resp.json()
            assert "scenarios" in data
            assert len(data["scenarios"]) == 5  # 0, 3, 7, 14, 28 days

            # Zero recommendation verification
            forbidden_labels = [
                "RECOMMENDED ACTION",
                "RECOMMENDED MARKET",
                "BEST MARKET",
                "WINNER",
                "ACTION: SELL",
                "ACTION: HOLD",
                "ACTION: BUY",
                "ACTION: STORE",
            ]
            data_str = str(data).upper()
            for label in forbidden_labels:
                assert label not in data_str, f"Forbidden label '{label}' found in response!"
    finally:
        settings.DATA_MODE = original_mode
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_nrv_sensitivity_endpoint(mock_db_session: AsyncMock) -> None:
    """Verifies GET /api/v1/nrv/sensitivity returns 3x3 orthogonal grid."""
    app.dependency_overrides[get_db] = lambda: mock_db_session
    original_mode = settings.DATA_MODE
    settings.DATA_MODE = "demo"

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get(
                "/api/v1/nrv/sensitivity",
                params={
                    "commodity_id": "tomato",
                    "market_id": "mandi_ch_49",
                    "quantity": 1000.0,
                    "variable_x": "price",
                    "variable_y": "transport",
                },
            )

            assert resp.status_code == 200
            data = resp.json()
            assert data["variable_x"] == "price"
            assert data["variable_y"] == "transport"
            assert len(data["grid_nrv_p50"]) == 3
            assert len(data["grid_nrv_p50"][0]) == 3
    finally:
        settings.DATA_MODE = original_mode
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_nrv_assumptions_endpoint(mock_db_session: AsyncMock) -> None:
    """Verifies GET /api/v1/nrv/assumptions returns parameters with demo labeling."""
    app.dependency_overrides[get_db] = lambda: mock_db_session
    original_mode = settings.DATA_MODE
    settings.DATA_MODE = "demo"

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/v1/nrv/assumptions")

            assert resp.status_code == 200
            data = resp.json()
            assert data["total"] > 0
            for a in data["assumptions"]:
                assert a["provenance_status"] == "DEMO"
                assert a["is_demo"] is True
    finally:
        settings.DATA_MODE = original_mode
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_nrv_database_mode_fails_closed_when_db_offline() -> None:
    """Verifies database mode fails closed with HTTP 503 rather than silently substituting demo data."""
    original_mode = settings.DATA_MODE
    settings.DATA_MODE = "database"

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get(
                "/api/v1/nrv",
                params={"commodity_id": "tomato", "market_id": "mandi_ch_49", "quantity": 1000.0},
            )
            assert resp.status_code == 503
            assert resp.headers.get("x-agriclutch-data-mode") == "DATABASE"
    finally:
        settings.DATA_MODE = original_mode
