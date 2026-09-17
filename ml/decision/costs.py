"""
AgriClutch Cost Models Subsystem.
Modular, auditable calculation of transport, storage, handling, market, and other costs.
SIH26132 — Market Linkages and Price Discovery for Farmers.
"""

from typing import Optional

from ml.decision.contracts import CostItem, EconomicProvenance, ProvenanceStatus


class TransportCostModel:
    """Calculates road freight logistics costs with explicit provenance."""

    @staticmethod
    def calculate(
        distance_km: float,
        quantity_kg: float,
        rate_per_km_tonne: float,
        base_dispatch_fee: float = 0.0,
        provenance: Optional[EconomicProvenance] = None,
    ) -> CostItem:
        if distance_km < 0:
            raise ValueError(f"Distance cannot be negative, received: {distance_km}")
        if quantity_kg <= 0:
            raise ValueError(f"Quantity must be positive, received: {quantity_kg}")
        if rate_per_km_tonne < 0:
            raise ValueError(f"Freight rate cannot be negative, received: {rate_per_km_tonne}")
        if base_dispatch_fee < 0:
            raise ValueError(f"Base dispatch fee cannot be negative, received: {base_dispatch_fee}")

        tonnage = quantity_kg / 1000.0
        distance_cost = distance_km * rate_per_km_tonne * tonnage
        total_transport = round(base_dispatch_fee + distance_cost, 2)

        prov = provenance or EconomicProvenance(
            source="REGIONAL_ROAD_LOGISTICS_BENCHMARK",
            status=ProvenanceStatus.DEMO,
            effective_date="2024-09-15",
            is_demo=True,
            description=f"Freight computed for {distance_km:.1f} km at ₹{rate_per_km_tonne:.2f}/km/tonne + ₹{base_dispatch_fee:.2f} base fee.",
        )

        return CostItem(
            name="Transport & Freight",
            category="transport",
            amount=total_transport,
            unit="INR",
            provenance=prov,
            rate_basis=f"₹{rate_per_km_tonne:.2f}/km/tonne (Tonnage: {tonnage:.3f} MT, Dist: {distance_km:.1f} km)",
            is_variable=False,
        )


class StorageCostModel:
    """Calculates holding storage tariffs by duration and storage infrastructure type."""

    @staticmethod
    def calculate(
        storage_type: str,
        storage_days: int,
        quantity_kg: float,
        daily_rate_per_kg: float,
        provenance: Optional[EconomicProvenance] = None,
    ) -> CostItem:
        if storage_days < 0:
            raise ValueError(f"Storage days cannot be negative, received: {storage_days}")
        if quantity_kg <= 0:
            raise ValueError(f"Quantity must be positive, received: {quantity_kg}")
        if daily_rate_per_kg < 0:
            raise ValueError(f"Storage rate cannot be negative, received: {daily_rate_per_kg}")

        norm_type = storage_type.strip().lower()
        effective_rate = daily_rate_per_kg if norm_type != "ambient" else 0.0
        total_storage = round(quantity_kg * storage_days * effective_rate, 2)

        prov = provenance or EconomicProvenance(
            source="WDRA_STORAGE_TARIFF_BENCHMARK",
            status=ProvenanceStatus.DEMO,
            effective_date="2024-09-15",
            is_demo=True,
            description=f"Storage in {norm_type} for {storage_days} days at ₹{effective_rate:.3f}/kg/day.",
        )

        return CostItem(
            name=f"Storage Rental ({norm_type.replace('_', ' ').title()})",
            category="storage",
            amount=total_storage,
            unit="INR",
            provenance=prov,
            rate_basis=f"₹{effective_rate:.3f}/kg/day ({storage_days} days)",
            is_variable=False,
        )


