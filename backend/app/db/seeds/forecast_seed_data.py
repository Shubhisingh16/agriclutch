"""
Synthetic Historical Price Fixtures for AgriClutch Demo Mode Forecasting.
Provides 90 consecutive trading days (2024-06-16 to 2024-09-14) for Tomato, Onion, and Potato
across benchmark APMC mandis.
All observations are explicitly flagged with is_demo: True and source_name: "SYNTHETIC_DEMO".
SIH26132 — Market Linkages and Price Discovery for Farmers.
"""

from datetime import date, timedelta
from typing import Any, Dict, List, Optional

import numpy as np

BASE_PRICES: Dict[str, Dict[str, float]] = {
    "tomato": {
        "mandi_ch_49": 28.5,
        "mandi_hr_01": 27.5,
        "mandi_hr_02": 26.8,
        "mandi_pb_12": 26.0,
        "mandi_dl_164": 31.5,
    },
    "onion": {
        "mandi_ch_49": 32.5,
        "mandi_hr_01": 31.8,
        "mandi_hr_02": 31.0,
        "mandi_pb_12": 30.5,
        "mandi_dl_164": 35.0,
    },
    "potato": {
        "mandi_ch_49": 18.5,
        "mandi_hr_01": 18.0,
        "mandi_hr_02": 17.5,
        "mandi_pb_12": 18.2,
        "mandi_dl_164": 21.0,
    },
}


def generate_demo_forecast_records(
    commodity_id: str,
    market_id: str,
    days: int = 90,
    end_date: Optional[date] = None,
) -> List[Dict[str, Any]]:
    """
    Generates deterministic synthetic historical trading records for demo mode.
    Returns fewer than 30 observations if market_id contains 'insufficient'.
    """
    norm_comm = commodity_id.lower().strip()
    norm_mkt = market_id.lower().strip()

    if "insufficient" in norm_mkt:
        days = 15

    base = BASE_PRICES.get(norm_comm, {}).get(norm_mkt, 25.0)
    target_end = end_date or date(2024, 9, 14)
    start_date = target_end - timedelta(days=days - 1)

    records: List[Dict[str, Any]] = []

    for i in range(days):
        rec_date = start_date + timedelta(days=i)

        # Skip Sundays to simulate realistic non-trading days
        if rec_date.weekday() == 6:
            continue

        # Deterministic variation
        seasonal = 1.8 * np.sin(2 * np.pi * (i % 7) / 7.0)
        drift = 0.04 * (i - days / 2)
        noise = float((i % 7 - 3) * 0.25)
        modal_price = round(max(5.0, base + seasonal + drift + noise), 2)
        min_price = round(modal_price * 0.90, 2)
        max_price = round(modal_price * 1.10, 2)
        arrival = round(20.0 + (i % 15) * 2.5, 1)

        records.append({
            "record_date": rec_date.isoformat(),
            "commodity_id": norm_comm,
            "market_id": norm_mkt,
            "normalized_modal_price": modal_price,
            "normalized_min_price": min_price,
            "normalized_max_price": max_price,
            "normalized_price_unit": "INR_PER_KG",
            "original_modal_price": round(modal_price * 100.0, 1),
            "original_price_unit": "Rs/Quintal",
            "arrival_tonnes": arrival,
            "source_record_id": f"DEMO_SERIES_{norm_comm}_{norm_mkt}_{rec_date}",
            "source_name": "SYNTHETIC_DEMO",
            "is_demo": True,
            "is_interpolated": False,
            "is_outlier": False,
        })

    return records
