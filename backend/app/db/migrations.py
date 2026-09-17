"""
Database Schema Initialization and TimescaleDB Hypertable Setup for AgriClutch.
Isolates TimescaleDB extension setup cleanly so unit tests run without live Docker.
"""

from typing import Any, Dict

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from app.models.base import Base


async def init_db(engine: AsyncEngine) -> Dict[str, Any]:
    """
    Initializes database tables from SQLAlchemy metadata and converts
    time-series tables to TimescaleDB hypertables if extension is active.

    Returns:
        Dict with initialization status and hypertable activation flags.
    """
    status: Dict[str, Any] = {
        "tables_created": False,
        "timescaledb_active": False,
        "hypertables_converted": [],
    }

    # 1. Create all relational tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        status["tables_created"] = True

    # 2. Check and conditionally convert to TimescaleDB Hypertables
    try:
        async with engine.begin() as conn:
            # Check if timescaledb extension is loaded
            ext_check = await conn.execute(
                text("SELECT extname FROM pg_extension WHERE extname = 'timescaledb';")
            )
            has_timescale = ext_check.scalar() == "timescaledb"

            if has_timescale:
                status["timescaledb_active"] = True
                # Convert mandi_daily_records hypertable
                try:
                    await conn.execute(
                        text(
                            "SELECT create_hypertable('mandi_daily_records', 'record_date', "
                            "if_not_exists => TRUE, migrate_data => TRUE);"
                        )
                    )
                    status["hypertables_converted"].append("mandi_daily_records")
                except Exception:
                    pass

                # Convert mandi_daily_arrivals hypertable
                try:
                    await conn.execute(
                        text(
                            "SELECT create_hypertable('mandi_daily_arrivals', 'record_date', "
                            "if_not_exists => TRUE, migrate_data => TRUE);"
                        )
                    )
                    status["hypertables_converted"].append("mandi_daily_arrivals")
                except Exception:
                    pass
    except Exception:
        # Non-PostgreSQL dialects (e.g. SQLite for tests) or restricted permissions
        status["timescaledb_active"] = False

    return status
