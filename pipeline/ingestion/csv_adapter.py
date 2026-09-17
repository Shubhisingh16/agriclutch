"""
Local CSV Source Adapter for AgriClutch.
Extracts agricultural price and arrival observations from local CSV files.
Features Git LFS / merge conflict auto-stripping and stateful Agmarknet forward-filling.
"""

import csv
import os
import re
from datetime import date
from typing import Any, Dict, List, Optional

from pipeline.ingestion.base import BaseSourceAdapter, RawRecord


class LocalCSVSourceAdapter(BaseSourceAdapter):
    """
    Source adapter for ingesting local CSV files.
    Robustly handles malformed headers, merge conflict markers, and missing continuation values.
    """

    GIT_CONFLICT_PATTERNS = [
        re.compile(r"^<{7}"),  # <<<<<<<
        re.compile(r"^={7}"),  # =======
        re.compile(r"^>{7}"),  # >>>>>>>
        re.compile(r"^version https://git-lfs"),
        re.compile(r"^oid sha256:"),
        re.compile(r"^size \d+"),
    ]

    def __init__(self, source_name: str = "LOCAL_CSV") -> None:
        self._source_name = source_name

    @property
    def source_name(self) -> str:
        return self._source_name

    def test_connectivity(self) -> bool:
        """Returns True if local filesystem environment is functional."""
        return True

    def read_records(
        self,
        file_path: str,
        commodity: Optional[str] = None,
        market: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[RawRecord]:
        """
        Reads CSV rows into RawRecord objects.
        Discards Git LFS/merge artifacts and forward-fills grouped market names.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Input CSV file not found: {file_path}")

        raw_lines: List[tuple[int, str]] = []
        encodings = ["utf-8-sig", "utf-8", "latin-1"]
        lines_read = False

        for enc in encodings:
            try:
                with open(file_path, "r", encoding=enc) as f:
                    for line_num, line in enumerate(f, start=1):
                        raw_lines.append((line_num, line))
                lines_read = True
                break
            except (UnicodeDecodeError, OSError):
                raw_lines.clear()
                continue

        if not lines_read:
            raise ValueError(f"Unable to read {file_path} with supported encodings.")

        # Filter out Git LFS pointers and merge conflict headers
        clean_lines: List[tuple[int, str]] = []
        for line_num, line in raw_lines:
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith("#"):
                continue
            if any(p.search(stripped) for p in self.GIT_CONFLICT_PATTERNS):
                continue
            clean_lines.append((line_num, line))

        if not clean_lines:
            return []

        # Find header line and parse with csv.DictReader
        header_line_num, header_text = clean_lines[0]
        data_lines = [line for _, line in clean_lines]

        reader = csv.DictReader(data_lines)
        records: List[RawRecord] = []
        last_seen_market: Optional[str] = None

        # Determine line numbers offset
        for idx, row in enumerate(reader):
            actual_line_num = clean_lines[min(idx + 1, len(clean_lines) - 1)][0]

            cleaned_row: Dict[str, Any] = {}
            for k, v in row.items():
                if k is not None:
                    cleaned_row[k.strip()] = v.strip() if isinstance(v, str) else v

            # Stateful forward-fill of market name if blank in grouped Agmarknet tables
            market_col = None
            for candidate in ("Market", "market", "mandi", "source_market_id", "market_id"):
                if candidate in cleaned_row:
                    market_col = candidate
                    break

            if market_col:
                val = cleaned_row.get(market_col)
                if val and str(val).strip():
                    last_seen_market = str(val).strip()
                elif last_seen_market:
                    cleaned_row[market_col] = last_seen_market

            # Extract source IDs if present
            src_market = cleaned_row.get(market_col) if market_col else None
            src_crop = None
            for c in ("Commodity", "commodity", "crop", "source_commodity_id", "commodity_id"):
                if c in cleaned_row and cleaned_row[c]:
                    src_crop = str(cleaned_row[c]).strip()
                    break

            src_rec_id = None
            for s in ("Sl no.", "sl_no", "slno", "id", "source_record_id"):
                if s in cleaned_row and cleaned_row[s]:
                    src_rec_id = str(cleaned_row[s]).strip()
                    break

            raw_record = RawRecord(
                source_name=self.source_name,
                source_record_id=src_rec_id,
                source_market_id=str(src_market) if src_market else None,
                source_commodity_id=str(src_crop) if src_crop else None,
                payload=cleaned_row,
                line_number=actual_line_num,
            )
            records.append(raw_record)

        return records
