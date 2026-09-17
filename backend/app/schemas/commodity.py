"""
Commodity Pydantic v2 Schemas for AgriClutch.
Strict domain contracts for agricultural produce classifications.
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class CropCategory(str, Enum):
    """Perishability and agricultural category classification."""

    PERISHABLE = "perishable"  # Tomato, Leafy Vegetables
    SEMI_PERISHABLE = "semi_perishable"  # Onion, Garlic, Ginger
    STORABLE = "storable"  # Potato
    CEREAL = "cereal"  # Wheat, Paddy, Maize
    PULSE = "pulse"  # Gram, Arhar, Moong


class CommodityBase(BaseModel):
    """Base commodity attributes."""

    id: str = Field(..., description="Unique alphanumeric identifier (e.g., 'tomato', 'onion')")
    name: str = Field(..., min_length=2, max_length=64, description="Standard English display name")
    hindi_name: Optional[str] = Field(default=None, description="Vernacular Hindi name")
    category: CropCategory = Field(..., description="Perishability classification")
    default_spoilage_rate: float = Field(
        ..., ge=0.0, le=1.0, description="Daily exponential decay delta at ambient temperature"
    )
    max_ambient_holding_days: int = Field(
        ..., ge=0, le=365, description="Maximum days safe to store without cold storage"
    )
    standard_moisture_pct: float = Field(
        default=14.0, ge=0.0, le=100.0, description="Standard FAQ moisture content percentage"
    )
    price_unit: str = Field(default="INR_PER_KG", description="Standard pricing unit")
    weight_unit: str = Field(default="KG", description="Standard weight unit")


class CommodityCreate(CommodityBase):
    """Schema for commodity creation."""

    pass


class CommodityResponse(CommodityBase):
    """Schema for public API commodity responses."""

    model_config = ConfigDict(from_attributes=True)

    created_at: datetime = Field(description="Record registration timestamp")
