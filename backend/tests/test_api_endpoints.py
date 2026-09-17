"""
Unit Tests for AgriClutch Read-Only API Endpoints.
Tests GET /commodities, GET /markets, and GET /prices using FastAPI TestClient with mocked async sessions.
SYNTHETIC TEST FIXTURES ONLY — NOT REAL AGRICULTURAL DATA.
"""

from datetime import date, datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from app.config import settings
from app.db.session import get_db
from app.main import app
from app.models.commodity import CommodityModel
from app.models.market import MarketModel
from app.models.price_observation import PriceObservationModel
from httpx import ASGITransport, AsyncClient


@pytest.fixture
def mock_db_session() -> AsyncMock:
    """Provides a mocked async session simulating database queries."""
    session = AsyncMock()

    # Sample models
    comm = CommodityModel(
        id="tomato",
        name="Tomato",
        hindi_name="टमाटर",
        category="perishable",
        default_spoilage_rate=0.08,
        max_ambient_holding_days=4,
        standard_moisture_pct=94.0,
        price_unit="INR_PER_KG",
        weight_unit="KG",
        created_at=datetime.now(timezone.utc),
    )

    market = MarketModel(
        id="mandi_ch_49",
        apmc_code=49,
        name="Chandigarh",
        state="Chandigarh",
        district="Chandigarh",
        latitude=30.7333,
        longitude=76.7794,
        is_terminal_market=True,
        source_market_id="Chandigarh(Grain)",
        created_at=datetime.now(timezone.utc),
    )

    price_obs = PriceObservationModel(
        observation_id=uuid4(),
        source_name="DEMO_BENCHMARK",
        source_record_id="REC001",
        source_market_id="Chandigarh",
        source_commodity_id="Tomato",
        record_date=date(2024, 9, 15),
        market_id="mandi_ch_49",
        commodity_id="tomato",
        variety="Common",
        grade="FAQ",
        original_modal_price=2850.0,
        original_min_price=2500.0,
        original_max_price=3200.0,
        original_price_unit="Rs/Quintal",
        normalized_modal_price=28.50,
        normalized_min_price=25.00,
        normalized_max_price=32.00,
        normalized_price_unit="INR_PER_KG",
        arrival_tonnes=45.0,
        is_interpolated=False,
        is_outlier=False,
        created_at=datetime.now(timezone.utc),
    )

    # Set up execute results
    async def mock_execute(stmt: MagicMock) -> MagicMock:
        stmt_str = str(stmt).lower()
        res = MagicMock()
        if "from commodities" in stmt_str:
            if "where commodities.id =" in stmt_str:
                res.scalar_one_or_none.return_value = comm
            else:
                res.scalars.return_value.all.return_value = [comm]
        elif "from mandis" in stmt_str:
            if "where mandis.id =" in stmt_str:
                res.scalar_one_or_none.return_value = market
            else:
                res.scalars.return_value.all.return_value = [market]
        elif "count" in stmt_str:
            res.scalar.return_value = 1
        elif "from mandi_daily_records" in stmt_str:
            res.scalars.return_value.all.return_value = [price_obs]
        else:
            res.scalars.return_value.all.return_value = []
            res.scalar_one_or_none.return_value = None
            res.scalar.return_value = 0
        return res

    session.execute.side_effect = mock_execute
    return session


