# AgriClutch: AI-Powered Agricultural Market Intelligence & Optimal Selling Platform

> **Problem Statement**: SIH26132 — Strengthening Market Linkages and Price Discovery for Farmers  
> **Platform Vision**: Institutional-grade decision-support intelligence answering the farmer's core economic question:  
> *"Given my crop, quantity, quality, location, storage capacity, liquidity requirement and risk preference, what is the optimal way to sell my produce?"*

---

## 1. System Overview

AgriClutch is an end-to-end agricultural market intelligence and decision-support platform engineered to eliminate information asymmetry and empower smallholder farmers across India.

Unlike traditional mandi dashboards that simply display delayed modal rates, AgriClutch synthesizes:
- **High-Resolution Market Intelligence**: Historical APMC records, cross-market spatial price dispersion, and market lead-lag graphs.
- **Probabilistic Time-Series Forecasting**: Deep learning foundation models (Amazon Chronos-2) forecasting $P_{10}, P_{50}, P_{90}$ price trajectories.
- **Net Realizable Value (NRV) Economics**: Comprehensive deduction of transit haulage, loading/unloading, ambient/cold storage decay, and statutory market fees to reveal true take-home earnings.
- **Commercial Buyer Intelligence (Step 12)**: Factual multi-dimensional compatibility matching, empirical contract reliability audits ($N \ge 3$), and regional demand depth with Herfindahl-Hirschman Index (HHI) market power concentration.

---

## 2. Platform Status & Verified Milestones

| Step | Subsystem | Status | Description |
| :--- | :--- | :---: | :--- |
| **Step 1** | Constitution & Clean-Room Firewall | ✅ Verified | Clean-room clean boundary; zero code copying from unverified references. |
| **Step 2** | System Architecture | ✅ Verified | Modular three-tier architecture documented in `ARCHITECTURE.md`. |
| **Step 3** | Repository & Tooling Foundation | ✅ Verified | Monorepo layout, Docker Compose, Git hygiene, and dependency isolation. |
| **Step 4** | Backend & Database Foundation | ✅ Verified | FastAPI asynchronous server, PostgreSQL 16 + TimescaleDB, Redis 7 caching. |
| **Step 5** | Frontend Dashboard Foundation | ✅ Verified | Next.js 14 App Router, Tailwind CSS, TypeScript strict mode, responsive layout. |
| **Step 6** | Engineering Verification | ✅ Verified | Comprehensive test suite, ruff linting, compileall validation. |
| **Step 7** | Agricultural Data Foundation | ✅ Verified | 10-year historical APMC price records for Tomato, Onion, and Potato across Punjab, Haryana, Chandigarh, and Delhi corridors. |
| **Step 8** | Agricultural Data Pipeline | ✅ Verified | Monotonic cubic interpolation, multi-horizon Median Absolute Deviation (MAD) anomaly detection. |
| **Step 9** | Market Intelligence Dashboard | ✅ Verified | Cross-mandi price comparison, spatial corridor map, and data quality provenance panels. |
| **Step 10** | Forecasting Intelligence Engine | ✅ Verified | Amazon Chronos-2 transformer, baseline models (Naive, Seasonal Naive, Holt-Winters, Quantile Gradient Boosting), rolling-origin evaluation. |
| **Step 11** | Decision Intelligence & NRV Engine | ✅ Verified | Non-linear crop perishability decay curves ($e^{-\delta t}$), freight haulage, exact break-even price $P_{\text{BE}} = C_{\text{non\_market}} / (Q_{\text{eff}} \cdot F_{\text{quality}} \cdot (1 - \mu_{\text{APMC}}))$, What-If sensitivity lab. |
| **Step 12** | Buyer Matching & Demand Aggregation | ✅ Verified | 6-D candidate matching, empirical reliability audits ($N \ge 3$), regional demand depth, HHI market concentration, zero recommendation leakage. |
| **Step 13** | Logistics + Storage + Perishability Engine | ✅ Verified | Physical and economic modeling of distance, haulage friction, decoupled decay $S(t)$ & $F(t)$, storage allocation, and scenario pathways (A–D) with zero recommendation leakage. |

---

## 3. Step 12: Buyer Intelligence & Matching Subsystems

