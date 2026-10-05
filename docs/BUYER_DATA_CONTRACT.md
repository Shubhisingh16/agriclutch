# AgriClutch: Buyer Intelligence Data Contracts & API Schema

> **Document Type**: Technical Interface Specification  
> **Step**: Step 12 — Buyer Matching & Demand Aggregation Engine  
> **API Version**: `v1`  
> **Protocol**: REST over JSON / Async FastAPI  

---

## 1. Domain Enumerations

### 1.1 `BuyerType`
```json
[
  "wholesaler",
  "processor",
  "retailer",
  "institutional_buyer",
  "exporter",
  "fpo",
  "cooperative",
  "aggregator",
  "trader"
]
```

### 1.2 `DeliveryMode`
- `FARMGATE_PICKUP`: Buyer collects produce at farmer's farmgate location.
- `BUYER_PREMISES`: Farmer transports produce to buyer warehouse or facility.
- `MANDI_DELIVERY`: Delivery at designated APMC yard or terminal market.
- `UNAVAILABLE`: Unspecified delivery logistics.

### 1.3 `PriceBasis`
- `FIXED_QUOTE`: Firm quote offered by buyer (e.g. ₹28.50/kg).
- `APMC_INDEXED`: Price indexed to local APMC modal rate (e.g., APMC + 5%).
- `NEGOTIABLE`: Open for bilateral settlement.
- `UNAVAILABLE`: Price basis not published.

### 1.4 `PaymentTerms`
- `IMMEDIATE_CASH`: Cash on loading / dispatch.
- `ADVANCE_PARTIAL`: Part advance prior to harvest, balance upon delivery.
- `NET_3_DAYS`: Electronic wire within 3 business days of delivery assay.
- `NET_7_DAYS`: Electronic wire within 7 business days.
- `NET_15_DAYS`: Formal institutional trade credit (15 days).
- `UPON_DELIVERY`: Same-day digital clearing upon physical delivery.
- `UNAVAILABLE`: Undisclosed payment terms.

### 1.5 `ProvenanceStatus`
- `EMPIRICAL`: Directly derived from audited trading contracts or APMC records.
- `OFFICIAL`: Sourced from certified statutory entities (e.g., APMC boards, Agmarknet).
- `RESEARCH`: Derived from published academic agricultural literature.
- `CONFIGURED`: User or operator defined parameters.
- `DEMO`: Synthetic or benchmark test fixture for offline demonstration.
- `UNAVAILABLE`: Data point absent; triggers fail-closed behavior.

---

## 2. Core REST Endpoints

### 2.1 Buyer Directory & Profiles
- `GET /api/v1/buyers`
  - **Query Parameters**:
    - `buyer_type` (optional string)
    - `location` (optional string)
    - `commodity_id` (optional string)
    - `data_mode` (optional string: `database` | `demo`)
  - **Response**: Array of `BuyerResponse` objects with `provenance_status` and `is_demo`.

- `GET /api/v1/buyers/{buyer_id}`
  - Returns individual buyer profile. Returns 404 if not found; returns 503 in database mode if database is offline.

- `GET /api/v1/buyers/{buyer_id}/requirements`
  - Returns list of standing procurement requirements (`BuyerRequirementResponse`).

- `GET /api/v1/buyers/{buyer_id}/demand`
  - Returns active spot procurement demands (`BuyerDemandResponse`).

- `GET /api/v1/buyers/{buyer_id}/reliability`
  - Returns audited performance metrics (`ReliabilityResponse`):
    - `status`: `CALCULATED` (if $N \ge 3$) or `INSUFFICIENT_HISTORY` (if $N < 3$)
    - `sample_size`: Number of immutable transactions audited
    - `fulfillment_rate`, `cancellation_rate`, `avg_payment_delay_days`, `dispute_rate`
    - `audit_note`: Explanatory audit commentary

---

