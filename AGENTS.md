# AGRI-LINK AI: Agent Guidelines & Engineering Playbook

> **Repository Governance & Operational Protocol for AI Coding Agents and Contributors**  
> **Problem Statement**: SIH26132 — Strengthening Market Linkages and Price Discovery for Farmers  
> **Platform Vision**: An AI-powered agricultural market intelligence and decision-support platform answering:  
> *"Given my crop, quantity, quality, location, storage capacity, liquidity requirement and risk preference, what is the optimal way to sell my produce?"*

---

## 1. Prime Directives & North Star

You are operating as a software engineer on **AGRI-LINK AI**. Every line of code, documentation, test, and configuration must adhere to strict engineering standards modeled after top-tier institutional projects (such as [darkinspect](https://github.com/Shubhisingh16/darkinspect)).

### The Core Question
Every subsystem in AGRI-LINK AI exists to serve one question:
$$\text{Optimal Selling Plan} = f(\text{Crop}, \text{Quantity}, \text{Quality}, \text{Location}, \text{Storage}, \text{Liquidity}, \text{Risk})$$

The platform is **NOT**:
- A basic price dashboard displaying yesteryear mandi rates.
- A raw price prediction tool outputting meaningless point forecasts.
- A dumb, unverified buyer directory.

The platform **IS**:
- An end-to-end decision-support intelligence engine fusing **Market Intelligence + Time-Series Forecasting + Buyer Matching + Logistics Costing + Storage Perishability + Risk Preferences** to output an actionable, mathematically grounded **Optimal Selling Plan** (e.g., *Sell 60% immediately to Buyer X at ₹28.50/kg; store 40% in cold storage for 14 days targeting Terminal Mandi Y at ₹34.00/kg*).

---

## 2. Research Foundations & Intellectual Property Firewall

We have previously inspected two academic research repositories in `references/`:
1. `references/farmers_collective` (ACT4D IIT Delhi / CCD / Google AI4SG, ACM COMPASS 2023)
2. `references/commodity_analysis` (ICTD Lab, IIT Delhi)

### CRITICAL CLEAN-ROOM LEGAL MANDATE:
- **Zero Code Contamination**: Neither reference repository contains an open-source license (`LICENSE` is absent; code is *All Rights Reserved* by default).
- **NEVER** copy, port, or vendor code, functions, variable blocks, or raw files from `references/`.
- **NEVER** import from or link to `references/` in application code.
- **NEVER** copy their application architecture verbatim.
- **Mathematical & Conceptual Clean-Room Implementation**: You may implement mathematical formulations, domain schemas, and public algorithmic concepts (e.g., Russell Stineman's 1980 interpolation, Median Absolute Deviation outlier detection, lead-lag cross-correlation, Kahneman-Tversky prospect theory) from first principles.
- **Modern Standards**: When implementing these concepts, use modern, robust Python 3.11+ and SciPy/NumPy/Pandas 2.x APIs. Never replicate the deprecated, broken patterns found in the reference repos (e.g., `np.float`, `DataFrame.append()`, `Series.mad()`).

---

## 3. Core Development Principles

1. **Zero Data Fabrication**: Never fabricate price records, market statistics, or performance metrics. If data is synthetic or simulated for a demo, it must be explicitly labeled: `is_demo: true`, `source: "synthetic_demo"`.
2. **No False Real-Time Claims**: If the system runs on static benchmark data, say so clearly in the UI and API metadata (`data_mode: "benchmark_demo"`, `last_synced: "2026-09-15T00:00:00Z"`).
3. **Reproducible Numerical Recommendations**: Optimization, Net Realizable Value (NRV), and risk models must be deterministic given fixed seeds and inputs. A farmer must receive explainable, verifiable numbers.
4. **Decouple ML Prediction from Business Optimization**: Machine learning models forecast price distributions $P(y_t \mid x_{<t})$. Business logic and optimization solvers calculate Net Realizable Value and split strategies. Never mix business logic into model weights or loss functions.
5. **No Black-Box Buyer Matching**: Every buyer recommendation must expose transparent, additive reasons (`+₹1.50/kg net realization`, `Grade A match`, `24h pickup window`, `High payment reliability (98%)`, `-15 km further distance`).
6. **LLMs Do NOT Generate Numeric Forecasts**: Multimodal LLMs (e.g., Gemini) are strictly restricted to synthesizing unstructured text, news, weather warnings, and explaining structured optimization outputs. Numeric forecasts must originate solely from verified time-series foundation models (Chronos-2) or statistical baselines.
7. **Modular & Replaceable Forecasting**: The forecasting pipeline must use an abstract interface (`BaseForecaster`). Chronos-2 is our primary model, but the system must gracefully run with fallback baselines (Naive, Seasonal Naive, XGBoost) if GPU/PyTorch dependencies are unavailable.
8. **Test-Driven Calculations**: Write automated unit tests for every mathematical formula: Stineman monotonic interpolation, MAD anomaly scores, spatial dispersion, lead-lag cross-correlation, perishable decay functions, and NRV calculations.
9. **Environment Variable Security**: Never commit API keys, database passwords, or JWT secrets. Use `.env.example` with clear placeholders and load settings via Pydantic `BaseSettings`.
10. **Demo Mode Parity**: The application must feature a bulletproof, 100% offline-capable `DEMO MODE` that runs without external network calls, third-party API dependencies, or live API credentials.

---

## 4. Repository Structure & Module Boundaries

The project follows a clean, modular monorepo layout:

```
agriclutch/
├── AGENTS.md                               # Agent guidelines and protocols (this file)
├── PRODUCT_SPEC.md                         # Product requirements and functional specification
├── ARCHITECTURE.md                         # System architecture and technical design
├── RESEARCH_REPOSITORY_ANALYSIS.md         # Reference repo empirical analysis
├── docker-compose.yml                      # Local infrastructure (DB, Redis, Backend, Frontend)
├── .env.example                            # Template environment configuration
│
├── backend/                                # FastAPI Python Backend
│   ├── pyproject.toml                      # Poetry / pip configuration
│   ├── Dockerfile                          # Backend container definition
│   ├── app/
│   │   ├── main.py                         # Application entrypoint & middleware
│   │   ├── config.py                       # Pydantic v2 application settings
│   │   │
│   │   ├── api/v1/                         # Versioned REST API routes
│   │   │   ├── router.py                   # Master v1 router aggregator
│   │   │   ├── endpoints/
│   │   │   │   ├── lots.py                 # Produce lot creation & profile
│   │   │   │   ├── markets.py              # Mandi listings, arrivals, prices
│   │   │   │   ├── forecast.py             # Chronos-2 price & arrival forecasts
│   │   │   │   ├── graph.py                # Lead-lag market graph queries
│   │   │   │   ├── buyers.py               # Buyer discovery & demand matching
│   │   │   │   ├── optimizer.py            # Optimal Selling Plan solver
│   │   │   │   ├── simulator.py            # What-If sensitivity simulator
│   │   │   │   ├── fpo.py                  # FPO aggregation workflows
│   │   │   │   └── demo.py                 # Demo mode reset & scenario loader
│   │   │
│   │   ├── core/                           # Shared foundational utilities
│   │   │   ├── database.py                 # SQLAlchemy 2.0 async engine & session
│   │   │   ├── redis.py                    # Redis connection pool & cache helpers
│   │   │   ├── exceptions.py               # Custom HTTP & domain exceptions
│   │   │   └── logging.py                  # Structured JSON logging
│   │   │
│   │   ├── db/                             # Data persistence layer
│   │   │   ├── models/                     # SQLAlchemy ORM models
│   │   │   │   ├── market.py               # Mandi & state master models
│   │   │   │   ├── price_record.py         # TimescaleDB hypertable for daily rates
│   │   │   │   ├── produce_lot.py          # Farmer lots & crop specifications
│   │   │   │   ├── buyer.py                # Buyers, demands, and reliability scores
│   │   │   │   └── selling_plan.py         # Saved selling plans & decision audits
│   │   │   └── seeds/                      # Demo seed data (Tomato, Onion, Potato)
│   │   │
│   │   ├── schemas/                        # Pydantic v2 validation contracts
│   │   │   ├── lot.py                      # Request/response schemas for lots
│   │   │   ├── market.py                   # Market & price schemas
│   │   │   ├── forecast.py                 # Quantile forecast schemas
│   │   │   ├── buyer.py                    # Buyer & matching schemas
│   │   │   └── plan.py                     # Selling plan & simulator schemas
│   │   │
│   │   ├── services/                       # Business logic & algorithms
│   │   │   ├── data_cleaning/              # Monotonic interpolation & anomaly detection
│   │   │   │   ├── interpolator.py         # Modern monotonic cubic / Stineman implementation
│   │   │   │   └── anomaly_detector.py     # Multi-horizon MAD & ratio outlier detector
│   │   │   │
│   │   │   ├── forecasting/                # Forecasting service layer
│   │   │   │   ├── base.py                 # Abstract BaseForecaster interface
│   │   │   │   ├── chronos_engine.py       # Amazon Chronos-2 inference runner
│   │   │   │   └── baseline_models.py      # Naive, Seasonal Naive, and tabular baselines
│   │   │   │
│   │   │   ├── graph/                      # Market relationship graph
│   │   │   │   └── lead_lag_builder.py     # Rolling cross-correlation graph generator
│   │   │   │
│   │   │   ├── perishability/              # Crop spoilage & decay engine
│   │   │   │   └── decay_models.py         # Tomato, Onion, Potato loss curves
│   │   │   │
│   │   │   ├── logistics/                  # Freight & transit cost calculations
│   │   │   │   └── route_cost.py           # Haulage, distance, and loading cost estimator
│   │   │   │
│   │   │   └── optimizer/                  # Decision Optimization Engine
│   │   │       ├── nrv_calculator.py       # Net Realizable Value calculator
│   │   │       ├── prospect_theory.py      # Behavioral risk valuation function
│   │   │       └── plan_solver.py          # Multi-strategy split allocation solver
│   │   │
│   │   └── tests/                          # Automated Pytest suite
│   │       ├── conftest.py                 # Async client & mock fixtures
│   │       ├── test_interpolation.py       # Math validation for interpolation
│   │       ├── test_anomaly.py             # MAD outlier detection tests
│   │       ├── test_nrv.py                 # NRV arithmetic & edge-case tests
│   │       ├── test_optimizer.py           # Split-strategy optimization tests
│   │       └── test_api_endpoints.py       # FastAPI contract & endpoint tests
│   │
└── frontend/                               # Next.js 14 Web Application
    ├── package.json                        # Node dependencies
    ├── Dockerfile                          # Frontend container definition
    ├── next.config.mjs                     # Next.js configuration
    ├── tailwind.config.ts                  # Tailwind styling & tokens
    ├── tsconfig.json                       # TypeScript compiler options
    ├── src/
    │   ├── app/                            # App Router routes & layouts
    │   │   ├── layout.tsx                  # Root layout & providers
    │   │   ├── page.tsx                    # Landing & navigation overview
    │   │   ├── dashboard/page.tsx          # Farmer main intelligence console
    │   │   ├── lot/new/page.tsx            # Produce lot creation flow
    │   │   ├── plan/[id]/page.tsx          # Optimal Selling Plan detail
    │   │   ├── simulator/page.tsx          # Interactive What-If sensitivity lab
    │   │   ├── markets/page.tsx            # Mandi comparison & lead-lag map
    │   │   └── fpo/page.tsx                # FPO aggregation & bulk selling portal
    │   ├── components/                     # Reusable React components
    │   │   ├── ui/                         # Design system primitives (buttons, modals, badges)
    │   │   ├── charts/                     # Recharts / Chart.js wrappers (Price, Forecast, Quantiles)
    │   │   ├── maps/                       # MapLibre / Leaflet market location & routing visualizer
    │   │   ├── forms/                      # Lot creator, preference sliders, and simulator inputs
    │   │   └── plan/                       # Strategy cards, NRV breakdown tables, risk alerts
    │   ├── hooks/                          # Custom React hooks (useForecast, useSimulation)
    │   ├── lib/                            # API client, utility functions, formatting
    │   └── types/                          # Shared TypeScript interfaces (aligned with Pydantic)
```

---

## 5. Technology Stack & Runtime Conventions

### 5.1 Backend (Python)
- **Runtime**: Python 3.11+
- **Framework**: FastAPI with asynchronous handlers (`async def`)
- **Validation**: Pydantic v2 (`from pydantic import BaseModel, Field, ConfigDict`)
- **ORM**: SQLAlchemy 2.0 (`AsyncSession`, `select`, declarative base)
- **Database**: PostgreSQL 16 (with TimescaleDB hypertable for time-series if enabled, or standard partitioned tables)
- **Caching & Job Queue**: Redis 7.x
- **Numerical & ML**: NumPy 1.26+, Pandas 2.2+, SciPy 1.12+, PyTorch 2.2+, Amazon Chronos-2 (`chronos-forecasting` or HuggingFace transformers)
- **Linting & Formatting**: `ruff` for linting and formatting; `mypy --strict` for static type verification

### 5.2 Frontend (TypeScript)
- **Runtime**: Node.js 20 LTS
- **Framework**: Next.js 14+ (App Router, React Server Components by default, `'use client'` only where interactive state is required)
- **Language**: TypeScript 5.x (strict mode, zero `any` policy)
- **Styling**: Tailwind CSS with CSS variables for dynamic theming
- **Component Library**: Radix UI / Shadcn UI patterns
- **Data Visualization**: Recharts (for time series, quantiles, and breakdown bars)
- **Geographic Maps**: MapLibre GL or Leaflet for mandi routing and spatial dispersion
- **State Management**: Zustand for client state, TanStack React Query for server cache

---

## 6. Coding Standards & Linter Guidelines

### 6.1 Backend Rules
- **Explicit Types**: Every function must specify argument types and return type annotations:
  ```python
  def calculate_net_realizable_value(
      gross_revenue: float,
      freight_cost: float,
      storage_cost: float,
      spoilage_loss: float,
      market_fees: float,
      risk_penalty: float = 0.0,
  ) -> float:
      """Calculates estimated net realization after deducting all friction costs."""
      ...
  ```
- **Pydantic Validation**: Never process untyped JSON dictionaries. Validate all payloads into Pydantic models with clear validation constraints (`gt=0`, `le=1.0`).
- **Async DB Sessions**: Always use `async with async_session() as session:` with transactional context managers.
- **Exceptions**: Never return naked HTTP 500 errors. Raise custom domain exceptions mapped to appropriate HTTP status codes (e.g., `ProduceLotNotFoundError`, `InfeasibleStrategyError`).

### 6.2 Frontend Rules
- **Zero `any`**: All API response payloads must have corresponding TypeScript interfaces in `src/types/`.
- **Server vs. Client Components**: Keep page wrappers as Server Components. Extract interactive sliders, charts, and form inputs into dedicated Client Components.
- **Fail Gracefully**: Every chart and data view must handle loading states (`Skeleton`), empty states (`No data for selected mandi`), and error states with user-friendly retry buttons.

---

## 7. Testing & Quality Verification Standards

Every agent creating or modifying logic must execute automated verification:

1. **Unit Tests (`backend/app/tests/`)**:
   - `test_interpolation.py`: Verify that interpolation never produces negative values and strictly preserves monotonicity on monotonic intervals.
   - `test_anomaly.py`: Test MAD outlier detection with known synthetic spikes; assert that robust median is invariant to single outlier corruption.
   - `test_nrv.py`: Verify NRV math under edge conditions (zero transport, 100% spoilage, negative price shock).
   - `test_optimizer.py`: Verify that split allocations sum to 100% of available lot quantity ($q_1 + q_2 + \dots = Q_{\text{total}}$).
2. **Deterministic Seeds**:
   - In all ML and synthetic generation scripts, set explicit random seeds (`torch.manual_seed(42)`, `np.random.seed(42)`).
3. **API Contract Verification**:
   - Ensure all endpoints match the OpenAPI schema specifications documented in `ARCHITECTURE.md`.

---

## 8. Synthetic & Demo Data Contracts

To ensure our 3-minute hackathon demo runs flawlessly without external internet reliance:
- The backend must ship with pre-compiled seed fixtures in `backend/app/db/seeds/`:
  - 3 target commodities: **Tomato**, **Onion**, **Potato**.
  - 5 major regional mandis: **Chandigarh (APMC)**, **Panchkula (Haryana)**, **Kalka (Haryana)**, **Patiala (Punjab)**, **Azadpur (Delhi - Terminal)**.
  - 3 pre-configured verified buyers with differentiated demands (Retail Chain, Food Processor, Local Mandi Wholesaler).
  - 10-year historical daily price and arrival series (2014–2024) and pre-computed Chronos-2 forecast distributions.
- Every API endpoint serving demo data must return the response header:
  `X-AgriLink-DataSource: DEMO_BENCHMARK_SEED`
- In the UI, display a clean, reassuring badge:
  `🟢 Demo Mode Active — Using Verified Benchmark Data`

---

## 9. Common Traps & Anti-Patterns to Avoid

| Anti-Pattern | Why It Fails | AGRI-LINK Correct Pattern |
| :--- | :--- | :--- |
| **Optimizing Headline Price** | Mandi A offers ₹30/kg (100 km away) while Mandi B offers ₹28/kg (10 km away). Recommending Mandi A loses money due to freight. | Always optimize **Net Realizable Value (NRV)** after freight, loading, storage, and market fees. |
| **Point Forecast (Single Scalar)** | Commodity markets have fat tails. A single number ₹32.00 implies false precision. | Forecast as a **probability distribution** (P10, P50, P90 quantiles) to evaluate downside risk. |
| **Ignoring Moisture & Quality** | A farmer with 20% moisture soybean cannot sell at the quoted FAQ price (12% standard). | Apply explicit **quality & moisture assay discount formulas**. |
| **Assuming Infinite Storage** | Perishable crops (Tomato) decay rapidly under non-refrigerated conditions. | Apply **non-linear crop perishability decay curves** ($e^{-\delta t}$) constrained by storage type. |
| **Synchronous File Reads in Routes** | Calling `pd.read_csv()` in route handlers blocks the event loop and crashes under concurrent load. | Store data in **PostgreSQL / TimescaleDB**, query via async SQLAlchemy, and cache hot records in **Redis**. |
| **Unexplained Black-Box Scores** | Giving a buyer an opaque score of "84/100" without explanation frustrates farmers. | Provide **transparent, additive justification bullets** (*Why this buyer?*). |
| **LLM Hallucinating Prices** | Asking an LLM "What will onion prices be next week?" causes catastrophic hallucination. | Let **Chronos-2** compute the numbers; use the LLM solely to summarize news, explain risks, and draft advisories. |

---

## 10. Agent Execution Checklist

Before concluding any development turn, verify:
- [ ] No code or text was copied from `references/`.
- [ ] No deprecated Python/Pandas functions (`np.float`, `.append()`, `.mad()`) were introduced.
- [ ] Every new endpoint has a typed Pydantic request and response schema.
- [ ] Business calculations (NRV, Spoilage, MAD) are covered by automated unit tests.
- [ ] Demo mode functions end-to-end without external internet or live third-party API keys.
- [ ] Code compiles cleanly with zero linter errors (`ruff check .`).
- [ ] All numerical recommendations provide clear, explainable justification text.

---
*End of AGENTS.md. Strictly adhere to these guidelines across all implementation phases.*
