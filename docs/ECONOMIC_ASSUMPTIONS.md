# AgriClutch Economic Assumptions & Parameter Catalog

> **Problem Statement**: SIH26132 — Strengthening Market Linkages and Price Discovery for Farmers  
> **Subsystem**: Decision Intelligence & Net Realizable Value (NRV) Engine (Step 11)  
> **Status**: Verified Clean-Room Parameter Inventory  

---

## 1. Governance & Non-Negotiable Rules

1. **Explicit Provenance on Every Parameter**: No cost, loss rate, or price adjustment may exist as an anonymous literal in code. Every parameter must be backed by a structured entity with provenance metadata (`status`, `source`, `effective_date`, `is_demo`).
2. **Provenance Status Hierarchy**:
   - `EMPIRICAL`: Observed from authorized market receipts, weighbridge slips, or APMC transaction logs.
   - `OFFICIAL`: Sourced directly from state agricultural marketing board tariff gazettes or APMC regulatory schedules.
   - `RESEARCH`: Derived from accredited agricultural research institutes (e.g., ICAR-CIPHET, DAC&FW).
   - `CONFIGURED`: User- or enterprise-configured parameters passed at runtime.
   - `DEMO`: Clean-room benchmark assumptions provided strictly for offline demo testing.
   - `UNAVAILABLE`: Explicitly marked absent; fails closed rather than fabricating values.
3. **No False Claims**: When running in demo mode, all assumptions are flagged `DEMO` and rendered in the UI with `DEMO ASSUMPTION` badges. They must never be described as live, official, verified, or guaranteed market rates.

---

## 2. Benchmark Economic Parameters Catalog

The following benchmark parameters populate the demo fixture database (`backend/app/db/seeds/economic_demo_seed_data.py`) for the Northern Indian horticultural corridor (Punjab, Haryana, Chandigarh, Delhi Azadpur).

### 2.1 Logistics & Freight Tariffs

| Parameter Key | Description | Default Value | Unit | Provenance Status | Source / Reference |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `freight_base_dispatch_fee` | Base vehicle dispatch / booking fee | `250.0` | `INR` | `DEMO` | Transport Operator Regional Survey 2024 (Demo) |
| `freight_rate_short_haul` | Freight rate per km per tonne ($\le 100$ km, LCV) | `4.50` | `INR_PER_KM_TONNE` | `DEMO` | Northern Tri-City Goods Transport Benchmark |
| `freight_rate_long_haul` | Freight rate per km per tonne ($> 100$ km, Medium Truck) | `3.20` | `INR_PER_KM_TONNE` | `DEMO` | Interstate Corridor Haulage Tariff (Demo) |

#### Default Road Transit Distances (from Chandigarh Production Centroid)
- Chandigarh APMC (`mandi_ch_49`): **8.0 km**
- Panchkula APMC (`mandi_hr_01`): **12.0 km**
- Kalka APMC (`mandi_hr_02`): **28.0 km**
- Patiala APMC (`mandi_pb_12`): **72.0 km**
- Azadpur Delhi Terminal (`mandi_dl_164`): **245.0 km**

---

### 2.2 Storage Tariffs

| Parameter Key | Description | Default Value | Unit | Provenance Status | Source / Reference |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `storage_ambient_daily_rate` | On-farm ventilated ambient shed rental | `0.00` | `INR_PER_KG_DAY` | `DEMO` | On-farm owned infrastructure (fixed asset) |
| `storage_cold_daily_rate` | Commercial temperature-controlled cold store | `0.20` | `INR_PER_KG_DAY` | `DEMO` | WDRA Accredited Cold Storage Tariff Benchmark |

---

### 2.3 Physical Handling & Yard Fees

| Parameter Key | Description | Default Value | Unit | Provenance Status | Source / Reference |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `handling_loading_rate` | Farm-gate vehicle loading labor | `0.30` | `INR_PER_KG` | `DEMO` | Labor Union Mandi Schedule Benchmark |
| `handling_unloading_rate` | APMC mandi yard unloading / stacking labor | `0.30` | `INR_PER_KG` | `DEMO` | APMC Licensed Porterage Benchmark |
| `handling_packaging_weighment` | Crating/bagging amortization + certified weighment | `0.40` | `INR_PER_KG` | `DEMO` | Standard Horticultural Packing Benchmark |
| `loss_culling_disposal_fee` | Spoilage sorting and municipal disposal fee | `0.10` | `INR_PER_KG` | `DEMO` | APMC Sanitation & Sorting Benchmark |

---

### 2.4 Statutory APMC Mandi Market Cess Rates ($\mu_{\text{APMC}}$)

