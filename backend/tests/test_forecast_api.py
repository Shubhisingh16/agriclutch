"""
Unit Tests for AgriClutch Forecasting REST API Endpoints.
Tests GET /api/v1/forecasts, GET /api/v1/forecasts/models, GET /api/v1/forecasts/evaluation.
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
async def test_get_forecast_demo_mode_baseline(mock_db_session: AsyncMock) -> None:
    app.dependency_overrides[get_db] = lambda: mock_db_session
    original_mode = settings.DATA_MODE
    settings.DATA_MODE = "demo"

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get(
                "/api/v1/forecasts",
                params={
                    "commodity": "tomato",
                    "market": "mandi_ch_49",
                    "horizon": 14,
                    "model": "gradient_boosting",
                },
            )

            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == "SUCCESS"
            assert data["commodity_id"] == "tomato"
            assert data["market_id"] == "mandi_ch_49"
            assert data["horizon"] == 14
            assert data["unit"] == "INR_PER_KG"
            assert len(data["points"]) == 14

            # Disclaimer check
            assert data["metadata"]["disclaimer"] == "Model forecast — not a guaranteed price."
            assert data["metadata"]["is_demo"] is True

            # Headers check
            assert resp.headers["x-agriclutch-data-mode"] == "DEMO"
            assert resp.headers["x-agriclutch-model"] == "gradient_boosting"

            # Quantile ordering
            for pt in data["points"]:
                assert pt["q10"] <= pt["q20"] <= pt["q50"] <= pt["q80"] <= pt["q90"]
    finally:
        settings.DATA_MODE = original_mode
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_forecast_data_sufficiency_gating(mock_db_session: AsyncMock) -> None:
    app.dependency_overrides[get_db] = lambda: mock_db_session
    original_mode = settings.DATA_MODE
    settings.DATA_MODE = "demo"

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # Querying market with 'insufficient' yields 15 records (< 30)
            resp = await client.get(
                "/api/v1/forecasts",
                params={
                    "commodity": "tomato",
                    "market": "mandi_insufficient_sample",
                    "horizon": 14,
                    "model": "naive",
                },
            )

            assert resp.status_code == 422
            detail = resp.json()["detail"]
            assert detail["status"] == "INSUFFICIENT_HISTORY"
            assert detail["available_records"] < detail["required_minimum"]
            assert "minimum 30 required" in detail["detail"]
            assert resp.headers["x-agriclutch-data-sufficiency"] == "INSUFFICIENT"
    finally:
        settings.DATA_MODE = original_mode
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_forecast_models_list() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/forecasts/models")
        assert resp.status_code == 200
        models = resp.json()
        assert len(models) >= 5
        model_ids = [m["id"] for m in models]
        assert "chronos-2" in model_ids
        assert "gradient_boosting" in model_ids
        assert "statistical" in model_ids
        assert "seasonal_naive" in model_ids
        assert "naive" in model_ids


@pytest.mark.asyncio
async def test_get_forecast_evaluation_benchmark(mock_db_session: AsyncMock) -> None:
    app.dependency_overrides[get_db] = lambda: mock_db_session
    original_mode = settings.DATA_MODE
    settings.DATA_MODE = "demo"

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get(
                "/api/v1/forecasts/evaluation",
                params={
                    "commodity": "tomato",
                    "market": "mandi_ch_49",
                    "horizon": 7,
                },
            )

            assert resp.status_code == 200
            data = resp.json()
            assert data["commodity_id"] == "tomato"
            assert data["market_id"] == "mandi_ch_49"
            assert data["evaluation_strategy"] == "ROLLING_ORIGIN"
            assert len(data["evaluations"]) >= 3
            for ev in data["evaluations"]:
                assert "mae" in ev
                assert "rmse" in ev
                assert "smape" in ev
                assert "mase" in ev
                assert "pinball_loss" in ev
                assert "coverage_80" in ev
    finally:
        settings.DATA_MODE = original_mode
        app.dependency_overrides.clear()
