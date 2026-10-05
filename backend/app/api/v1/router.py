"""
AgriClutch API v1 Master Router.
Aggregates versioned routes across commodities, markets, and prices.
"""

from fastapi import APIRouter

from app.api.v1.endpoints.buyer_matching import router as buyer_matching_router
from app.api.v1.endpoints.buyers import router as buyers_router
from app.api.v1.endpoints.commodities import router as commodities_router
from app.api.v1.endpoints.demand import router as demand_router
from app.api.v1.endpoints.forecasts import router as forecasts_router
from app.api.v1.endpoints.logistics import router as logistics_router
from app.api.v1.endpoints.markets import router as markets_router
from app.api.v1.endpoints.nrv import router as nrv_router
from app.api.v1.endpoints.perishability import router as perishability_router
from app.api.v1.endpoints.prices import router as prices_router
from app.api.v1.endpoints.storage import router as storage_router

api_v1_router = APIRouter()

# Register core data layer endpoints
api_v1_router.include_router(commodities_router)
api_v1_router.include_router(markets_router)
api_v1_router.include_router(prices_router)
api_v1_router.include_router(forecasts_router)
api_v1_router.include_router(nrv_router)
api_v1_router.include_router(buyers_router)
api_v1_router.include_router(buyer_matching_router)
api_v1_router.include_router(demand_router)

# Step 13: Logistics, Storage & Perishability Feasibility
api_v1_router.include_router(logistics_router)
api_v1_router.include_router(storage_router)
api_v1_router.include_router(perishability_router)


