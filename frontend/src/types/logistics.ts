/**
 * AgriClutch Step 13 Logistics, Storage & Perishability TypeScript Definitions.
 * Strictly typed interfaces mirroring FastAPI Pydantic v2 schemas.
 * Exclusively factual: zero recommendation, ranking, or scoring fields.
 * SIH26132 — Strengthening Market Linkages and Price Discovery for Farmers.
 */

export type StorageType = "AMBIENT" | "COLD" | "VENTILATED" | "UNKNOWN";

export type DistanceType =
  | "STRAIGHT_LINE_DISTANCE"
  | "ESTIMATED_ROUTE_DISTANCE"
  | "ROAD_DISTANCE"
  | "UNKNOWN_DISTANCE";

export type TransitTimeStatus =
  | "OBSERVED"
  | "CONFIGURED"
  | "TRANSIT_TIME_UNAVAILABLE";

export type FeasibilityStatus =
  | "FEASIBLE"
  | "PARTIALLY_FEASIBLE"
  | "INFEASIBLE"
  | "INSUFFICIENT_DATA"
  | "UNAVAILABLE";

export type EconomicStatus =
  | "COMPLETE_EMPIRICAL"
  | "COMPLETE_MIXED_PROVENANCE"
  | "DEMO_ASSUMPTION"
  | "INCOMPLETE"
  | "UNAVAILABLE";

export interface EconomicProvenance {
  source_name: string;
  source_record_id?: string | null;
  source_reference?: string | null;
  observed_at?: string | null;
  effective_from?: string | null;
  effective_to?: string | null;
  validity_range?: string | null;
  status: string;
  is_demo: boolean;
  justification?: string | null;
}

export interface TransportMode {
  id: string;
  display_name: string;
  vehicle_type: string;
  capacity_kg: number;
  base_dispatch_fee: number;
  cost_per_km?: number | null;
  cost_per_km_tonne?: number | null;
  speed_kmh?: number | null;
  temperature_controlled: boolean;
  active_status: boolean;
  source_name: string;
  provenance_status: string;
  is_demo: boolean;
}

export interface StorageFacility {
  id: string;
  facility_name: string;
  storage_type: StorageType;
  location: string;
  latitude?: number | null;
  longitude?: number | null;
  total_capacity_kg: number;
  available_capacity_kg: number;
  cost_per_kg_day: number;
  min_duration_days: number;
  max_duration_days: number;
  temperature_celsius?: number | null;
  humidity_pct?: number | null;
  active_status: boolean;
  source_name: string;
  provenance_status: string;
  is_demo: boolean;
}

export interface StorageAvailability {
  facility_id: string;
  facility_name: string;
  storage_type: string;
  available_capacity_kg: number;
  total_capacity_kg: number;
  cost_per_kg_day: number;
  is_available: boolean;
  provenance: EconomicProvenance;
}

export interface DistanceResult {
  distance_km: number | null;
  distance_type: DistanceType;
  straight_line_distance_km?: number | null;
  circuity_factor?: number | null;
  estimated_route_distance_km?: number | null;
  transit_duration_hours: number | null;
  transit_time_status: TransitTimeStatus;
  provenance: EconomicProvenance;
}

export interface LogisticsCostItem {
  component_name: string;
  amount: number;
  currency: string;
  unit_basis: string;
  quantity_basis_kg?: number | null;
  distance_basis_km?: number | null;
  duration_days?: number | null;
  provenance: EconomicProvenance;
}

export interface LogisticsCostBreakdown {
  total_cost: number;
  transport_cost: number;
  loading_cost: number;
  unloading_cost: number;
  handling_cost: number;
  other_cost: number;
  items: LogisticsCostItem[];
  economic_status: EconomicStatus;
  provenance: EconomicProvenance;
}

export interface PerishabilityPoint {
  day: number;
  elapsed_hours: number;
  quantity_kg: number;
  quantity_loss_kg: number;
  survival_factor: number;
  quality_factor: number;
}

export interface PerishabilityModelSpec {
  crop: string;
  storage_type: string;
  decay_parameter_delta: number;
  quality_decay_beta: number;
  unit: string;
  max_supported_days: number;
  equation: string;
  assumptions: string;
  calibration_status: string;
  provenance: EconomicProvenance;
}

export interface PerishabilityTrajectory {
  commodity_id: string;
  storage_type: string;
  initial_quantity_kg: number;
  final_quantity_kg: number;
  final_quality_factor: number;
  duration_days: number;
  trajectory: PerishabilityPoint[];
  model_spec?: PerishabilityModelSpec | null;
  status: string;
  provenance: EconomicProvenance;
}

export interface HandlingStage {
  stage_id: string;
  stage_type: string;
  duration_hours: number;
  cost: number;
  quantity_loss_pct: number;
  quality_impact_pct: number;
  provenance: EconomicProvenance;
}

export interface StorageFeasibility {
  facility_id: string;
  facility_name: string;
  storage_type: string;
  requested_quantity_kg: number;
  available_capacity_kg: number;
  stored_quantity_kg: number;
  unstored_quantity_kg: number;
  requested_duration_days: number;
  min_supported_days: number;
  max_supported_days: number;
  storage_cost: number;
  status: FeasibilityStatus;
  warnings: string[];
  provenance: EconomicProvenance;
}

export interface LogisticsFeasibility {
  feasible: boolean;
  status: FeasibilityStatus;
  transportable_quantity_kg: number;
  untransportable_quantity_kg: number;
  distance_km?: number | null;
  distance_type: DistanceType;
  transit_duration_hours?: number | null;
  transit_time_status: TransitTimeStatus;
  failed_constraints: string[];
  warnings: string[];
  assumptions: string[];
  provenance: EconomicProvenance;
}

export interface LogisticsScenario {
  scenario_id: string;
  scenario_name: string;
  destination: {
    destination_id: string;
    name: string;
    destination_type: string;
    location: string;
    latitude?: number | null;
    longitude?: number | null;
  };
  stages: HandlingStage[];
  storage_facility?: StorageFacility | null;
  transport_mode: TransportMode;
  distance_km?: number | null;
  distance_type: DistanceType;
  transit_duration_hours?: number | null;
  transit_time_status: TransitTimeStatus;
  storage_duration_days: number;
  total_elapsed_hours: number;
  initial_quantity_kg: number;
  transportable_quantity_kg: number;
  effective_delivered_quantity_kg: number;
  final_quality_factor: number;
  logistics_cost: LogisticsCostBreakdown;
  storage_cost: number;
  total_pathway_cost: number;
  feasibility: LogisticsFeasibility;
  storage_feasibility?: StorageFeasibility | null;
  perishability?: PerishabilityTrajectory | null;
  economic_status: EconomicStatus;
  provenance: EconomicProvenance;
}

export interface EvaluatePathwaysPayload {
  commodity_id: string;
  quantity_kg: number;
  quality_grade?: string;
  origin_location: string;
  origin_latitude?: number | null;
  origin_longitude?: number | null;
  available_from: string;
  available_until: string;
  transport_mode_id?: string | null;
  storage_facility_id?: string | null;
  storage_duration_days?: number;
  destination_ids?: string[] | null;
}

export interface EvaluatePathwaysResponse {
  lot_summary: {
    produce_id: string;
    commodity_id: string;
    quantity_kg: number;
    quality_grade: string;
    origin_location: string;
  };
  scenarios: LogisticsScenario[];
  economic_status: EconomicStatus;
  provenance: EconomicProvenance;
}
