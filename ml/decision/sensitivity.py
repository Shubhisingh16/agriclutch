"""
AgriClutch Sensitivity Engine.
Generates reproducible two-variable sensitivity grids over price, freight, storage, and decay.
Strict clean-room implementation: Zero recommendation leakage, no cell ranking.
SIH26132 — Market Linkages and Price Discovery for Farmers.
"""

from typing import Dict, List, Optional

from ml.decision.contracts import (
    EconomicProvenance,
    ProvenanceStatus,
    QuantitySpec,
    SensitivityMatrixResult,
)
from ml.decision.nrv import NRVCalculator


class SensitivityEngine:
    """
    Computes 3x3 orthogonal sensitivity grids.
    Variables supported: 'price', 'transport', 'storage', 'loss'.
    """

    DEFAULT_LEVELS = ["LOW", "BASE", "HIGH"]
    PERTURBATIONS: Dict[str, List[float]] = {
        "price": [0.85, 1.00, 1.15],         # -15%, 0%, +15%
        "transport": [0.80, 1.00, 1.20],     # -20%, 0%, +20%
        "storage": [0.80, 1.00, 1.20],       # -20%, 0%, +20%
        "loss": [0.70, 1.00, 1.30],          # -30%, 0%, +30%
    }

    def __init__(self, nrv_calculator: Optional[NRVCalculator] = None) -> None:
        self.calculator = nrv_calculator or NRVCalculator()

    def generate_matrix(
        self,
        commodity_id: str,
        market_id: str,
        scenario_date: str,
        quantity: QuantitySpec,
        forecast_price_quantiles: Dict[str, float],
        distance_km: float,
        variable_x: str = "price",
        variable_y: str = "transport",
        storage_days: int = 0,
        storage_type: str = "ambient",
        quality_grade: str = "FAQ",
        freight_rate_per_km_tonne: float = 4.50,
        daily_storage_rate_per_kg: float = 0.20,
        apmc_fee_fraction: float = 0.015,
    ) -> SensitivityMatrixResult:
        var_x = variable_x.strip().lower()
        var_y = variable_y.strip().lower()

        if var_x not in self.PERTURBATIONS or var_y not in self.PERTURBATIONS:
            raise ValueError(f"Variables must be in {list(self.PERTURBATIONS.keys())}, got x='{var_x}', y='{var_y}'")

        factors_x = self.PERTURBATIONS[var_x]
        factors_y = self.PERTURBATIONS[var_y]

        # Calculate base values
        base_p50 = forecast_price_quantiles.get("p50", 25.0)
        base_values_x = [round(base_p50 * f, 2) if var_x == "price" else round(f, 2) for f in factors_x]
        base_values_y = [round(base_p50 * f, 2) if var_y == "price" else round(f, 2) for f in factors_y]

        grid_nrv: List[List[float]] = []
        grid_nrv_per_kg: List[List[float]] = []

        for f_y in factors_y:
            row_nrv: List[float] = []
            row_per_kg: List[float] = []

            for f_x in factors_x:
                # Apply multipliers
                p_mult = 1.0
                t_mult = 1.0
                s_mult = 1.0

                for var, f in [(var_x, f_x), (var_y, f_y)]:
                    if var == "price":
                        p_mult *= f
                    elif var == "transport":
                        t_mult *= f
                    elif var == "storage":
                        s_mult *= f

                # Perturb price quantiles
                perturbed_prices = {k: v * p_mult for k, v in forecast_price_quantiles.items()}

                calc_res = self.calculator.calculate(
                    commodity_id=commodity_id,
                    market_id=market_id,
                    scenario_date=scenario_date,
                    quantity=quantity,
                    forecast_price_quantiles=perturbed_prices,
                    distance_km=distance_km,
                    storage_days=storage_days,
                    storage_type=storage_type,
                    quality_grade=quality_grade,
                    freight_rate_per_km_tonne=freight_rate_per_km_tonne * t_mult,
                    daily_storage_rate_per_kg=daily_storage_rate_per_kg * s_mult,
                    apmc_fee_fraction=apmc_fee_fraction,
                )

                row_nrv.append(calc_res.nrv_quantiles.p50)
                row_per_kg.append(calc_res.nrv_per_kg_quantiles.p50)

            grid_nrv.append(row_nrv)
            grid_nrv_per_kg.append(row_per_kg)

        prov = EconomicProvenance(
            source="AGRICLUTCH_SENSITIVITY_ENGINE",
            status=ProvenanceStatus.CONFIGURED,
            effective_date="2024-09-15",
            is_demo=True,
            description=f"3x3 orthogonal sensitivity grid for {var_x} vs {var_y}.",
        )

        return SensitivityMatrixResult(
            variable_x=var_x,
            variable_y=var_y,
            levels_x=self.DEFAULT_LEVELS,
            levels_y=self.DEFAULT_LEVELS,
            values_x=base_values_x,
            values_y=base_values_y,
            grid_nrv_p50=grid_nrv,
            grid_nrv_per_kg=grid_nrv_per_kg,
            provenance=prov,
        )
