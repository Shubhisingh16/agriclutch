# AgriClutch Storage Capacity & Holding Feasibility Model

> **Subsystem**: Step 13 — Logistics + Storage + Perishability Feasibility Engine  
> **Problem Statement**: SIH26132 — Strengthening Market Linkages and Price Discovery for Farmers  
> **Platform Vision**: Mathematical and operational modeling of warehouse and cold storage facility holding.

---

## 1. Storage Feasibility Formulation

Storage evaluation determines whether produce can be accommodated at a designated facility without exceeding capacity bounds or operating duration horizons.

### 1.1 Capacity Partitioning

Given requested lot volume $Q_{\text{requested}}$ and facility available capacity $C_{\text{avail}}$:

$$Q_{\text{stored}} = \min(Q_{\text{requested}}, \max(0, C_{\text{avail}}))$$

$$Q_{\text{unstored}} = \max(0, Q_{\text{requested}} - C_{\text{avail}})$$

- If $Q_{\text{unstored}} > 0$ and $Q_{\text{stored}} > 0$: **`PARTIALLY_FEASIBLE`**
- If $Q_{\text{stored}} = 0$ and $Q_{\text{requested}} > 0$: **`INFEASIBLE`** (Capacity Exhausted)
- If $Q_{\text{unstored}} = 0$: **`FEASIBLE`** (Full Capacity Accommodated)

The system **never** rounds away capacity shortfalls.

### 1.2 Duration Horizon Bounding

Given requested duration $D$ days and facility parameters $[D_{\min}, D_{\max}]$:

$$\text{Valid Duration} = \begin{cases}
\text{True} & \text{if } D_{\min} \le D \le D_{\max} \\
\text{False} & \text{otherwise}
\end{cases}$$

If $D > D_{\max}$, status is strictly **`INFEASIBLE`** with explicit audit warning.

### 1.3 Commercial Holding Fee Calculation

$$\text{Cost}_{\text{storage}} = Q_{\text{stored}} \times D \times r_{\text{cost/kg/day}}$$

---

## 2. Synthetic Facility Archetypes (Demo Fixtures)

Per Pre-Implementation Hardening Patch Rule 1, facilities use clearly synthetic identifiers and are tagged with `is_demo=true` and `provenance_status="DEMO"`:

| Facility Identifier | Facility Archetype | Storage Type | Total Capacity | Available Capacity | Holding Rate | Horizon | Climate Control |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `DEMO_WAREHOUSE_MOHALI` | Mohali Demo Ventilated Warehouse | `VENTILATED` | 100,000 kg | 35,000 kg | ₹0.15/kg/d | 2–60 d | 24°C, 65% RH |
| `DEMO_COLD_STORAGE_NORTH` | Demo Northern Cold Chain Terminal | `COLD` | 250,000 kg | 75,000 kg | ₹0.25/kg/d | 3–90 d | 10°C, 92% RH |
| `DEMO_SILO_PUNJAB` | Punjab Demo Grain & Bulk Silo Hub | `VENTILATED` | 500,000 kg | 150,000 kg | ₹0.10/kg/d | 7–180 d | 22°C, 55% RH |
| `DEMO_COLD_CHAIN_DELHI` | Delhi Terminal Demo Cold Hub | `COLD` | 500,000 kg | 120,000 kg | ₹0.35/kg/d | 1–60 d | 4°C, 95% RH |

---

## 3. Storage Audit Lineage & Provenance

Every storage query response returns verifiable provenance metadata:
```json
{
  "source_name": "DEMO_FACILITY_BENCHMARK_SCHEDULE",
  "status": "DEMO",
  "is_demo": true,
  "justification": "DEMO ASSUMPTION — Model based on indicative regional cold storage benchmarks; not verified physical infrastructure."
}
```
