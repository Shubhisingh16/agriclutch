"""
Source Column Mapping Registry for AgriClutch.
Translates heterogeneous upstream CSV / API headers into canonical domain dictionary keys.
"""

from typing import Any, Dict


class ColumnMapper:
    """
    Translates raw record dictionaries from various upstream sources into standardized keys.
    Isolates source-specific terminology from canonical domain logic.
    """

    AGMARKNET_MAPPINGS: Dict[str, str] = {
        "arrival_date": "record_date",
        "date": "record_date",
        "market": "source_market_id",
        "mandi": "source_market_id",
        "commodity": "source_commodity_id",
        "crop": "source_commodity_id",
        "variety": "variety",
        "grade": "grade",
        "min price": "original_min_price",
        "min_x0020_price": "original_min_price",
        "minprice": "original_min_price",
        "max price": "original_max_price",
        "max_x0020_price": "original_max_price",
        "maxprice": "original_max_price",
        "modal price": "original_modal_price",
        "modal_x0020_price": "original_modal_price",
        "modalprice": "original_modal_price",
        "arrivals": "arrival_tonnes",
        "arrival": "arrival_tonnes",
        "unit of price": "original_price_unit",
        "unit_of_price": "original_price_unit",
        "price_unit": "original_price_unit",
        "unit of arrivals": "original_arrival_unit",
        "unit_of_arrivals": "original_arrival_unit",
        "arrival_unit": "original_arrival_unit",
        "sl no.": "source_record_id",
        "sl_no": "source_record_id",
        "slno": "source_record_id",
    }

    CANONICAL_MAPPINGS: Dict[str, str] = {
        "record_date": "record_date",
        "date": "record_date",
        "source_name": "source_name",
        "source_record_id": "source_record_id",
        "source_market_id": "source_market_id",
        "market_id": "market_id",
        "market": "source_market_id",
        "source_commodity_id": "source_commodity_id",
        "commodity_id": "commodity_id",
        "commodity": "source_commodity_id",
        "variety": "variety",
        "grade": "grade",
        "original_modal_price": "original_modal_price",
        "original_min_price": "original_min_price",
        "original_max_price": "original_max_price",
        "original_price_unit": "original_price_unit",
        "normalized_modal_price": "normalized_modal_price",
        "normalized_min_price": "normalized_min_price",
        "normalized_max_price": "normalized_max_price",
        "normalized_price_unit": "normalized_price_unit",
        "modal_price": "original_modal_price",
        "min_price": "original_min_price",
        "max_price": "original_max_price",
        "price_unit": "original_price_unit",
        "arrival_tonnes": "arrival_tonnes",
        "arrivals": "arrival_tonnes",
        "is_interpolated": "is_interpolated",
        "is_outlier": "is_outlier",
    }

    @classmethod
    def map_record(
        cls,
        raw_payload: Dict[str, Any],
        format_name: str = "canonical",
    ) -> Dict[str, Any]:
        """
        Maps raw dictionary keys to canonical field names based on format_name.

        Args:
            raw_payload: Raw extracted dictionary from source.
            format_name: One of 'canonical', 'agmarknet', or 'auto'.

        Returns:
            Dictionary with canonical keys.
        """
        mapping = cls.CANONICAL_MAPPINGS
        if format_name.lower() == "agmarknet":
            mapping = cls.AGMARKNET_MAPPINGS
        elif format_name.lower() == "auto":
            # Autodetect if Agmarknet markers are present
            raw_lower_keys = {k.strip().lower() for k in raw_payload.keys()}
            if any(k in raw_lower_keys for k in ("modal price", "modal_x0020_price", "arrival_date")):
                mapping = cls.AGMARKNET_MAPPINGS

        mapped: Dict[str, Any] = {}
        for k, v in raw_payload.items():
            norm_key = k.strip().lower()
            target_key = mapping.get(norm_key, norm_key)
            mapped[target_key] = v

        # If source_market_id is not mapped but market_id is present, copy it
        if "source_market_id" not in mapped and "market_id" in mapped:
            mapped["source_market_id"] = mapped["market_id"]

        # If source_commodity_id is not mapped but commodity_id is present, copy it
        if "source_commodity_id" not in mapped and "commodity_id" in mapped:
            mapped["source_commodity_id"] = mapped["commodity_id"]

        return mapped
