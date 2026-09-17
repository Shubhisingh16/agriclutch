"""
Abstract Base Ingestor and Raw Record Container for AgriClutch Data Pipeline.
Preserves raw upstream payloads and source provenance metadata.
"""

from abc import ABC, abstractmethod
from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class RawRecord(BaseModel):
    """
    Unprocessed record container emitted by upstream source adapters.
    Preserves exact source payloads, line numbers, and source identity.
    """

    model_config = ConfigDict(frozen=True)

    source_name: str = Field(..., description="Origin source system identifier")
    source_record_id: Optional[str] = Field(default=None, description="External record identifier")
    source_market_id: Optional[str] = Field(default=None, description="Raw external market string")
    source_commodity_id: Optional[str] = Field(default=None, description="Raw external commodity string")
    payload: Dict[str, Any] = Field(..., description="Raw extracted dictionary payload")
    line_number: Optional[int] = Field(default=None, description="Source file row / line number")
    captured_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class BaseSourceAdapter(ABC):
    """
    Abstract contract for ingesting agricultural price and arrival records.
    Concrete adapters (Local CSV, Parquet, Agmarknet API, DCA) inherit this.
    """

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Identifier for the data source (e.g., 'local_csv', 'agmarknet_api')."""
        pass

    @abstractmethod
    def read_records(
        self,
        file_path: str,
        commodity: Optional[str] = None,
        market: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[RawRecord]:
        """
        Extract raw records from an underlying source.

        Args:
            file_path: Path to target file or endpoint URI.
            commodity: Optional filter for commodity name.
            market: Optional filter for market name.
            start_date: Optional lower date bound.
            end_date: Optional upper date bound.

        Returns:
            List of RawRecord containers.
        """
        pass

    @abstractmethod
    def test_connectivity(self) -> bool:
        """Test reachability of the underlying source asset or filesystem."""
        pass
