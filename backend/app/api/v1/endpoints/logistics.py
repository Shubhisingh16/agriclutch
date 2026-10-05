"""
Logistics & Physical Pathway API Endpoints for AgriClutch.
Provides access to vehicle transport modes, distance and transit duration calculations,
and multi-stage pathway evaluations.
Strictly zero recommendation, ranking, or scoring.
SIH26132 — Strengthening Market Linkages and Price Discovery for Farmers.
"""

from typing import List

from app.db.session import get_db
from app.schemas.logistics import (
    DistanceCalculationRequest,
    DistanceCalculationResponse,
    EvaluatePathwaysRequest,
    EvaluatePathwaysResponse,
    TransportModeResponse,
)
from app.services.logistics_service import LogisticsService
from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/logistics", tags=["Logistics & Transport"])


@router.get(
    "/modes",
    response_model=List[TransportModeResponse],
    summary="List Transport Vehicle Modes",
    description="Retrieve available transport equipment archetypes (Tractor Trolley, LCV, Heavy Truck, Reefer) with capacity and freight rates.",
)
async def list_transport_modes(
    response: Response,
    active_only: bool = Query(True, description="Filter for active transport modes only"),
    db: AsyncSession = Depends(get_db),
) -> List[TransportModeResponse]:
    """Returns available transport modes with provenance metadata."""
    response.headers["X-AgriClutch-Step"] = "13"
    response.headers["X-AgriClutch-DataSource"] = "DEMO_BENCHMARK_SEED"

    modes = await LogisticsService.get_transport_modes(session=db, active_only=active_only)
    return [TransportModeResponse.model_validate(m) for m in modes]


@router.post(
    "/distance",
    response_model=DistanceCalculationResponse,
    summary="Calculate Geodesic or Road Distance",
    description="Computes spherical Haversine distance and estimated transit hours. Explicitly identifies distance type and never fabricates road routes.",
)
async def calculate_distance(
    payload: DistanceCalculationRequest,
    response: Response,
) -> DistanceCalculationResponse:
    """Calculates route distance and duration metrics."""
    response.headers["X-AgriClutch-Step"] = "13"
    response.headers["X-AgriClutch-DataSource"] = "DEMO_BENCHMARK_SEED"

    res = LogisticsService.calculate_distance(payload)
    return DistanceCalculationResponse.model_validate(res)


@router.post(
    "/evaluate",
    response_model=EvaluatePathwaysResponse,
    summary="Evaluate Physical Logistics Pathways",
    description="Evaluates Scenarios A, B, C, D (Direct Buyer, Storage Holding, Regional Mandi, Cold Chain Terminal) with elapsed hours, loss, and costs. Purely descriptive with zero recommendation leakage.",
)
async def evaluate_pathways(
    payload: EvaluatePathwaysRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> EvaluatePathwaysResponse:
    """Evaluates multi-stage logistics pathways for produce lot."""
    response.headers["X-AgriClutch-Step"] = "13"
    response.headers["X-AgriClutch-DataSource"] = "DEMO_BENCHMARK_SEED"

    result = await LogisticsService.evaluate_pathways(request=payload, session=db)
    return EvaluatePathwaysResponse.model_validate(result)
