"""
AgriClutch REST API Endpoints for Produce Lot Buyer Matching.
Evaluates bipartite compatibility between farmer produce lots and candidate buyers
across commodity, variety, quality grade, quantity bounds, temporal windows, and distance.
SIH26132 — Strengthening Market Linkages and Price Discovery for Farmers.
"""

from datetime import date, timedelta
from typing import List, Optional

from app.config import settings
from app.db.session import get_db
from app.schemas.buyer import (
    FarmerSupplyRequest,
    MatchingListResponse,
)
from app.services.buyer_service import BuyerService
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/buyer-matching", tags=["Buyer Compatibility Matching Engine"])


def _apply_headers(response: Response, data_mode: Optional[str] = None) -> None:
    mode = data_mode or settings.DATA_MODE
    if mode.lower() == "demo":
        response.headers["X-AgriClutch-Data-Mode"] = "DEMO"
        response.headers["X-AgriClutch-DataSource"] = "DEMO_BENCHMARK_SEED"
    else:
        response.headers["X-AgriClutch-Data-Mode"] = "DATABASE"
        response.headers["X-AgriClutch-DataSource"] = "POSTGRESQL"


@router.post(
    "",
    response_model=MatchingListResponse,
    summary="Evaluate Buyer Compatibility for Farmer Supply Lot",
    description="Calculates deterministic multi-dimensional compatibility without normative ranking or recommendation scores.",
)
async def evaluate_buyer_matching(
    supply: FarmerSupplyRequest,
    response: Response,
    max_distance_km: Optional[float] = Query(None, description="Optional maximum search radius in km", ge=1.0),
    data_mode: Optional[str] = Query(None, description="Operational data mode override ('demo', 'database')"),
    db: AsyncSession = Depends(get_db),
) -> MatchingListResponse:
    _apply_headers(response, data_mode)
    service = BuyerService(db=db)
    return await service.match_supply(
        supply=supply,
        max_distance_km=max_distance_km,
        data_mode=data_mode,
    )


@router.get(
    "",
    response_model=MatchingListResponse,
    summary="Evaluate Buyer Compatibility (Query Parameter Interface)",
    description="Convenience endpoint evaluating compatibility from GET query parameters.",
)
async def evaluate_buyer_matching_query(
    response: Response,
    commodity_id: str = Query("tomato", description="Commodity identifier (e.g. 'tomato', 'onion', 'potato')"),
    quantity_kg: float = Query(2500.0, description="Available lot quantity in kg", gt=0),
    quality_grade: str = Query("GRADE_A", description="Produce quality grade (GRADE_A, GRADE_B, GRADE_C)"),
    origin_location: str = Query("Mohali Rural Farmgate", description="Dispatch farmgate location"),
    origin_latitude: Optional[float] = Query(30.6970, description="Farmgate latitude"),
    origin_longitude: Optional[float] = Query(76.6948, description="Farmgate longitude"),
    available_days: int = Query(7, description="Holding readiness duration in days", ge=1),
    max_distance_km: Optional[float] = Query(None, description="Maximum haulage distance filter in km", ge=1.0),
    data_mode: Optional[str] = Query(None, description="Operational data mode override ('demo', 'database')"),
    db: AsyncSession = Depends(get_db),
) -> MatchingListResponse:
    _apply_headers(response, data_mode)
    service = BuyerService(db=db)
    today = date(2024, 9, 15)  # Benchmark demo epoch
    supply = FarmerSupplyRequest(
        id="supply_query_auto",
        commodity_id=commodity_id,
        quantity_kg=quantity_kg,
        quality_grade=quality_grade,
        available_from=today,
        available_until=today + timedelta(days=available_days),
        origin_location=origin_location,
        origin_latitude=origin_latitude,
        origin_longitude=origin_longitude,
    )
    return await service.match_supply(
        supply=supply,
        max_distance_km=max_distance_km,
        data_mode=data_mode,
    )


@router.get(
    "/sample-supplies",
    response_model=List[FarmerSupplyRequest],
    summary="Get Pre-configured Sample Produce Supply Lots",
    description="Retrieves documented benchmark produce lots for rapid frontend demonstration.",
)
async def get_sample_supplies(
    response: Response,
    commodity_id: Optional[str] = Query(None, description="Filter sample supplies by commodity"),
    data_mode: Optional[str] = Query(None, description="Operational data mode override ('demo', 'database')"),
    db: AsyncSession = Depends(get_db),
) -> List[FarmerSupplyRequest]:
    _apply_headers(response, data_mode)
    service = BuyerService(db=db)
    return await service.get_sample_supplies(commodity_id=commodity_id, data_mode=data_mode)


@router.get(
    "/{supply_id}",
    response_model=FarmerSupplyRequest,
    summary="Get Farmer Supply Lot by ID",
    description="Retrieves a specific farmer supply lot by its unique identifier. Route registered strictly after /sample-supplies to prevent route capture.",
)
async def get_supply_by_id(
    supply_id: str,
    response: Response,
    data_mode: Optional[str] = Query(None, description="Operational data mode override ('demo', 'database')"),
    db: AsyncSession = Depends(get_db),
) -> FarmerSupplyRequest:
    _apply_headers(response, data_mode)
    service = BuyerService(db=db)
    samples = await service.get_sample_supplies(data_mode=data_mode)
    matched = next((s for s in samples if s.id == supply_id), None)
    if matched:
        return matched
    raise HTTPException(status_code=404, detail=f"Farmer supply lot '{supply_id}' not found.")

