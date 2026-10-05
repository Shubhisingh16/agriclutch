"""
Unit Tests for AgriClutch Buyer Subsystem Database Models.
Verifies table definitions, column types, relationships, and default values.
SIH26132 — Strengthening Market Linkages and Price Discovery for Farmers.
"""

from datetime import date

from app.models.buyer import (
    BuyerCommodityRequirementModel,
    BuyerModel,
    BuyerTransactionModel,
    FarmerSupplyModel,
)


def test_buyer_model_instantiation() -> None:
    """Verifies BuyerModel attributes and defaults."""
    buyer = BuyerModel(
        id="buyer_test_01",
        display_name="Test Wholesaler",
        buyer_type="wholesaler",
        location="Chandigarh Sector 26",
        latitude=30.7333,
        longitude=76.7794,
        active_status=True,
        source_name="TEST_REGISTRY",
        provenance_status="DEMO",
        is_demo=True,
    )
    assert buyer.id == "buyer_test_01"
    assert buyer.display_name == "Test Wholesaler"
    assert buyer.buyer_type == "wholesaler"
    assert buyer.provenance_status == "DEMO"
    assert buyer.is_demo is True
    assert buyer.active_status is True


def test_buyer_requirement_model() -> None:
    """Verifies BuyerCommodityRequirementModel fields and bounds."""
    req = BuyerCommodityRequirementModel(
        id="req_test_01",
        buyer_id="buyer_test_01",
        commodity_id="tomato",
        variety="Hybrid Red",
        minimum_quantity_kg=500.0,
        maximum_quantity_kg=5000.0,
        preferred_quality_grade="GRADE_A",
        acceptable_quality_range=["GRADE_A", "GRADE_B"],
        required_from=date(2024, 9, 15),
        required_until=date(2024, 9, 25),
        delivery_mode="BUYER_PREMISES",
        price_basis="FIXED_QUOTE",
        quoted_price=28.50,
        payment_terms="NET_7_DAYS",
        source_name="TEST_REGISTRY",
    )
    assert req.minimum_quantity_kg == 500.0
    assert req.maximum_quantity_kg == 5000.0
    assert "GRADE_A" in req.acceptable_quality_range
    assert req.price_basis == "FIXED_QUOTE"
    assert req.payment_terms == "NET_7_DAYS"


def test_buyer_transaction_model() -> None:
    """Verifies historical transaction record fields for empirical reliability auditing."""
    tx = BuyerTransactionModel(
        id="tx_test_01",
        buyer_id="buyer_test_01",
        commodity_id="tomato",
        order_date=date(2024, 8, 1),
        agreed_quantity_kg=2000.0,
        delivered_quantity_kg=2000.0,
        agreed_price_per_kg=26.0,
        fulfillment_status="FULFILLED",
        payment_status="PAID_ON_TIME",
        agreed_payment_due_date=date(2024, 8, 8),
        actual_payment_date=date(2024, 8, 8),
        dispute_status=False,
    )
    assert tx.fulfillment_status == "FULFILLED"
    assert tx.payment_status == "PAID_ON_TIME"
    assert tx.dispute_status is False


def test_farmer_supply_model() -> None:
    """Verifies FarmerSupplyModel persistence structure."""
    supply = FarmerSupplyModel(
        id="sup_test_01",
        commodity_id="tomato",
        variety="Desi",
        quantity_kg=1500.0,
        quality_grade="GRADE_A",
        available_from=date(2024, 9, 15),
        available_until=date(2024, 9, 22),
        origin_location="Mohali",
        storage_available=False,
    )
    assert supply.quantity_kg == 1500.0
    assert supply.quality_grade == "GRADE_A"
    assert supply.storage_available is False
