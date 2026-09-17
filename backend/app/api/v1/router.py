"""
AgriClutch API v1 Master Router.
Aggregates versioned routes across commodities, markets, and prices.
"""

from fastapi import APIRouter

from app.api.v1.endpoints.commodities import router as commodities_router
from app.api.v1.endpoints.forecasts import router as forecasts_router
from app.api.v1.endpoints.markets import router as markets_router
from app.api.v1.endpoints.nrv import router as nrv_router
from app.api.v1.endpoints.prices import router as prices_router

api_v1_router = APIRouter()

# Register core data layer endpoints
api_v1_router.include_router(commodities_router)
api_v1_router.include_router(markets_router)
api_v1_router.include_router(prices_router)
api_v1_router.include_router(forecasts_router)
api_v1_router.include_router(nrv_router)

