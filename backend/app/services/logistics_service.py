"""
AgriClutch Logistics, Storage & Perishability Service.
Provides business logic for transport modes, storage facilities, route distance resolution,
crop shelf-life modeling, and auditable physical pathway evaluation.
SIH26132 — Strengthening Market Linkages and Price Discovery for Farmers.
"""

import uuid
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.seeds.logistics_demo_seed_data import (
    DEMO_STORAGE_FACILITIES,
    DEMO_TRANSPORT_MODES,
)
from app.models.logistics import (
    LogisticsScenarioAuditModel,
    StorageFacilityModel,
    TransportModeModel,
)
from app.schemas.logistics import (
    DistanceCalculationRequest,
    EvaluatePathwaysRequest,
)
from ml.logistics import (
    Destination,
    DistanceEngine,
    DistanceType,
    EconomicProvenance,
    EconomicStatus,
    LogisticsScenario,
    LogisticsScenarioComposer,
    PerishabilityEngine,
    ProduceInput,
    ProvenanceStatus,
    StorageEngine,
    StorageFacility,
    StorageType,
    TransportModeSpec,
)


class LogisticsService:
    """
    Service layer for physical transit, storage allocations, decay curves, and scenario pathways.
    Exclusively factual: zero recommendation, ranking, or scoring logic.
    """

    @classmethod
    async def get_transport_modes(
        cls,
        session: Optional[AsyncSession] = None,
        active_only: bool = True,
    ) -> List[Dict[str, Any]]:
        """Retrieves available transport vehicle modes from DB or demo seed fixtures."""
        if session is not None:
            try:
                stmt = select(TransportModeModel)
                if active_only:
                    stmt = stmt.where(TransportModeModel.active_status.is_(True))
                result = await session.execute(stmt)
                if hasattr(result, "scalars"):
                    scalars_res = result.scalars()
                    if hasattr(scalars_res, "all"):
                        db_modes = scalars_res.all()
                        if isinstance(db_modes, list) and db_modes and hasattr(db_modes[0], "id"):
                            return [
                                {
                                    "id": m.id,
                                    "display_name": m.display_name,
                                    "vehicle_type": m.vehicle_type,
                                    "capacity_kg": m.capacity_kg,
                                    "base_dispatch_fee": m.base_dispatch_fee,
                                    "cost_per_km": m.cost_per_km,
                                    "cost_per_km_tonne": m.cost_per_km_tonne,
                                    "speed_kmh": m.speed_kmh,
                                    "temperature_controlled": m.temperature_controlled,
                                    "active_status": m.active_status,
                                    "source_name": m.source_name,
                                    "provenance_status": m.provenance_status,
                                    "is_demo": m.is_demo,
                                }
                                for m in db_modes
                            ]
            except Exception:
                pass  # Fall back to demo fixtures

        # Return demo fixtures
        modes = DEMO_TRANSPORT_MODES
        if active_only:
            modes = [m for m in modes if m.get("active_status", True)]
        return modes

    @classmethod
    async def get_storage_facilities(
        cls,
        session: Optional[AsyncSession] = None,
        storage_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieves storage facilities from DB or demo seed fixtures."""
        if session is not None:
            try:
                stmt = select(StorageFacilityModel).where(StorageFacilityModel.active_status.is_(True))
                if storage_type:
                    stmt = stmt.where(StorageFacilityModel.storage_type == storage_type.upper())
                result = await session.execute(stmt)
                if hasattr(result, "scalars"):
                    scalars_res = result.scalars()
                    if hasattr(scalars_res, "all"):
                        db_facilities = scalars_res.all()
                        if isinstance(db_facilities, list) and db_facilities and hasattr(db_facilities[0], "id"):
                            return [
                                {
                                    "id": f.id,
                                    "facility_name": f.facility_name,
                                    "storage_type": f.storage_type,
                                    "location": f.location,
                                    "latitude": f.latitude,
                                    "longitude": f.longitude,
                                    "total_capacity_kg": f.total_capacity_kg,
                                    "available_capacity_kg": f.available_capacity_kg,
                                    "cost_per_kg_day": f.cost_per_kg_day,
                                    "min_duration_days": f.min_duration_days,
                                    "max_duration_days": f.max_duration_days,
                                    "temperature_celsius": f.temperature_celsius,
                                    "humidity_pct": f.humidity_pct,
                                    "active_status": f.active_status,
                                    "source_name": f.source_name,
                                    "provenance_status": f.provenance_status,
                                    "is_demo": f.is_demo,
                                }
                                for f in db_facilities
                            ]
            except Exception:
                pass

        facilities = DEMO_STORAGE_FACILITIES
        if storage_type:
            facilities = [f for f in facilities if f.get("storage_type", "").upper() == storage_type.upper()]
        return facilities

    @classmethod
    async def get_storage_availability(
        cls,
        facility_id: str,
        session: Optional[AsyncSession] = None,
    ) -> Dict[str, Any]:
        """Queries capacity and operating bounds for a specific facility."""
        facilities = await cls.get_storage_facilities(session=session)
        matching = next((f for f in facilities if f["id"] == facility_id), None)
        if not matching:
            return {
                "facility_id": facility_id,
                "facility_name": "UNKNOWN_FACILITY",
                "storage_type": "UNKNOWN",
                "available_capacity_kg": 0.0,
                "total_capacity_kg": 0.0,
                "cost_per_kg_day": 0.0,
                "is_available": False,
                "provenance": {
                    "source_name": "STORAGE_AVAILABILITY_QUERY",
                    "status": "UNAVAILABLE",
                    "is_demo": True,
                    "justification": f"Facility ID '{facility_id}' not found.",
                },
            }

        return {
            "facility_id": matching["id"],
            "facility_name": matching["facility_name"],
            "storage_type": matching["storage_type"],
            "available_capacity_kg": matching["available_capacity_kg"],
            "total_capacity_kg": matching["total_capacity_kg"],
            "cost_per_kg_day": matching["cost_per_kg_day"],
            "is_available": matching["available_capacity_kg"] > 0,
            "provenance": {
                "source_name": matching["source_name"],
                "status": matching["provenance_status"],
                "is_demo": matching["is_demo"],
                "justification": "Facility capacity lookup from verified schedule or demo fixtures.",
            },
        }

    @classmethod
    def calculate_distance(
        cls,
        request: DistanceCalculationRequest,
    ) -> Dict[str, Any]:
        """Calculates geographic distance and transit duration without inventing road speed."""
        straight_dist, _ = DistanceEngine.resolve_route_distance(
            origin_lat=request.origin_lat,
            origin_lon=request.origin_lon,
            dest_lat=request.dest_lat,
            dest_lon=request.dest_lon,
            road_distance_km=None,
        )

        circuity_factor = 1.25
        estimated_route_km = (
            round(straight_dist * circuity_factor, 1) if straight_dist is not None else None
        )

        dist: float | None = None
        dist_type: DistanceType = DistanceType.UNKNOWN_DISTANCE

        if request.road_distance_km is not None and request.road_distance_km >= 0:
            dist = request.road_distance_km
            dist_type = DistanceType.ROAD_DISTANCE
            provenance = EconomicProvenance(
                source_name="DOCUMENTED_ROAD_DISTANCE",
                status=ProvenanceStatus.EMPIRICAL,
                is_demo=True,
                justification="Empirically documented corridor road distance.",
            )
        elif straight_dist is not None:
            dist = estimated_route_km
            dist_type = DistanceType.ESTIMATED_ROUTE_DISTANCE
            provenance = EconomicProvenance(
                source_name="CONFIGURED_CIRCUITY_MODEL",
                status=ProvenanceStatus.CONFIGURED,
                is_demo=True,
                justification="Estimated route distance using configured 1.25x circuity factor.",
            )
        else:
            dist = None
            dist_type = DistanceType.UNKNOWN_DISTANCE
            provenance = EconomicProvenance(
                source_name="HAVERSINE_SPHERICAL_ENGINE",
                status=ProvenanceStatus.UNAVAILABLE,
                is_demo=True,
                justification="Coordinates missing; distance cannot be determined.",
            )

        transit_hours, transit_status = DistanceEngine.calculate_transit_time(
            distance_km=dist,
            speed_kmh=request.speed_kmh,
        )

        return {
            "distance_km": round(dist, 1) if dist is not None else None,
            "distance_type": dist_type.value,
            "straight_line_distance_km": round(straight_dist, 1) if straight_dist is not None else None,
            "circuity_factor": circuity_factor,
            "estimated_route_distance_km": estimated_route_km,
            "transit_duration_hours": round(transit_hours, 1) if transit_hours is not None else None,
            "transit_time_status": transit_status.value,
            "provenance": provenance.to_dict(),
        }

    @classmethod
    def calculate_perishability_trajectory(
        cls,
        commodity_id: str,
        storage_type: str,
        initial_quantity_kg: float,
        duration_days: int,
        initial_quality_factor: float = 1.0,
    ) -> Dict[str, Any]:
        """Generates daily physical loss and quality decay points."""
        try:
            st = StorageType(storage_type.upper())
        except ValueError:
            st = StorageType.AMBIENT

        traj = PerishabilityEngine.calculate_trajectory(
            commodity_id=commodity_id,
            storage_type=st,
            initial_quantity_kg=initial_quantity_kg,
            duration_days=duration_days,
            initial_quality_factor=initial_quality_factor,
        )
        return traj.to_dict()

    @classmethod
    def evaluate_storage_feasibility(
        cls,
        facility_id: str,
        requested_quantity_kg: float,
        requested_duration_days: int,
    ) -> Dict[str, Any]:
        """Evaluates capacity and horizon bounds for storage holding."""
        facility_dict = next((f for f in DEMO_STORAGE_FACILITIES if f["id"] == facility_id), None)
        fac_obj: Optional[StorageFacility] = None
        if facility_dict:
            fac_obj = StorageFacility(
                facility_id=facility_dict["id"],
                name=facility_dict["facility_name"],
                storage_type=StorageType(facility_dict["storage_type"]),
                location=facility_dict["location"],
                capacity_kg=facility_dict["total_capacity_kg"],
                available_capacity_kg=facility_dict["available_capacity_kg"],
                cost_per_kg_day=facility_dict["cost_per_kg_day"],
                min_duration_days=facility_dict["min_duration_days"],
                max_duration_days=facility_dict["max_duration_days"],
                latitude=facility_dict.get("latitude"),
                longitude=facility_dict.get("longitude"),
            )

        res = StorageEngine.evaluate_storage(
            facility=fac_obj,
            requested_quantity_kg=requested_quantity_kg,
            requested_duration_days=requested_duration_days,
        )
        return res.to_dict()

    @classmethod
    async def evaluate_pathways(
        cls,
        request: EvaluatePathwaysRequest,
        session: Optional[AsyncSession] = None,
    ) -> Dict[str, Any]:
        """
        Evaluates physical multi-stage pathways (Scenarios A through D) for a farmer produce lot.
        Compares transit distance, duration, holding loss, quality retention, and friction costs.
        Strictly zero ranking, zero scoring, and zero recommendation.
        """
        # 1. Instantiate ProduceInput
        produce = ProduceInput(
            produce_id=f"LOT_{uuid.uuid4().hex[:8].upper()}",
            commodity_id=request.commodity_id.strip().lower(),
            quantity_kg=request.quantity_kg,
            quality_grade=request.quality_grade,
            origin_location=request.origin_location,
            origin_latitude=request.origin_latitude or 30.8350,  # Default to Kalka coords if not given
            origin_longitude=request.origin_longitude or 76.9350,
            available_from=request.available_from,
            available_until=request.available_until,
            initial_quality_factor=1.0,
            provenance=EconomicProvenance(
                source_name="FARMER_EVALUATE_PATHWAYS_REQUEST",
                status=ProvenanceStatus.DEMO,
                is_demo=True,
            ),
        )

        # 2. Select Transport Mode
        transport_modes = await cls.get_transport_modes(session=session)
        selected_mode_dict = None
        if request.transport_mode_id:
            selected_mode_dict = next((m for m in transport_modes if m["id"] == request.transport_mode_id), None)
        if not selected_mode_dict:
            # Default to LCV
            selected_mode_dict = next(
                (m for m in transport_modes if m["id"] == "DEMO_LCV_TATA_407"), transport_modes[0]
            )

        transport_mode = TransportModeSpec(
            mode_id=selected_mode_dict["id"],
            display_name=selected_mode_dict["display_name"],
            vehicle_type=selected_mode_dict["vehicle_type"],
            capacity_kg=selected_mode_dict["capacity_kg"],
            base_dispatch_fee=selected_mode_dict["base_dispatch_fee"],
            cost_per_km=selected_mode_dict.get("cost_per_km"),
            cost_per_km_tonne=selected_mode_dict.get("cost_per_km_tonne"),
            speed_kmh=selected_mode_dict.get("speed_kmh"),
            temperature_controlled=selected_mode_dict.get("temperature_controlled", False),
        )

        # 3. Available Storage Facilities
        storage_facilities = await cls.get_storage_facilities(session=session)
        ambient_fac_dict = next(
            (f for f in storage_facilities if f["id"] == "DEMO_WAREHOUSE_MOHALI"), storage_facilities[0]
        )
        cold_fac_dict = next(
            (f for f in storage_facilities if f["id"] == "DEMO_COLD_STORAGE_NORTH"), storage_facilities[1]
        )

        ambient_storage = StorageFacility(
            facility_id=ambient_fac_dict["id"],
            name=ambient_fac_dict["facility_name"],
            storage_type=StorageType(ambient_fac_dict["storage_type"]),
            location=ambient_fac_dict["location"],
            capacity_kg=ambient_fac_dict["total_capacity_kg"],
            available_capacity_kg=ambient_fac_dict["available_capacity_kg"],
            cost_per_kg_day=ambient_fac_dict["cost_per_kg_day"],
            latitude=ambient_fac_dict.get("latitude"),
            longitude=ambient_fac_dict.get("longitude"),
            min_duration_days=ambient_fac_dict["min_duration_days"],
            max_duration_days=ambient_fac_dict["max_duration_days"],
        )

        cold_storage = StorageFacility(
            facility_id=cold_fac_dict["id"],
            name=cold_fac_dict["facility_name"],
            storage_type=StorageType(cold_fac_dict["storage_type"]),
            location=cold_fac_dict["location"],
            capacity_kg=cold_fac_dict["total_capacity_kg"],
            available_capacity_kg=cold_fac_dict["available_capacity_kg"],
            cost_per_kg_day=cold_fac_dict["cost_per_kg_day"],
            latitude=cold_fac_dict.get("latitude"),
            longitude=cold_fac_dict.get("longitude"),
            min_duration_days=cold_fac_dict["min_duration_days"],
            max_duration_days=cold_fac_dict["max_duration_days"],
        )

        # 4. Standard Benchmark Destinations
        destinations = [
            Destination(
                destination_id="DEST_BUYER_LOCAL_HUB",
                name="Punjab Fresh Mart Hub (Commercial Retail Buyer)",
                destination_type="BUYER",
                location="Mohali Sector 82, Punjab",
                latitude=30.6800,
                longitude=76.7200,
                delivery_window_start=request.available_from,
                delivery_window_end=request.available_until,
            ),
            Destination(
                destination_id="DEST_MANDI_CHD_APMC",
                name="Chandigarh APMC Yard (Regional Mandi)",
                destination_type="MANDI",
                location="Sector 26, Chandigarh",
                latitude=30.7250,
                longitude=76.8000,
                delivery_window_start=request.available_from,
                delivery_window_end=request.available_until,
            ),
            Destination(
                destination_id="DEST_MANDI_AZADPUR",
                name="Azadpur APMC Mandi Delhi (Terminal Market)",
                destination_type="MANDI",
                location="Azadpur, New Delhi",
                latitude=28.7150,
                longitude=77.1750,
                delivery_window_start=request.available_from,
                delivery_window_end=request.available_until,
            ),
        ]

        # 5. Compose Scenarios A, B, C, D
        scenarios: List[LogisticsScenario] = []

        # Scenario A: Direct Farm -> Local Buyer
        scen_a = LogisticsScenarioComposer.build_scenario_a(
            produce=produce,
            destination=destinations[0],
            transport_mode=transport_mode,
            road_distance_km=34.5,
            is_demo=True,
        )
        scenarios.append(scen_a)

        # Scenario B: Farm -> Ambient Storage (7 days) -> Local Buyer
        storage_days = max(1, request.storage_duration_days if request.storage_duration_days > 0 else 7)
        scen_b = LogisticsScenarioComposer.build_scenario_b(
            produce=produce,
            destination=destinations[0],
            storage_facility=ambient_storage,
            transport_mode=transport_mode,
            storage_duration_days=storage_days,
            road_distance_km=38.0,
            is_demo=True,
        )
        scenarios.append(scen_b)

        # Scenario C: Farm -> Regional APMC Mandi
        scen_c = LogisticsScenarioComposer.build_scenario_c(
            produce=produce,
            mandi_destination=destinations[1],
            transport_mode=transport_mode,
            road_distance_km=24.0,
            is_demo=True,
        )
        scenarios.append(scen_c)

        # Scenario D: Farm -> Cold Storage (14 days) -> Terminal APMC Mandi Delhi
        scen_d = LogisticsScenarioComposer.build_scenario_d(
            produce=produce,
            destination=destinations[2],
            cold_storage_facility=cold_storage,
            transport_mode=transport_mode,
            storage_duration_days=14,
            road_distance_km=258.0,
            is_demo=True,
        )
        scenarios.append(scen_d)

        # 6. Persist Audit Trail if DB session available
        if session is not None:
            try:
                for sc in scenarios:
                    audit_record = LogisticsScenarioAuditModel(
                        id=f"AUDIT_{uuid.uuid4().hex[:12].upper()}",
                        produce_id=produce.produce_id,
                        destination_id=sc.destination.destination_id,
                        scenario_id=sc.scenario_id,
                        scenario_name=sc.scenario_name,
                        storage_facility_id=sc.storage_facility.facility_id if sc.storage_facility else None,
                        transport_mode_id=sc.transport_mode.mode_id,
                        distance_km=sc.distance_km,
                        transit_duration_hours=sc.transit_duration_hours,
                        storage_duration_days=sc.storage_duration_days,
                        delivered_quantity_kg=sc.effective_delivered_quantity_kg,
                        final_quality_factor=sc.final_quality_factor,
                        logistics_cost=sc.logistics_cost.total_cost,
                        storage_cost=sc.storage_cost,
                        total_pathway_cost=sc.total_pathway_cost,
                        feasibility_status=sc.feasibility.status.value,
                        economic_status=sc.economic_status.value,
                        provenance_status=sc.provenance.status.value,
                        is_demo=sc.provenance.is_demo,
                        audit_payload=sc.to_dict(),
                    )
                    session.add(audit_record)
                await session.commit()
            except Exception:
                pass

        return {
            "lot_summary": produce.to_dict(),
            "scenarios": [s.to_dict() for s in scenarios],
            "economic_status": EconomicStatus.DEMO_ASSUMPTION.value,
            "provenance": {
                "source_name": "LOGISTICS_PATHWAY_EVALUATION_SERVICE",
                "status": "DEMO",
                "is_demo": True,
                "justification": "Modeled physical transit, storage allocations, and shelf-life trajectories.",
            },
        }