Step 12 introduces structured commercial demand intelligence to complement APMC open-auction market data:

### 3.1 Multi-Dimensional Candidate Matching (`ml/buyer/compatibility.py`)
Evaluates candidate produce lots against standing procurement requirements across 6 independent dimensions:
1. **Commodity & Variety**: Strict identifier matching and variety equivalence.
2. **Quality Grade Range**: Grade hierarchy validation (`GRADE_A`, `GRADE_B`, `GRADE_C`, `FAQ`).
3. **Quantity Lot Boundaries**: Checks minimum threshold $Q_{\min}$ and partitions volume into `compatible_quantity_kg` and `unmatched_supply_kg` if supply exceeds buyer maximum $Q_{\max}$.
4. **Temporal Delivery Window**: Computes calendar day overlap between farmgate availability and buyer demand windows.
5. **Geospatial Distance**: Geodesic Haversine spherical distance calculation evaluated against delivery radius limits.
6. **Commercial Terms**: Extracts price basis (`FIXED_QUOTE`, `APMC_INDEXED`, `NEGOTIABLE`) and payment terms (`IMMEDIATE_CASH`, `NET_3_DAYS`, `NET_7_DAYS`, etc.).

### 3.2 Empirical Reliability Auditing (`ml/buyer/reliability.py`)
Computes four objective performance indicators from completed, audited buyer transaction ledgers:
- **Contract Fulfillment Rate**: $R_{\text{fulfill}} = N_{\text{fulfilled}} / N_{\text{confirmed}}$
- **Cancellation Rate**: $R_{\text{cancel}} = N_{\text{cancelled}} / N_{\text{confirmed}}$
- **Average Payment Delay Days**: $\overline{\Delta t}_{\text{pay}} = \frac{1}{N_{\text{dated}}} \sum \max(0, t_{\text{settled}} - t_{\text{due}})$ (missing dates strictly distinguished from 0; returns None if zero dated records exist)
- **Dispute Frequency**: $R_{\text{dispute}} = N_{\text{disputed}} / N_{\text{confirmed}}$

*Sample-Size Gating (`provenance_status = CONFIGURED`)*: Minimum descriptive sample-size gate ($N \ge 3$) used to suppress extremely small sample summaries; fails closed to `INSUFFICIENT_HISTORY` (heuristic gate, not a claim of statistical significance).

### 3.3 Regional Demand Depth & Market Concentration (`ml/buyer/aggregation.py`)
- **Herfindahl-Hirschman Index (HHI)** (`provenance_status = CONFIGURED`):
  $$HHI = 10,000 \times \sum_{i=1}^M \left(\frac{q_i}{Q_{\text{total}}}\right)^2$$
  Adapted convention based on U.S. DOJ/FTC Horizontal Merger Guidelines (<1500 unconcentrated, 1500–2500 moderate, >2500 concentrated). Provided as a descriptive benchmark, not an empirical agricultural truth.
- **Order Size Distribution Quantiles**: Min, P10, P25, Median (P50), P75, P90, Max, Mean (gated at $N \ge 3$, `provenance_status = CONFIGURED`).
- **Strict Non-Normative Contract**: Pure factual demand statistics with zero recommendation tags (`NO "BEST BUYER"`, `NO "SELL NOW"`).
- **Demo Fixture Disclosure**: In demo mode, features 6 synthetic demo buyer entities representing commercial buyer archetypes (`provenance_status = DEMO`, `is_demo = true`).

---

## 4. Step 13: Logistics, Storage & Perishability Subsystems

Step 13 implements the physical and economic feasibility engine answering:
*"What physically happens to the produce between the farmer's current location and each potential buyer/market over time?"*

### 4.1 Geodesic & Road Distance Modeling (`ml/logistics/distance.py`)
- **Haversine Great-Circle Geodesic**: Spherical distance calculation with Earth radius $R = 6371.0\text{ km}$, validating inputs strictly within $[-90, +90]^\circ$ lat and $[-180, +180]^\circ$ lon.
- **Road vs. Straight-Line Resolution**: Road distance is preferred when empirically documented; straight-line distance is multiplied by a configured circuity factor ($1.25\times$) with explicit `DistanceType` provenance annotation.
- **Transit Time & Speed Validation**: $t_{\text{transit}} = d / v_{\text{avg}}$, verifying realistic speeds ($1 \le v \le 120\text{ km/h}$).

