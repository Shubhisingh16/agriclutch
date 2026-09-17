# AgriClutch Backend Service

> AI-Powered Agricultural Market Intelligence & Optimal Selling Platform  
> Problem Statement: SIH26132 — Strengthening Market Linkages and Price Discovery for Farmers

## Overview
FastAPI asynchronous backend service powering AgriClutch decision intelligence, time-series forecasting integration, and buyer matching.

## Development Setup

Dependencies are authoritatively managed via `pyproject.toml`.

```bash
# Install in development mode
pip install -e .

# With development tools (pytest, ruff, mypy)
pip install -e ".[dev]"

# Run service
uvicorn app.main:app --reload --port 8000
```

## Running Tests

```bash
python -m unittest tests/test_health.py
```
