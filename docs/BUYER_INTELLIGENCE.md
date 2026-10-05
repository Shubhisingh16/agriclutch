# AgriClutch: Buyer Intelligence & Demand Aggregation Engine

> **System Component**: Step 12 — Buyer Matching & Demand Aggregation  
> **Problem Statement**: SIH26132 — Strengthening Market Linkages and Price Discovery for Farmers  
> **Architectural Role**: Converts unstructured and semi-structured commercial demand into auditable, deterministic inputs for downstream decision optimization (Steps 13 & 14).

---

## 1. Executive Summary & North Star

Prior to Step 12, AgriClutch provided market-price intelligence: historical APMC trading records, multi-horizon probabilistic price forecasts (Chronos-2), and Net Realizable Value (NRV) realizations at regulated mandis.

In agricultural supply chains, however, farmers do not solely sell through open APMC auctions. A substantial and increasing volume of trade flows directly through commercial channels:
- Modern Retail Chains (e.g., Reliance Fresh, Mother Dairy)
- Agro-Food Processors (e.g., Tomato paste manufacturers, potato chip processors)
- Institutional Buyers (e.g., hotels, hospitals, universities)
- Farmer Producer Organizations (FPOs) & Aggregators
- Agricultural Exporters & Interstate Wholesalers

**Step 12 — Buyer Matching & Demand Aggregation Engine** bridges this gap. It introduces:
1. **Multi-Dimensional Candidate Matching**: Evaluates physical commodity compatibility, quality grade ranges, quantity lot boundaries, temporal delivery windows, and geospatial Haversine transport feasibility between a farmer's produce lot and buyer procurement requirements.
2. **Empirical Reliability Auditing**: Computes historical contract fulfillment rates, payment delays, cancellation rates, and dispute frequencies from immutable transaction ledgers with strict statistical gating ($N \ge 3$).
3. **Regional Demand Depth & Market Concentration**: Aggregates total stated demand, breaks down demand by quality requirement and buyer channel, computes the Herfindahl-Hirschman Index (HHI) for market power concentration, and generates order size distribution quantiles.

---

## 2. Strict Non-Normative Governance Mandate

### Zero Recommendation Leakage
Step 12 is **NOT** the final Optimal Selling Plan. Under the AgriClutch governance protocol:
- **No Normative Advice**: Step 12 never outputs directives such as `SELL NOW`, `HOLD`, `BUY`, or `STORE`.
- **No Winner Selection**: Step 12 never labels a buyer as `BEST BUYER`, `WINNER`, `TOP CHOICE`, or `RECOMMENDED BUYER`.
- **Additive Justification Only**: Step 12 outputs candidate matches with transparent, factual constraint checks and additive explanations (e.g., `Quality Grade A matches requirement [Grade A, Grade B]`, `Distance 18.4 km within delivery radius 40.0 km`, `Buyer provides immediate cash settlement`).

Downstream engines (Step 13 Portfolio Split Optimization & Step 14 Strategic Decision Execution) consume these factual matrices alongside price forecasts and risk profiles to formulate selling plans.

---

## 3. Core Subsystems

```
                                +---------------------------+
                                |  Farmer Produce Lot Input |
                                +-------------+-------------+
                                              |
                                              v
+-----------------------+       +---------------------------+       +-------------------------+
| Buyer Requirements &  | ----> |  Compatibility Matching   | <---> |  Geospatial Haversine   |
| Commercial Demands    |       |  Engine (6-D Constraints) |       |  Corridor Calculator    |
+-----------+-----------+       +-------------+-------------+       +-------------------------+
            |                                 |
            v                                 v
+-----------------------+       +---------------------------+       +-------------------------+
| Regional Demand & HHI |       |   Factual Match Matrix    | ----> | Inputs for Step 13 & 14 |
| Concentration Engine  |       |   (Zero Recommendations)  |       | Decision Optimization   |
+-----------+-----------+       +---------------------------+       +-------------------------+
            |
            v
+-----------------------+
| Empirical Reliability |
| Auditing (N >= 3)     |
+-----------------------+
```

### 3.1 Candidate Compatibility Matching (`ml/buyer/compatibility.py`)
Evaluates the Cartesian product of available produce lots and active commercial buyer requirements across six explicit dimensions:
1. **Commodity & Variety**: Strict identifier matching; variety compatibility evaluates equivalence or unrestricted buyer acceptance.
2. **Quality Grade Range**: Compares farmer assay grade against buyer's acceptable grade hierarchy (`GRADE_A`, `GRADE_B`, `GRADE_C`, `FAQ`).
3. **Quantity Lot Boundaries**: Checks whether lot satisfies minimum threshold $Q_{\text{min}}$. Partitions quantity into `compatible_quantity_kg` and `unmatched_supply_kg` if supply exceeds buyer maximum $Q_{\text{max}}$.
4. **Temporal Delivery Window**: Computes calendar day overlap between produce availability $[t_{s,\text{avail}}, t_{e,\text{avail}}]$ and buyer delivery requirement $[t_{s,\text{req}}, t_{e,\text{req}}]$.
5. **Geospatial Distance**: Computes great-circle Haversine distance from farmgate coordinates to delivery destination and evaluates against maximum haulage tolerance.
6. **Commercial Terms**: Extracts price basis (`FIXED_QUOTE`, `APMC_INDEXED`, `NEGOTIABLE`) and payment terms (`IMMEDIATE_CASH`, `NET_3_DAYS`, `NET_7_DAYS`, etc.).

### 3.2 Empirical Reliability Auditing (`ml/buyer/reliability.py`)
Computes four objective performance indicators from completed, audited buyer transaction logs. Every metric has strictly documented semantics, denominators, and missing-data treatments:

