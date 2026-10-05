"""
AgriClutch Logistics Scenario Composer.
Composes multi-stage physical pathways from farmer origin to destination.
Evaluates handling stages, cumulative elapsed time, storage holding, and perishability.
SIH26132 — Strengthening Market Linkages and Price Discovery for Farmers.
"""


from ml.logistics.contracts import (
    Destination,
    EconomicProvenance,
    EconomicStatus,
    HandlingStage,
    HandlingStageType,
    LogisticsScenario,
    PerishabilityTrajectory,
    ProduceInput,
    ProvenanceStatus,
    StorageFacility,
    StorageFeasibilityResult,
    StorageType,
    TransportModeSpec,
)
from ml.logistics.costs import LogisticsCostEngine
from ml.logistics.distance import DistanceEngine
from ml.logistics.feasibility import LogisticsFeasibilityEvaluator
from ml.logistics.perishability import PerishabilityEngine
from ml.logistics.storage import StorageEngine


class LogisticsScenarioComposer:
    """
    Composes factual, auditable multi-stage logistics pathways.
    Strictly descriptive: does NOT rank, recommend, or optimize scenarios.
    """

    @classmethod
    def compose_scenario(
        cls,
        scenario_id: str,
        scenario_name: str,
        produce: ProduceInput,
        destination: Destination,
        transport_mode: TransportModeSpec,
        stages: list[HandlingStage],
        storage_facility: StorageFacility | None = None,
        storage_duration_days: int = 0,
        road_distance_km: float | None = None,
        loading_fee_per_quintal: float | None = None,
        unloading_fee_per_quintal: float | None = None,
        extra_handling_fee: float | None = None,
        is_demo: bool = True,
    ) -> LogisticsScenario:
        """
        Generic multi-stage scenario composer.
        Calculates physical transit, storage duration, stage deterioration,
        perishability trajectory, itemized costs, and feasibility.
        """
        # 1. Geographic Distance & Transit Duration
        distance_km, distance_type = DistanceEngine.resolve_route_distance(
            origin_lat=produce.origin_latitude,
            origin_lon=produce.origin_longitude,
            dest_lat=destination.latitude,
            dest_lon=destination.longitude,
            road_distance_km=road_distance_km,
        )

        transit_hours, transit_time_status = DistanceEngine.calculate_transit_time(
            distance_km=distance_km,
            speed_kmh=transport_mode.speed_kmh,
        )

        # 2. Storage Feasibility & Holding Cost
        storage_feasibility: StorageFeasibilityResult | None = None
        storage_cost = 0.0

        if storage_facility is not None or storage_duration_days > 0:
            storage_feasibility = StorageEngine.evaluate_storage(
                facility=storage_facility,
                requested_quantity_kg=produce.quantity_kg,
                requested_duration_days=storage_duration_days,
            )
            storage_cost = storage_feasibility.storage_cost

        # 3. Handling Stages & Elapsed Duration
        stage_duration_hours = sum(s.duration_hours for s in stages)
        storage_duration_hours = storage_duration_days * 24.0
        total_transit_hours = transit_hours if transit_hours is not None else 0.0
        total_elapsed_hours = stage_duration_hours + storage_duration_hours + total_transit_hours

        # 4. Quantity & Quality Deterioration across Handling Stages
        transportable_kg = min(produce.quantity_kg, transport_mode.capacity_kg) if transport_mode.capacity_kg > 0 else 0.0

        current_qty = transportable_kg
        current_quality = produce.initial_quality_factor

        for stg in stages:
            if stg.quantity_loss_pct > 0:
                current_qty *= max(0.0, 1.0 - (stg.quantity_loss_pct / 100.0))
            if stg.quality_impact_pct > 0:
                current_quality *= max(0.0, 1.0 - (stg.quality_impact_pct / 100.0))

        # 5. Crop Perishability Modeling
        perishability_storage_type = (
            storage_facility.storage_type if storage_facility else StorageType.AMBIENT
        )
        total_days = max(1, int(round(total_elapsed_hours / 24.0)))

        perishability: PerishabilityTrajectory = PerishabilityEngine.calculate_trajectory(
            commodity_id=produce.commodity_id,
            storage_type=perishability_storage_type,
            initial_quantity_kg=current_qty,
            duration_days=total_days,
            initial_quality_factor=current_quality,
        )

        effective_delivered_qty = perishability.final_quantity_kg
        final_quality = perishability.final_quality_factor

        # 6. Logistics Costing
        stages_handling_fee = sum(s.cost for s in stages)
        combined_handling_fee = (extra_handling_fee or 0.0) + stages_handling_fee

        logistics_cost = LogisticsCostEngine.calculate_cost_breakdown(
            transport_mode=transport_mode,
            quantity_kg=transportable_kg if transportable_kg > 0 else produce.quantity_kg,
            distance_km=distance_km,
            loading_fee_per_quintal=loading_fee_per_quintal,
            unloading_fee_per_quintal=unloading_fee_per_quintal,
            extra_handling_fee=combined_handling_fee if combined_handling_fee > 0 else None,
            is_demo=is_demo,
        )

        total_pathway_cost = logistics_cost.total_cost + storage_cost

        # 7. Logistics Feasibility
        feasibility = LogisticsFeasibilityEvaluator.evaluate(
            produce=produce,
            destination=destination,
            transport_mode=transport_mode,
            distance_km=distance_km,
            distance_type=distance_type,
            transit_duration_hours=transit_hours,
            transit_time_status=transit_time_status,
            storage_facility=storage_facility,
            storage_feasibility=storage_feasibility,
            storage_duration_days=storage_duration_days,
            quality_factor=final_quality,
        )

        # 8. Composite Economic Status
        economic_status = logistics_cost.economic_status
        if storage_facility is not None:
            if storage_facility.provenance.status == ProvenanceStatus.DEMO and economic_status != EconomicStatus.UNAVAILABLE:
                economic_status = EconomicStatus.DEMO_ASSUMPTION

        scenario_provenance = EconomicProvenance(
            source_name="LOGISTICS_SCENARIO_COMPOSER",
            status=ProvenanceStatus.DEMO if is_demo else ProvenanceStatus.CONFIGURED,
            is_demo=is_demo,
            justification=f"Modeled multi-stage physical pathway: {scenario_name}",
        )

        return LogisticsScenario(
            scenario_id=scenario_id,
            scenario_name=scenario_name,
            destination=destination,
            stages=stages,
            storage_facility=storage_facility,
            transport_mode=transport_mode,
            distance_km=distance_km,
            distance_type=distance_type,
            transit_duration_hours=transit_hours,
            transit_time_status=transit_time_status,
            storage_duration_days=storage_duration_days,
            total_elapsed_hours=total_elapsed_hours,
            initial_quantity_kg=produce.quantity_kg,
            transportable_quantity_kg=transportable_kg,
            effective_delivered_quantity_kg=effective_delivered_qty,
            final_quality_factor=final_quality,
            logistics_cost=logistics_cost,
            storage_cost=storage_cost,
            total_pathway_cost=total_pathway_cost,
            feasibility=feasibility,
            storage_feasibility=storage_feasibility,
            perishability=perishability,
            economic_status=economic_status,
            provenance=scenario_provenance,
        )

    @classmethod
    def build_scenario_a(
        cls,
        produce: ProduceInput,
        destination: Destination,
        transport_mode: TransportModeSpec,
        road_distance_km: float | None = None,
        loading_fee_per_quintal: float = 12.0,
        unloading_fee_per_quintal: float = 10.0,
        is_demo: bool = True,
    ) -> LogisticsScenario:
        """
        Scenario A: Direct Farm Gate to Commercial Buyer.
        Stages: Loading at farm, direct transit, unloading at buyer facility.
        Storage duration: 0 days.
        """
        stages = [
            HandlingStage(
                stage_id="STG_A_LOAD",
                stage_type=HandlingStageType.LOADING,
                duration_hours=2.0,
                cost=0.0,  # Covered in logistics cost breakdown loading fee
                quantity_loss_pct=0.2,
                quality_impact_pct=0.1,
            ),
            HandlingStage(
                stage_id="STG_A_UNLOAD",
                stage_type=HandlingStageType.UNLOADING,
                duration_hours=1.5,
                cost=0.0,  # Covered in logistics cost breakdown unloading fee
                quantity_loss_pct=0.1,
                quality_impact_pct=0.1,
            ),
        ]

        return cls.compose_scenario(
            scenario_id=f"SCENARIO_A_{destination.destination_id}",
            scenario_name="Direct Farm to Buyer",
            produce=produce,
            destination=destination,
            transport_mode=transport_mode,
            stages=stages,
            storage_facility=None,
            storage_duration_days=0,
            road_distance_km=road_distance_km,
            loading_fee_per_quintal=loading_fee_per_quintal,
            unloading_fee_per_quintal=unloading_fee_per_quintal,
            is_demo=is_demo,
        )

    @classmethod
    def build_scenario_b(
        cls,
        produce: ProduceInput,
        destination: Destination,
        storage_facility: StorageFacility,
        transport_mode: TransportModeSpec,
        storage_duration_days: int = 14,
        road_distance_km: float | None = None,
        loading_fee_per_quintal: float = 12.0,
        unloading_fee_per_quintal: float = 10.0,
        is_demo: bool = True,
    ) -> LogisticsScenario:
        """
        Scenario B: Farm Gate -> Ventilated / Ambient Storage -> Buyer.
        Stages: Loading, transit to storage, storage intake, holding, storage dispatch, transit, unloading.
        Storage duration: D days.
        """
        stages = [
            HandlingStage(
                stage_id="STG_B_LOAD_FARM",
                stage_type=HandlingStageType.LOADING,
                duration_hours=2.0,
                cost=0.0,
                quantity_loss_pct=0.2,
                quality_impact_pct=0.1,
            ),
            HandlingStage(
                stage_id="STG_B_STORAGE_ENTRY",
                stage_type=HandlingStageType.STORAGE_ENTRY,
                duration_hours=2.0,
                cost=0.0,
                quantity_loss_pct=0.3,
                quality_impact_pct=0.2,
            ),
            HandlingStage(
                stage_id="STG_B_STORAGE_EXIT",
                stage_type=HandlingStageType.STORAGE_EXIT,
                duration_hours=2.0,
                cost=0.0,
                quantity_loss_pct=0.2,
                quality_impact_pct=0.2,
            ),
            HandlingStage(
                stage_id="STG_B_UNLOAD_BUYER",
                stage_type=HandlingStageType.UNLOADING,
                duration_hours=1.5,
                cost=0.0,
                quantity_loss_pct=0.1,
                quality_impact_pct=0.1,
            ),
        ]

        return cls.compose_scenario(
            scenario_id=f"SCENARIO_B_{storage_facility.facility_id}_{destination.destination_id}",
            scenario_name="Farm to Ambient Storage to Buyer",
            produce=produce,
            destination=destination,
            transport_mode=transport_mode,
            stages=stages,
            storage_facility=storage_facility,
            storage_duration_days=storage_duration_days,
            road_distance_km=road_distance_km,
            loading_fee_per_quintal=loading_fee_per_quintal,
            unloading_fee_per_quintal=unloading_fee_per_quintal,
            is_demo=is_demo,
        )

    @classmethod
    def build_scenario_c(
        cls,
        produce: ProduceInput,
        mandi_destination: Destination,
        transport_mode: TransportModeSpec,
        road_distance_km: float | None = None,
        loading_fee_per_quintal: float = 12.0,
        unloading_fee_per_quintal: float = 10.0,
        is_demo: bool = True,
    ) -> LogisticsScenario:
        """
        Scenario C: Farm Gate to Physical Mandi / APMC Yard.
        Stages: Loading at farm, road haulage to APMC, yard unloading.
        Storage duration: 0 days.
        """
        stages = [
            HandlingStage(
                stage_id="STG_C_LOAD",
                stage_type=HandlingStageType.LOADING,
                duration_hours=2.0,
                cost=0.0,
                quantity_loss_pct=0.2,
                quality_impact_pct=0.1,
            ),
            HandlingStage(
                stage_id="STG_C_UNLOAD_MANDI",
                stage_type=HandlingStageType.UNLOADING,
                duration_hours=2.5,  # Yard congestion
                cost=0.0,
                quantity_loss_pct=0.3,
                quality_impact_pct=0.2,
            ),
        ]

        return cls.compose_scenario(
            scenario_id=f"SCENARIO_C_{mandi_destination.destination_id}",
            scenario_name="Farm to APMC Mandi Yard",
            produce=produce,
            destination=mandi_destination,
            transport_mode=transport_mode,
            stages=stages,
            storage_facility=None,
            storage_duration_days=0,
            road_distance_km=road_distance_km,
            loading_fee_per_quintal=loading_fee_per_quintal,
            unloading_fee_per_quintal=unloading_fee_per_quintal,
            is_demo=is_demo,
        )

    @classmethod
    def build_scenario_d(
        cls,
        produce: ProduceInput,
        destination: Destination,
        cold_storage_facility: StorageFacility,
        transport_mode: TransportModeSpec,
        storage_duration_days: int = 14,
        road_distance_km: float | None = None,
        loading_fee_per_quintal: float = 15.0,
        unloading_fee_per_quintal: float = 12.0,
        is_demo: bool = True,
    ) -> LogisticsScenario:
        """
        Scenario D: Farm Gate -> Cold Storage Hub -> Premium Buyer / Terminal Market.
        Stages: Loading, transit, cold intake, temperature-controlled holding, cold dispatch, reefer transit, delivery.
        Storage duration: D days in cold chain.
        """
        stages = [
            HandlingStage(
                stage_id="STG_D_LOAD_FARM",
                stage_type=HandlingStageType.LOADING,
                duration_hours=2.0,
                cost=0.0,
                quantity_loss_pct=0.15,
                quality_impact_pct=0.1,
            ),
            HandlingStage(
                stage_id="STG_D_COLD_ENTRY",
                stage_type=HandlingStageType.STORAGE_ENTRY,
                duration_hours=1.5,
                cost=0.0,
                quantity_loss_pct=0.1,
                quality_impact_pct=0.05,
            ),
            HandlingStage(
                stage_id="STG_D_COLD_EXIT",
                stage_type=HandlingStageType.STORAGE_EXIT,
                duration_hours=1.5,
                cost=0.0,
                quantity_loss_pct=0.1,
                quality_impact_pct=0.05,
            ),
            HandlingStage(
                stage_id="STG_D_UNLOAD_DEST",
                stage_type=HandlingStageType.UNLOADING,
                duration_hours=1.5,
                cost=0.0,
                quantity_loss_pct=0.1,
                quality_impact_pct=0.05,
            ),
        ]

        return cls.compose_scenario(
            scenario_id=f"SCENARIO_D_{cold_storage_facility.facility_id}_{destination.destination_id}",
            scenario_name="Farm to Cold Chain Hub to Buyer",
            produce=produce,
            destination=destination,
            transport_mode=transport_mode,
            stages=stages,
            storage_facility=cold_storage_facility,
            storage_duration_days=storage_duration_days,
            road_distance_km=road_distance_km,
            loading_fee_per_quintal=loading_fee_per_quintal,
            unloading_fee_per_quintal=unloading_fee_per_quintal,
            is_demo=is_demo,
        )
