"""
Crop Perishability & Shelf-Life API Endpoints for AgriClutch.
Provides access to mathematical decay specifications and day-by-day loss trajectories.
SIH26132 — Strengthening Market Linkages and Price Discovery for Farmers.
"""

from typing import List, Optional

from app.schemas.logistics import (
    PerishabilityModelSpecResponse,
    PerishabilityTrajectoryResponse,
)
from app.services.logistics_service import LogisticsService
from fastapi import APIRouter, Query, Response

from ml.logistics.perishability import CROP_STORAGE_MODELS

router = APIRouter(prefix="/perishability", tags=["Crop Perishability & Shelf-Life"])


@router.get(
    "/models",
    response_model=List[PerishabilityModelSpecResponse],
    summary="List Perishability Decay Models",
    description="Retrieve documented mathematical exponential decay specifications: S(t) = exp(-delta * t), F_qual(t) = F0 * exp(-beta * t).",
)
async def list_perishability_models(
    response: Response,
    crop: Optional[str] = Query(None, description="Filter by crop (tomato, onion, potato)"),
    storage_type: Optional[str] = Query(None, description="Filter by storage type (AMBIENT, COLD)"),
) -> List[PerishabilityModelSpecResponse]:
    """Returns active decay model parameters."""
    response.headers["X-AgriClutch-Step"] = "13"
    response.headers["X-AgriClutch-DataSource"] = "DEMO_BENCHMARK_SEED"

    models: List[PerishabilityModelSpecResponse] = []
    for (c, st), spec in CROP_STORAGE_MODELS.items():
        if crop and c.lower() != crop.strip().lower():
            continue
        if storage_type and st.value != storage_type.strip().upper():
            continue
        models.append(PerishabilityModelSpecResponse.model_validate(spec.to_dict()))

    return models


@router.get(
    "/trajectory",
    response_model=PerishabilityTrajectoryResponse,
    summary="Calculate Crop Perishability Trajectory",
    description="Generates daily physical loss and quality grade assay degradation points over modeled duration.",
)
async def get_perishability_trajectory(
    response: Response,
    commodity_id: str = Query("tomato", description="Target agricultural crop"),
    storage_type: str = Query("AMBIENT", description="Storage environment (AMBIENT, COLD)"),
    initial_quantity_kg: float = Query(1000.0, gt=0, description="Initial harvest volume"),
    duration_days: int = Query(7, ge=0, le=90, description="Holding duration in days"),
    initial_quality_factor: float = Query(1.0, ge=0.0, le=1.0, description="Starting quality assay factor"),
) -> PerishabilityTrajectoryResponse:
    """Calculates day-by-day deterioration points."""
    response.headers["X-AgriClutch-Step"] = "13"
    response.headers["X-AgriClutch-DataSource"] = "DEMO_BENCHMARK_SEED"

    result = LogisticsService.calculate_perishability_trajectory(
        commodity_id=commodity_id,
        storage_type=storage_type,
        initial_quantity_kg=initial_quantity_kg,
        duration_days=duration_days,
        initial_quality_factor=initial_quality_factor,
    )
    return PerishabilityTrajectoryResponse.model_validate(result)
