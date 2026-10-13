/**
 * AgriClutch Step 14: Decision Intelligence, Optimal Selling Plan & What-If Simulator Types.
 * Aligned with backend Pydantic v2 schemas and optimizer contracts.
 * SIH26132 — Strengthening Market Linkages and Price Discovery for Farmers.
 */

export type SolverStatus =
  | "OPTIMAL"
  | "FEASIBLE"
  | "INFEASIBLE"
  | "UNBOUNDED"
  | "NUMERICAL_ERROR"
  | "TIME_LIMIT";

export type RiskPreference = "RISK_NEUTRAL" | "RISK_AWARE" | "RISK_AVERSE";

export type LiquidityPreference = "IMMEDIATE" | "BALANCED" | "DELAY_TOLERANT";

export type DestinationType =
  | "LOCAL_MANDI"
  | "TERMINAL_MANDI"
  | "COMMERCIAL_BUYER"
  | "FARM_GATE"
  | "COLD_STORAGE_HOLD"
  | "DRY_STORAGE_HOLD";

export type DecisionProvenanceStatus =
  | "EMPIRICAL"
  | "OFFICIAL"
  | "RESEARCH"
  | "CONFIGURED"
  | "DEMO"
  | "UNAVAILABLE";

export type ValidationStatus = "PASSED" | "FAILED" | "WARNING";

export interface PlanAllocation {
  candidate_id: string;
  destination_id: string;
  destination_name: string;
  destination_type: DestinationType;
  buyer_id?: string | null;
  buyer_name?: string | null;
  allocated_quantity_kg: number;
  allocation_percentage: number;
  execution_day: number;
  storage_facility_id?: string | null;
  storage_facility_name?: string | null;
  storage_duration_days: number;
  storage_type: string;
  transport_mode: string;
  distance_km: number;
  transit_loss_pct: number;
  spoilage_loss_pct: number;
  delivered_quantity_kg: number;
  expected_gross_price_per_kg: number;
  expected_gross_revenue: number;
  transport_cost: number;
  storage_cost: number;
  handling_cost: number;
  market_fee: number;
  total_friction_cost: number;
  expected_net_realizable_value: number;
  effective_nrv_per_kg: number;
  nrv_p10_per_kg: number;
  nrv_p50_per_kg: number;
  nrv_p90_per_kg: number;
  downside_risk_spread_per_kg: number;
  risk_penalty_per_kg: number;
  net_risk_adjusted_nrv: number;
  binding_reasons: string[];
  provenance_status: DecisionProvenanceStatus;
  is_demo: boolean;
}

export interface RiskMetrics {
  total_expected_nrv: number;
  total_p10_nrv: number;
  total_p50_nrv: number;
  total_p90_nrv: number;
  portfolio_downside_spread?: number;
  configured_tail_stress_estimate?: number;
  downside_spread_penalty?: number;
  confidence_level?: number;
  tail_stress_multiplier?: number;
  tail_stress_provenance?: DecisionProvenanceStatus;
  var_95: number;
  cvar_95: number;
  downside_standard_deviation: number;
  risk_penalty_total: number;
  risk_adjusted_nrv: number;
  risk_preference_used: RiskPreference;
  risk_weight_lambda: number;
}

export interface ConstraintAuditItem {
  constraint_name: string;
  constraint_type: string;
  limit_value: number;
  actual_value: number;
  slack: number;
  is_binding: boolean;
  status: string;
}

export interface ConstraintSummary {
  total_constraints_checked: number;
  binding_constraints: string[];
  violated_constraints: string[];
  constraint_items: ConstraintAuditItem[];
  all_satisfied: boolean;
}

export interface OptimalSellingPlan {
  plan_id: string;
  farmer_lot_id?: string | null;
  commodity_id: string;
  variety: string;
  quality_grade: string;
  total_supply_kg: number;
  decision_horizon_days: number;
  risk_preference: RiskPreference;
  liquidity_preference: LiquidityPreference;
  solver_status: SolverStatus;
  validation_status: ValidationStatus;
  solver_message: string;
  solver_duration_ms: number;
  solver_version: string;
  configuration_hash: string;
  total_allocated_kg: number;
  total_delivered_kg: number;
  expected_total_gross_revenue: number;
  total_transport_cost: number;
  total_storage_cost: number;
  total_handling_cost: number;
  total_friction_cost: number;
  expected_total_nrv: number;
  average_effective_nrv_per_kg: number;
  allocations: PlanAllocation[];
  risk_metrics: RiskMetrics;
  constraint_summary: ConstraintSummary;
  executive_summary: string;
  structured_explanations: string[];
  provenance_status: DecisionProvenanceStatus;
  is_demo: boolean;
  created_at: string;
}

export interface CounterfactualDelta {
  parameter_changed?: string;
  baseline_value?: string;
  counterfactual_value?: string;
  baseline_nrv?: number;
  counterfactual_nrv?: number;
  nrv_delta: number;
  nrv_percentage_change: number;
  baseline_allocated_kg?: number;
  counterfactual_allocated_kg?: number;
  allocation_shift_summary?: string;
  baseline_input_hash?: string;
  counterfactual_input_hash?: string;
  baseline_solver_status?: SolverStatus;
  new_solver_status?: SolverStatus;
  feasibility_changed?: boolean;
  cvar_delta?: number;
  allocation_delta_kg?: number;
  delivered_quantity_delta_kg?: number;
  risk_adjusted_nrv_delta?: number;
  reallocated_quantity_kg?: number;
  allocation_changes?: Record<string, number>;
  interpretation_notes?: string[];
}

export interface WhatIfSimulationResult {
  simulation_id: string;
  baseline_plan: OptimalSellingPlan;
  counterfactual_plan: OptimalSellingPlan;
  applied_overrides: Record<string, unknown>;
  comparison: CounterfactualDelta;
  provenance_status: DecisionProvenanceStatus;
  is_demo: boolean;
  created_at: string;
}

export interface SensitivityPoint {
  parameter_value: number;
  expected_total_nrv: number;
  effective_nrv_per_kg: number;
  cvar_95: number;
  total_allocated_kg: number;
  dominant_channel: string;
}

export interface SensitivitySweepResult {
  sweep_id: string;
  parameter_type: string;
  points: SensitivityPoint[];
  provenance_status: DecisionProvenanceStatus;
  is_demo: boolean;
}
