"""
Commodities Read-Only API Endpoints for AgriClutch.
Provides access to master agricultural produce definitions and perishability classifications.
"""

from typing import List, Optional

from app.config import settings
from app.db.seeds.seed_data import SEED_COMMODITIES, filter_seed_commodities
from app.db.session import get_db
from app.repositories.commodity_repo import CommodityRepository
from app.schemas.commodity import CommodityResponse, CropCategory
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/commodities", tags=["Commodities"])


@router.get(
    "",
    response_model=List[CommodityResponse],
    summary="List Agricultural Commodities",
    description="Retrieve all tracked commodities with optional perishability category filtering.",
)
async def list_commodities(
    response: Response,
    category: Optional[CropCategory] = Query(
        None, description="Filter by crop category (perishable, semi_perishable, storable)"
    ),
    db: AsyncSession = Depends(get_db),
) -> List[CommodityResponse]:
    """Returns list of registered commodities with explicit data mode semantics."""
    if settings.DATA_MODE == "demo":
        response.headers["X-AgriClutch-Data-Mode"] = "DEMO"
        response.headers["X-AgriClutch-DataSource"] = "SYNTHETIC_TEST_FIXTURE"
        return filter_seed_commodities(category=category)

    try:
        repo = CommodityRepository(db)
        cat_val = category.value if category else None
        models = await repo.list_all(category=cat_val)
        response.headers["X-AgriClutch-Data-Mode"] = "DATABASE"
        response.headers["X-AgriClutch-DataSource"] = "POSTGRESQL"
        return [CommodityResponse.model_validate(m) for m in models]
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Database service is unavailable. Automatic fallback to synthetic data "
                "is disabled in database mode to prevent silent data contamination."
            ),
        ) from exc


@router.get(
    "/{commodity_id}",
    response_model=CommodityResponse,
    summary="Get Commodity Details",
    description="Fetch master attributes for a specific commodity by ID.",
)
async def get_commodity(
    commodity_id: str,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> CommodityResponse:
    """Returns specific commodity with explicit data mode semantics."""
    if settings.DATA_MODE == "demo":
        for seed in SEED_COMMODITIES:
            if seed.id.lower() == commodity_id.lower():
                response.headers["X-AgriClutch-Data-Mode"] = "DEMO"
                response.headers["X-AgriClutch-DataSource"] = "SYNTHETIC_TEST_FIXTURE"
                return seed
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Commodity with ID '{commodity_id}' not found in demo fixture.",
        )

    try:
        repo = CommodityRepository(db)
        model = await repo.get_by_id(commodity_id)
        if not model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Commodity with ID '{commodity_id}' not found.",
            )
        response.headers["X-AgriClutch-Data-Mode"] = "DATABASE"
        response.headers["X-AgriClutch-DataSource"] = "POSTGRESQL"
        return CommodityResponse.model_validate(model)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Database service is unavailable. Automatic fallback to synthetic data "
                "is disabled in database mode."
            ),
        ) from exc
