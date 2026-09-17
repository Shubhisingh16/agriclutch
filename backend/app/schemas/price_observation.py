"""
Market Price Observation Pydantic v2 Schemas for AgriClutch.
Enforces price hierarchies, full source provenance, and dual-unit pricing.
"""

from datetime import date, datetime
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator


class PriceObservationBase(BaseModel):
    """Base price observation attributes."""

    # Source Provenance
    source_name: str = Field(..., description="Origin source system identifier")
    source_record_id: Optional[str] = Field(default=None, description="Original record ID if present")
    source_market_id: str = Field(..., description="Raw external market identifier")
    source_commodity_id: str = Field(..., description="Raw external commodity identifier")

    # Canonical References & Dimensions
    market_id: str = Field(..., description="Canonical APMC mandi ID")
    commodity_id: str = Field(..., description="Canonical commodity ID")
    record_date: date = Field(..., description="Trading session date (YYYY-MM-DD)")
    variety: str = Field(default="Common", max_length=64, description="Crop cultivar / variety name")
    grade: str = Field(default="FAQ", max_length=16, description="Commercial grade")

    # Original Source Observation (Auditable)
    original_modal_price: float = Field(..., gt=0.0, description="Raw unscaled modal price")
    original_min_price: float = Field(..., gt=0.0, description="Raw unscaled minimum price")
    original_max_price: float = Field(..., gt=0.0, description="Raw unscaled maximum price")
    original_price_unit: str = Field(..., description="Source price unit (e.g. 'Rs/Quintal', 'INR_PER_KG')")

    # Normalized Canonical Observation (INR/kg)
    normalized_modal_price: float = Field(..., gt=0.0, description="Canonical modal price in INR/kg")
    normalized_min_price: float = Field(..., gt=0.0, description="Canonical minimum price in INR/kg")
    normalized_max_price: float = Field(..., gt=0.0, description="Canonical maximum price in INR/kg")
    normalized_price_unit: str = Field(default="INR_PER_KG", description="Canonical currency per unit")

    # Volume & Analytical Flags
    arrival_tonnes: float = Field(default=0.0, ge=0.0, description="Daily arrival in metric tonnes")
    is_interpolated: bool = Field(default=False, description="True if imputed via monotonic gap fill")
    is_outlier: bool = Field(default=False, description="True if flagged by MAD anomaly detection")

    @model_validator(mode="after")
    def validate_price_bounds(self) -> "PriceObservationBase":
        """Enforces min <= modal <= max hierarchy on both original and normalized prices."""
        if not (self.original_min_price <= self.original_modal_price <= self.original_max_price):
            raise ValueError(
                f"Original price invariant violated: min ({self.original_min_price}) <= "
                f"modal ({self.original_modal_price}) <= max ({self.original_max_price})"
            )
        if not (self.normalized_min_price <= self.normalized_modal_price <= self.normalized_max_price):
            raise ValueError(
                f"Normalized price invariant violated: min ({self.normalized_min_price}) <= "
                f"modal ({self.normalized_modal_price}) <= max ({self.normalized_max_price})"
            )
        return self


class PriceObservationCreate(PriceObservationBase):
    """Schema for creating a price observation with optional explicit observation_id."""

    observation_id: Optional[UUID] = Field(default_factory=uuid4)


class PriceObservationResponse(PriceObservationBase):
    """Schema for public API price observation responses."""

    model_config = ConfigDict(from_attributes=True)

    observation_id: UUID = Field(description="Surrogate observation UUID")
    created_at: datetime = Field(description="Ingestion timestamp")


class PriceFilterParams(BaseModel):
    """Query parameter filter for price observations."""

    commodity_id: Optional[str] = None
    market_id: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)