### 2.2 Candidate Compatibility Matching
- `POST /api/v1/buyer-matching`
  - **Request Body**: `FarmerSupplyCreate`
    ```json
    {
      "commodity_id": "tomato",
      "variety": "Himsona",
      "quantity_kg": 2500.0,
      "quality_grade": "GRADE_A",
      "available_from": "2026-10-01",
      "available_until": "2026-10-10",
      "origin_location": "Mohali Rural Farmgate",
      "origin_latitude": 30.6942,
      "origin_longitude": 76.7179,
      "storage_available": true,
      "storage_type": "farm_ambient"
    }
    ```
  - **Query Parameters**:
    - `max_distance_km` (optional float)
    - `data_mode` (optional string)
  - **Response**: `MatchingListResponse`
    - `supply_id`: Supply reference identifier
    - `matches_evaluated`: Total buyer requirements compared
    - `compatible_matches_count`: Number of requirements meeting all 6 constraint dimensions
    - `matches`: Array of `CompatibilityMatchResponse` objects, each detailing:
      - `buyer_id`, `buyer_name`, `requirement_id`
      - `is_compatible`: boolean
      - `quantity_status`: `FULLY_SATISFIES` | `EXCEEDS_MAXIMUM_PARTIAL` | `BELOW_MINIMUM`
      - `compatible_quantity_kg`, `unmatched_supply_kg`
      - `temporal_status`: `COMPLETE_OVERLAP` | `PARTIAL_OVERLAP` | `NO_OVERLAP`
      - `overlap_days`: integer
      - `distance_status`: `DISTANCE_DIRECT` | `DISTANCE_UNAVAILABLE`
      - `distance_km`: float or null
      - `explanations`: array of transparent additive justification strings
      - `provenance_status`, `is_demo`

- `GET /api/v1/buyer-matching`
  - Convenience endpoint allowing query-string driven matching for rapid dashboard exploration.

- `GET /api/v1/buyer-matching/sample-supplies`
  - Provides pre-configured benchmark farmer produce lots (e.g., Tomato Grade A 2,500 kg, Tomato Grade B 5,000 kg, Potato Grade A 10,000 kg).
  - **Route Ordering Note**: Registered before dynamic `/{supply_id}` to prevent static path capture.

- `GET /api/v1/buyer-matching/{supply_id}`
  - Fetches matching candidate list for a registered demo or database supply lot by identifier.

---

### 2.3 Regional Demand Aggregation & Concentration
- `GET /api/v1/demand/aggregate`
  - **Query Parameters**: `commodity_id` (required), `region` (optional), `data_mode` (optional)
  - **Response**: `DemandAggregateResponse`
    - `total_demand_kg`: Total volume demanded across all active requirements
    - `buyer_count`: Number of distinct purchasing entities
    - `top_buyer_share_pct`: Market share percentage of the largest buyer
    - `hhi_concentration`: Herfindahl-Hirschman Index value (`provenance_status = CONFIGURED`, adapted from DOJ/FTC Horizontal Merger Guidelines convention)
    - `breakdown_by_quality`: Volume per quality grade mapping
    - `breakdown_by_type`: Volume per buyer channel category mapping
    - `provenance_status`, `is_demo`

- `GET /api/v1/demand/distribution`
  - **Query Parameters**: `commodity_id` (required), `region` (optional), `data_mode` (optional)
  - **Response**: `DemandDistributionResponse`
    - `status`: `VALID` (if $N \ge 3$) or `INSUFFICIENT_DATA` (if $N < 3$, `provenance_status = CONFIGURED` minimum descriptive sample-size gate)
    - `sample_size`: integer
    - `min_kg`, `p10_kg`, `p25_kg`, `p50_kg` (median), `p75_kg`, `p90_kg`, `max_kg`, `mean_kg`
    - `provenance_status`, `is_demo`

---

## 3. Fail-Closed Error Handling & Demo Integrity

| Scenario | HTTP Status | Response Contract |
| :--- | :--- | :--- |
| Database mode selected, database unreachable | `503 Service Unavailable` | `{"detail": "Database unseeded or buyer records unavailable. AgriClutch fails closed."}` |
| Unknown commodity requested in aggregate | `404 Not Found` | `{"detail": "No demand records found for commodity 'xyz'"}` |
| Minimum descriptive sample-size gate < 3 | `200 OK` | `{"status": "INSUFFICIENT_DATA", "min_kg": null, "median_kg": null}` |
| Buyer reliability sample-size gate < 3 | `200 OK` | `{"status": "INSUFFICIENT_HISTORY", "fulfillment_rate": null}` |

**Demo Data Integrity**: In demo mode, all buyer profiles represent **6 synthetic demo buyer entities representing commercial buyer archetypes** (`provenance_status = DEMO`, `is_demo = true`). Synthetic entities are never represented as verified real commercial buyers.