class HandlingCostModel:
    """Calculates farm-gate vehicle loading and APMC mandi yard unloading porterage."""

    @staticmethod
    def calculate(
        quantity_kg: float,
        loading_rate_per_kg: float = 0.30,
        unloading_rate_per_kg: float = 0.30,
        provenance: Optional[EconomicProvenance] = None,
    ) -> CostItem:
        if quantity_kg <= 0:
            raise ValueError(f"Quantity must be positive, received: {quantity_kg}")
        if loading_rate_per_kg < 0 or unloading_rate_per_kg < 0:
            raise ValueError("Handling rates cannot be negative")

        total_handling_rate = loading_rate_per_kg + unloading_rate_per_kg
        total_handling = round(quantity_kg * total_handling_rate, 2)

        prov = provenance or EconomicProvenance(
            source="APMC_MANDI_PORTERAGE_UNION_BENCHMARK",
            status=ProvenanceStatus.DEMO,
            effective_date="2024-09-15",
            is_demo=True,
            description=f"Loading (₹{loading_rate_per_kg:.2f}/kg) + Unloading (₹{unloading_rate_per_kg:.2f}/kg).",
        )

        return CostItem(
            name="Physical Handling & Porterage",
            category="handling",
            amount=total_handling,
            unit="INR",
            provenance=prov,
            rate_basis=f"₹{total_handling_rate:.2f}/kg (Loading ₹{loading_rate_per_kg:.2f} + Unloading ₹{unloading_rate_per_kg:.2f})",
            is_variable=False,
        )


class MarketChargesModel:
    """Calculates statutory APMC Mandi Cess and Market Development Fees."""

    @staticmethod
    def calculate(
        gross_revenue: float,
        fee_fraction: float,
        market_id: str,
        provenance: Optional[EconomicProvenance] = None,
    ) -> CostItem:
        if gross_revenue < 0:
            raise ValueError(f"Gross revenue cannot be negative, received: {gross_revenue}")
        if fee_fraction < 0 or fee_fraction > 0.10:
            raise ValueError(f"Market fee fraction must be between 0.0 and 0.10, received: {fee_fraction}")

        total_fee = round(gross_revenue * fee_fraction, 2)

        prov = provenance or EconomicProvenance(
            source=f"APMC_STATUTORY_REGULATION_{market_id.upper()}",
            status=ProvenanceStatus.DEMO,
            effective_date="2024-09-15",
            is_demo=True,
            description=f"Statutory APMC fee of {fee_fraction * 100:.2f}% applied to gross realized revenue.",
        )

        return CostItem(
            name="APMC Mandi Fee & Cess",
            category="market",
            amount=total_fee,
            unit="INR",
            provenance=prov,
            rate_basis=f"{fee_fraction * 100:.2f}% of gross sales",
            is_variable=True,
        )


class OtherCostsModel:
    """Calculates weighbridge, crating amortization, and packing materials fees."""

    @staticmethod
    def calculate(
        quantity_kg: float,
        rate_per_kg: float = 0.40,
        provenance: Optional[EconomicProvenance] = None,
    ) -> CostItem:
        if quantity_kg <= 0:
            raise ValueError(f"Quantity must be positive, received: {quantity_kg}")
        if rate_per_kg < 0:
            raise ValueError(f"Rate cannot be negative, received: {rate_per_kg}")

        total_other = round(quantity_kg * rate_per_kg, 2)

        prov = provenance or EconomicProvenance(
            source="HORTICULTURAL_PACKAGING_WEIGHMENT_BENCHMARK",
            status=ProvenanceStatus.DEMO,
            effective_date="2024-09-15",
            is_demo=True,
            description=f"Crate packaging amortization & certified weighment fee at ₹{rate_per_kg:.2f}/kg.",
        )

        return CostItem(
            name="Packaging & Weighment",
            category="other",
            amount=total_other,
            unit="INR",
            provenance=prov,
            rate_basis=f"₹{rate_per_kg:.2f}/kg",
            is_variable=False,
        )


class SpoilageDisposalCostModel:
    """Calculates municipal disposal and labor costs for sorting out spoiled produce."""

    @staticmethod
    def calculate(
        lost_quantity_kg: float,
        disposal_rate_per_kg: float = 0.10,
        provenance: Optional[EconomicProvenance] = None,
    ) -> CostItem:
        if lost_quantity_kg < 0:
            raise ValueError(f"Lost quantity cannot be negative, received: {lost_quantity_kg}")

        total_cost = round(lost_quantity_kg * disposal_rate_per_kg, 2)

        prov = provenance or EconomicProvenance(
            source="APMC_SPOILAGE_DISPOSAL_BENCHMARK",
            status=ProvenanceStatus.DEMO,
            effective_date="2024-09-15",
            is_demo=True,
            description=f"Labor and culling fee for {lost_quantity_kg:.2f} kg degraded produce at ₹{disposal_rate_per_kg:.2f}/kg.",
        )

        return CostItem(
            name="Spoilage Culling & Disposal",
            category="loss",
            amount=total_cost,
            unit="INR",
            provenance=prov,
            rate_basis=f"₹{disposal_rate_per_kg:.2f}/kg on lost volume",
            is_variable=False,
        )
