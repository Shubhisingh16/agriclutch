/**
 * TypeScript Contracts for AgriClutch Buyer Matching & Demand Aggregation Subsystem.
 * Aligned strictly with Pydantic v2 schemas and backend contracts.
 * SIH26132 — Strengthening Market Linkages and Price Discovery for Farmers.
 */

export type BuyerType =
  | "wholesaler"
  | "processor"
  | "retailer"
  | "institutional_buyer"
  | "exporter"
  | "fpo"
  | "cooperative"
  | "aggregator"
  | "trader";

export type DeliveryMode =
  | "EX_FARM"
  | "MANDI_GATE"
  | "BUYER_PREMISES"
  | "WAREHOUSE";

export type PriceBasis =
  | "FIXED_QUOTE"
  | "APMC_INDEXED"
  | "NEGOTIABLE"
  | "UNAVAILABLE";

export type PaymentTerms =
  | "IMMEDIATE_CASH"
  | "ADVANCE_PARTIAL"
  | "NET_3_DAYS"
  | "NET_7_DAYS"
  | "NET_15_DAYS"
  | "UPON_DELIVERY"
  | "UNAVAILABLE";

export type DemandType =
  | "OBSERVED_DEMAND"
  | "QUOTED_DEMAND"
  | "CONTRACTED_DEMAND"
  | "ESTIMATED_DEMAND"
  | "DEMO_DEMAND"
  | "UNAVAILABLE";

export type DemandStatus =
  | "ACTIVE"
  | "FULFILLED"
  | "EXPIRED"
  | "CANCELLED";

export type QuantityMatchStatus =
  | "EXACT_MATCH"
  | "PARTIAL_MATCH"
  | "INSUFFICIENT_SUPPLY"
  | "INSUFFICIENT_DEMAND"
  | "ZERO_MATCH";

export type TemporalOverlapStatus =
  | "FULL_OVERLAP"
  | "PARTIAL_OVERLAP"
  | "NO_OVERLAP"
  | "EXPIRED_REQUIREMENT"
  | "FUTURE_REQUIREMENT"
  | "UNAVAILABLE";

export type DistanceStatus =
  | "DISTANCE_GEODESIC"
  | "DISTANCE_ROUTE"
  | "DISTANCE_UNAVAILABLE";

export type ReliabilityStatus =
  | "CALCULATED"
  | "INSUFFICIENT_HISTORY"
  | "UNAVAILABLE";

export type DistributionStatus =
  | "VALID"
  | "INSUFFICIENT_DATA";

export type ProvenanceStatus =
  | "EMPIRICAL"
  | "OFFICIAL"
  | "RESEARCH"
  | "CONFIGURED"
  | "DEMO"
  | "UNAVAILABLE";

export interface Buyer {
  id: string;
  display_name: string;
  buyer_type: BuyerType;
  location: string;
  latitude?: number | null;
  longitude?: number | null;
  active_status: boolean;
  source_name: string;
  source_record_id?: string | null;
  source_reference?: string | null;
  provenance_status: ProvenanceStatus;
  is_demo: boolean;
  created_at?: string | null;
}

export interface BuyerRequirement {
  id: string;
  buyer_id: string;
  commodity_id: string;
  variety?: string | null;
  minimum_quantity_kg: number;
  maximum_quantity_kg: number;
  preferred_quality_grade: string;
  acceptable_quality_range: string[];
  required_from: string;
  required_until: string;
  delivery_mode: DeliveryMode;
  delivery_location?: string | null;
  delivery_latitude?: number | null;
  delivery_longitude?: number | null;
  price_basis: PriceBasis;
  quoted_price?: number | null;
  currency: string;
  price_unit: string;
  payment_terms: PaymentTerms;
  validity_start?: string | null;
  validity_end?: string | null;
  provenance_status: ProvenanceStatus;
  is_demo: boolean;
}

export interface BuyerDemand {
  id: string;
  buyer_id: string;
  commodity_id: string;
  variety?: string | null;
  quantity_kg: number;
  quality_requirement: string;
  date_window_start: string;
  date_window_end: string;
  location: string;
  price_per_kg?: number | null;
  price_unit: string;
  demand_type: DemandType;
  demand_status: DemandStatus;
  provenance_status: ProvenanceStatus;
  is_demo: boolean;
}

export interface FarmerSupply {
  id: string;
  supply_reference_id?: string | null;
  commodity_id: string;
  variety?: string | null;
  quantity_kg: number;
  quality_grade: string;
  available_from: string;
  available_until: string;
  origin_location: string;
  origin_latitude?: number | null;
  origin_longitude?: number | null;
  storage_available: boolean;
  storage_type?: string | null;
  provenance_status: ProvenanceStatus;
  is_demo: boolean;
}

export interface CompatibilityMatch {
  buyer_id: string;
  buyer_name: string;
  requirement_id: string;
  commodity_id: string;
  variety_match: boolean;
  quality_match: boolean;
  preferred_grade: string;
  acceptable_grades: string[];
  quantity_status: QuantityMatchStatus;
  compatible_quantity_kg: number;
  unmatched_supply_kg: number;
  temporal_status: TemporalOverlapStatus;
  overlap_days: number;
  distance_status: DistanceStatus;
  distance_km?: number | null;
  delivery_mode: DeliveryMode;
  delivery_location?: string | null;
  price_basis: PriceBasis;
  quoted_price?: number | null;
  payment_terms: PaymentTerms;
  is_compatible: boolean;
  explanations: string[];
  provenance_status: ProvenanceStatus;
  is_demo: boolean;
}

export interface MatchingListResponse {
  supply_id: string;
  commodity_id: string;
  total_supply_kg: number;
  matches_evaluated: number;
  compatible_matches_count: number;
  matches: CompatibilityMatch[];
}

export interface ReliabilityMetrics {
  buyer_id: string;
  status: ReliabilityStatus;
  sample_size: number;
  fulfillment_rate?: number | null;
  cancellation_rate?: number | null;
  avg_payment_delay_days?: number | null;
  dispute_rate?: number | null;
  provenance_status: ProvenanceStatus;
  is_demo: boolean;
  audit_note: string;
}

export interface DemandAggregate {
  commodity_id: string;
  region?: string | null;
  total_demand_kg: number;
  buyer_count: number;
  top_buyer_share_pct?: number | null;
  hhi_concentration?: number | null;
  breakdown_by_quality: Record<string, number>;
  breakdown_by_type: Record<string, number>;
  provenance_status: ProvenanceStatus;
  is_demo: boolean;
}

export interface DemandDistribution {
  commodity_id: string;
  status: DistributionStatus;
  sample_size: number;
  min_kg?: number | null;
  max_kg?: number | null;
  mean_kg?: number | null;
  median_kg?: number | null;
  p10_kg?: number | null;
  p25_kg?: number | null;
  p50_kg?: number | null;
  p75_kg?: number | null;
  p90_kg?: number | null;
  provenance_status: ProvenanceStatus;
  is_demo: boolean;
}
