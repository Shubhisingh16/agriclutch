"""
Market (Mandi) Pydantic v2 Schemas for AgriClutch.
Enforces Indian territorial coordinate bounds and APMC master contracts.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class MarketBase(BaseModel):
    """Base APMC mandi attributes."""

    id: str = Field(
        ..., description="Canonical AgriClutch identifier derived deterministically (e.g. 'mandi_ch_49')"
    )
    apmc_code: int = Field(..., gt=0, description="Official Agmarknet APMC center code")
    name: str = Field(..., min_length=2, max_length=128, description="Standardized mandi name")
    state: str = Field(..., min_length=2, max_length=64, description="Indian State or Union Territory")
    district: str = Field(..., min_length=2, max_length=64, description="District name")
    latitude: float = Field(..., ge=8.0, le=37.5, description="WGS84 latitude within Indian territory")
    longitude: float = Field(..., ge=68.5, le=97.5, description="WGS84 longitude within Indian territory")
    is_terminal_market: bool = Field(default=False, description="True if high-volume terminal market")
    dca_centre_id: Optional[int] = Field(
        default=None, description="Department of Consumer Affairs reporting center mapping"
    )
    source_market_id: Optional[str] = Field(
        default=None, description="Raw external market identifier from upstream source"
    )


class MarketCreate(MarketBase):
    """Schema for market registration."""

    pass


class MarketResponse(MarketBase):
    """Schema for public API market responses."""

    model_config = ConfigDict(from_attributes=True)

    created_at: datetime = Field(description="Record registration timestamp")
