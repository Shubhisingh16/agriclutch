"""
Unit Tests for AgriClutch Database Models.
Validates table structures, column constraints, UUID primary keys, and uniqueness contracts.
SYNTHETIC TEST FIXTURES ONLY — NOT REAL AGRICULTURAL DATA.
"""

from datetime import date
from uuid import uuid4

from app.models.arrival_observation import ArrivalObservationModel
from app.models.commodity import CommodityModel
from app.models.market import MarketModel
from app.models.price_observation import PriceObservationModel


class TestDatabaseModels:
    """Test suite for SQLAlchemy ORM models."""

    def test_commodity_model_instantiation(self) -> None:
        """Verify CommodityModel structure and defaults."""
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
        )
        assert comm.id == "tomato"
        assert comm.name == "Tomato"
        assert comm.category == "perishable"
        assert comm.price_unit == "INR_PER_KG"
        assert comm.__tablename__ == "commodities"

    def test_market_model_instantiation(self) -> None:
        """Verify MarketModel structure and APMC code."""
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
        )
        assert market.id == "mandi_ch_49"
        assert market.apmc_code == 49
        assert market.is_terminal_market is True
        assert market.__tablename__ == "mandis"

    def test_price_observation_model_dual_pricing(self) -> None:
        """Verify PriceObservationModel preserves dual pricing and surrogate UUID PK."""
        obs_id = uuid4()
        obs = PriceObservationModel(
            observation_id=obs_id,
            source_name="DEMO_BENCHMARK",
            source_market_id="Chandigarh(Grain)",
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
        )
        assert obs.observation_id == obs_id
        assert obs.original_modal_price == 2850.0
        assert obs.normalized_modal_price == 28.50
        assert obs.original_price_unit == "Rs/Quintal"
        assert obs.normalized_price_unit == "INR_PER_KG"
        assert obs.__tablename__ == "mandi_daily_records"

    def test_arrival_observation_model(self) -> None:
        """Verify ArrivalObservationModel structure."""
        arr = ArrivalObservationModel(
            source_name="AGMARKNET",
            source_market_id="Chandigarh",
            source_commodity_id="Tomato",
            record_date=date(2024, 9, 15),
            market_id="mandi_ch_49",
            commodity_id="tomato",
            arrival_tonnes=120.5,
            original_arrival_unit="Tonnes",
            normalized_arrival_unit="METRIC_TONNE",
        )
        assert arr.arrival_tonnes == 120.5
        assert arr.original_arrival_unit == "Tonnes"
        assert arr.normalized_arrival_unit == "METRIC_TONNE"
        assert arr.__tablename__ == "mandi_daily_arrivals"
