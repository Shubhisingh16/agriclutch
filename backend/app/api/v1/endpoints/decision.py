"""
AgriClutch Step 14: Decision Intelligence REST API Endpoints.
Exposes routes for optimal selling plan generation, counterfactual What-If simulation,
parameter sensitivity sweeps, and plan audits.
SIH26132 — Strengthening Market Linkages and Price Discovery for Farmers.
"""

from typing import Any, Dict

from app.db.session import get_db
from app.schemas.decision import (
    OptimalSellingPlanResponse,
    OptimizePlanRequest,
    SensitivityRequest,
    SensitivitySweepResponse,
    WhatIfSimulationRequest,
    WhatIfSimulationResponse,
)
from app.services.decision_service import DecisionService
from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/decision", tags=["Decision Intelligence & Optimal Selling"])


@router.post(
    "/optimize",
    response_model=OptimalSellingPlanResponse,
    summary="Compute Optimal Multi-Destination Selling Plan",
    description="Solves the mathematical linear programming problem across channels, time horizons, and storage.",
)
async def optimize_selling_plan(
    payload: OptimizePlanRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> OptimalSellingPlanResponse:
    """Computes mathematically optimal multi-destination selling allocation."""
    response.headers["X-AgriClutch-Step"] = "14"
    response.headers["X-AgriClutch-DataSource"] = "DEMO_DECISION"
    return await DecisionService.optimize_selling_plan(req=payload, session=db)


@router.post(
    "/what-if",
    response_model=WhatIfSimulationResponse,
    summary="Run Counterfactual What-If Simulation",
    description="Perturbs logistics costs, storage duration, buyer demand, or risk preferences and re-solves.",
)
async def simulate_what_if(
    payload: WhatIfSimulationRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> WhatIfSimulationResponse:
    """Executes counterfactual simulation comparing baseline to alternative."""
    response.headers["X-AgriClutch-Step"] = "14"
    response.headers["X-AgriClutch-DataSource"] = "DEMO_DECISION"
    return await DecisionService.simulate_what_if(req=payload, session=db)


@router.post(
    "/sensitivity",
    response_model=SensitivitySweepResponse,
    summary="Evaluate Multi-Point Sensitivity Sweep",
    description="Sweeps parameter multipliers across a declared range to trace NRV and allocation curves.",
)
async def evaluate_sensitivity(
    payload: SensitivityRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> SensitivitySweepResponse:
    """Evaluates multi-point sensitivity sweep."""
    response.headers["X-AgriClutch-Step"] = "14"
    response.headers["X-AgriClutch-DataSource"] = "DEMO_DECISION"
    return await DecisionService.evaluate_sensitivity_sweep(req=payload, session=db)


@router.get(
    "/plans/{plan_id}",
    response_model=OptimalSellingPlanResponse,
    summary="Retrieve Stored Selling Plan by ID",
)
async def get_plan_by_id(
    plan_id: str,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> OptimalSellingPlanResponse:
    """Retrieves an existing plan or default demo plan."""
    response.headers["X-AgriClutch-Step"] = "14"
    response.headers["X-AgriClutch-DataSource"] = "DEMO_DECISION"
    return await DecisionService.get_plan_by_id(plan_id=plan_id, session=db)


@router.get(
    "/configuration",
    summary="Retrieve Optimizer Configuration & Default Constraints",
)
async def get_configuration(response: Response) -> Dict[str, Any]:
    """Exposes transparent optimizer settings and default mathematical parameters."""
    response.headers["X-AgriClutch-Step"] = "14"
    response.headers["X-AgriClutch-DataSource"] = "CONFIGURED"
    return {
        "solver": "SciPy-HiGHS-DualSimplex",
        "objective": "Max(ExpectedNRV - DownsideCVaRPenalty)",
        "risk_weights": {
            "RISK_NEUTRAL": 0.0,
            "RISK_AWARE": 0.5,
            "RISK_AVERSE": 1.0,
        },
        "liquidity_min_ratios": {
            "IMMEDIATE": 0.60,
            "BALANCED": 0.30,
            "DELAY_TOLERANT": 0.00,
        },
        "supported_decision_horizons_days": [1, 3, 5, 7, 14, 30],
        "default_confidence_level": 0.95,
        "is_demo": True,
        "provenance_status": "CONFIGURED",
    }
