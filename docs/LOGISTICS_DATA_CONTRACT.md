# AgriClutch Step 13 Logistics & Storage Data Contract

> **Subsystem**: Step 13 — Logistics + Storage + Perishability Feasibility Engine  
> **Problem Statement**: SIH26132 — Strengthening Market Linkages and Price Discovery for Farmers  
> **Platform Vision**: Canonical data contracts and REST specifications.

---

## 1. REST Endpoints Overview

| Method | Endpoint | Description | Response Model |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/logistics/modes` | List vehicle transport modes | `List[TransportModeResponse]` |
| `POST` | `/api/v1/logistics/distance` | Compute geodesic or road distance | `DistanceCalculationResponse` |
| `POST` | `/api/v1/logistics/evaluate` | Evaluate multi-stage physical pathways | `EvaluatePathwaysResponse` |
| `GET` | `/api/v1/storage/facilities` | List storage warehouse and cold hub facilities | `List[StorageFacilityResponse]` |
| `GET` | `/api/v1/storage/facilities/{id}/availability` | Query real-time capacity and rates | `StorageAvailabilityResponse` |
| `POST` | `/api/v1/storage/evaluate` | Evaluate storage volume and duration feasibility | `StorageFeasibilityResponse` |
| `GET` | `/api/v1/perishability/models` | List documented exponential decay models | `List[PerishabilityModelSpecResponse]` |
| `GET` | `/api/v1/perishability/trajectory` | Calculate day-by-day loss trajectory points | `PerishabilityTrajectoryResponse` |

---

## 2. Mandatory Protocol Headers

Every response from Step 13 endpoints emits:
- `X-AgriClutch-Step: 13`
- `X-AgriClutch-DataSource: DEMO_BENCHMARK_SEED`
- `X-AgriClutch-Data-Mode: DEMO` (or `DATABASE`)

---

## 3. Strict Absence of Normative / Recommendation Fields

In accordance with Hardening Rule 6, the following fields are **strictly prohibited** in Step 13 request/response models:
- `winner`, `is_winner`
- `rank`, `ranking`
- `recommended`, `recommended_action`, `recommended_buyer`, `recommended_market`
- `best`, `is_best`
- `optimal`, `score`, `score_total`
- `sell`, `hold`

Step 13 outputs purely descriptive metrics:
`distance_km`, `transit_duration_hours`, `effective_delivered_quantity_kg`, `final_quality_factor`, `total_pathway_cost`, `feasibility_status`, `economic_status`.