@pytest.mark.asyncio
class TestApiEndpoints:
    """Test suite for AgriClutch v1 REST endpoints."""

    async def test_get_commodities(self, mock_db_session: AsyncMock) -> None:
        """Verify GET /api/v1/commodities returns typed commodities list."""
        app.dependency_overrides[get_db] = lambda: mock_db_session
        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/api/v1/commodities")
                assert response.status_code == 200
                data = response.json()
                assert len(data) == 1
                assert data[0]["id"] == "tomato"
                assert data[0]["category"] == "perishable"
        finally:
            app.dependency_overrides.pop(get_db, None)

    async def test_get_markets(self, mock_db_session: AsyncMock) -> None:
        """Verify GET /api/v1/markets returns registered mandis."""
        app.dependency_overrides[get_db] = lambda: mock_db_session
        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/api/v1/markets")
                assert response.status_code == 200
                data = response.json()
                assert len(data) == 1
                assert data[0]["id"] == "mandi_ch_49"
                assert data[0]["apmc_code"] == 49
        finally:
            app.dependency_overrides.pop(get_db, None)

    async def test_get_prices_with_filters(self, mock_db_session: AsyncMock) -> None:
        """Verify GET /api/v1/prices returns observations and pagination headers."""
        app.dependency_overrides[get_db] = lambda: mock_db_session
        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get(
                    "/api/v1/prices?commodity=tomato&market=mandi_ch_49&start_date=2024-09-01&end_date=2024-09-30"
                )
                assert response.status_code == 200
                data = response.json()
                assert len(data) == 1
                assert data[0]["commodity_id"] == "tomato"
                assert data[0]["original_price_unit"] == "Rs/Quintal"
                assert data[0]["normalized_price_unit"] == "INR_PER_KG"
                assert data[0]["normalized_modal_price"] == 28.50

                assert "x-total-count" in response.headers
                assert response.headers["x-total-count"] == "1"
        finally:
            app.dependency_overrides.pop(get_db, None)

    async def test_get_prices_invalid_date_format(self, mock_db_session: AsyncMock) -> None:
        """Verify 422 Unprocessable Entity on invalid date query parameter."""
        app.dependency_overrides[get_db] = lambda: mock_db_session
        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/api/v1/prices?start_date=invalid-date")
                assert response.status_code == 422
        finally:
            app.dependency_overrides.pop(get_db, None)

    async def test_database_mode_fails_closed_when_db_offline(self) -> None:
        """Verify database mode returns 503 rather than silently substituting synthetic data."""
        failing_session = AsyncMock()
        failing_session.execute.side_effect = ConnectionRefusedError("Database unreachable")
        app.dependency_overrides[get_db] = lambda: failing_session

        orig_mode = settings.DATA_MODE
        settings.DATA_MODE = "database"
        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/api/v1/commodities")
                assert response.status_code == 503
                assert "Database service is unavailable" in response.json()["detail"]
                # Must NOT return 200 with synthetic data
                assert response.headers.get("x-agriclutch-data-mode") is None
        finally:
            settings.DATA_MODE = orig_mode
            app.dependency_overrides.pop(get_db, None)

    async def test_demo_mode_explicitly_serves_synthetic_fixture(self) -> None:
        """Verify demo mode explicitly serves synthetic test fixture with unmistakable metadata."""
        orig_mode = settings.DATA_MODE
        settings.DATA_MODE = "demo"
        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/api/v1/commodities")
                assert response.status_code == 200
                assert response.headers["x-agriclutch-data-mode"] == "DEMO"
                assert response.headers["x-agriclutch-datasource"] == "SYNTHETIC_TEST_FIXTURE"

                data = response.json()
                assert len(data) == 3
                assert data[0]["id"] == "tomato"

                # Check prices in demo mode
                price_res = await client.get("/api/v1/prices?commodity=tomato")
                assert price_res.status_code == 200
                assert price_res.headers["x-agriclutch-data-mode"] == "DEMO"
                assert price_res.headers["x-agriclutch-datasource"] == "SYNTHETIC_TEST_FIXTURE"
                price_data = price_res.json()
                assert len(price_data) > 0
                assert price_data[0]["source_name"] == "SYNTHETIC_DEMO"
        finally:
            settings.DATA_MODE = orig_mode

    async def test_database_mode_exposes_database_metadata(self, mock_db_session: AsyncMock) -> None:
        """Verify database mode exposes DATABASE headers when database is operational."""
        orig_mode = settings.DATA_MODE
        settings.DATA_MODE = "database"
        app.dependency_overrides[get_db] = lambda: mock_db_session
        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/api/v1/commodities")
                assert response.status_code == 200
                assert response.headers["x-agriclutch-data-mode"] == "DATABASE"
                assert response.headers["x-agriclutch-datasource"] == "POSTGRESQL"
        finally:
            settings.DATA_MODE = orig_mode
            app.dependency_overrides.pop(get_db, None)
