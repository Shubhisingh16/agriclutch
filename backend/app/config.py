"""
AgriClutch Application Configuration.
Manages environment variables, database connections, and service metadata.
"""

import os
from typing import List

from pydantic import BaseModel, Field


class Settings(BaseModel):
    """Application settings validated via Pydantic."""

    APP_NAME: str = Field(default="AgriClutch", description="Application brand name")
    APP_ENV: str = Field(
        default=os.getenv("APP_ENV", "development"),
        description="Deployment environment (development, staging, production, demo)",
    )
    DEBUG: bool = Field(
        default=os.getenv("DEBUG", "True").lower() in ("true", "1", "t"), description="Debug flag"
    )
    DATA_MODE: str = Field(
        default=os.getenv("AGRICLUTCH_DATA_MODE", "database").lower(),
        description="Data mode: 'database' (fail-closed PostgreSQL) or 'demo' (synthetic test fixture)",
    )
    SERVICE_NAME: str = Field(
        default="agriclutch-api", description="Service identifier for health checks and tracing"
    )
    VERSION: str = Field(default="0.1.0", description="Application semantic version")
    API_V1_PREFIX: str = Field(default="/api/v1", description="Prefix for versioned API endpoints")

    # Server settings
    HOST: str = Field(default=os.getenv("HOST", "0.0.0.0"), description="Listening host interface")
    PORT: int = Field(default=int(os.getenv("PORT", "8000")), description="Listening port")

    # Database Settings
    DATABASE_URL: str = Field(
        default=os.getenv(
            "DATABASE_URL",
            "postgresql+asyncpg://agrilink:agrilink_secure_password@localhost:5432/agrilink_db",
        ),
        description="Async SQLAlchemy database connection URL",
    )

    # CORS Settings
    ALLOWED_ORIGINS: List[str] = Field(
        default=[
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:8000",
            "http://127.0.0.1:8000",
        ],
        description="Allowed CORS origin domains",
    )


settings = Settings()
