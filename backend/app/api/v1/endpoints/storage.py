"""
Storage Facility & Holding API Endpoints for AgriClutch.
Provides access to storage facility listings, real-time availability lookups,
and capacity / duration feasibility evaluations.
SIH26132 — Strengthening Market Linkages and Price Discovery for Farmers.
"""

from typing import List, Optional

from app.db.session import get_db
from app.schemas.logistics import (
    StorageAvailabilityResponse,
    StorageFacilityResponse,
    StorageFeasibilityResponse,
)
from app.services.logistics_service import LogisticsService
from fastapi import APIRouter, Depends, Query, Response
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/storage", tags=["Storage & Warehousing"])


class StorageFeasibilityRequest(BaseModel):
    """Payload for evaluating storage holding feasibility."""
    facility_id: str
    requested_quantity_kg: float = Field(..., gt=0)
    requested_duration_days: int = Field(..., ge=0)


@router.get(
    "/facilities",
    response_model=List[StorageFacilityResponse],
    summary="List Storage Facilities",
    description="Retrieve storage warehouses, silos, and cold-chain hubs with capacity, cost, and temperature controls.",
)
async def list_storage_facilities(
    response: Response,
    storage_type: Optional[str] = Query(None, description="Filter by storage type (AMBIENT, COLD, VENTILATED)"),
    db: AsyncSession = Depends(get_db),
) -> List[StorageFacilityResponse]:
    """Returns storage facilities."""
    response.headers["X-AgriClutch-Step"] = "13"
    response.headers["X-AgriClutch-DataSource"] = "DEMO_BENCHMARK_SEED"

    facilities = await LogisticsService.get_storage_facilities(session=db, storage_type=storage_type)
    return [StorageFacilityResponse.model_validate(f) for f in facilities]


@router.get(
    "/facilities/{facility_id}/availability",
    response_model=StorageAvailabilityResponse,
    summary="Get Storage Facility Capacity & Availability",
    description="Query available capacity and commercial holding fees for a designated facility.",
)
async def get_storage_availability(
    facility_id: str,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> StorageAvailabilityResponse:
    """Returns capacity availability for specified facility."""
    response.headers["X-AgriClutch-Step"] = "13"
    response.headers["X-AgriClutch-DataSource"] = "DEMO_BENCHMARK_SEED"

    avail = await LogisticsService.get_storage_availability(facility_id=facility_id, session=db)
    return StorageAvailabilityResponse.model_validate(avail)


@router.post(
    "/evaluate",
    response_model=StorageFeasibilityResponse,
    summary="Evaluate Storage Feasibility",
    description="Evaluates whether a produce quantity can be stored for a duration, returning stored vs unstored partition.",
)
async def evaluate_storage(
    payload: StorageFeasibilityRequest,
    response: Response,
) -> StorageFeasibilityResponse:
    """Evaluates holding feasibility and fees."""
    response.headers["X-AgriClutch-Step"] = "13"
    response.headers["X-AgriClutch-DataSource"] = "DEMO_BENCHMARK_SEED"

    result = LogisticsService.evaluate_storage_feasibility(
        facility_id=payload.facility_id,
        requested_quantity_kg=payload.requested_quantity_kg,
        requested_duration_days=payload.requested_duration_days,
    )
    return StorageFeasibilityResponse.model_validate(result)
