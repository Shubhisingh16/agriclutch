"""
Agricultural Time-Series Dataset Preparation & Sufficiency Verification.
Ensures strictly chronological, auditable, leakage-free time-series series.
SIH26132 — Market Linkages and Price Discovery for Farmers.
"""

from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import date
from typing import Any


@dataclass
class DateGap:
    """Represents an observed calendar gap between consecutive trading sessions."""

    start_date: str
    end_date: str
    calendar_days_missing: int
    gap_type: str  # 'EXPECTED_CALENDAR_GAP' or 'UNEXPECTED_REPORTING_GAP'


@dataclass
class TimeSeriesDataset:
    """
    Structured container for commodity market historical price observations.
    Enforces chronological integrity, deduplication, and data sufficiency gates.
    """

    commodity_id: str
    market_id: str
    dates: list[str]
    prices: list[float]
    arrivals: list[float] = field(default_factory=list)
    source_records: list[str] = field(default_factory=list)
    gaps: list[DateGap] = field(default_factory=list)

    @classmethod
    def from_records(
        cls,
        records: Sequence[Any],
        commodity_id: str,
        market_id: str,
    ) -> "TimeSeriesDataset":
        """
        Builds a verified TimeSeriesDataset from an arbitrary sequence of price records.
        Handles both ORM models and dictionary payloads.

        Args:
            records: Sequence of price observations.
            commodity_id: Target commodity slug.
            market_id: Target canonical mandi ID.
        """
        parsed_items: list[tuple[date, float, float, str]] = []

        for r in records:
            if isinstance(r, dict):
                rec_date_raw = r.get("record_date")
                price_raw = r.get("normalized_modal_price")
                arr_raw = r.get("arrival_tonnes", 0.0)
                src_id = str(r.get("source_record_id", ""))
            else:
                rec_date_raw = getattr(r, "record_date", None)
                price_raw = getattr(r, "normalized_modal_price", None)
                arr_raw = getattr(r, "arrival_tonnes", 0.0)
                src_id = str(getattr(r, "source_record_id", ""))

            if isinstance(rec_date_raw, str):
                rec_date = date.fromisoformat(rec_date_raw)
            elif isinstance(rec_date_raw, date):
                rec_date = rec_date_raw
            else:
                continue

            if price_raw is None:
                continue
            price = float(price_raw)
            arrival = float(arr_raw or 0.0)

            parsed_items.append((rec_date, price, arrival, src_id))

        # 1. Chronological Sorting (Ascending)
        parsed_items.sort(key=lambda x: x[0])

        # 2. Deterministic Deduplication by Date
        # If multiple records exist on the same date, average price and sum arrivals
        dedup_dates: list[date] = []
        dedup_prices: list[float] = []
        dedup_arrivals: list[float] = []
        dedup_src_ids: list[str] = []

        date_groups: dict[date, list[tuple[float, float, str]]] = {}
        for d, p, a, sid in parsed_items:
            if d not in date_groups:
                date_groups[d] = []
            date_groups[d].append((p, a, sid))

        for d in sorted(date_groups.keys()):
            group = date_groups[d]
            avg_p = sum(item[0] for item in group) / len(group)
            sum_a = sum(item[1] for item in group)
            sids = ",".join(item[2] for item in group if item[2])
            dedup_dates.append(d)
            dedup_prices.append(round(avg_p, 4))
            dedup_arrivals.append(round(sum_a, 4))
            dedup_src_ids.append(sids)

        # 3. Calendar Gap Detection (Without Silent Imputation)
        detected_gaps: list[DateGap] = []
        for i in range(len(dedup_dates) - 1):
            curr_d = dedup_dates[i]
            next_d = dedup_dates[i + 1]
            diff = (next_d - curr_d).days
            if diff > 1:
                # Monday is weekday 0, Friday is 4, Sunday is 6
                # Weekend gap is typically 2 or 3 calendar days (Fri->Mon is 3)
                gap_type = (
                    "EXPECTED_CALENDAR_GAP"
                    if (diff <= 3 and curr_d.weekday() in (4, 5))
                    else "UNEXPECTED_REPORTING_GAP"
                )
                detected_gaps.append(
                    DateGap(
                        start_date=curr_d.isoformat(),
                        end_date=next_d.isoformat(),
                        calendar_days_missing=diff - 1,
                        gap_type=gap_type,
                    )
                )

        return cls(
            commodity_id=commodity_id,
            market_id=market_id,
            dates=[d.isoformat() for d in dedup_dates],
            prices=dedup_prices,
            arrivals=dedup_arrivals,
            source_records=dedup_src_ids,
            gaps=detected_gaps,
        )

    def check_sufficiency(self, min_observations: int = 30) -> tuple[bool, int, str]:
        """
        Evaluates whether the series meets minimum length criteria for forecasting.

        Returns:
            Tuple of (is_sufficient, count, detail_message).
        """
        count = len(self.prices)
        if count < min_observations:
            msg = (
                f"Series contains {count} trading sessions; minimum "
                f"{min_observations} required for dependable forecasting."
            )
            return False, count, msg
        return True, count, f"Sufficient history: {count} trading sessions available."

    @property
    def origin_date(self) -> str | None:
        """Date of the latest physical observation (forecast origin t0)."""
        return self.dates[-1] if self.dates else None

    @property
    def observation_count(self) -> int:
        """Total distinct valid trading sessions."""
        return len(self.prices)
