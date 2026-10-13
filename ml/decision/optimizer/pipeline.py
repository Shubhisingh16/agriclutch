"""
AgriClutch Step 14: Upstream Adapter & Candidate Pipeline.
Synthesizes candidate allocations from Steps 10-13 (Forecast, NRV, Buyers, Logistics, Storage).
SIH26132 — Strengthening Market Linkages and Price Discovery for Farmers.
"""

from typing import Any, Dict, List

from ml.decision.optimizer.contracts import (
    AllocationCandidate,
    DecisionProvenanceStatus,
    DestinationType,
)


class DecisionCandidatePipeline:
    """
    Ingests authoritative outputs from Steps 10, 11, 12, and 13 to build
    a strictly verified list of feasible allocation candidates.
    Pre-filters candidates before passing them into the mathematical solver.
    """

    @classmethod
    def build_demo_candidates(
        cls,
        commodity_id: str = "tomato",
        variety: str = "Standard",
        quality_grade: str = "GRADE_A",
        decision_horizon_days: int = 7,
        origin_lat: float = 30.8350,
        origin_lon: float = 76.9350,
        base_date_str: str = "2026-09-15",
    ) -> List[AllocationCandidate]:
        """
        Synthesizes a representative set of multi-channel candidate options
        connecting Kalka/Mohali Farmgate to Regional Buyers, Mandis, and Storage hubs.
        """
        # Baseline prices and friction by commodity
        commodity_profiles: Dict[str, Dict[str, Any]] = {
            "tomato": {
                "direct_buyer_price": 31.50,
                "local_mandi_price": 28.00,
                "terminal_mandi_price": 34.00,  # Delhi Azadpur
                "stored_buyer_price": 36.50,    # Day 5 forward price
                "direct_buyer_demand": 2500.0,
                "local_mandi_demand": 10000.0,
                "terminal_mandi_demand": 15000.0,
                "stored_buyer_demand": 3000.0,
                "decay_ambient_daily": 0.035,
                "decay_cold_daily": 0.008,
            },
            "onion": {
                "direct_buyer_price": 27.50,
                "local_mandi_price": 25.00,
                "terminal_mandi_price": 30.00,
                "stored_buyer_price": 32.00,
                "direct_buyer_demand": 5000.0,
                "local_mandi_demand": 20000.0,
                "terminal_mandi_demand": 30000.0,
                "stored_buyer_demand": 8000.0,
                "decay_ambient_daily": 0.005,
                "decay_cold_daily": 0.0015,
            },
            "potato": {
                "direct_buyer_price": 22.00,
                "local_mandi_price": 20.00,
                "terminal_mandi_price": 24.50,
                "stored_buyer_price": 26.00,
                "direct_buyer_demand": 6000.0,
                "local_mandi_demand": 25000.0,
                "terminal_mandi_demand": 40000.0,
                "stored_buyer_demand": 10000.0,
                "decay_ambient_daily": 0.004,
                "decay_cold_daily": 0.0008,
            },
        }

        profile = commodity_profiles.get(commodity_id.lower(), commodity_profiles["tomato"])

        # Candidate 1: Immediate Direct Sale to Commercial Buyer (e.g., DEMO_BUYER_PROCESSOR)
        c1_price = profile["direct_buyer_price"]
        c1_freight = 1.20   # 20 km local pickup
        c1_handling = 0.50
        c1_storage = 0.0
        c1_mkt = 0.0        # No APMC mandi cess for direct farmgate buyer
        c1_nrv = c1_price - (c1_freight + c1_handling + c1_storage + c1_mkt)

        c1 = AllocationCandidate(
            candidate_id="cand_direct_buyer_proc",
            destination_type=DestinationType.BUYER,
            destination_id="DEMO_BUYER_PROCESSOR",
            destination_name="DEMO Commercial Food Processor (Panchkula)",
            sale_day_offset=0,
            sale_date=base_date_str,
            expected_price_per_kg=c1_price,
            price_p10=c1_price * 0.92,
            price_p50=c1_price,
            price_p90=c1_price * 1.08,
            expected_nrv_per_kg=c1_nrv,
            nrv_p10=c1_nrv * 0.90,
            nrv_p50=c1_nrv,
            nrv_p90=c1_nrv * 1.09,
            freight_cost_per_kg=c1_freight,
            handling_cost_per_kg=c1_handling,
            storage_cost_per_kg=c1_storage,
            market_fee_per_kg=c1_mkt,
            mass_retention_factor=1.00,
            quality_factor=1.00,
            max_demand_kg=profile["direct_buyer_demand"],
            max_transport_kg=4000.0,  # 4-ton truck
            max_storage_kg=0.0,
            is_immediate_window=True,
            pathway_id="scen_a_direct",
            buyer_id="DEMO_BUYER_PROCESSOR",
            forecast_model="Chronos-2-Benchmark",
            provenance_status=DecisionProvenanceStatus.DEMO,
            is_demo=True,
        )

        # Candidate 2: Immediate Sale at Local Mandi (Chandigarh APMC)
        c2_price = profile["local_mandi_price"]
        c2_freight = 1.45   # 28 km
        c2_handling = 0.65
        c2_storage = 0.0
        c2_mkt = c2_price * 0.02  # 2% APMC mandi fee
        c2_nrv = c2_price - (c2_freight + c2_handling + c2_storage + c2_mkt)

        c2 = AllocationCandidate(
            candidate_id="cand_local_mandi_chd",
            destination_type=DestinationType.MARKET,
            destination_id="CHD_APMC",
            destination_name="Chandigarh APMC Mandi",
            sale_day_offset=0,
            sale_date=base_date_str,
            expected_price_per_kg=c2_price,
            price_p10=c2_price * 0.88,
            price_p50=c2_price,
            price_p90=c2_price * 1.12,
            expected_nrv_per_kg=c2_nrv,
            nrv_p10=c2_nrv * 0.85,
            nrv_p50=c2_nrv,
            nrv_p90=c2_nrv * 1.14,
            freight_cost_per_kg=c2_freight,
            handling_cost_per_kg=c2_handling,
            storage_cost_per_kg=c2_storage,
            market_fee_per_kg=c2_mkt,
            mass_retention_factor=0.99,
            quality_factor=0.99,
            max_demand_kg=profile["local_mandi_demand"],
            max_transport_kg=5000.0,
            max_storage_kg=0.0,
            is_immediate_window=True,
            pathway_id="scen_b_local_mandi",
            market_id="CHD_APMC",
            forecast_model="Chronos-2-Benchmark",
            provenance_status=DecisionProvenanceStatus.DEMO,
            is_demo=True,
        )

        # Candidate 3: Distant Terminal Mandi (Delhi Azadpur)
        c3_price = profile["terminal_mandi_price"]
        c3_freight = 4.80   # ~250 km haulage
        c3_handling = 0.90
        c3_storage = 0.0
        c3_mkt = c3_price * 0.015  # 1.5% APMC market fee
        c3_nrv = c3_price - (c3_freight + c3_handling + c3_storage + c3_mkt)

        c3 = AllocationCandidate(
            candidate_id="cand_terminal_mandi_del",
            destination_type=DestinationType.MARKET,
            destination_id="DEL_AZADPUR",
            destination_name="Delhi Azadpur Terminal Mandi",
            sale_day_offset=1,
            sale_date="2026-09-16",
            expected_price_per_kg=c3_price,
            price_p10=c3_price * 0.85,
            price_p50=c3_price,
            price_p90=c3_price * 1.15,
            expected_nrv_per_kg=c3_nrv,
            nrv_p10=c3_nrv * 0.82,
            nrv_p50=c3_nrv,
            nrv_p90=c3_nrv * 1.18,
            freight_cost_per_kg=c3_freight,
            handling_cost_per_kg=c3_handling,
            storage_cost_per_kg=c3_storage,
            market_fee_per_kg=c3_mkt,
            mass_retention_factor=0.97,
            quality_factor=0.96,
            max_demand_kg=profile["terminal_mandi_demand"],
            max_transport_kg=10000.0,  # 10-ton heavy carrier
            max_storage_kg=0.0,
            is_immediate_window=True,  # Day 1 is within immediate window
            pathway_id="scen_c_terminal_mandi",
            market_id="DEL_AZADPUR",
            forecast_model="Chronos-2-Benchmark",
            provenance_status=DecisionProvenanceStatus.DEMO,
            is_demo=True,
        )

        # Candidate 4: Cold Storage Holding for 5 Days targeting Premium Buyer
        c4_price = profile["stored_buyer_price"]
        c4_freight = 2.40   # Transit to cold storage and onward delivery
        c4_handling = 1.10
        c4_storage = 0.25 * 5  # ₹0.25/kg/day * 5 days = ₹1.25/kg
        c4_mkt = 0.0        # Direct off-taker
        c4_nrv = c4_price - (c4_freight + c4_handling + c4_storage + c4_mkt)

        # Mass retention after 5 days cold storage
        decay_rate = profile["decay_cold_daily"]
        s_5 = float((1.0 - decay_rate) ** 5)

        c4 = AllocationCandidate(
            candidate_id="cand_cold_store_buyer",
            destination_type=DestinationType.BUYER,
            destination_id="DEMO_BUYER_RETAIL_CHAIN",
            destination_name="DEMO Modern Retail Chain (via Cold Chain Hub)",
            sale_day_offset=5,
            sale_date="2026-09-20",
            expected_price_per_kg=c4_price,
            price_p10=c4_price * 0.88,
            price_p50=c4_price,
            price_p90=c4_price * 1.18,
            expected_nrv_per_kg=c4_nrv,
            nrv_p10=c4_nrv * 0.84,
            nrv_p50=c4_nrv,
            nrv_p90=c4_nrv * 1.20,
            freight_cost_per_kg=c4_freight,
            handling_cost_per_kg=c4_handling,
            storage_cost_per_kg=c4_storage,
            market_fee_per_kg=c4_mkt,
            mass_retention_factor=round(s_5, 4),
            quality_factor=0.95,
            max_demand_kg=profile["stored_buyer_demand"],
            max_transport_kg=5000.0,
            max_storage_kg=4000.0,   # Cold store slot limit
            is_immediate_window=False,
            pathway_id="scen_d_cold_storage",
            buyer_id="DEMO_BUYER_RETAIL_CHAIN",
            storage_facility_id="DEMO_COLD_STORAGE_NORTH",
            forecast_model="Chronos-2-Benchmark",
            provenance_status=DecisionProvenanceStatus.DEMO,
            is_demo=True,
        )

        return [c1, c2, c3, c4]
