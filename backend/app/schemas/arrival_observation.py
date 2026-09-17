"""
Market Arrival Observation Pydantic v2 Schemas for AgriClutch.
Enforces arrival metrics and source provenance tracking.
"""

from datetime import date, datetime
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class ArrivalObservationBase(BaseModel):
    """Base arrival observation attributes."""

    source_name: str = Field(..., description="Origin source system identifier")
    source_record_id: Optional[str] = Field(default=None)
    source_market_id: str = Field(..., description="Raw external market identifier")
    source_commodity_id: str = Field(..., description="Raw external commodity identifier")

    market_id: str = Field(..., description="Canonical APMC mandi ID")
    commodity_id: str = Field(..., description="Canonical commodity ID")
    record_date: date = Field(..., description="Arrival trading date (YYYY-MM-DD)")
    arrival_tonnes: float = Field(..., ge=0.0, description="Volume in metric tonnes")
    original_arrival_unit: str = Field(default="Tonnes", description="Unit as reported by source")
    normalized_arrival_unit: str = Field(default="METRIC_TONNE", description="Canonical weight unit")
    truck_count_estimate: Optional[int] = Field(default=None, ge=0)


class ArrivalObservationCreate(ArrivalObservationBase):
    """Schema for creating an arrival observation."""

    observation_id: Optional[UUID] = Field(default_factory=uuid4)


class ArrivalObservationResponse(ArrivalObservationBase):
    """Schema for public API arrival observation responses."""

    model_config = ConfigDict(from_attributes=True)

    observation_id: UUID = Field(description="Surrogate observation UUID")
    created_at: datetime = Field(description="Ingestion timestamp")
