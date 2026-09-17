"""
Database session management and health verification.
Supports SQLAlchemy 2.0 async engine, sessionmaker, and TimescaleDB checks.
"""

from typing import Any, AsyncGenerator, Dict

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings

# Initialize SQLAlchemy async engine
# Use connect_args for timeout control
try:
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False,
        future=True,
        pool_pre_ping=True,
    )
    async_session = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )
except Exception:
    engine = None  # type: ignore
    async_session = None  # type: ignore


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for obtaining an asynchronous database session."""
    if async_session is None:
        raise RuntimeError("Database engine is not initialized.")
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def check_db_health() -> Dict[str, Any]:
    """
    Verifies database connectivity and checks for TimescaleDB extension.
    Returns status dictionary for health check endpoints.
    """
    if engine is None:
        return {
            "status": "unavailable",
            "connected": False,
            "error": "Engine initialization failed or driver not installed.",
            "timescaledb": False,
        }

    try:
        async with engine.connect() as conn:
            # Check basic query execution
            result = await conn.execute(text("SELECT 1;"))
            row = result.scalar()

            # Check if timescaledb extension is active (PostgreSQL only)
            timescale_active = False
            try:
                ext_result = await conn.execute(
                    text("SELECT extname FROM pg_extension WHERE extname = 'timescaledb';")
                )
                ext_row = ext_result.scalar()
                if ext_row == "timescaledb":
                    timescale_active = True
            except Exception:
                # Non-Postgres or extension table not present
                timescale_active = False

            return {
                "status": "ok",
                "connected": True,
                "scalar_check": row == 1,
                "timescaledb": timescale_active,
                "database_url": settings.DATABASE_URL.split("@")[-1]
                if "@" in settings.DATABASE_URL
                else "configured",
            }
    except Exception as exc:
        return {
            "status": "disconnected",
            "connected": False,
            "error": str(exc),
            "timescaledb": False,
        }
