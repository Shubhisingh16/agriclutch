"""
AgriClutch Step 14: Decision Intelligence & Optimal Selling Plan Service.
Coordinates upstream data resolution, candidate filtering, SciPy LP optimization,
persistence of plan audits, counterfactual What-If simulation, and sensitivity sweeps.
SIH26132 — Strengthening Market Linkages and Price Discovery for Farmers.
"""

import logging
from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.decision import (
    OptimalSellingPlanModel,
    PlanAllocationModel,
)
from app.schemas.decision import (
    ConstraintItemResponse,
    ConstraintSummaryResponse,
    CounterfactualDeltaResponse,
    OptimalSellingPlanResponse,
    OptimizePlanRequest,
    PlanAllocationResponse,
    RiskMetricsResponse,
    SensitivityPointResponse,
    SensitivityRequest,
    SensitivitySweepResponse,
    WhatIfSimulationRequest,
    WhatIfSimulationResponse,
)
from ml.decision.optimizer import (
    DecisionCandidatePipeline,
    DecisionPlanAssembler,
    DecisionSolver,
    OptimalSellingPlan,
    WhatIfSimulatorEngine,
)

logger = logging.getLogger("agriclutch.services.decision")


class DecisionService:
    """
    Business logic layer for Decision Optimization and What-If Counterfactuals.
    Consumes verified upstream contracts and produces mathematical selling decisions.
    """

    @classmethod
    async def optimize_selling_plan(
        cls,
        req: OptimizePlanRequest,
        session: Optional[AsyncSession] = None,
    ) -> OptimalSellingPlanResponse:
        """
        Generates a mathematically optimal multi-destination selling allocation.
        """
        # 1. Fetch / build feasible candidates using upstream pipeline
        candidates = DecisionCandidatePipeline.build_demo_candidates(
            commodity_id=req.commodity_id,
            variety=req.variety,
            quality_grade=req.quality_grade,
            decision_horizon_days=req.decision_horizon_days,
            origin_lat=req.origin_latitude or 30.8350,
            origin_lon=req.origin_longitude or 76.9350,
        )

        if not candidates:
            raise HTTPException(
                status_code=400,
                detail=f"No feasible candidate channels available for commodity {req.commodity_id} within {req.decision_horizon_days}-day horizon.",
            )

        # 2. Solve the linear programming optimization problem
        solver_res = DecisionSolver.solve(
            candidates=candidates,
            total_supply_kg=req.total_supply_kg,
            risk_preference=req.risk_preference,
            liquidity_preference=req.liquidity_preference,
        )

        # 3. Assemble validated OptimalSellingPlan
        plan = DecisionPlanAssembler.assemble(
            candidates=candidates,
            solver_res=solver_res,
            commodity_id=req.commodity_id,
            total_supply_kg=req.total_supply_kg,
            variety=req.variety,
            quality_grade=req.quality_grade,
            decision_horizon_days=req.decision_horizon_days,
            risk_preference=req.risk_preference,
            liquidity_preference=req.liquidity_preference,
        )

        # 4. Persist to DB if session provided
        if session is not None:
            try:
                plan_orm = OptimalSellingPlanModel(
                    id=plan.plan_id,
                    input_snapshot_id=plan.input_snapshot_id,
                    commodity_id=plan.commodity_id,
                    variety=plan.variety,
                    quality_grade=plan.quality_grade,
                    total_supply_kg=plan.total_supply_kg,
                    decision_horizon_days=plan.decision_horizon_days,
                    risk_preference=plan.risk_preference.value,
                    liquidity_preference=plan.liquidity_preference.value,
                    total_allocated_kg=plan.total_allocated_kg,
                    total_unallocated_kg=plan.total_unallocated_kg,
                    total_effective_kg=plan.total_effective_kg,
                    expected_gross_revenue=plan.expected_gross_revenue,
                    total_friction_cost=plan.total_friction_cost,
                    expected_total_nrv=plan.expected_total_nrv,
                    risk_adjusted_nrv=plan.risk_adjusted_nrv,
                    solver_status=plan.solver_status.value,
                    validation_status=plan.validation_status.value,
                    solver_message=plan.solver_message,
                    solver_duration_ms=plan.solver_duration_ms,
                    solver_version=plan.solver_version,
                    configuration_hash=plan.configuration_hash,
                    executive_summary=plan.executive_summary,
                    structured_explanations=plan.structured_explanations,
                    risk_metrics_json=plan.risk_metrics.to_dict() if plan.risk_metrics else {},
                    constraint_summary_json=plan.constraint_summary.to_dict() if plan.constraint_summary else {},
                    provenance_status=plan.provenance.provenance_status.value,
                    is_demo=plan.is_demo,
                )
                session.add(plan_orm)

                for a in plan.allocations:
                    alloc_orm = PlanAllocationModel(
                        id=a.allocation_id,
                        plan_id=plan.plan_id,
                        destination_type=a.destination_type.value,
                        destination_id=a.destination_id,
                        destination_name=a.destination_name,
                        sale_day_offset=a.sale_day_offset,
                        sale_date=a.sale_date,
                        allocated_quantity_kg=a.allocated_quantity_kg,
                        effective_quantity_kg=a.effective_quantity_kg,
                        allocation_percentage=a.allocation_percentage,
                        expected_price_per_kg=a.expected_price_per_kg,
                        expected_nrv_per_kg=a.expected_nrv_per_kg,
                        gross_revenue=a.gross_revenue,
                        total_freight_cost=a.total_freight_cost,
                        total_storage_cost=a.total_storage_cost,
                        total_handling_cost=a.total_handling_cost,
                        total_market_fee=a.total_market_fee,
                        expected_total_nrv=a.expected_total_nrv,
                        quality_factor=a.quality_factor,
                        mass_retention_factor=a.mass_retention_factor,
                        pathway_id=a.pathway_id,
                        buyer_id=a.buyer_id,
                        market_id=a.market_id,
                        storage_facility_id=a.storage_facility_id,
                        explanation=a.explanation,
                    )
                    session.add(alloc_orm)
                await session.flush()
            except Exception as e:
                logger.warning("Database persistence of plan skipped or failed in session: %s", e)

        return cls._to_plan_response(plan)

    @classmethod
    async def simulate_what_if(
        cls,
        req: WhatIfSimulationRequest,
        session: Optional[AsyncSession] = None,
    ) -> WhatIfSimulationResponse:
        """
        Executes a counterfactual What-If simulation by re-optimizing with modified parameters.
        """
        candidates = DecisionCandidatePipeline.build_demo_candidates(
            commodity_id=req.commodity_id,
            decision_horizon_days=req.decision_horizon_days,
        )

        sim_res = WhatIfSimulatorEngine.run_simulation(
            baseline_candidates=candidates,
            total_supply_kg=req.total_supply_kg,
            commodity_id=req.commodity_id,
            decision_horizon_days=req.decision_horizon_days,
            baseline_risk=req.baseline_risk,
            baseline_liquidity=req.baseline_liquidity,
            cf_supply_kg=req.cf_supply_kg,
            cf_risk=req.cf_risk,
            cf_liquidity=req.cf_liquidity,
            transport_cost_multiplier=req.transport_cost_multiplier,
            storage_cost_multiplier=req.storage_cost_multiplier,
            buyer_demand_multiplier=req.buyer_demand_multiplier,
            price_shock_multiplier=req.price_shock_multiplier,
            additional_storage_days=req.additional_storage_days,
            parameter_label=req.scenario_label,
        )

        base_resp = cls._to_plan_response(sim_res.baseline_plan)
        cf_resp = cls._to_plan_response(sim_res.counterfactual_plan)

        comp = sim_res.comparison
        comp_resp = CounterfactualDeltaResponse(
            parameter_changed=comp.parameter_changed,
            baseline_value=str(comp.baseline_value),
            counterfactual_value=str(comp.counterfactual_value),
            baseline_nrv=comp.baseline_nrv,
            counterfactual_nrv=comp.counterfactual_nrv,
            nrv_delta=comp.nrv_delta,
            nrv_percentage_change=comp.nrv_percentage_change,
            baseline_allocated_kg=comp.baseline_allocated_kg,
            counterfactual_allocated_kg=comp.counterfactual_allocated_kg,
            allocation_shift_summary=comp.allocation_shift_summary,
            baseline_input_hash=comp.baseline_input_hash,
            counterfactual_input_hash=comp.counterfactual_input_hash,
            baseline_solver_status=comp.baseline_solver_status,
            new_solver_status=comp.new_solver_status,
            feasibility_changed=comp.feasibility_changed,
            cvar_delta=comp.cvar_delta,
            allocation_delta_kg=comp.allocation_delta_kg,
        )

        return WhatIfSimulationResponse(
            simulation_id=sim_res.simulation_id,
            baseline_plan=base_resp,
            counterfactual_plan=cf_resp,
            comparison=comp_resp,
            is_demo=True,
        )

    @classmethod
    async def evaluate_sensitivity_sweep(
        cls,
        req: SensitivityRequest,
        session: Optional[AsyncSession] = None,
    ) -> SensitivitySweepResponse:
        """
        Executes a multi-point parameter sensitivity sweep curve.
        """
        candidates = DecisionCandidatePipeline.build_demo_candidates(
            commodity_id=req.commodity_id,
        )

        sweep_res = WhatIfSimulatorEngine.run_sensitivity_sweep(
            candidates=candidates,
            total_supply_kg=req.total_supply_kg,
            parameter_type=req.parameter_type,
            sweep_range=req.sweep_multipliers,
            commodity_id=req.commodity_id,
            risk_preference=req.risk_preference,
            liquidity_preference=req.liquidity_preference,
        )

        pts: List[SensitivityPointResponse] = [
            SensitivityPointResponse(
                step_index=p.step_index,
                parameter_value=p.parameter_value,
                parameter_label=p.parameter_label,
                expected_total_nrv=p.expected_total_nrv,
                risk_adjusted_nrv=p.risk_adjusted_nrv,
                allocated_percentage=p.allocated_percentage,
                is_feasible=p.is_feasible,
                solver_status=p.solver_status,
            )
            for p in sweep_res.points
        ]

        return SensitivitySweepResponse(
            parameter_name=sweep_res.parameter_name,
            baseline_value=sweep_res.baseline_value,
            unit=sweep_res.unit,
            points=pts,
            interpretation=sweep_res.interpretation,
        )

    @classmethod
    async def get_plan_by_id(
        cls,
        plan_id: str,
        session: Optional[AsyncSession] = None,
    ) -> OptimalSellingPlanResponse:
        """Retrieves a previously stored plan or recomputes demo default."""
        if session is not None:
            stmt = select(OptimalSellingPlanModel).where(OptimalSellingPlanModel.id == plan_id)
            res = await session.execute(stmt)
            plan_orm = res.scalar_one_or_none()
            if plan_orm is not None:
                # Query child allocations
                alloc_stmt = select(PlanAllocationModel).where(PlanAllocationModel.plan_id == plan_id)
                alloc_res = await session.execute(alloc_stmt)
                allocs = alloc_res.scalars().all()

                alloc_resp_list: List[PlanAllocationResponse] = []
                for a in allocs:
                    alloc_resp_list.append(PlanAllocationResponse(
                        allocation_id=a.id,
                        candidate_id=f"cand_{a.destination_id}",
                        destination_type=a.destination_type,  # type: ignore[arg-type]
                        destination_id=a.destination_id,
                        destination_name=a.destination_name,
                        sale_day_offset=a.sale_day_offset,
                        sale_date=a.sale_date,
                        allocated_quantity_kg=a.allocated_quantity_kg,
                        effective_quantity_kg=a.effective_quantity_kg,
                        allocation_percentage=a.allocation_percentage,
                        expected_price_per_kg=a.expected_price_per_kg,
                        expected_nrv_per_kg=a.expected_nrv_per_kg,
                        gross_revenue=a.gross_revenue,
                        total_freight_cost=a.total_freight_cost,
                        total_storage_cost=a.total_storage_cost,
                        total_handling_cost=a.total_handling_cost,
                        total_market_fee=a.total_market_fee,
                        expected_total_nrv=a.expected_total_nrv,
                        nrv_p10_total=a.expected_total_nrv * 0.9,
                        nrv_p50_total=a.expected_total_nrv,
                        nrv_p90_total=a.expected_total_nrv * 1.1,
                        quality_factor=a.quality_factor,
                        mass_retention_factor=a.mass_retention_factor,
                        limiting_constraints=[],
                        explanation=a.explanation,
                    ))

                return OptimalSellingPlanResponse(
                    plan_id=plan_orm.id,
                    created_at=plan_orm.created_at.isoformat() + "Z",
                    commodity_id=plan_orm.commodity_id,
                    variety=plan_orm.variety,
                    quality_grade=plan_orm.quality_grade,
                    total_supply_kg=plan_orm.total_supply_kg,
                    decision_horizon_days=plan_orm.decision_horizon_days,
                    risk_preference=plan_orm.risk_preference,  # type: ignore[arg-type]
                    liquidity_preference=plan_orm.liquidity_preference,  # type: ignore[arg-type]
                    allocations=alloc_resp_list,
                    total_allocated_kg=plan_orm.total_allocated_kg,
                    total_unallocated_kg=plan_orm.total_unallocated_kg,
                    total_effective_kg=plan_orm.total_effective_kg,
                    expected_gross_revenue=plan_orm.expected_gross_revenue,
                    total_friction_cost=plan_orm.total_friction_cost,
                    expected_total_nrv=plan_orm.expected_total_nrv,
                    risk_adjusted_nrv=plan_orm.risk_adjusted_nrv,
                    solver_status=plan_orm.solver_status,  # type: ignore[arg-type]
                    validation_status=plan_orm.validation_status,  # type: ignore[arg-type]
                    solver_message=plan_orm.solver_message,
                    solver_duration_ms=plan_orm.solver_duration_ms,
                    solver_version=plan_orm.solver_version,
                    configuration_hash=plan_orm.configuration_hash,
                    executive_summary=plan_orm.executive_summary,
                    structured_explanations=plan_orm.structured_explanations,
                    is_demo=plan_orm.is_demo,
                    provenance={"source_name": "Database-OptimalSellingPlan", "is_demo": plan_orm.is_demo},
                )

        # Fallback to computing fresh standard demo plan
        default_req = OptimizePlanRequest(
            commodity_id="tomato",
            total_supply_kg=2500.0,
        )
        return await cls.optimize_selling_plan(default_req, session=session)

    @classmethod
    def _to_plan_response(cls, plan: OptimalSellingPlan) -> OptimalSellingPlanResponse:
        """Converts internal OptimalSellingPlan to Pydantic response contract."""
        alloc_list: List[PlanAllocationResponse] = []
        for a in plan.allocations:
            alloc_list.append(PlanAllocationResponse(
                allocation_id=a.allocation_id,
                candidate_id=a.candidate_id,
                destination_type=a.destination_type,
                destination_id=a.destination_id,
                destination_name=a.destination_name,
                sale_day_offset=a.sale_day_offset,
                sale_date=a.sale_date,
                allocated_quantity_kg=a.allocated_quantity_kg,
                effective_quantity_kg=a.effective_quantity_kg,
                allocation_percentage=a.allocation_percentage,
                expected_price_per_kg=a.expected_price_per_kg,
                expected_nrv_per_kg=a.expected_nrv_per_kg,
                gross_revenue=a.gross_revenue,
                total_freight_cost=a.total_freight_cost,
                total_storage_cost=a.total_storage_cost,
                total_handling_cost=a.total_handling_cost,
                total_market_fee=a.total_market_fee,
                expected_total_nrv=a.expected_total_nrv,
                nrv_p10_total=a.nrv_p10_total,
                nrv_p50_total=a.nrv_p50_total,
                nrv_p90_total=a.nrv_p90_total,
                quality_factor=a.quality_factor,
                mass_retention_factor=a.mass_retention_factor,
                limiting_constraints=a.limiting_constraints,
                explanation=a.explanation,
            ))

        risk_resp = None
        if plan.risk_metrics:
            rm = plan.risk_metrics
            risk_resp = RiskMetricsResponse(
                risk_preference=rm.risk_preference,
                risk_penalty_weight=rm.risk_penalty_weight,
                portfolio_downside_spread=rm.portfolio_downside_spread,
                configured_tail_stress_estimate=rm.configured_tail_stress_estimate,
                expected_total_nrv=rm.expected_total_nrv,
                risk_adjusted_nrv=rm.risk_adjusted_nrv,
                downside_spread_penalty=rm.downside_spread_penalty,
                confidence_level=rm.confidence_level,
                p10_total_nrv=rm.p10_total_nrv,
                p50_total_nrv=rm.p50_total_nrv,
                p90_total_nrv=rm.p90_total_nrv,
                tail_stress_multiplier=rm.tail_stress_multiplier,
                tail_stress_provenance=rm.tail_stress_provenance.value,
                provenance_status=rm.provenance_status.value,
                is_demo=rm.is_demo,
                # Backward compatibility aliases
                var_95=rm.var_95,
                cvar_95=rm.cvar_95,
                downside_cvar_penalty=rm.downside_cvar_penalty,
                tail_risk_multiplier=rm.tail_risk_multiplier,
                tail_risk_provenance=rm.tail_risk_provenance.value,
            )

        cs_resp = None
        if plan.constraint_summary:
            cs = plan.constraint_summary
            items_resp = [
                ConstraintItemResponse(
                    constraint_name=i.constraint_name,
                    status=i.status,
                    lhs_value=i.lhs_value,
                    rhs_bound=i.rhs_bound,
                    unit=i.unit,
                    slack=i.slack,
                    description=i.description,
                )
                for i in cs.items
            ]
            cs_resp = ConstraintSummaryResponse(
                supply_constraint_status=cs.supply_constraint_status,
                liquidity_constraint_status=cs.liquidity_constraint_status,
                demand_constraint_status=cs.demand_constraint_status,
                transport_constraint_status=cs.transport_constraint_status,
                storage_constraint_status=cs.storage_constraint_status,
                perishability_constraint_status=cs.perishability_constraint_status,
                items=items_resp,
                violated_constraints=cs.violated_constraints,
            )

        return OptimalSellingPlanResponse(
            plan_id=plan.plan_id,
            created_at=plan.created_at,
            commodity_id=plan.commodity_id,
            variety=plan.variety,
            quality_grade=plan.quality_grade,
            total_supply_kg=plan.total_supply_kg,
            decision_horizon_days=plan.decision_horizon_days,
            risk_preference=plan.risk_preference,
            liquidity_preference=plan.liquidity_preference,
            allocations=alloc_list,
            total_allocated_kg=plan.total_allocated_kg,
            total_unallocated_kg=plan.total_unallocated_kg,
            total_effective_kg=plan.total_effective_kg,
            expected_gross_revenue=plan.expected_gross_revenue,
            total_friction_cost=plan.total_friction_cost,
            expected_total_nrv=plan.expected_total_nrv,
            risk_adjusted_nrv=plan.risk_adjusted_nrv,
            risk_metrics=risk_resp,
            constraint_summary=cs_resp,
            solver_status=plan.solver_status,
            validation_status=plan.validation_status,
            solver_message=plan.solver_message,
            solver_duration_ms=plan.solver_duration_ms,
            solver_version=plan.solver_version,
            configuration_hash=plan.configuration_hash,
            executive_summary=plan.executive_summary,
            structured_explanations=plan.structured_explanations,
            is_demo=plan.is_demo,
            provenance=plan.provenance.to_dict(),
        )
