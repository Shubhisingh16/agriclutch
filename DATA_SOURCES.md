# AgriClutch: Agricultural Data Sources & Provenance Specification

> **Document Type**: Data Governance, Provenance & Legal Specification  
> **Problem Statement**: SIH26132 — Strengthening Market Linkages and Price Discovery for Farmers  
> **Clean-Room Policy**: Strictly clean-room implementation; zero code copying from reference repositories.

---

## 1. Executive Summary

This document establishes the official data discovery, empirical provenance audit, legal licensing status, and benchmark suitability for all datasets investigated in the agricultural reference repositories (`references/commodity_analysis` and `references/farmers_collective`) as well as official Government of India public data portals.

AgriClutch enforces an uncompromising standard:
- **Zero Data Fabrication**: No synthetic prices or metrics without explicit `is_demo: true` labeling.
- **No False Real-Time Claims**: Clear differentiation between live upstream feeds and static benchmark seeds.
- **Legal & Clean-Room Compliance**: Complete isolation from unlicensed third-party academic code and raw redistributions.

---

## 2. Discovered Datasets & Inventory

The table below catalogs every empirical dataset identified across reference repositories, detailing its source, coverage, size, legal status, and architectural role in AgriClutch.

| Dataset Name | Path / Source | Temporal & Spatial Coverage | Volume & Format | Legal / License Status | AgriClutch Role & Suitability |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **APMC Mandis Master** | `references/commodity_analysis/Data/Information/mandis.csv` | 3,384 mandis across all Indian states/UTs with coordinates & DCA centre IDs | 3,384 rows, CSV (256 KB) | **Unlicensed Repository**; derived from Agmarknet public portal. Cannot redistribute raw repo file directly. | **Benchmark Reference**: Used to construct our canonical Mandi Master fixtures for Chandigarh, Panchkula, Kalka, Patiala, and Azadpur. |
| **Full Mandis Info** | `references/commodity_analysis/Data/Information/FullMandisInfo.csv` | 3,322 mandis mapped to State, District, and Consumer Affairs Price Reporting Centres | 3,322 rows, CSV (245 KB) | **Unlicensed Repository**; derived from Agmarknet & Dept of Consumer Affairs (DCA). | **Cross-Referencing**: Validates APMC code to DCA reporting center joins for retail-wholesale spread analysis. |
| **Calibrated MAD Parameters ($k$)** | `references/commodity_analysis/Data/Information/KforMADs.csv` | Calibrated MAD outlier sensitivity thresholds for Tomato, Onion, Potato across SameMonth, LastMonth, LastYear | 18 rows, CSV (1.2 KB) | **Unlicensed Repository**; academic analytical output (ICTD IIT Delhi). | **Algorithm Design**: Informing our clean-room implementation of multi-horizon MAD anomaly detection thresholds. |
| **Commodity News & Shocks** | `references/commodity_analysis/Data/Information/relevantNews.csv` | ~1,400 news articles (2010–2020) on onion, potato, tomato price spikes, floods, export bans, Doc2Vec vectors | ~1,400 rows, CSV (4.8 MB) | **Unlicensed Repository**; scraped news snippets. Proprietary text aggregations. | **Evaluation Benchmark**: Benchmark test scenarios for What-If market shock simulations (e.g. unseasonal rain, export curbs). |
| **Lead-Lag Mandi Pairs** | `references/commodity_analysis/Data/Information/neighbouringMandiInformation.csv` | Cross-correlation lead-lag pairs (e.g. Azadpur vs Faizabad $r=0.90$, lag=-1) | 48 pairs, CSV (3.4 KB) | **Unlicensed Repository**; analytical output. | **Graph Verification**: Ground-truth baseline to verify our dynamic Pearson cross-correlation graph algorithms. |
| **Agmarknet Raw Wholesale Dumps** | `references/commodity_analysis/Data/Original/{Tomato,Onion,Potato}/*.csv` | 2016–2021 daily modal/min/max prices & arrivals across NCT Delhi, Maharashtra, UP, Karnataka, AP | Hundreds of monthly CSVs (~120 MB total) | **Public Domain Data** (Agmarknet / NDSAP), but packaged in an unlicensed repo with Git LFS corruptions. | **ETL Inspection**: Used to audit raw scrape flaws (missing headers, triplicate rows, non-standard units). |
| **DCA Retail Price Series (FCA)** | `references/commodity_analysis/Data/Original/RetailFCA/*.csv` | 2010-01-01 to 2021-12-09 (4,346 daily CSVs) covering 22 essential commodities across ~180 centers | 4,346 CSVs (~45 MB total) | **Government Open Data** (Department of Consumer Affairs, NDSAP). | **Price Spread Reference**: Informs farmgate-to-retail margin calculations for direct buyer linkages. |
| **DCA Wholesale Price Series (FCA)** | `references/commodity_analysis/Data/Original/WholesaleFCA/*.csv` | 2016-01-01 to 2021-12-09 (2,173 daily CSVs) covering 22 commodities across ~180 centers | 2,173 CSVs (~28 MB total) | **Government Open Data** (Department of Consumer Affairs, NDSAP). | **Wholesale Price Verification**: Provides multi-year macro trends across North Indian consumption centers. |
| **Processed Mandi Series** | `references/commodity_analysis/Data/Processed/*.csv` | Daily price & arrival time series for major states (e.g., `Tomato_NCT of Delhi.csv` with 7,847 rows) | 15 large CSVs (~22 MB) | **Unlicensed Repository**; derived artifacts with Git LFS merge artifacts. | **Pattern Inspection Only**: Examined for interpolation validation; rejected from direct inclusion due to merge artifacts. |
| **Farmer Survey Instruments** | `references/farmers_collective/FormDesign/*.xlsx` | XLSForms for ODK mobile collection in Adilabad & Anantapur (member surveys, crop plans, land size) | 4 Excel files (~350 KB) | **Unlicensed Repository** (ACT4D IIT Delhi / CCD / Google AI4SG). | **Domain Modeling**: Informs our `ProduceLot` and FPO aggregation schema design (crop variety, harvest window, grade). |
| **Trader & Price App Schemas** | `references/farmers_collective/farmers_collective/app/src/main/java/.../*.kt` | Android Room entities (`OdkSubmission.kt`, `IntPriceEntry.kt`, `BuyerDemand.kt`) | Kotlin code files | **All Rights Reserved** (No open-source license). | **Domain Reference**: Validates farmer-to-buyer transaction workflows from first principles. |

