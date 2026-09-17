# AgriClutch NRV Data Handling, Fail-Closed Policy & Unit Protocols

> **Problem Statement**: SIH26132 — Strengthening Market Linkages and Price Discovery for Farmers  
> **Subsystem**: Decision Intelligence & Net Realizable Value (NRV) Engine (Step 11)  
> **Status**: Verified Operational Protocol  

---

## 1. Fail-Closed Economic Policy & Anti-Fabrication Mandate

AgriClutch enforces a strict clean-room and anti-fabrication mandate:

1. **No Silent Fallbacks in Database Mode**:
   When configured in production database mode (`AGRICLUTCH_DATA_MODE=database`), if any required economic assumption (e.g. freight rate, APMC cess, storage tariff) is missing from the database, the system **strictly fails closed** with a typed domain error (e.g. `ECONOMIC_ASSUMPTION_UNAVAILABLE` or `MARKET_CHARGE_UNAVAILABLE`).
   The backend **never** silently injects synthetic demo values into a database-backed session.
2. **Explicit Demo Mode**:
   Synthetic benchmark economic parameters from `backend/app/db/seeds/economic_demo_seed_data.py` are loaded **only** when explicitly configured with:
   ```env
   AGRICLUTCH_DATA_MODE=demo
   ```
   Every response carrying demo assumptions includes:
   - Header: `X-AgriClutch-Data-Mode: DEMO`
   - Header: `X-AgriClutch-DataSource: DEMO_BENCHMARK_SEED`
   - Provenance tag on all parameters: `provenance_status: "DEMO"`, `is_demo: true`
3. **No Fabricated Real-World Claims**:
   Demo assumptions must never be described in documentation, code, or user interfaces as "official APMC rates", "real-time transport costs", or "verified market quotes".

---

## 2. Unit System & Dimensional Safety

All calculations in the NRV Engine adhere to rigorous dimensional consistency:

### Supported Input Units
- `kg` (Kilogram, standard base unit)
- `quintal` ($1\text{ quintal} = 100\text{ kg}$)
- `tonne` / `ton` / `metric_ton` ($1\text{ tonne} = 1,000\text{ kg}$)

### Dimensional Normalization Protocol
1. Input harvest quantity $Q_{\text{input}}$ in unit $U_{\text{input}}$ is validated:
   - Must be strictly positive ($Q > 0$).
   - Must be finite (no `NaN`, no `+inf`, no `-inf`).
2. Internal normalization to base kilogram quantity:
   $$Q_0 = Q_{\text{input}} \cdot \text{Multiplier}(U_{\text{input}})$$
3. Price units from Step 10 forecast:
   - Denominated strictly in `INR_PER_KG` (₹/kg).
4. Haulage tonnage:
   $$\text{Tonnage} = \frac{Q_0}{1000.0}$$
5. Gross Revenue:
   $$\text{GrossRevenue} = Q_{\text{effective}} (\text{kg}) \cdot P_{\text{adjusted}} (\text{INR/kg}) = \text{INR}$$
6. Dimensional Preservation:
   The result preserves both the original user input (`original_quantity`, `original_unit`) and the canonical normalized representation (`normalized_quantity_kg`, `normalized_unit="KG"`).

---

## 3. Typed Domain Error Codes

When inputs are out of bounds or required model dependencies are absent, the engine raises or returns explicit typed error objects:

| Error Code | HTTP Status | Trigger Condition |
| :--- | :--- | :--- |
| `INVALID_QUANTITY` | 400 Bad Request | Quantity $\le 0$, non-numeric, `NaN`, or infinite. |
| `INVALID_UNIT` | 400 Bad Request | Unrecognized quantity unit (not in `kg`, `quintal`, `tonne`). |
| `INSUFFICIENT_FORECAST` | 422 Unprocessable Entity | Price forecast missing required quantiles or insufficient historical data. |
| `ECONOMIC_ASSUMPTION_UNAVAILABLE` | 503 Service Unavailable | Required cost parameter absent in database mode without fallback. |
| `TRANSPORT_COST_UNAVAILABLE` | 503 Service Unavailable | Mandi distance or freight rate absent. |
| `STORAGE_COST_UNAVAILABLE` | 503 Service Unavailable | Storage tariff absent for requested storage type. |
| `MARKET_CHARGE_UNAVAILABLE` | 503 Service Unavailable | Mandi fee rate absent for target APMC market. |
| `LOSS_MODEL_UNAVAILABLE` | 503 Service Unavailable | Crop perishability decay parameters unavailable. |
| `QUALITY_MODEL_UNAVAILABLE` | 503 Service Unavailable | Quality grade multiplier unavailable for specified grade. |
| `BREAK_EVEN_UNAVAILABLE` | 422 Unprocessable Entity | Effective quantity is zero or required non-market costs unavailable. |
| `MISSING_PROVENANCE` | 500 Internal Error | An economic parameter was injected without complete provenance fields. |

---

## 4. Uncertainty & Risk Status Codes

The engine recognizes that "no risk adjustment modeled" is fundamentally distinct from "zero operational risk":
- If an empirical or behavioral risk model is active: `risk_cost > 0.0`, `status="MODELED"`.
- If no risk model is applied: `risk_cost = 0.0`, `status="NOT_MODELED"`.
- Missing risk parameters are never disguised as proven certainty.