### 4.2 Additive Friction Cost Accounting (`ml/logistics/costs.py`)
- **Decomposed Cost Stack**:
  $$C_{\text{logistics}} = C_{\text{transport}} + C_{\text{loading}} + C_{\text{unloading}} + C_{\text{handling}}$$
  where $C_{\text{transport}} = \max(\text{min\_charge}, d \times \text{rate\_per\_km})$.
- **Missing Distance Fail-Closed**: Missing distance appends an explicit `HAULAGE_DISTANCE_FEE` line item with amount $0.0$ and `status = UNAVAILABLE`, setting `economic_status = INCOMPLETE`.
- **Zero Silent Zeros**: Every line item carries its own provenance (`EMPIRICAL`, `OFFICIAL`, `RESEARCH`, `CONFIGURED`, `DEMO`).

### 4.3 Storage Capacity & Holding Costs (`ml/logistics/storage.py`)
- **Capacity Partitioning**: $Q_{\text{stored}} = \min(Q, Q_{\text{avail}})$, $Q_{\text{unstored}} = \max(0, Q - Q_{\text{avail}})$.
- **Feasibility Classification**: Categorizes requests into `FEASIBLE`, `PARTIALLY_FEASIBLE`, `INFEASIBLE_CAPACITY`, or `INFEASIBLE_DURATION` without rounding away capacity shortfalls.
- **Holding Cost Calculation**: Accrues monthly or daily holding rates based on allocated volume.

### 4.4 Decoupled Exponential Perishability (`ml/logistics/perishability.py`)
- **Physical Volume Retention**: $S(t) = \exp(-\delta t) \implies Q_{\text{effective}}(t) = Q_0 \times S(t)$.
- **Commercial Quality Factor**: $F_{\text{quality}}(t) = F_0 \times \exp(-\beta t)$.
- **Storage Temperature Regimes**: Calibrated decay constants ($\delta, \beta$) for Tomato, Onion, and Potato across Ambient and Cold Storage. Fails closed to `LOSS_MODEL_UNAVAILABLE` on unsupported commodities.

### 4.5 Scenario Evaluation Pathways (`ml/logistics/scenarios.py`)
- **Scenario A**: Immediate local mandi sale (baseline road transit + handling).
- **Scenario B**: Immediate distant terminal mandi sale (long-haul transit + multi-stage handling).
- **Scenario C**: Farmgate/local buyer sale with buyer pickup or farmer delivery.
- **Scenario D**: Storage hold with delayed dispatch (storage holding fee + perishability decay trajectory).
- **Zero Recommendation Leakage**: Pure factual comparison of elapsed hours, effective quantity, quality retention, and friction costs with zero normative scores or rankings.

---

## 5. Repository Structure

