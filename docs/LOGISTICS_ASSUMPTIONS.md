# AgriClutch Step 13 Logistics & Storage Assumptions Schedule

> **Subsystem**: Step 13 — Logistics + Storage + Perishability Feasibility Engine  
> **Problem Statement**: SIH26132 — Strengthening Market Linkages and Price Discovery for Farmers  
> **Platform Vision**: Complete transparency regarding physical and economic assumptions.

---

## 1. Provenance Semantics

Per Pre-Implementation Hardening Patch Rule 2, provenance statuses carry strict definitions:

- **`EMPIRICAL`**: Directly observed or documented empirical data (e.g. historical transit logs, official weighbridge records).
- **`OFFICIAL`**: Authoritative government or institutional source (e.g. APMC gazette fee schedules).
- **`RESEARCH`**: Peer-reviewed academic literature or institutional research benchmarks.
- **`CONFIGURED`**: Explicitly configured system parameter assumption without live empirical telemetry.
- **`DEMO`**: Synthetic demo assumption created for offline hackathon demonstration without claim to real-world infrastructure.
- **`UNAVAILABLE`**: Missing parameter where estimation is prohibited to prevent false precision.

---

## 2. Vehicle Assumptions

| Vehicle Type | Capacity (kg) | Base Dispatch Fee (₹) | Freight Rate (₹/km) | Speed Assumption (km/h) | Provenance Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Tractor Trolley | 1,500 | 500.00 | 18.00 | 25.0 | `DEMO` |
| Light Commercial Vehicle (LCV) | 2,500 | 800.00 | 25.00 | 45.0 | `DEMO` |
| Heavy Truck (10T) | 10,000 | 2,500.00 | 55.00 | 40.0 | `DEMO` |
| Reefer Container Truck | 8,000 | 3,500.00 | 75.00 | 50.0 | `DEMO` |

---

## 3. Storage Facility Assumptions

| Facility Name | Storage Type | Capacity (MT) | Holding Fee (₹/kg/day) | Duration Horizon (days) | Provenance Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `DEMO_WAREHOUSE_MOHALI` | Ventilated | 100 MT | 0.15 | 2–60 | `DEMO` |
| `DEMO_COLD_STORAGE_NORTH` | Cold Chain Hub | 250 MT | 0.25 | 3–90 | `DEMO` |
| `DEMO_SILO_PUNJAB` | Ventilated Silo | 500 MT | 0.10 | 7–180 | `DEMO` |
| `DEMO_COLD_CHAIN_DELHI` | Cold Chain Hub | 500 MT | 0.35 | 1–60 | `DEMO` |

---

## 4. Handling & Labor Fee Assumptions

- Farm Loading Labor Fee: ₹12.00 / quintal (₹0.12/kg)
- Buyer Unloading Labor Fee: ₹10.00 / quintal (₹0.10/kg)
- Mandi Yard Congestion Unloading: ₹12.00 / quintal (₹0.12/kg)
- Cold Storage Pallet Handling: ₹15.00 / quintal (₹0.15/kg)

---

## 5. Economic Provenance Gate & Statuses

Aggregate scenario costing returns one of five strict economic statuses:
1. `COMPLETE_EMPIRICAL`: All fee items verified empirically.
2. `COMPLETE_MIXED_PROVENANCE`: Combination of empirical rates and configured assumptions.
3. `DEMO_ASSUMPTION`: Synthetic demo assumptions used throughout.
4. `INCOMPLETE`: Distance or rate parameters missing; missing items are not silently zeroed.
5. `UNAVAILABLE`: Costing unavailable due to missing core data.
