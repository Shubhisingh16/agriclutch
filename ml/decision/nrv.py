"""
AgriClutch Net Realizable Value (NRV) Calculator.
Translates price forecast distributions and itemized operational costs into
distribution-aware farmer net economic realization estimates.
SIH26132 — Market Linkages and Price Discovery for Farmers.
"""

from typing import Dict, List, Optional

from ml.decision.contracts import (
    BreakEvenResult,
    CostBreakdown,
    CostItem,
    EconomicProvenance,
    NRVCalculationResult,
    NRVDistribution,
    ProvenanceStatus,
    QualitySpec,
    QuantitySpec,
)
from ml.decision.costs import (
    HandlingCostModel,
    MarketChargesModel,
    OtherCostsModel,
    SpoilageDisposalCostModel,
    StorageCostModel,
    TransportCostModel,
)
from ml.decision.loss import BaseLossModel, DocumentedLossModel
from ml.decision.risk import RiskModel


class NRVCalculator:
    """
    Mathematical solver for Net Realizable Value (NRV).
    Zero recommendation logic. Pure economic realization modeling.
    """

    GRADE_FACTORS: Dict[str, float] = {
        "grade_a": 1.08,
        "faq": 1.00,
        "grade_b": 0.85,
    }

    def __init__(self, loss_model: Optional[BaseLossModel] = None) -> None:
        self.loss_model = loss_model or DocumentedLossModel()

    def calculate(
        self,
        commodity_id: str,
        market_id: str,
        scenario_date: str,
        quantity: QuantitySpec,
        forecast_price_quantiles: Dict[str, float],
        distance_km: float,
        storage_days: int = 0,
        storage_type: str = "ambient",
        quality_grade: str = "FAQ",
        freight_rate_per_km_tonne: float = 4.50,
        base_dispatch_fee: float = 250.0,
        daily_storage_rate_per_kg: float = 0.20,
        loading_rate_per_kg: float = 0.30,
        unloading_rate_per_kg: float = 0.30,
        apmc_fee_fraction: float = 0.015,
        other_rate_per_kg: float = 0.40,
        culling_rate_per_kg: float = 0.10,
        scenario_type: str = "EXPECTED",
        provenance_map: Optional[Dict[str, EconomicProvenance]] = None,
    ) -> NRVCalculationResult:
        """
        Executes complete Net Realizable Value calculation.
        """
        prov_map = provenance_map or {}
        q_kg = quantity.normalized_quantity_kg

        # 1. Physical Spoilage and Loss Estimation
        loss_estimate = self.loss_model.estimate_loss(
            crop=commodity_id,
            storage_type=storage_type,
            storage_days=storage_days,
            initial_quantity_kg=q_kg,
        )
        effective_qty_kg = loss_estimate.effective_quantity_kg
        lost_qty_kg = loss_estimate.loss_quantity_kg

        # 2. Quality Factor and Downgrade Resolution
        norm_grade = quality_grade.strip().lower()
        base_grade_factor = self.GRADE_FACTORS.get(norm_grade, 1.00)
        downgrade_penalty = 0.0
        if isinstance(self.loss_model, DocumentedLossModel):
            downgrade_penalty = self.loss_model.check_downgrade(
                crop=commodity_id,
                storage_type=storage_type,
                storage_days=storage_days,
            )

        quality_factor = round(base_grade_factor * (1.0 - downgrade_penalty), 4)
        quality_prov = prov_map.get(
            "quality",
            EconomicProvenance(
                source="AGMARK_GRADE_SPECIFICATIONS",
                status=ProvenanceStatus.DEMO,
                effective_date="2024-09-15",
                is_demo=True,
                description=f"Grade factor {base_grade_factor:.2f} with downgrade penalty {downgrade_penalty:.2f}.",
            ),
        )
        quality_spec = QualitySpec(
            grade=quality_grade,
            quality_factor=quality_factor,
            downgrade_penalty=downgrade_penalty,
            provenance=quality_prov,
        )

        # 3. Forecast Quantile Normalization
        q_keys = ["p10", "p20", "p50", "p80", "p90"]
        raw_prices: Dict[str, float] = {}
        for k in q_keys:
            if k in forecast_price_quantiles:
                raw_prices[k] = forecast_price_quantiles[k]
            elif k.upper() in forecast_price_quantiles:
                raw_prices[k] = forecast_price_quantiles[k.upper()]
            else:
                raise ValueError(f"Missing required forecast quantile '{k}'.")

        # 4. Scenario Multipliers
        multipliers = RiskModel.get_scenario_cost_multipliers(scenario_type)
        t_mult = multipliers["transport_multiplier"]
        s_mult = multipliers["storage_multiplier"]
        h_mult = multipliers["handling_multiplier"]

        # 5. Itemized Cost Calculation
        t_item = TransportCostModel.calculate(
            distance_km=distance_km,
            quantity_kg=q_kg,
            rate_per_km_tonne=freight_rate_per_km_tonne * t_mult,
            base_dispatch_fee=base_dispatch_fee,
            provenance=prov_map.get("transport"),
        )
        s_item = StorageCostModel.calculate(
            storage_type=storage_type,
            storage_days=storage_days,
            quantity_kg=q_kg,
            daily_rate_per_kg=daily_storage_rate_per_kg * s_mult,
            provenance=prov_map.get("storage"),
        )
        h_item = HandlingCostModel.calculate(
            quantity_kg=q_kg,
            loading_rate_per_kg=loading_rate_per_kg * h_mult,
            unloading_rate_per_kg=unloading_rate_per_kg * h_mult,
            provenance=prov_map.get("handling"),
        )
        o_item = OtherCostsModel.calculate(
            quantity_kg=q_kg,
            rate_per_kg=other_rate_per_kg,
            provenance=prov_map.get("other"),
        )
        l_item = SpoilageDisposalCostModel.calculate(
            lost_quantity_kg=lost_qty_kg,
            disposal_rate_per_kg=culling_rate_per_kg,
            provenance=prov_map.get("loss"),
        )
        r_spec = RiskModel.get_default_risk_spec()
        r_item = CostItem(
            name="Operational Risk Penalty",
            category="risk",
            amount=r_spec.operational_risk_cost,
            unit="INR",
            provenance=r_spec.provenance,
            rate_basis=r_spec.risk_status,
            is_variable=False,
        )

        # 6. Quantile Gross Revenue & Quantile NRV
        gross_rev: Dict[str, float] = {}
        nrv_vals: Dict[str, float] = {}
        nrv_per_kg_vals: Dict[str, float] = {}

        # Non-market fixed cost components (independent of price quantile)
        fixed_deductions = (
            t_item.amount
            + s_item.amount
            + h_item.amount
            + o_item.amount
            + l_item.amount
            + r_item.amount
        )

        for k in q_keys:
            adj_p = raw_prices[k] * quality_factor
            rev_q = round(effective_qty_kg * adj_p, 2)
            gross_rev[k] = rev_q

            # Statutory APMC Market Fee is variable with gross realization
            mkt_fee_q = round(rev_q * apmc_fee_fraction, 2)
            tot_cost_q = round(fixed_deductions + mkt_fee_q, 2)
            nrv_q = round(rev_q - tot_cost_q, 2)
            nrv_vals[k] = nrv_q
            nrv_per_kg_vals[k] = round(nrv_q / q_kg, 2)

        # Benchmark P50 market charge item for baseline breakdown
        m_item = MarketChargesModel.calculate(
            gross_revenue=gross_rev["p50"],
            fee_fraction=apmc_fee_fraction,
            market_id=market_id,
            provenance=prov_map.get("market"),
        )

        cost_breakdown = CostBreakdown(
            transport_cost=t_item,
            storage_cost=s_item,
            handling_cost=h_item,
            market_charges=m_item,
            other_costs=o_item,
            loss_cost=l_item,
            risk_cost=r_item,
        )

        nrv_dist = NRVDistribution(
            p10=nrv_vals["p10"],
            p20=nrv_vals["p20"],
            p50=nrv_vals["p50"],
            p80=nrv_vals["p80"],
            p90=nrv_vals["p90"],
        )

        nrv_per_kg_dist = NRVDistribution(
            p10=nrv_per_kg_vals["p10"],
            p20=nrv_per_kg_vals["p20"],
            p50=nrv_per_kg_vals["p50"],
            p80=nrv_per_kg_vals["p80"],
            p90=nrv_per_kg_vals["p90"],
        )

        # 7. Break-Even Price Derivation
        # P_BE = C_non_market / (Q_eff * QualityFactor * (1 - mu))
        be_denom = effective_qty_kg * quality_factor * (1.0 - apmc_fee_fraction)
        if be_denom > 0 and fixed_deductions >= 0:
            be_price = round(fixed_deductions / be_denom, 2)
            be_result = BreakEvenResult(
                break_even_price=be_price,
                price_unit="INR_PER_KG",
                is_available=True,
                detail=f"Minimum quoted price required to cover total operational deductions of ₹{fixed_deductions:.2f}.",
            )
        else:
            be_result = BreakEvenResult(
                break_even_price=None,
                price_unit="INR_PER_KG",
                is_available=False,
                detail="Break-even price unavailable: effective usable volume is zero.",
            )

        provenance_list: List[EconomicProvenance] = [
            t_item.provenance,
            s_item.provenance,
            h_item.provenance,
            m_item.provenance,
            o_item.provenance,
            l_item.provenance,
            quality_prov,
        ]

        return NRVCalculationResult(
            commodity_id=commodity_id,
            market_id=market_id,
            scenario_date=scenario_date,
            storage_days=storage_days,
            storage_type=storage_type,
            quantity=quantity,
            quality=quality_spec,
            loss=loss_estimate,
            forecast_price_quantiles=raw_prices,
            gross_revenue_quantiles=gross_rev,
            cost_breakdown=cost_breakdown,
            total_cost=cost_breakdown.total_cost,
            nrv_quantiles=nrv_dist,
            nrv_per_kg_quantiles=nrv_per_kg_dist,
            break_even=be_result,
            scenario_type=scenario_type,
            provenance_items=provenance_list,
            status="VALID",
        )