```
agriclutch/
├── backend/                             # FastAPI Python Backend
│   ├── app/
│   │   ├── api/v1/endpoints/            # Versioned API routes (lots, markets, forecast, buyers, demand, logistics, storage, perishability)
│   │   ├── core/                        # Database sessions, settings, exceptions, logging
│   │   ├── db/seeds/                    # Benchmark demo fixtures (Chandigarh agricultural corridor)
│   │   ├── models/                      # SQLAlchemy 2.0 models (markets, prices, buyers, demands, logistics)
│   │   ├── schemas/                     # Pydantic v2 validation contracts
│   │   └── services/                    # Domain logic & algorithms (logistics_service, buyer_service, forecasting, nrv)
│   └── tests/                           # Pytest automated test suite (logistics, buyers, NRV, forecasting)
│
├── frontend/                            # Next.js 14 App Router Frontend
│   ├── src/
│   │   ├── app/                         # App Router pages and layouts
│   │   ├── components/logistics/        # Step 13 Logistics & Storage components
│   │   │   ├── LogisticsPanel.tsx       # Master logistics pathways & parameters console
│   │   │   ├── StoragePanel.tsx         # Storage facility capacity & duration explorer
│   │   │   ├── ScenarioCard.tsx         # Multi-stage pathway scenario fact cards (A-D)
│   │   │   ├── DistanceCard.tsx         # Geodesic vs road distance comparison
│   │   │   ├── PerishabilityChart.tsx   # Decoupled decay trajectory visualizer
│   │   │   └── AssumptionBadge.tsx      # Provenance and demo status badges
│   │   ├── components/buyer/            # Buyer Intelligence & Matching components
│   │   ├── lib/api/                     # Typed API client fetchers (logistics, buyers, nrv)
│   │   └── types/                       # Shared TypeScript interfaces (logistics, buyer, nrv)
│   └── tests/                           # Node.js automated test runner suite
│
├── docs/                                # Technical & Architectural Documentation
│   ├── LOGISTICS_ENGINE.md              # Multi-stage logistics pathway & haulage architecture
│   ├── STORAGE_MODEL.md                 # Storage facility capacity & holding cost model
│   ├── PERISHABILITY_MODEL.md           # Decoupled exponential decay equations & parameters
│   ├── LOGISTICS_DATA_CONTRACT.md       # API schemas and fail-closed error handling
│   ├── LOGISTICS_ASSUMPTIONS.md         # Comprehensive provenance status and demo fixtures
│   ├── BUYER_INTELLIGENCE.md            # High-level architecture of Step 12
│   ├── BUYER_MATCHING.md                # Multi-dimensional matching mathematical specification
│   ├── DEMAND_AGGREGATION.md            # Regional demand depth & HHI formulation
│   ├── BUYER_DATA_CONTRACT.md           # API schemas and fail-closed error handling
│   ├── NRV_ENGINE.md                    # Economic Net Realizable Value engine
│   └── FORECASTING_MODEL.md             # Time-series forecasting models
│
├── ml/
│   ├── logistics/                       # Standalone Step 13 Logistics & Storage Package
│   │   ├── contracts.py                 # Strict Python dataclasses & enums
│   │   ├── distance.py                  # Haversine geodesic & transit time calculations
│   │   ├── costs.py                     # Additive friction cost decomposition engine
│   │   ├── storage.py                   # Storage capacity allocation & holding cost engine
│   │   ├── perishability.py             # Decoupled exponential perishability decay models
│   │   ├── feasibility.py               # Factual multi-dimensional feasibility evaluator
│   │   ├── scenarios.py                 # Multi-stage pathway composer (Scenarios A through D)
│   │   └── smoke_test.py                # Standalone 15-stage verification suite
│   ├── buyer/                           # Standalone Step 12 Buyer Intelligence Package
│   └── decision/                        # Standalone Step 11 NRV & Decision Package
│
├── ARCHITECTURE.md                      # System Architecture & Technical Design Document
├── AGENTS.md                            # Repository governance and engineering rules
└── docker-compose.yml                   # Local container orchestration
```

---

## 6. Getting Started & Verification

### 6.1 Prerequisites
- Python 3.11+
- Node.js 20 LTS
- PostgreSQL 16 (optional for demo mode)

### 6.2 Backend Verification
```bash
# 1. Run standalone mathematics smoke tests
python -m ml.buyer.smoke_test
python -m ml.logistics.smoke_test

# 2. Run backend pytest suite (all 133 tests including Step 13)
pytest backend/tests/

# 3. Static type and lint verification
python -m ruff check --config backend/pyproject.toml backend/ ml/
python -m compileall backend/ ml/
```

### 6.3 Frontend Verification
```bash
cd frontend

# 1. Run frontend mathematical and UI test suite (36 tests)
npm test

# 2. Static type and lint check
npm run lint
npx tsc --noEmit
```

### 6.4 Starting the Application
```bash
# Terminal 1: Backend
uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8000 --reload

# Terminal 2: Frontend
cd frontend && npm run dev
```
Navigate to `http://localhost:3000` and select the **Logistics & Pathways** or **Storage Facilities** tab.

---

## 6. Intellectual Property & Clean-Room Standard

In accordance with strict clean-room software engineering standards:
- All mathematical formulas, Haversine spherical distance models, HHI concentration algorithms, and statistical gating logic were authored cleanly from first principles.
- Zero code or files were copied or imported from third-party non-open-source repositories.
- All demo data fixtures are explicitly labeled with `provenance_status = "DEMO"` and `is_demo = true`.

---
*AgriClutch — Empowering Indian Farmers with Actionable Market & Selling Intelligence.*