---

## 3. Legal, Licensing & Redistribution Rights Assessment

### 3.1 Third-Party Academic Repositories
Neither `references/commodity_analysis` nor `references/farmers_collective` contains an open-source license file (`LICENSE`, `COPYING`, or Apache/MIT/GPL declaration). Under Indian Copyright Act, 1957 and international copyright conventions (Berne Convention):
1. **Default Status**: Code, processed data combinations, and documentation are **All Rights Reserved** by their respective institutional authors (IIT Delhi, ACT4D, Center for Collective Development).
2. **Redistribution Prohibition**: We **CANNOT** commit, copy, or redistribute any code or derived processed datasets from these repositories directly into the AgriClutch repository or production artifacts.
3. **Clean-Room Boundary**: We use these repositories solely for **non-infringing empirical inspection, mathematical formulation discovery, and flaw auditing**. All production code, schemas, and algorithms in AgriClutch are authored completely clean-room from first principles.

### 3.2 Underlying Government of India Public Data
The underlying commodity price and arrival records originate from:
- **Agmarknet Portal** (Directorate of Marketing & Inspection, Ministry of Agriculture & Farmers Welfare, GoI).
- **Price Monitoring Division** (Department of Consumer Affairs, Ministry of Consumer Affairs, Food & Public Distribution, GoI).
- **Data.gov.in** (Open Government Data - OGD Platform India).

Under the **National Data Sharing and Accessibility Policy (NDSAP)**:
- Open government datasets published on data.gov.in are licensed under the **Government Open Data License - India (GODL)**.
- Users are granted a worldwide, royalty-free, non-exclusive license to use, adapt, and build upon the data for commercial and non-commercial purposes, provided appropriate attribution is cited.

