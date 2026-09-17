"""
Concrete Agricultural Data Validator for AgriClutch.
Validates required dimensions, pricing hierarchies, arrivals, and natural observation uniqueness.
"""

from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple

from app.schemas.validation import (
    ValidationIssue,
    ValidationReport,
    ValidationSeverity,
    ValidationStatus,
)

from pipeline.ingestion.market_resolver import MarketResolver, default_market_resolver
from pipeline.validation.base import BaseDataValidator


class AgriDataValidator(BaseDataValidator):
    """
    Deterministic domain validator enforcing contracts from docs/DATA_CONTRACT.md.
    Never silently discards malformed records; emits structured issues and health scores.
    """

    KNOWN_COMMODITIES = {"tomato", "onion", "potato", "wheat", "rice", "mustard"}

    VALID_PRICE_UNITS = {
        "rs/quintal",
        "inr_per_quintal",
        "rs./quintal",
        "rs/qtl",
        "inr/quintal",
        "inr_per_kg",
        "rs/kg",
        "rs./kg",
        "inr/kg",
    }

    def __init__(self, market_resolver: Optional[MarketResolver] = None) -> None:
        self.market_resolver = market_resolver or default_market_resolver

    @staticmethod
    def parse_date(date_val: Any) -> Optional[date]:
        """Parse varied string dates into standard datetime.date."""
        if isinstance(date_val, date) and not isinstance(date_val, datetime):
            return date_val
        if isinstance(date_val, datetime):
            return date_val.date()
        if not isinstance(date_val, str):
            return None

        clean_str = date_val.strip()
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d"):
            try:
                return datetime.strptime(clean_str, fmt).date()
            except ValueError:
                continue
        return None

    def validate_record(
        self,
        record: Dict[str, Any],
        row_num: Optional[int] = None,
    ) -> Tuple[ValidationStatus, List[ValidationIssue]]:
        """Validate an individual record dictionary."""
        issues: List[ValidationIssue] = []

        # 1. Validate Date
        raw_date = record.get("record_date")
        if not raw_date:
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    field="record_date",
                    message="Missing required field: record_date",
                    raw_value=raw_date,
                    row_number=row_num,
                )
            )
        else:
            parsed_d = self.parse_date(raw_date)
            if parsed_d is None:
                issues.append(
                    ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        field="record_date",
                        message="Invalid date format. Expected YYYY-MM-DD or DD/MM/YYYY",
                        raw_value=raw_date,
                        row_number=row_num,
                    )
                )

        # 2. Validate Market
        src_market = record.get("source_market_id") or record.get("market_id")
        if not src_market or not str(src_market).strip():
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    field="source_market_id",
                    message="Missing required field: source_market_id / market_id",
                    raw_value=src_market,
                    row_number=row_num,
                )
            )
        else:
            # Check market resolution
            canonical_mandi = self.market_resolver.resolve_market(source_market_str=str(src_market))
            if not canonical_mandi:
                issues.append(
                    ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        field="source_market_id",
                        message=f"Market '{src_market}' not found in authoritative master registry.",
                        raw_value=src_market,
                        row_number=row_num,
                    )
                )

        # 3. Validate Commodity
        src_crop = record.get("source_commodity_id") or record.get("commodity_id")
        if not src_crop or not str(src_crop).strip():
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    field="source_commodity_id",
                    message="Missing required field: source_commodity_id / commodity_id",
                    raw_value=src_crop,
                    row_number=row_num,
                )
            )
        else:
            crop_slug = str(src_crop).strip().lower()
            if crop_slug not in self.KNOWN_COMMODITIES:
                issues.append(
                    ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        field="source_commodity_id",
                        message=f"Commodity '{src_crop}' is outside standard benchmark commodities.",
                        raw_value=src_crop,
                        row_number=row_num,
                    )
                )

        # 4. Validate Prices
        modal_raw = record.get("original_modal_price") or record.get("modal_price")
        min_raw = record.get("original_min_price") or record.get("min_price")
        max_raw = record.get("original_max_price") or record.get("max_price")

        modal_val: Optional[float] = None
        min_val: Optional[float] = None
        max_val: Optional[float] = None

        if modal_raw is None or str(modal_raw).strip() == "":
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    field="original_modal_price",
                    message="Missing required price: original_modal_price",
                    raw_value=modal_raw,
                    row_number=row_num,
                )
            )
        else:
            try:
                modal_val = float(modal_raw)
                if modal_val <= 0.0:
                    issues.append(
                        ValidationIssue(
                            severity=ValidationSeverity.ERROR,
                            field="original_modal_price",
                            message="Modal price must be strictly positive (> 0.0)",
                            raw_value=modal_val,
                            row_number=row_num,
                        )
                    )
            except (ValueError, TypeError):
                issues.append(
                    ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        field="original_modal_price",
                        message="Modal price could not be converted to float",
                        raw_value=modal_raw,
                        row_number=row_num,
                    )
                )

        if min_raw is not None and str(min_raw).strip() != "":
            try:
                min_val = float(min_raw)
                if min_val <= 0.0:
                    issues.append(
                        ValidationIssue(
                            severity=ValidationSeverity.ERROR,
                            field="original_min_price",
                            message="Minimum price must be strictly positive (> 0.0)",
                            raw_value=min_val,
                            row_number=row_num,
                        )
                    )
            except (ValueError, TypeError):
                issues.append(
                    ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        field="original_min_price",
                        message="Minimum price could not be converted to float",
                        raw_value=min_raw,
                        row_number=row_num,
                    )
                )

        if max_raw is not None and str(max_raw).strip() != "":
            try:
                max_val = float(max_raw)
                if max_val <= 0.0:
                    issues.append(
                        ValidationIssue(
                            severity=ValidationSeverity.ERROR,
                            field="original_max_price",
                            message="Maximum price must be strictly positive (> 0.0)",
                            raw_value=max_val,
                            row_number=row_num,
                        )
                    )
            except (ValueError, TypeError):
                issues.append(
                    ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        field="original_max_price",
                        message="Maximum price could not be converted to float",
                        raw_value=max_raw,
                        row_number=row_num,
                    )
                )

        # Hierarchy validation
        if modal_val is not None and min_val is not None and max_val is not None:
            if not (min_val <= modal_val <= max_val):
                issues.append(
                    ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        field="prices",
                        message=f"Price hierarchy violation: min ({min_val}) <= modal ({modal_val}) <= max ({max_val})",
                        raw_value={"min": min_val, "modal": modal_val, "max": max_val},
                        row_number=row_num,
                    )
                )

        # 5. Validate Arrivals
        arr_raw = record.get("arrival_tonnes") or record.get("arrivals")
        if arr_raw is not None and str(arr_raw).strip() != "":
            try:
                arr_val = float(arr_raw)
                if arr_val < 0.0:
                    issues.append(
                        ValidationIssue(
                            severity=ValidationSeverity.ERROR,
                            field="arrival_tonnes",
                            message="Arrival volume cannot be negative",
                            raw_value=arr_val,
                            row_number=row_num,
                        )
                    )
            except (ValueError, TypeError):
                issues.append(
                    ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        field="arrival_tonnes",
                        message="Arrivals could not be converted to float",
                        raw_value=arr_raw,
                        row_number=row_num,
                    )
                )

        # 6. Validate Units
        unit_raw = record.get("original_price_unit") or record.get("price_unit")
        if not unit_raw:
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    field="original_price_unit",
                    message="Missing price unit; defaulting to 'Rs/Quintal'",
                    raw_value=unit_raw,
                    row_number=row_num,
                )
            )
        elif str(unit_raw).strip().lower() not in self.VALID_PRICE_UNITS:
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    field="original_price_unit",
                    message=f"Unrecognized price unit: '{unit_raw}'",
                    raw_value=unit_raw,
                    row_number=row_num,
                )
            )

        # Determine overall status
        has_errors = any(i.severity == ValidationSeverity.ERROR for i in issues)
        has_warnings = any(i.severity == ValidationSeverity.WARNING for i in issues)

        if has_errors:
            status = ValidationStatus.INVALID
        elif has_warnings:
            status = ValidationStatus.WARNING
        else:
            status = ValidationStatus.VALID

        return status, issues

    def validate_batch(
        self,
        records: List[Dict[str, Any]],
        source_name: str,
    ) -> Tuple[List[Dict[str, Any]], ValidationReport]:
        """
        Validate a batch of records, evaluate natural identity duplicates,
        and calculate the dataset health scorecard.
        """
        valid_records: List[Dict[str, Any]] = []
        all_errors: List[ValidationIssue] = []
        all_warnings: List[ValidationIssue] = []

        valid_count = 0
        warning_count = 0
        invalid_count = 0
        duplicate_count = 0

        seen_natural_identities: Set[Tuple[str, str, str, str, str]] = set()

        for idx, rec in enumerate(records, start=1):
            status, issues = self.validate_record(rec, row_num=idx)

            for issue in issues:
                if issue.severity == ValidationSeverity.ERROR:
                    all_errors.append(issue)
                else:
                    all_warnings.append(issue)

            if status == ValidationStatus.INVALID:
                invalid_count += 1
                continue

            # Evaluate duplicate observations based on natural identity:
            # (record_date, canonical_market_id, commodity_id, variety, grade)
            parsed_d = self.parse_date(rec.get("record_date"))
            d_str = parsed_d.isoformat() if parsed_d else str(rec.get("record_date"))

            src_m = str(rec.get("source_market_id") or rec.get("market_id") or "").strip()
            canonical_m = self.market_resolver.get_canonical_id(src_m) or src_m

            src_c = str(rec.get("source_commodity_id") or rec.get("commodity_id") or "").strip().lower()
            variety = str(rec.get("variety") or "Common").strip()
            grade = str(rec.get("grade") or "FAQ").strip()

            natural_key = (d_str, canonical_m, src_c, variety, grade)

            if natural_key in seen_natural_identities:
                duplicate_count += 1
                dup_issue = ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    field="natural_identity",
                    message=f"Duplicate observation detected for key: {natural_key}",
                    raw_value=natural_key,
                    row_number=idx,
                )
                all_warnings.append(dup_issue)
                # Keep latest observation by updating or skipping
            else:
                seen_natural_identities.add(natural_key)

            if status == ValidationStatus.WARNING:
                warning_count += 1
            else:
                valid_count += 1

            valid_records.append(rec)

        total = len(records)
        if total > 0:
            penalty = (
                (len(all_errors) * 0.4 / total)
                + (len(all_warnings) * 0.1 / total)
                + (duplicate_count * 0.2 / total)
            )
            health_score = max(0.0, min(100.0, round((1.0 - penalty) * 100.0, 2)))
        else:
            health_score = 100.0

        report = ValidationReport(
            source=source_name,
            total_records=total,
            valid_records=valid_count,
            warning_records=warning_count,
            invalid_records=invalid_count,
            duplicate_records=duplicate_count,
            errors=all_errors,
            warnings=all_warnings,
            health_score=health_score,
            generated_at=datetime.now(timezone.utc),
        )

        return valid_records, report