| Metric | Numerator | Denominator | Eligible Population | Missing Data Treatment | Provenance Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Fulfillment Rate** | Confirmed orders with `fulfillment_status == 'FULFILLED'` | Total confirmed orders ($N_{\text{confirmed}}$) | All confirmed buyer purchase contracts on file | Unsettled or pending orders are not counted in numerator | `EMPIRICAL` (DB) / `DEMO` (Synthetic Fixture) |
| **Cancellation Rate** | Confirmed orders with `fulfillment_status == 'CANCELLED'` | Total confirmed orders ($N_{\text{confirmed}}$) | All confirmed buyer purchase contracts on file | Non-cancelled orders evaluate to 0 | `EMPIRICAL` (DB) / `DEMO` (Synthetic Fixture) |
| **Dispute Rate** | Orders with recorded commercial disputes (`dispute_status == true`) | Total confirmed orders ($N_{\text{confirmed}}$) | All confirmed buyer purchase contracts on file | Undisputed orders evaluate to 0 | `EMPIRICAL` (DB) / `DEMO` (Synthetic Fixture) |
| **Average Payment Delay (Days)** | $\sum \max(0, t_{\text{actual\_settle}} - t_{\text{due}})$ across orders where both dates exist | $N_{\text{dated\_settlements}}$ (Count of settled orders with valid dates) | Settled orders having both `actual_payment_date` and `agreed_payment_due_date` | **Strict Distinction**: Missing payment dates are NEVER silently converted to 0. Valid observations are tracked separately. If $N_{\text{dated\_settlements}} = 0$, metric returns `None` | `EMPIRICAL` (DB) / `DEMO` (Synthetic Fixture) |

#### Sample-Size Gating Protocol (`provenance_status = CONFIGURED`):
- **Classification**: `provenance_status = CONFIGURED`
- **Definition**: *"Minimum descriptive sample-size gate used to suppress extremely small sample summaries."*
- **Behavior**:
  - If a buyer has fewer than 3 historical transactions ($N_{\text{confirmed}} < 3$), reliability status fails closed to `INSUFFICIENT_HISTORY`.
  - All rate and delay metrics are strictly suppressed (`null` / `None`) to prevent presenting misleading metrics from 1 or 2 historical transactions.
  - If zero records exist, status is `UNAVAILABLE`.
  - The threshold $N \ge 3$ is **NOT** described as statistically significant, universally sufficient, or an econometric standard; it is a conservative heuristic suppression gate.

### 3.3 Regional Demand & Market Concentration (`ml/buyer/aggregation.py`)
Provides macro market depth intelligence across the agricultural corridor:
- **Total Stated Demand ($Q_{\text{total}}$)**: Sum of all active procurement requirements and spot demands.
- **Herfindahl-Hirschman Index (HHI)** (`provenance_status = CONFIGURED`):
  $$HHI = 10,000 \times \sum_{i=1}^{M} s_i^2 = 10,000 \times \sum_{i=1}^{M} \left(\frac{q_i}{Q_{\text{total}}}\right)^2$$
  - **Threshold Framework (Adapted Convention)**: Adapted from the 1982/2010 U.S. Department of Justice & Federal Trade Commission (DOJ/FTC) Horizontal Merger Guidelines.
  - **Disclosure**: Thresholds are **NOT** empirical agricultural truths or objective economic judgments. They are provided solely as configured comparative benchmark bands:
    - $HHI < 1,500$: Unconcentrated benchmark band (distributed volume).
    - $1,500 \le HHI \le 2,500$: Moderately concentrated benchmark band.
    - $HHI > 2,500$: Concentrated benchmark band.
  - In the UI, the numeric HHI is displayed directly, accompanied by an explicit `CONFIGURED (DOJ/FTC CONVENTION)` badge.
- **Order Size Distribution Quantiles** (`provenance_status = CONFIGURED` Gate): Computes Min, P10, P25, Median (P50), P75, P90, Max, and Mean lot sizes across all active buyer orders. Requires minimum $N \ge 3$ observations as a configured heuristic gate; otherwise returns `INSUFFICIENT_DATA` and suppresses quantiles.

---

## 4. Data Provenance & Fail-Closed Policy

Every record, matching output, reliability metric, and aggregate statistic carries mandatory metadata:
- `provenance_status`: One of `EMPIRICAL`, `OFFICIAL`, `RESEARCH`, `CONFIGURED`, `DEMO`, or `UNAVAILABLE`.
- `is_demo`: Boolean flag denoting whether the record originated from verified benchmark seed fixtures or synthetic testing data.
- **Demo Fixture Disclosure**: In demo mode, all buyer entities are **6 synthetic demo buyer entities representing commercial buyer archetypes** (`is_demo = true`, `provenance_status = DEMO`), representing modern retail chains, agro-food processors, regional wholesalers, exporters, and institutional buyers across the TriCity/Punjab/Haryana/Delhi corridor. Never describe synthetic demo entities as verified real commercial buyers.
- **Fail-Closed Behavior**:
  - In `DATABASE` mode: If the underlying PostgreSQL database is unseeded, unreachable, or returns zero records, all endpoints fail closed with HTTP 503 (`Database unseeded or buyer records unavailable`).
  - In `DEMO` mode: Deterministic benchmark fixtures are loaded and explicitly marked with `provenance_status = "DEMO"` and `is_demo = true`.

---

## 5. Clean-Room Implementation Verification

In accordance with Section 2 of `AGENTS.md`, zero code or text was copied, imported, or referenced from external non-open-source repositories in `references/`. All compatibility logic, spherical distance geometry, statistical quantiles, and HHI arithmetic were authored cleanly from first principles.