---

## 4. Benchmark Dataset Selection for AgriClutch Demo Mode

To ensure our 3-minute hackathon evaluation operates 100% offline, deterministic, and without external network reliance, AgriClutch constructs curated, clean-room **Demo Benchmark Fixtures** under `backend/app/db/seeds/`.

### 4.1 Selected Target Commodities
1. **Tomato (Perishable)**:
   - High perishability decay rate ($\delta = 0.08$ daily at ambient temperature).
   - Extreme price volatility and acute seasonal supply crunches.
2. **Onion (Semi-Perishable)**:
   - Moderate storage capability (30–90 days with ambient aeration).
   - Significant lead-lag correlation between Maharashtra production hubs (Lasalgaon, Nashik) and North Indian consumer mandis.
3. **Potato (Storable)**:
   - High cold storage durability (up to 180 days).
   - High volume, low freight tolerance, sensitive to transport cost per quintal.

### 4.2 Selected Regional Mandi Cluster (Chandigarh Triangle)
We focus on the North Indian agricultural cluster centered on Chandigarh:
- **Chandigarh APMC (Grain/Sabzi Mandi, Sector 26)**: Primary consumption terminal mandi (Mandi Code: 49).
- **Panchkula Mandi (Haryana)**: Satellite suburban mandi, 12 km (Mandi Code: 660).
- **Kalka Mandi (Haryana)**: Foothills local assembly mandi, 28 km.
- **Patiala Mandi (Punjab)**: Major agrarian district assembly hub, 72 km.
- **Azadpur APMC (Delhi)**: National benchmark terminal price-discovery market, 245 km (Mandi Code: 164).

### 4.3 Provenance Metadata Contract
Every record loaded from benchmark seed fixtures is tagged with standardized metadata:
```json
{
  "data_mode": "benchmark_demo",
  "data_source": "DEMO_BENCHMARK_SEED",
  "base_source": "Agmarknet Historical (DMI, GoI)",
  "benchmark_period": "2021-01-01 to 2024-12-31",
  "is_demo": true,
  "is_interpolated": false
}
```

---

## 5. Data Acquisition & Pipeline Ingestion Strategy

```mermaid
flowchart TD
    subgraph Live Production Mode
        APMC_API[data.gov.in Agmarknet API / OGD] -->|Secure HTTPS / API Key| Ingest_Adapter[AgmarknetSourceAdapter]
        DCA_API[DCA Price Monitoring Feed] -->|Daily Batch Poll| DCA_Adapter[DCASourceAdapter]
    end

    subgraph Benchmark Demo Mode
        Seed_Files[Curated Demo Seeds: backend/app/db/seeds/] -->|Zero Network| Seed_Adapter[BenchmarkSeedAdapter]
    end

    subgraph Processing Pipeline
        Ingest_Adapter --> Raw_Validator[DataValidator: Format & Boundary Checks]
        DCA_Adapter --> Raw_Validator
        Seed_Adapter --> Raw_Validator

        Raw_Validator --> Normalizer[DataNormalizer: INR/kg, ISO-8601, TitleCase]
        Normalizer --> Deduplicator[Row Deduplication: (date, mandi, crop)]
        Deduplicator --> Anomaly_MAD[MAD Outlier Detection Engine]
        Anomaly_MAD --> Timescale_DB[(PostgreSQL 16 / TimescaleDB Hypertables)]
    end
```

### 5.1 Pipeline Operational Invariants
1. **Atomic Ingestion**: Batch writes occur within database transactions; partial or malformed batches are rejected with an explicit `DataQualityReport`.
2. **Deterministic Units**: All ingested wholesale prices (quoted in ₹/quintal) are converted immediately to **₹/kg** (`INR_PER_KG`) via exact division by 100.0.
3. **Zero-Price Rejection**: Days reporting modal price $\le 0.0$ are flagged as market closure days (`is_market_closed: true`) rather than free produce.
4. **Header Cleanliness**: Ingestion adapters must automatically detect and discard Git LFS headers and HTML artifact blocks before schema validation.
