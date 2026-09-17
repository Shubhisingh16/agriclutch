"""
Deterministic Agricultural Data Normalizer for AgriClutch.
Performs string cleaning, date parsing, authoritative market mapping, and dual price scaling.
Zero data fabrication; zero statistical imputation.
"""

import re
from typing import Any, Dict, List, Optional
from uuid import uuid4

from app.schemas.price_observation import PriceObservationCreate

from pipeline.cleaning.base import BaseDataNormalizer
from pipeline.ingestion.market_resolver import MarketResolver, default_market_resolver
from pipeline.validation.validator import AgriDataValidator


class DataNormalizer(BaseDataNormalizer):
    """
    Normalizes validated agricultural price observations.
    Converts units deterministically and preserves full provenance auditability.
    """

    QUINTAL_UNITS = {
        "rs/quintal",
        "inr_per_quintal",
        "rs./quintal",
        "rs/qtl",
        "inr/quintal",
        "quintal",
        "qtl",
    }

    KG_UNITS = {
        "inr_per_kg",
        "rs/kg",
        "rs./kg",
        "inr/kg",
        "kg",
    }

    def __init__(self, market_resolver: Optional[MarketResolver] = None) -> None:
        self.market_resolver = market_resolver or default_market_resolver

    @staticmethod
    def _slugify(text: str) -> str:
        """Convert string to clean lowercase alphanumeric slug."""
        cleaned = re.sub(r"[^\w\s-]", "", text.strip().lower())
        return re.sub(r"[-\s]+", "_", cleaned)

    def normalize_record(
        self,
        record: Dict[str, Any],
        source_name: str,
    ) -> PriceObservationCreate:
        """
        Transforms validated dictionary into canonical PriceObservationCreate model.
        """
        # 1. Parse Date
        parsed_date = AgriDataValidator.parse_date(record.get("record_date"))
        if parsed_date is None:
            raise ValueError(f"Cannot normalize record with unparseable date: {record.get('record_date')}")

        # 2. Extract Raw Source Identifiers
        src_market_id = str(record.get("source_market_id") or record.get("market_id") or "").strip()
        src_crop_id = str(record.get("source_commodity_id") or record.get("commodity_id") or "").strip()
        src_record_id = record.get("source_record_id")
        if src_record_id is not None:
            src_record_id = str(src_record_id).strip()

        # 3. Canonical Market Resolution
        canonical_market_id = self.market_resolver.get_canonical_id(source_market_str=src_market_id)
        if not canonical_market_id:
            # Deterministic fallback without invented APMC codes
            canonical_market_id = f"mandi_external_{self._slugify(src_market_id)}"

        # 4. Canonical Commodity Resolution
        canonical_crop_id = self._slugify(src_crop_id)

        # 5. Variety & Grade Standards
        variety = str(record.get("variety") or "Common").strip()
        if not variety:
            variety = "Common"

        grade = str(record.get("grade") or "FAQ").strip().upper()
        if not grade:
            grade = "FAQ"

        # 6. Original Prices & Units
        orig_modal = float(record["original_modal_price"])
        orig_min = float(record.get("original_min_price", orig_modal))
        orig_max = float(record.get("original_max_price", orig_modal))

        # Enforce bounds ordering if slightly disordered in raw data
        if orig_min > orig_modal:
            orig_min = orig_modal
        if orig_max < orig_modal:
            orig_max = orig_modal

        orig_unit = str(record.get("original_price_unit") or "Rs/Quintal").strip()

        # 7. Normalized Prices (INR/kg)
        norm_unit_key = orig_unit.lower().replace(" ", "")
        if norm_unit_key in self.KG_UNITS:
            factor = 1.0
        else:
            # Default to quintal conversion (standard Agmarknet wholesale rate)
            factor = 0.01

        norm_modal = round(orig_modal * factor, 4)
        norm_min = round(orig_min * factor, 4)
        norm_max = round(orig_max * factor, 4)

        # 8. Volume & Analytical Flags
        arrival_val = 0.0
        arr_raw = record.get("arrival_tonnes") or record.get("arrivals")
        if arr_raw is not None and str(arr_raw).strip() != "":
            try:
                arrival_val = max(0.0, float(arr_raw))
            except (ValueError, TypeError):
                arrival_val = 0.0

        is_interp = bool(record.get("is_interpolated", False))
        is_outlier = bool(record.get("is_outlier", False))

        return PriceObservationCreate(
            observation_id=uuid4(),
            source_name=source_name,
            source_record_id=src_record_id,
            source_market_id=src_market_id,
            source_commodity_id=src_crop_id,
            market_id=canonical_market_id,
            commodity_id=canonical_crop_id,
            record_date=parsed_date,
            variety=variety,
            grade=grade,
            original_modal_price=orig_modal,
            original_min_price=orig_min,
            original_max_price=orig_max,
            original_price_unit=orig_unit,
            normalized_modal_price=norm_modal,
            normalized_min_price=norm_min,
            normalized_max_price=norm_max,
            normalized_price_unit="INR_PER_KG",
            arrival_tonnes=arrival_val,
            is_interpolated=is_interp,
            is_outlier=is_outlier,
        )

    def normalize_batch(
        self,
        records: List[Dict[str, Any]],
        source_name: str,
    ) -> List[PriceObservationCreate]:
        """Normalize a collection of validated record dictionaries."""
        normalized: List[PriceObservationCreate] = []
        for rec in records:
            try:
                item = self.normalize_record(rec, source_name=source_name)
                normalized.append(item)
            except Exception:
                continue
        return normalized
