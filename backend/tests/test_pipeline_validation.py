"""
Unit Tests for AgriClutch Agricultural Data Validator.
Validates invariant enforcement, price hierarchy checks, duplicate detection, and health scorecards.
SYNTHETIC TEST FIXTURES ONLY — NOT REAL AGRICULTURAL DATA.
"""

import pytest
from app.schemas.validation import ValidationSeverity, ValidationStatus

from pipeline.validation.validator import AgriDataValidator


class TestPipelineValidation:
    """Test suite for AgriDataValidator."""

    @pytest.fixture
    def validator(self) -> AgriDataValidator:
        return AgriDataValidator()

    def test_valid_record_passes(self, validator: AgriDataValidator) -> None:
        """Verify that a valid observation is classified as VALID with no errors."""
        record = {
            "record_date": "2024-09-15",
            "source_market_id": "Chandigarh",
            "source_commodity_id": "Tomato",
            "original_modal_price": "2800.0",
            "original_min_price": "2500.0",
            "original_max_price": "3000.0",
            "original_price_unit": "Rs/Quintal",
            "arrival_tonnes": "40.0",
        }
        status, issues = validator.validate_record(record, row_num=1)
        assert status == ValidationStatus.VALID
        assert len(issues) == 0

    def test_negative_price_rejected(self, validator: AgriDataValidator) -> None:
        """Verify that negative or zero prices produce an ERROR and INVALID status."""
        record = {
            "record_date": "2024-09-15",
            "source_market_id": "Chandigarh",
            "source_commodity_id": "Tomato",
            "original_modal_price": "-500.0",
        }
        status, issues = validator.validate_record(record, row_num=1)
        assert status == ValidationStatus.INVALID
        errors = [i for i in issues if i.severity == ValidationSeverity.ERROR]
        assert any("strictly positive" in e.message for e in errors)

    def test_invalid_date_format_rejected(self, validator: AgriDataValidator) -> None:
        """Verify rejection of unparseable date strings."""
        record = {
            "record_date": "not-a-valid-date",
            "source_market_id": "Chandigarh",
            "source_commodity_id": "Tomato",
            "original_modal_price": "2500.0",
        }
        status, issues = validator.validate_record(record, row_num=1)
        assert status == ValidationStatus.INVALID
        assert any(i.field == "record_date" and i.severity == ValidationSeverity.ERROR for i in issues)

    def test_price_hierarchy_violation(self, validator: AgriDataValidator) -> None:
        """Verify that min > modal or modal > max is flagged as an ERROR."""
        record = {
            "record_date": "2024-09-15",
            "source_market_id": "Chandigarh",
            "source_commodity_id": "Tomato",
            "original_modal_price": "2000.0",
            "original_min_price": "2500.0",  # min > modal violation!
            "original_max_price": "3000.0",
        }
        status, issues = validator.validate_record(record, row_num=1)
        assert status == ValidationStatus.INVALID
        assert any("hierarchy violation" in i.message for i in issues)

    def test_negative_arrivals_rejected(self, validator: AgriDataValidator) -> None:
        """Verify that negative arrival volumes are rejected."""
        record = {
            "record_date": "2024-09-15",
            "source_market_id": "Chandigarh",
            "source_commodity_id": "Tomato",
            "original_modal_price": "2500.0",
            "arrival_tonnes": "-15.0",
        }
        status, issues = validator.validate_record(record, row_num=1)
        assert status == ValidationStatus.INVALID
        assert any(i.field == "arrival_tonnes" and i.severity == ValidationSeverity.ERROR for i in issues)

    def test_unrecognized_unit_warning(self, validator: AgriDataValidator) -> None:
        """Verify that unrecognized price units produce a WARNING without invalidating."""
        record = {
            "record_date": "2024-09-15",
            "source_market_id": "Chandigarh",
            "source_commodity_id": "Tomato",
            "original_modal_price": "2500.0",
            "original_price_unit": "UnknownCurrencyUnit",
        }
        status, issues = validator.validate_record(record, row_num=1)
        assert status == ValidationStatus.WARNING
        assert any(i.field == "original_price_unit" and i.severity == ValidationSeverity.WARNING for i in issues)

    def test_duplicate_detection_in_batch(self, validator: AgriDataValidator) -> None:
        """Verify that duplicate natural identity observations are counted and logged."""
        records = [
            {
                "record_date": "2024-09-15",
                "source_market_id": "Chandigarh",
                "source_commodity_id": "Tomato",
                "original_modal_price": "2800.0",
                "variety": "Common",
                "grade": "FAQ",
            },
            {
                "record_date": "2024-09-15",
                "source_market_id": "Chandigarh",
                "source_commodity_id": "Tomato",
                "original_modal_price": "2850.0",
                "variety": "Common",
                "grade": "FAQ",
            },
        ]
        valid_recs, report = validator.validate_batch(records, source_name="TEST_BATCH")

        assert report.total_records == 2
        assert report.duplicate_records == 1
        assert any("Duplicate observation" in w.message for w in report.warnings)
        assert report.health_score < 100.0
