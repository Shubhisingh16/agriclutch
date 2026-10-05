# AgriClutch Logistics & Physical Pathway Feasibility Engine

> **Subsystem**: Step 13 — Logistics + Storage + Perishability Feasibility Engine  
> **Problem Statement**: SIH26132 — Strengthening Market Linkages and Price Discovery for Farmers  
> **Platform Vision**: An AI-powered agricultural market intelligence and decision-support platform answering:  
> *"What physically happens to the produce between the farmer's current location and each potential buyer/market over time?"*

---

## 1. Prime Directives & Scope Boundaries

The Logistics Feasibility Engine evaluates the physical and operational realities of moving produce from the farm gate to regional APMC yards, storage warehouses, and commercial procurement destinations.

### Non-Negotiable Operational Directives:
1. **Strictly Non-Normative**: Step 13 outputs purely descriptive physical profiles, duration estimates, itemized friction costs, and constraint evaluations.
2. **Zero Recommendation Leakage**: Step 13 **NEVER** outputs `SELL`, `HOLD`, `BUY`, `WINNER`, `BEST MARKET`, `RECOMMENDED BUYER`, `"optimal"`, ranking integers, or superiority badges. Decision optimization belongs exclusively to **Step 14**.
3. **No Distance Fabrication**: Distances are either explicitly documented road distances (`DistanceType.ROAD_DISTANCE`) or great-circle geodesic approximations (`DistanceType.STRAIGHT_LINE_DISTANCE`). If coordinates are absent, distance is `UNKNOWN_DISTANCE` and fails closed to `INSUFFICIENT_DATA`.
4. **No Speed Fabrication**: Vehicle speed is never assumed without explicit configuration. Missing speed yields `TransitTimeStatus.TRANSIT_TIME_UNAVAILABLE`.
5. **Decoupled NRV Adapter**: Step 13 outputs adapt cleanly into Step 11 (`LogisticsNRVAdapter`) without altering locked Step 10–12 engines.

---

## 2. Mathematical Formulations

### 2.1 Great-Circle Spherical Geodesic Distance (Haversine Formula)

The spherical distance $d$ across the earth's surface between origin $(\varphi_1, \lambda_1)$ and destination $(\varphi_2, \lambda_2)$ is:

$$\Delta\varphi = \varphi_2 - \varphi_1, \quad \Delta\lambda = \lambda_2 - \lambda_1$$

$$a = \sin^2\left(\frac{\Delta\varphi}{2}\right) + \cos(\varphi_1)\cos(\varphi_2)\sin^2\left(\frac{\Delta\lambda}{2}\right)$$

$$c = 2 \cdot \operatorname{atan2}\left(\sqrt{a}, \sqrt{1 - a}\right)$$

$$d_{\text{geodesic}} = R \cdot c$$

where mean earth radius $R = 6371.0 \text{ km}$.

### 2.2 Route Distance & Circuity Factor Modeling

When documented road distance is available:
$$d_{\text{route}} = d_{\text{road}} \quad (\text{DistanceType.ROAD\_DISTANCE})$$

When only geographic coordinates are known:
$$d_{\text{straight}} = d_{\text{geodesic}} \quad (\text{DistanceType.STRAIGHT\_LINE\_DISTANCE})$$
$$d_{\text{estimated\_route}} = d_{\text{straight}} \times f_{\text{circuity}} \quad (\text{DistanceType.ESTIMATED\_ROUTE\_DISTANCE})$$

Where $f_{\text{circuity}} = 1.25$ is an explicitly **CONFIGURED ASSUMPTION** (`provenance_status = "CONFIGURED"`). It is disclosed as an estimated model approximation and never presented as observed road mileage.

### 2.3 Transit Duration Determination

$$\text{duration}_{\text{hours}} = \begin{cases}
t_{\text{observed}} & \text{if documented in empirical transit log} \\
\frac{d}{v_{\text{configured}}} & \text{if distance } d \text{ and cruise speed } v > 0 \text{ configured} \\
\text{null} & \text{otherwise (Status: TRANSIT\_TIME\_UNAVAILABLE)}
\end{cases}$$

### 2.3 Additive Friction Cost Decomposition

Logistics costs are strictly additive and transparent:

$$C_{\text{logistics}} = C_{\text{transport}} + C_{\text{loading}} + C_{\text{unloading}} + C_{\text{handling}} + C_{\text{other}}$$

where:
$$C_{\text{transport}} = C_{\text{base}} + \begin{cases}
r_{\text{km-tonne}} \times d \times \frac{Q}{1000} & \text{if tonne-km rate configured} \\
r_{\text{km}} \times d & \text{if vehicle-km rate configured} \\
0 & \text{otherwise}
\end{cases}$$

$$C_{\text{loading}} = r_{\text{load/qtl}} \times \frac{Q}{100}, \quad C_{\text{unloading}} = r_{\text{unload/qtl}} \times \frac{Q}{100}$$

---

## 3. Standard Vehicle Archetypes (Synthetic Demo Fixtures)

All vehicles are explicitly labeled with `provenance_status = "DEMO"` and `is_demo = true`:

| Vehicle Identifier | Display Name | Capacity | Base Dispatch | Haulage Rate | Cruise Speed | Climate Control |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `DEMO_TRACTOR_TROLLEY` | Tractor Trolley | 1,500 kg | ₹500 | ₹18/km | 25 km/h | No |
| `DEMO_LCV_TATA_407` | Light Commercial Vehicle (LCV) | 2,500 kg | ₹800 | ₹25/km | 45 km/h | No |
| `DEMO_HEAVY_TRUCK_10T` | Medium/Heavy Commercial Truck | 10,000 kg | ₹2,500 | ₹55/km | 40 km/h | No |
| `DEMO_REEFER_CONTAINER` | Refrigerated Multi-Axle Reefer | 8,000 kg | ₹3,500 | ₹75/km | 50 km/h | Yes (Controlled) |

---

## 4. Multi-Stage Physical Pathways

Step 13 composes 4 standardized physical pathways:

- **Scenario A (Direct Farm Gate $\to$ Buyer)**: Farm loading $\to$ direct transit $\to$ buyer unloading. Storage duration = 0.
- **Scenario B (Farm Gate $\to$ Local Storage $\to$ Buyer)**: Farm loading $\to$ storage entry $\to$ holding for $D$ days $\to$ storage dispatch $\to$ delivery to buyer.
- **Scenario C (Farm Gate $\to$ APMC Mandi)**: Farm loading $\to$ road haulage to regional APMC yard $\to$ yard unloading & commission sorting. Storage duration = 0.
- **Scenario D (Farm Gate $\to$ Cold Storage $\to$ Terminal Market)**: Farm loading $\to$ cold store intake $\to$ temperature-controlled holding for $D$ days $\to$ cold chain reefer transit $\to$ terminal market delivery.

> [!WARNING]
> **Demo Scenario Disclosure**: All pre-compiled routes (Mohali Farmgate, Chandigarh APMC, Delhi Azadpur, etc.) are synthetic demo fixtures (`is_demo = true`, `provenance_status = "DEMO"`). They are provided for testing multi-stage arithmetic and do **NOT** represent live GPS telemetry or empirical commercial haulage contracts.

---

## 5. Clean-Room Architecture Compliance

In accordance with `AGENTS.md`:
- Zero code copied from academic reference repositories.
- Zero deprecated Pandas or NumPy methods.
- Every route and scenario includes complete provenance metadata.
- Step 13 strictly avoids normative selections; Step 14 integrates these factual outputs for decision solving.
