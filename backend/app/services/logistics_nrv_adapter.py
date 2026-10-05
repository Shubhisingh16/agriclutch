"""
AgriClutch Logistics to NRV Adapter.
Clean, typed adapter bridging Step 13 physical logistics and perishability calculations
to Step 11 Net Realizable Value inputs without mutating locked Step 11 contracts.
SIH26132 — Strengthening Market Linkages and Price Discovery for Farmers.
"""

from typing import Any, Dict

from ml.logistics.contracts import LogisticsScenario


class LogisticsNRVAdapter:
    """
    Adapter translating physical transit, handling, and perishability results
    into parameters consumable by the Step 11 NRV Engine.
    """

    @staticmethod
    def to_nrv_friction_costs(scenario: LogisticsScenario) -> Dict[str, Any]:
        """
        Extracts itemized friction deductions suitable for Step 11 NRV computation:
        - freight_cost: physical haulage cost
        - loading_cost: farm loading fee
        - unloading_cost: destination unloading fee
        - storage_cost: holding fee at facility
        - extra_handling_cost: sorting/grading/intermediate transfer fees
        - effective_delivered_quantity_kg: produce quantity surviving transit & holding
        - quality_factor: grade discount factor
        """
        breakdown = scenario.logistics_cost

        return {
            "freight_cost": breakdown.transport_cost,
            "loading_cost": breakdown.loading_cost,
            "unloading_cost": breakdown.unloading_cost,
            "storage_cost": scenario.storage_cost,
            "handling_cost": breakdown.handling_cost + breakdown.other_cost,
            "total_friction_cost": scenario.total_pathway_cost,
            "initial_quantity_kg": scenario.initial_quantity_kg,
            "effective_delivered_quantity_kg": scenario.effective_delivered_quantity_kg,
            "final_quality_factor": scenario.final_quality_factor,
            "distance_km": scenario.distance_km,
            "transit_duration_hours": scenario.transit_duration_hours,
            "storage_duration_days": scenario.storage_duration_days,
            "economic_status": scenario.economic_status.value,
            "provenance": scenario.provenance.to_dict(),
        }
