"""
Demo Seed Fixtures for Economic Assumptions & Parameters.
Explicitly labeled with provenance_status: DEMO, is_demo: True.
Used strictly for demonstration, integration testing, and offline benchmarking.
SIH26132 — Market Linkages and Price Discovery for Farmers.
"""

from datetime import date
from typing import Any, Dict, List

# Regional Road Transit Distances (km) from production centroid (Chandigarh tri-city region)
DEMO_MARKET_DISTANCES: Dict[str, float] = {
    "mandi_ch_49": 8.0,
    "mandi_hr_01": 12.0,
    "mandi_hr_02": 28.0,
    "mandi_pb_12": 72.0,
    "mandi_dl_164": 245.0,
}

# Statutory Mandi Cess & Market Development Fees (fraction of gross sales)
DEMO_APMC_CHARGES: Dict[str, float] = {
    "mandi_ch_49": 0.015,   # 1.50%
    "mandi_hr_01": 0.020,   # 2.00%
    "mandi_hr_02": 0.020,   # 2.00%
    "mandi_pb_12": 0.020,   # 2.00%
    "mandi_dl_164": 0.010,  # 1.00%
}

# Synthetic Economic Demo Fixtures
DEMO_ECONOMIC_ASSUMPTIONS: List[Dict[str, Any]] = [
    # Freight & Logistics
    {
        "id": "demo_freight_base_dispatch",
        "category": "transport",
        "parameter_key": "freight_base_dispatch_fee",
        "commodity_id": None,
        "market_id": None,
        "value": 250.0,
        "unit": "INR",
        "source": "REGIONAL_ROAD_LOGISTICS_BENCHMARK",
        "provenance_status": "DEMO",
        "effective_from": date(2024, 9, 15),
        "is_demo": True,
        "description": "Base vehicle booking and dispatch coordination fee.",
    },
    {
        "id": "demo_freight_short_haul",
        "category": "transport",
        "parameter_key": "freight_rate_short_haul",
        "commodity_id": None,
        "market_id": None,
        "value": 4.50,
        "unit": "INR_PER_KM_TONNE",
        "source": "REGIONAL_ROAD_LOGISTICS_BENCHMARK",
        "provenance_status": "DEMO",
        "effective_from": date(2024, 9, 15),
        "is_demo": True,
        "description": "Light Commercial Vehicle (LCV) freight rate for trips <= 100 km.",
    },
    {
        "id": "demo_freight_long_haul",
        "category": "transport",
        "parameter_key": "freight_rate_long_haul",
        "commodity_id": None,
        "market_id": None,
        "value": 3.20,
        "unit": "INR_PER_KM_TONNE",
        "source": "REGIONAL_ROAD_LOGISTICS_BENCHMARK",
        "provenance_status": "DEMO",
        "effective_from": date(2024, 9, 15),
        "is_demo": True,
        "description": "Medium Heavy Vehicle (MHV) freight rate for interstate trips > 100 km.",
    },
    # Storage Rental Tariffs
    {
        "id": "demo_storage_ambient",
        "category": "storage",
        "parameter_key": "storage_ambient_daily_rate",
        "commodity_id": None,
        "market_id": None,
        "value": 0.00,
        "unit": "INR_PER_KG_DAY",
        "source": "ON_FARM_AMBIENT_SHED_BENCHMARK",
        "provenance_status": "DEMO",
        "effective_from": date(2024, 9, 15),
        "is_demo": True,
        "description": "On-farm ambient shed holding cost (fixed capital asset).",
    },
    {
        "id": "demo_storage_cold",
        "category": "storage",
        "parameter_key": "storage_cold_daily_rate",
        "commodity_id": None,
        "market_id": None,
        "value": 0.20,
        "unit": "INR_PER_KG_DAY",
        "source": "WDRA_COLD_STORAGE_TARIFF_BENCHMARK",
        "provenance_status": "DEMO",
        "effective_from": date(2024, 9, 15),
        "is_demo": True,
        "description": "Commercial cold storage rental tariff for horticulture in Northern India.",
    },
    # Physical Handling & Porterage
    {
        "id": "demo_handling_loading",
        "category": "handling",
        "parameter_key": "handling_loading_rate",
        "commodity_id": None,
        "market_id": None,
        "value": 0.30,
        "unit": "INR_PER_KG",
        "source": "APMC_MANDI_PORTERAGE_UNION_BENCHMARK",
        "provenance_status": "DEMO",
        "effective_from": date(2024, 9, 15),
        "is_demo": True,
        "description": "Farm-gate vehicle loading labor fee.",
    },
    {
        "id": "demo_handling_unloading",
        "category": "handling",
        "parameter_key": "handling_unloading_rate",
        "commodity_id": None,
        "market_id": None,
        "value": 0.30,
        "unit": "INR_PER_KG",
        "source": "APMC_MANDI_PORTERAGE_UNION_BENCHMARK",
        "provenance_status": "DEMO",
        "effective_from": date(2024, 9, 15),
        "is_demo": True,
        "description": "APMC mandi yard unloading and stacking labor fee.",
    },
    {
        "id": "demo_handling_packaging_weighment",
        "category": "other",
        "parameter_key": "handling_packaging_weighment",
        "commodity_id": None,
        "market_id": None,
        "value": 0.40,
        "unit": "INR_PER_KG",
        "source": "HORTICULTURAL_PACKAGING_WEIGHMENT_BENCHMARK",
        "provenance_status": "DEMO",
        "effective_from": date(2024, 9, 15),
        "is_demo": True,
        "description": "Plastic crate amortization & certified weighbridge slip fee.",
    },
    {
        "id": "demo_spoilage_culling_disposal",
        "category": "loss",
        "parameter_key": "loss_culling_disposal_fee",
        "commodity_id": None,
        "market_id": None,
        "value": 0.10,
        "unit": "INR_PER_KG",
        "source": "APMC_SPOILAGE_DISPOSAL_BENCHMARK",
        "provenance_status": "DEMO",
        "effective_from": date(2024, 9, 15),
        "is_demo": True,
        "description": "Labor and municipal culling fee for disposing of degraded produce.",
    },
    # Crop Perishability Decay Coefficients
    {
        "id": "demo_decay_tomato_ambient",
        "category": "decay",
        "parameter_key": "decay_rate_tomato_ambient",
        "commodity_id": "tomato",
        "market_id": None,
        "value": 0.045,
        "unit": "PER_DAY",
        "source": "ICAR_CIPHET_POST_HARVEST_BENCHMARK",
        "provenance_status": "DEMO",
        "effective_from": date(2024, 9, 15),
        "is_demo": True,
        "description": "Tomato ambient storage decay delta (4.5%/day), max safe holding 5.0 days.",
    },
    {
        "id": "demo_decay_tomato_cold",
        "category": "decay",
        "parameter_key": "decay_rate_tomato_cold_storage",
        "commodity_id": "tomato",
        "market_id": None,
        "value": 0.008,
        "unit": "PER_DAY",
        "source": "NHB_COLD_CHAIN_BENCHMARK",
        "provenance_status": "DEMO",
        "effective_from": date(2024, 9, 15),
        "is_demo": True,
        "description": "Tomato cold storage decay delta (0.8%/day), max safe holding 21.0 days.",
    },
    {
        "id": "demo_decay_onion_ambient",
        "category": "decay",
        "parameter_key": "decay_rate_onion_ambient",
        "commodity_id": "onion",
        "market_id": None,
        "value": 0.008,
        "unit": "PER_DAY",
        "source": "NHRDF_RABI_ONION_STORAGE_BENCHMARK",
        "provenance_status": "DEMO",
        "effective_from": date(2024, 9, 15),
        "is_demo": True,
        "description": "Onion ambient storage decay delta (0.8%/day), max safe holding 60.0 days.",
    },
    {
        "id": "demo_decay_onion_cold",
        "category": "decay",
        "parameter_key": "decay_rate_onion_cold_storage",
        "commodity_id": "onion",
        "market_id": None,
        "value": 0.002,
        "unit": "PER_DAY",
        "source": "NHRDF_COLD_STORAGE_BENCHMARK",
        "provenance_status": "DEMO",
        "effective_from": date(2024, 9, 15),
        "is_demo": True,
        "description": "Onion cold storage decay delta (0.2%/day), max safe holding 180.0 days.",
    },
    {
        "id": "demo_decay_potato_ambient",
        "category": "decay",
        "parameter_key": "decay_rate_potato_ambient",
        "commodity_id": "potato",
        "market_id": None,
        "value": 0.004,
        "unit": "PER_DAY",
        "source": "CPRI_POST_HARVEST_BENCHMARK",
        "provenance_status": "DEMO",
        "effective_from": date(2024, 9, 15),
        "is_demo": True,
        "description": "Potato ambient storage decay delta (0.4%/day), max safe holding 45.0 days.",
    },
    {
        "id": "demo_decay_potato_cold",
        "category": "decay",
        "parameter_key": "decay_rate_potato_cold_storage",
        "commodity_id": "potato",
        "market_id": None,
        "value": 0.0008,
        "unit": "PER_DAY",
        "source": "CPRI_COLD_CHAIN_BENCHMARK",
        "provenance_status": "DEMO",
        "effective_from": date(2024, 9, 15),
        "is_demo": True,
        "description": "Potato cold storage decay delta (0.08%/day), max safe holding 240.0 days.",
    },
]


def get_demo_economic_assumptions(category: str | None = None) -> List[Dict[str, Any]]:
    """Returns demo economic assumption records with optional category filtering."""
    if not category:
        return DEMO_ECONOMIC_ASSUMPTIONS
    norm_cat = category.strip().lower()
    return [a for a in DEMO_ECONOMIC_ASSUMPTIONS if a["category"].lower() == norm_cat]


def get_demo_market_distance(market_id: str) -> float:
    """Returns road transit distance in km from regional centroid, or 15.0 km fallback."""
    return DEMO_MARKET_DISTANCES.get(market_id.lower().strip(), 15.0)


def get_demo_apmc_fee(market_id: str) -> float:
    """Returns statutory APMC mandi fee fraction (e.g. 0.015 for 1.5%), or 0.015 fallback."""
    return DEMO_APMC_CHARGES.get(market_id.lower().strip(), 0.015)
