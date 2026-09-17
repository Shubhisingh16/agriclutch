"""
Unit Tests for AgriClutch Local CSV Ingestion Adapter.
Validates file reading, Git LFS conflict stripping, forward-filling, and column mapping.
SYNTHETIC TEST FIXTURES ONLY — NOT REAL AGRICULTURAL DATA.
"""

import tempfile

import pytest

from pipeline.ingestion.column_mapper import ColumnMapper
from pipeline.ingestion.csv_adapter import LocalCSVSourceAdapter


class TestPipelineIngestion:
    """Test suite for LocalCSVSourceAdapter and ColumnMapper."""

    def test_valid_canonical_csv_ingestion(self) -> None:
        """Verify reading a well-formed canonical CSV."""
        csv_content = (
            "record_date,source_name,source_record_id,source_market_id,source_commodity_id,"
            "variety,grade,original_modal_price,original_min_price,original_max_price,"
            "original_price_unit,arrival_tonnes\n"
            "2024-09-15,SYNTHETIC,REC1,Chandigarh,Tomato,Common,FAQ,2800.0,2500.0,3000.0,Rs/Quintal,25.0\n"
            "2024-09-16,SYNTHETIC,REC2,Panchkula,Onion,Common,FAQ,3200.0,3000.0,3400.0,Rs/Quintal,15.0\n"
        )
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".csv") as tmp:
            tmp.write(csv_content)
            tmp_path = tmp.name

        adapter = LocalCSVSourceAdapter(source_name="TEST_SRC")
        records = adapter.read_records(tmp_path)

        assert len(records) == 2
        assert records[0].source_name == "TEST_SRC"
        assert records[0].source_record_id == "REC1"
        assert records[0].source_market_id == "Chandigarh"
        assert records[0].payload["original_modal_price"] == "2800.0"

    def test_git_lfs_conflict_stripping(self) -> None:
        """Verify automatic detection and stripping of Git LFS and merge conflict lines."""
        corrupted_content = (
            "<<<<<<< HEAD\n"
            "version https://git-lfs.github.com/spec/v1\n"
            "oid sha256:d17c98b8131bf4e8f172cfd8616fae30ea28dbab8cf6df769490076a445cb490\n"
            "size 171630\n"
            "=======\n"
            "record_date,source_market_id,source_commodity_id,original_modal_price\n"
            ">>>>>>> 8a3dfb091f09c7ba8d3ad480a4ddbbbaaa19a584\n"
            "2024-09-15,Chandigarh,Tomato,2500.0\n"
        )
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".csv") as tmp:
            tmp.write(corrupted_content)
            tmp_path = tmp.name

        adapter = LocalCSVSourceAdapter()
        records = adapter.read_records(tmp_path)

        assert len(records) == 1
        assert records[0].payload["source_market_id"] == "Chandigarh"
        assert records[0].payload["original_modal_price"] == "2500.0"

    def test_agmarknet_stateful_forward_fill(self) -> None:
        """Verify that blank market names on continuation rows are correctly forward-filled."""
        agmarknet_content = (
            "Market,Arrival_Date,Modal Price,Min Price,Max Price,Unit of Price\n"
            '"Chandigarh",15/09/2024,2800,2600,3000,Rs/Quintal\n'
            '"",16/09/2024,2900,2700,3100,Rs/Quintal\n'
            '"Panchkula",15/09/2024,2700,2500,2900,Rs/Quintal\n'
        )
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".csv") as tmp:
            tmp.write(agmarknet_content)
            tmp_path = tmp.name

        adapter = LocalCSVSourceAdapter()
        records = adapter.read_records(tmp_path)

        assert len(records) == 3
        # Row 0: Chandigarh
        assert records[0].source_market_id == "Chandigarh"
        # Row 1: Forward-filled to Chandigarh
        assert records[1].source_market_id == "Chandigarh"
        # Row 2: Panchkula
        assert records[2].source_market_id == "Panchkula"

    def test_column_mapper_agmarknet(self) -> None:
        """Verify mapping of legacy Agmarknet headers to canonical dictionary keys."""
        raw_agmarknet = {
            "Arrival_Date": "15/09/2024",
            "Market": "Chandigarh",
            "Commodity": "Tomato",
            "Modal Price": "2800",
            "Min Price": "2500",
            "Max Price": "3000",
            "Unit of Price": "Rs/Quintal",
            "Arrivals": "35.5",
        }
        mapped = ColumnMapper.map_record(raw_agmarknet, format_name="agmarknet")

        assert mapped["record_date"] == "15/09/2024"
        assert mapped["source_market_id"] == "Chandigarh"
        assert mapped["source_commodity_id"] == "Tomato"
        assert mapped["original_modal_price"] == "2800"
        assert mapped["original_min_price"] == "2500"
        assert mapped["original_max_price"] == "3000"
        assert mapped["original_price_unit"] == "Rs/Quintal"
        assert mapped["arrival_tonnes"] == "35.5"

    def test_missing_file_raises_not_found(self) -> None:
        """Verify proper exception when file does not exist."""
        adapter = LocalCSVSourceAdapter()
        with pytest.raises(FileNotFoundError):
            adapter.read_records("non_existent_file_path.csv")
