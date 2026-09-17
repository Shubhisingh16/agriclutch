"""
AgriClutch Scenario Engine.
Coordinates multi-market comparisons and multi-horizon time scenarios.
Strict clean-room implementation: Zero recommendation leakage, zero market ranking.
SIH26132 — Market Linkages and Price Discovery for Farmers.
"""

from typing import Any, Dict, List, Optional

from ml.decision.contracts import QuantitySpec, ScenarioResult
from ml.decision.nrv import NRVCalculator


class ScenarioEngine:
    """
    Evaluates and compares candidate economic scenarios across markets and storage horizons.
    Exposes objective economic figures without selecting or recommending winners.
    """

    def __init__(self, nrv_calculator: Optional[NRVCalculator] = None) -> None:
        self.calculator = nrv_calculator or NRVCalculator()

    def compare_markets(
        self,
        commodity_id: str,
        quantity: QuantitySpec,
        scenario_date: str,
        markets_data: List[Dict[str, Any]],
        storage_days: int = 0,
        storage_type: str = "ambient",
        quality_grade: str = "FAQ",
    ) -> List[ScenarioResult]:
        """
        Calculates Net Realizable Value across candidate regional mandis.
        Does NOT score, rank, or select a 'best' market.
        """
        results: List[ScenarioResult] = []

        for m_info in markets_data:
            m_id = m_info["market_id"]
            m_name = m_info.get("market_name", m_id)
            dist_km = m_info.get("distance_km", 10.0)
            apmc_rate = m_info.get("apmc_fee_fraction", 0.015)
            q_prices = m_info["forecast_price_quantiles"]
            freight_rate = m_info.get("freight_rate_per_km_tonne", 4.50)

            calc_res = self.calculator.calculate(
                commodity_id=commodity_id,
                market_id=m_id,
                scenario_date=scenario_date,
                quantity=quantity,
                forecast_price_quantiles=q_prices,
                distance_km=dist_km,
                storage_days=storage_days,
                storage_type=storage_type,
                quality_grade=quality_grade,
                freight_rate_per_km_tonne=freight_rate,
                apmc_fee_fraction=apmc_rate,
            )

            cb = calc_res.cost_breakdown
            prov_status = calc_res.provenance_items[0].status.value if calc_res.provenance_items else "DEMO"

            results.append(
                ScenarioResult(
                    scenario_id=f"mkt_{m_id}_d{storage_days}",
                    market_id=m_id,
                    market_name=m_name,
                    scenario_date=scenario_date,
                    storage_days=storage_days,
                    storage_type=storage_type,
                    distance_km=dist_km,
                    effective_quantity_kg=calc_res.loss.effective_quantity_kg,
                    forecast_modal_price=calc_res.forecast_price_quantiles["p50"],
                    gross_revenue=calc_res.gross_revenue_quantiles["p50"],
                    transport_cost=cb.transport_cost.amount,
                    storage_cost=cb.storage_cost.amount,
                    handling_cost=cb.handling_cost.amount,
                    market_charges=cb.market_charges.amount,
                    other_costs=cb.other_costs.amount,
                    spoilage_loss_cost=cb.loss_cost.amount,
                    total_cost=calc_res.total_cost,
                    nrv_p10=calc_res.nrv_quantiles.p10,
                    nrv_p50=calc_res.nrv_quantiles.p50,
                    nrv_p90=calc_res.nrv_quantiles.p90,
                    nrv_per_kg_p50=calc_res.nrv_per_kg_quantiles.p50,
                    break_even_price=calc_res.break_even.break_even_price,
                    provenance_status=prov_status,
                )
            )

        return results

    def compare_time_horizons(
        self,
        commodity_id: str,
        market_id: str,
        market_name: str,
        distance_km: float,
        quantity: QuantitySpec,
        horizon_forecasts: Dict[int, Dict[str, Any]],  # map of day_offset -> {date, quantiles}
        horizons: Optional[List[int]] = None,
        storage_type: str = "ambient",
        quality_grade: str = "FAQ",
        apmc_fee_fraction: float = 0.015,
    ) -> List[ScenarioResult]:
        """
        Evaluates holding scenarios across future dates (e.g. t+0, t+3, t+7, t+14, t+28).
        Reveals perishability degradation and storage rent accumulation without selecting a horizon.
        """
        target_horizons = horizons or [0, 3, 7, 14, 28]
        results: List[ScenarioResult] = []

        for h_days in target_horizons:
            h_data = horizon_forecasts.get(h_days)
            if not h_data:
                continue

            s_date = h_data["date"]
            q_prices = h_data["quantiles"]

            calc_res = self.calculator.calculate(
                commodity_id=commodity_id,
                market_id=market_id,
                scenario_date=s_date,
                quantity=quantity,
                forecast_price_quantiles=q_prices,
                distance_km=distance_km,
                storage_days=h_days,
                storage_type=storage_type,
                quality_grade=quality_grade,
                apmc_fee_fraction=apmc_fee_fraction,
            )

            cb = calc_res.cost_breakdown
            prov_status = calc_res.provenance_items[0].status.value if calc_res.provenance_items else "DEMO"

            results.append(
                ScenarioResult(
                    scenario_id=f"time_{market_id}_h{h_days}",
                    market_id=market_id,
                    market_name=market_name,
                    scenario_date=s_date,
                    storage_days=h_days,
                    storage_type=storage_type,
                    distance_km=distance_km,
                    effective_quantity_kg=calc_res.loss.effective_quantity_kg,
                    forecast_modal_price=calc_res.forecast_price_quantiles["p50"],
                    gross_revenue=calc_res.gross_revenue_quantiles["p50"],
                    transport_cost=cb.transport_cost.amount,
                    storage_cost=cb.storage_cost.amount,
                    handling_cost=cb.handling_cost.amount,
                    market_charges=cb.market_charges.amount,
                    other_costs=cb.other_costs.amount,
                    spoilage_loss_cost=cb.loss_cost.amount,
                    total_cost=calc_res.total_cost,
                    nrv_p10=calc_res.nrv_quantiles.p10,
                    nrv_p50=calc_res.nrv_quantiles.p50,
                    nrv_p90=calc_res.nrv_quantiles.p90,
                    nrv_per_kg_p50=calc_res.nrv_per_kg_quantiles.p50,
                    break_even_price=calc_res.break_even.break_even_price,
                    provenance_status=prov_status,
                )
            )

        return results
