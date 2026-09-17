"""
Unit Tests for AgriClutch Agricultural Data Normalizer.
Validates string cleaning, date standardisation, dual pricing, and quintal-to-kg scaling.
SYNTHETIC TEST FIXTURES ONLY — NOT REAL AGRICULTURAL DATA.
"""

from datetime import date

from pipeline.cleaning.normalizer import DataNormalizer


class TestPipelineNormalization:
    """Test suite for DataNormalizer."""

    def test_quintal_to_kg_price_scaling(self) -> None:
        """Verify that Rs/Quintal prices are scaled to INR/kg by dividing by 100.0."""
        normalizer = DataNormalizer()
        raw_rec = {
            "record_date": "2024-09-15",
            "source_market_id": "Chandigarh",
            "source_commodity_id": "Tomato",
            "variety": "Common",
            "grade": "FAQ",
            "original_modal_price": "2850.0",
            "original_min_price": "2500.0",
            "original_max_price": "3200.0",
            "original_price_unit": "Rs/Quintal",
            "arrival_tonnes": "45.0",
        }
        normalized = normalizer.normalize_record(raw_rec, source_name="TEST_SRC")

        # Original preserved intact
        assert normalized.original_modal_price == 2850.0
        assert normalized.original_min_price == 2500.0
        assert normalized.original_max_price == 3200.0
        assert normalized.original_price_unit == "Rs/Quintal"

        # Normalized scaled to INR/kg
        assert normalized.normalized_modal_price == 28.50
        assert normalized.normalized_min_price == 25.00
        assert normalized.normalized_max_price == 32.00
        assert normalized.normalized_price_unit == "INR_PER_KG"

    def test_kg_unit_unscaled(self) -> None:
        """Verify that if prices are already in INR/kg, scalar factor is 1.0."""
        normalizer = DataNormalizer()
        raw_rec = {
            "record_date": "2024-09-15",
            "source_market_id": "Chandigarh",
            "source_commodity_id": "Tomato",
            "original_modal_price": "30.0",
            "original_min_price": "28.0",
            "original_max_price": "32.0",
            "original_price_unit": "INR_PER_KG",
        }
        normalized = normalizer.normalize_record(raw_rec, source_name="TEST_SRC")

        assert normalized.original_modal_price == 30.0
        assert normalized.normalized_modal_price == 30.0
        assert normalized.normalized_price_unit == "INR_PER_KG"

    def test_string_trimming_and_slugification(self) -> None:
        """Verify that crop names and market names have whitespace trimmed and IDs slugified."""
        normalizer = DataNormalizer()
        raw_rec = {
            "record_date": "15/09/2024",
            "source_market_id": "  Chandigarh(Grain)  ",
            "source_commodity_id": "  Tomato Hybrid  ",
            "original_modal_price": "2500.0",
        }
        normalized = normalizer.normalize_record(raw_rec, source_name="TEST_SRC")

        assert normalized.commodity_id == "tomato_hybrid"
        assert normalized.record_date == date(2024, 9, 15)
        # Resolved via AuthoritativeMarketRegistry
        assert normalized.market_id == "mandi_ch_49"
        assert normalized.source_market_id == "Chandigarh(Grain)"

    def test_batch_normalization(self) -> None:
        """Verify that valid records in a batch are normalized into typed Pydantic models."""
        normalizer = DataNormalizer()
        records = [
            {
                "record_date": "2024-09-15",
                "source_market_id": "Chandigarh",
                "source_commodity_id": "Tomato",
                "original_modal_price": "2800.0",
            },
            {
                "record_date": "2024-09-16",
                "source_market_id": "Panchkula",
                "source_commodity_id": "Onion",
                "original_modal_price": "3200.0",
            },
        ]
        results = normalizer.normalize_batch(records, source_name="BATCH_TEST")
        assert len(results) == 2
        assert results[0].commodity_id == "tomato"
        assert results[0].normalized_modal_price == 28.0
        assert results[1].commodity_id == "onion"
        assert results[1].normalized_modal_price == 32.0
