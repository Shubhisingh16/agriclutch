"""
AgriClutch Logistics Cost Engine.
Computes deterministic, itemized logistics and transit fee breakdowns.
Never silently replaces missing fees with zero and preserves full economic provenance.
SIH26132 — Strengthening Market Linkages and Price Discovery for Farmers.
"""


from ml.logistics.contracts import (
    CostUnitBasis,
    EconomicProvenance,
    EconomicStatus,
    LogisticsCostBreakdown,
    LogisticsCostItem,
    ProvenanceStatus,
    TransportModeSpec,
)


class LogisticsCostEngine:
    """
    Evaluates physical haulage, loading, unloading, and stage handling costs.
    Decomposes aggregate cost into verifiable additive line items.
    """

    @staticmethod
    def calculate_cost_breakdown(
        transport_mode: TransportModeSpec,
        quantity_kg: float,
        distance_km: float | None = None,
        loading_fee_per_quintal: float | None = None,
        unloading_fee_per_quintal: float | None = None,
        extra_handling_fee: float | None = None,
        is_demo: bool = True,
    ) -> LogisticsCostBreakdown:
        """
        Calculates itemized logistics cost breakdown:
            C_logistics = C_transport + C_loading + C_unloading + C_handling + C_other

        Raises ValueError if negative values are supplied.
        """
        if quantity_kg <= 0:
            raise ValueError(f"Quantity must be strictly positive: {quantity_kg}")
        if distance_km is not None and distance_km < 0:
            raise ValueError(f"Distance cannot be negative: {distance_km}")

        items: list[LogisticsCostItem] = []
        quantity_tonnes = quantity_kg / 1000.0
        quantity_quintals = quantity_kg / 100.0

        # 1. Base Dispatch Fee
        base_fee = transport_mode.base_dispatch_fee
        if base_fee < 0:
            raise ValueError(f"Base dispatch fee cannot be negative: {base_fee}")

        items.append(
            LogisticsCostItem(
                component_name="BASE_DISPATCH_FEE",
                amount=base_fee,
                currency="INR",
                unit_basis=CostUnitBasis.INR_FIXED,
                quantity_basis_kg=quantity_kg,
                provenance=transport_mode.provenance,
            )
        )

        # 2. Distance-Based Haulage
        transport_variable_cost = 0.0
        if distance_km is None:
            items.append(
                LogisticsCostItem(
                    component_name="HAULAGE_DISTANCE_FEE",
                    amount=0.0,
                    currency="INR",
                    unit_basis=CostUnitBasis.INR_PER_KM,
                    quantity_basis_kg=quantity_kg,
                    provenance=EconomicProvenance(
                        source_name="TRANSPORT_MODE_RATE_SPEC",
                        status=ProvenanceStatus.UNAVAILABLE,
                        is_demo=False,
                        justification="Distance is unknown; haulage freight fee cannot be calculated.",
                    ),
                )
            )
        elif distance_km > 0:
            if transport_mode.cost_per_km_tonne is not None:
                rate = transport_mode.cost_per_km_tonne
                transport_variable_cost = rate * distance_km * quantity_tonnes
                items.append(
                    LogisticsCostItem(
                        component_name="FREIGHT_HAULAGE_PER_KM_TONNE",
                        amount=transport_variable_cost,
                        currency="INR",
                        unit_basis=CostUnitBasis.INR_PER_KM_TONNE,
                        quantity_basis_kg=quantity_kg,
                        distance_basis_km=distance_km,
                        provenance=EconomicProvenance(
                            source_name="TRANSPORT_MODE_RATE_SPEC",
                            status=transport_mode.provenance.status,
                            is_demo=transport_mode.provenance.is_demo,
                            justification=f"Rate of {rate} INR/km/tonne applied across {distance_km:.1f} km and {quantity_tonnes:.2f} MT.",
                        ),
                    )
                )
            elif transport_mode.cost_per_km is not None:
                rate = transport_mode.cost_per_km
                transport_variable_cost = rate * distance_km
                items.append(
                    LogisticsCostItem(
                        component_name="FREIGHT_HAULAGE_PER_KM",
                        amount=transport_variable_cost,
                        currency="INR",
                        unit_basis=CostUnitBasis.INR_PER_KM,
                        quantity_basis_kg=quantity_kg,
                        distance_basis_km=distance_km,
                        provenance=EconomicProvenance(
                            source_name="TRANSPORT_MODE_RATE_SPEC",
                            status=transport_mode.provenance.status,
                            is_demo=transport_mode.provenance.is_demo,
                            justification=f"Vehicle rate of {rate} INR/km applied across {distance_km:.1f} km.",
                        ),
                    )
                )

        total_transport_cost = base_fee + transport_variable_cost

        # 3. Loading Cost
        total_loading_cost = 0.0
        if loading_fee_per_quintal is not None:
            if loading_fee_per_quintal < 0:
                raise ValueError(f"Loading fee cannot be negative: {loading_fee_per_quintal}")
            total_loading_cost = loading_fee_per_quintal * quantity_quintals
            items.append(
                LogisticsCostItem(
                    component_name="MANDI_OR_FARMGATE_LOADING",
                    amount=total_loading_cost,
                    currency="INR",
                    unit_basis=CostUnitBasis.INR_PER_QUINTAL,
                    quantity_basis_kg=quantity_kg,
                    provenance=EconomicProvenance(
                        source_name="HANDLING_RATE_SCHEDULE",
                        status=ProvenanceStatus.DEMO if is_demo else ProvenanceStatus.CONFIGURED,
                        is_demo=is_demo,
                        justification=f"Loading labor charge of {loading_fee_per_quintal} INR/quintal across {quantity_quintals:.2f} qtl.",
                    ),
                )
            )

        # 4. Unloading Cost
        total_unloading_cost = 0.0
        if unloading_fee_per_quintal is not None:
            if unloading_fee_per_quintal < 0:
                raise ValueError(f"Unloading fee cannot be negative: {unloading_fee_per_quintal}")
            total_unloading_cost = unloading_fee_per_quintal * quantity_quintals
            items.append(
                LogisticsCostItem(
                    component_name="DESTINATION_UNLOADING",
                    amount=total_unloading_cost,
                    currency="INR",
                    unit_basis=CostUnitBasis.INR_PER_QUINTAL,
                    quantity_basis_kg=quantity_kg,
                    provenance=EconomicProvenance(
                        source_name="HANDLING_RATE_SCHEDULE",
                        status=ProvenanceStatus.DEMO if is_demo else ProvenanceStatus.CONFIGURED,
                        is_demo=is_demo,
                        justification=f"Unloading charge of {unloading_fee_per_quintal} INR/quintal across {quantity_quintals:.2f} qtl.",
                    ),
                )
            )

        # 5. Extra Handling / Sorting Fees
        total_handling_cost = 0.0
        if extra_handling_fee is not None:
            if extra_handling_fee < 0:
                raise ValueError(f"Extra handling fee cannot be negative: {extra_handling_fee}")
            total_handling_cost = extra_handling_fee
            items.append(
                LogisticsCostItem(
                    component_name="INTERMEDIATE_HANDLING_STAGE",
                    amount=total_handling_cost,
                    currency="INR",
                    unit_basis=CostUnitBasis.INR_FIXED,
                    quantity_basis_kg=quantity_kg,
                    provenance=EconomicProvenance(
                        source_name="HANDLING_STAGE_SPEC",
                        status=ProvenanceStatus.DEMO if is_demo else ProvenanceStatus.CONFIGURED,
                        is_demo=is_demo,
                        justification="Fixed stage handling fee for physical sorting, assay, or transfer.",
                    ),
                )
            )

        total_cost = (
            total_transport_cost
            + total_loading_cost
            + total_unloading_cost
            + total_handling_cost
        )

        # Determine aggregate economic status
        any_unavailable = any(it.provenance.status == ProvenanceStatus.UNAVAILABLE for it in items)
        all_empirical = all(it.provenance.status == ProvenanceStatus.EMPIRICAL for it in items)
        all_demo = all(it.provenance.is_demo for it in items)

        if any_unavailable or distance_km is None:
            econ_status = EconomicStatus.INCOMPLETE
        elif all_empirical:
            econ_status = EconomicStatus.COMPLETE_EMPIRICAL
        elif all_demo:
            econ_status = EconomicStatus.DEMO_ASSUMPTION
        else:
            econ_status = EconomicStatus.COMPLETE_MIXED_PROVENANCE

        prov = EconomicProvenance(
            source_name="LOGISTICS_COST_ENGINE",
            status=ProvenanceStatus.DEMO if all_demo else ProvenanceStatus.CONFIGURED,
            is_demo=all_demo,
            justification=f"Decomposed logistics costing composed of {len(items)} itemized fee components (economic_status={econ_status.value}).",
        )

        return LogisticsCostBreakdown(
            total_cost=total_cost,
            transport_cost=total_transport_cost,
            loading_cost=total_loading_cost,
            unloading_cost=total_unloading_cost,
            handling_cost=total_handling_cost,
            other_cost=0.0,
            items=items,
            economic_status=econ_status,
            provenance=prov,
        )
