"""
AgriClutch FastAPI Application Entrypoint.
Smart India Hackathon SIH26132 — Market Linkages & Price Discovery for Farmers.
"""

from typing import Any

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_v1_router
from app.config import settings
from app.db.session import check_db_health

app = FastAPI(
    title="AgriClutch API",
    description=(
        "AI-Powered Agricultural Market Intelligence & Optimal Selling Platform. "
        "SIH26132 — Strengthening Market Linkages and Price Discovery for Farmers."
    ),
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Configure CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get(
    "/health",
    tags=["System"],
    summary="Application Health Probe",
    status_code=status.HTTP_200_OK,
)
async def health_check() -> dict[str, Any]:
    """Returns basic liveness and service metadata."""
    return {
        "status": "ok",
        "service": settings.SERVICE_NAME,
        "version": settings.VERSION,
        "environment": settings.APP_ENV,
        "data_mode": settings.DATA_MODE,
    }


@app.get(
    "/health/db",
    tags=["System"],
    summary="Database & TimescaleDB Health Probe",
)
async def database_health_check() -> JSONResponse:
    """
    Verifies database connectivity and TimescaleDB extension status.
    Returns 200 OK when database is connected, 503 Service Unavailable when disconnected.
    """
    db_status = await check_db_health()
    if db_status.get("connected"):
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "ok",
                "service": settings.SERVICE_NAME,
                "database": db_status,
            },
        )
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "status": "disconnected",
            "service": settings.SERVICE_NAME,
            "database": db_status,
        },
    )


@app.get(
    "/",
    tags=["System"],
    summary="AgriClutch Root Information",
)
async def root() -> dict[str, Any]:
    """AgriClutch root metadata and API sitemap."""
    return {
        "platform": "AgriClutch",
        "description": "AI-Powered Agricultural Market Intelligence & Optimal Selling Platform",
        "problem_statement": "SIH26132",
        "version": settings.VERSION,
        "docs": "/docs",
        "api_v1": settings.API_V1_PREFIX,
        "health": "/health",
        "health_db": "/health/db",
    }


# Mount versioned API routes
app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)