| Market ID | Mandi Name | State / UT | Statutory Rate ($\mu$) | Provenance Status | Regulatory Basis |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `mandi_ch_49` | Chandigarh APMC | Chandigarh | `0.015` (1.50%) | `DEMO` | Punjab Agricultural Produce Markets Act (UT Extension) |
| `mandi_hr_01` | Panchkula | Haryana | `0.020` (2.00%) | `DEMO` | Haryana State Agricultural Marketing Board (HSAMB) Schedule |
| `mandi_hr_02` | Kalka | Haryana | `0.020` (2.00%) | `DEMO` | Haryana State Agricultural Marketing Board (HSAMB) Schedule |
| `mandi_pb_12` | Patiala | Punjab | `0.020` (2.00%) | `DEMO` | Punjab Mandi Board Market Development Cess Schedule |
| `mandi_dl_164` | Azadpur Terminal | Delhi | `0.010` (1.00%) | `DEMO` | Delhi Agricultural Marketing Board (DAMB) Notification |

---

### 2.5 Crop Perishability Decay Parameters ($\delta_{\text{decay}}$ in $\text{day}^{-1}$)

The decay rate $\delta_{\text{decay}}$ governs the exponential usable quantity curve:
$$Q_{\text{effective}}(t) = Q_0 \cdot e^{-\delta_{\text{decay}} \cdot t}$$

| Crop | Storage Type | Parameter Value ($\delta$) | Unit | Source | Source Reference | Effective Date | Provenance Status | Validity Range | Justification & Audit Classification |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `tomato` | `ambient` | `0.045` | `day^-1` | ICAR-CIPHET | Post-Harvest Losses Benchmark (2022) | 2024-09-15 | `DEMO` | 0 to 5 days | Rapid transpiration, softening, microbial breakdown (28–35°C).<br>**DEMO ASSUMPTION — NOT EMPIRICALLY VALIDATED** |
| `tomato` | `cold_storage` | `0.008` | `day^-1` | National Horticulture Board (NHB) | Technical Standards for Cold Storage (2021) | 2024-09-15 | `DEMO` | 0 to 21 days | Controlled temperature (10–13°C, 90–95% RH) suppresses ethylene.<br>**DEMO ASSUMPTION — NOT EMPIRICALLY VALIDATED** |
| `onion` | `ambient` | `0.008` | `day^-1` | NHRDF | Guidelines for Post-Harvest Management of Onion (2023) | 2024-09-15 | `DEMO` | 0 to 60 days | Well-cured Rabi onion in ventilated storage; desiccation losses.<br>**DEMO ASSUMPTION — NOT EMPIRICALLY VALIDATED** |
| `onion` | `cold_storage` | `0.002` | `day^-1` | NHRDF | Scientific Cold Storage Protocol for Onion (2022) | 2024-09-15 | `DEMO` | 0 to 180 days | Controlled cold storage (0–2°C, 65–70% RH) prevents dormancy break.<br>**DEMO ASSUMPTION — NOT EMPIRICALLY VALIDATED** |
| `potato` | `ambient` | `0.004` | `day^-1` | ICAR-CPRI | Technical Bulletin on Potato Post-Harvest Management (2022) | 2024-09-15 | `DEMO` | 0 to 45 days | Tuber weight loss from respiration and sprouting after dormancy release.<br>**DEMO ASSUMPTION — NOT EMPIRICALLY VALIDATED** |
| `potato` | `cold_storage` | `0.0008` | `day^-1` | ICAR-CPRI | Cold Chain Storage Standard for Processing Potato (2023) | 2024-09-15 | `DEMO` | 0 to 240 days | Modern CIPC-treated cold holding (8–10°C) enables multi-month storage.<br>**DEMO ASSUMPTION — NOT EMPIRICALLY VALIDATED** |

> [!IMPORTANT]
> **Loss Parameter Provenance Audit Sign-Off:**
> Because exact batch-level physical assay data has not been calibrated for live production lots, all six perishability decay coefficients are strictly retained with `provenance_status = "DEMO"` and clearly labeled **`DEMO ASSUMPTION — NOT EMPIRICALLY VALIDATED`**.
> No replacement values are fabricated or invented. Any uncalibrated crop or storage combination fails closed with `LOSS_MODEL_UNAVAILABLE` (HTTP 503).


---

### 2.6 Quality Grade Adjustments

| Grade | Adjustment Multiplier | Premium / Discount | Provenance Status | Justification |
| :--- | :--- | :--- | :--- | :--- |
| `Grade_A` | `1.08` | +8% Premium | `DEMO` | Uniform size, high firmness, export/retail standard |
| `FAQ` | `1.00` | Baseline (0%) | `DEMO` | Fair Average Quality (APMC modal rate standard) |
| `Grade_B` | `0.85` | -15% Discount | `DEMO` | Irregular size, minor skin blemishes, processing grade |

#### Ambient Holding Quality Downgrade
If perishable produce is held under ambient conditions past the safe holding threshold ($T_{\text{ambient\_max}}$), an additional $15\%$ downgrade penalty ($\kappa_{\text{downgrade}} = 0.15$) is applied to reflect softening and cosmetic deterioration.
