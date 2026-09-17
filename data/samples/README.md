# AgriClutch: Agricultural Data Samples & Ingestion Guide

> **Notice**: In compliance with the clean-room legal mandate and National Data Sharing & Accessibility Policy (NDSAP), empirical research dumps from unlicensed third-party academic repositories are **not** committed to this repository.  
> This directory provides specifications and synthetic test fixtures for local testing and validation.

---

## 1. Supported Input Formats

AgriClutch's data pipeline supports two standard CSV input profiles:

### 1.1 Canonical AgriClutch Format (`format: canonical`)
Recommended format for pre-processed or standardized data feeds:

| Column Name | Required | Type | Description / Example |
| :--- | :--- | :--- | :--- |
| `record_date` | **Yes** | ISO Date (`YYYY-MM-DD`) | Trading date, e.g. `2024-09-15` |
| `source_market_id` | **Yes** | String | External market name, e.g. `Chandigarh` |
| `source_commodity_id` | **Yes** | String | Commodity name, e.g. `Tomato` |
| `variety` | No | String | Cultivar (defaults to `Common`) |
| `grade` | No | String | Commercial grade (defaults to `FAQ`) |
| `original_modal_price` | **Yes** | Positive Float | Dominant traded price |
| `original_min_price` | No | Positive Float | Minimum traded price ($\le \text{modal}$) |
| `original_max_price` | No | Positive Float | Maximum traded price ($\ge \text{modal}$) |
| `original_price_unit` | No | String | E.g. `Rs/Quintal` or `INR_PER_KG` |
| `arrival_tonnes` | No | Non-negative Float | Volume in metric tonnes, e.g. `45.5` |
| `source_record_id` | No | String | Upstream unique row identifier |

---

### 1.2 Raw Agmarknet Tabular Dump Format (`format: agmarknet`)
Compatible with official Government of India Agmarknet daily bulletin reports:

| Agmarknet Column | Canonical Target | Expected Units |
| :--- | :--- | :--- |
| `Arrival_Date` | `record_date` | `DD/MM/YYYY` or `YYYY-MM-DD` |
| `Market` | `source_market_id` | Mandi name (supports grouped forward-fill) |
| `Commodity` | `source_commodity_id` | Crop name (e.g. `Tomato`, `Onion`) |
| `Variety` | `variety` | Cultivar name |
| `Grade` | `grade` | E.g. `FAQ`, `Medium` |
| `Min Price` | `original_min_price` | ₹ / Quintal |
| `Max Price` | `original_max_price` | ₹ / Quintal |
| `Modal Price` | `original_modal_price` | ₹ / Quintal |
| `Arrivals` | `arrival_tonnes` | Tonnes |
| `Unit of Price` | `original_price_unit` | `Rs/Quintal` |
| `Unit of Arrivals` | `original_arrival_unit` | `Tonnes` |

---

## 2. Placing an Authorized Dataset Locally

To ingest an authorized empirical dataset obtained from official portals (e.g., [data.gov.in](https://data.gov.in) or [agmarknet.gov.in](https://agmarknet.gov.in)):

1. Download the official CSV export.
2. Save the file into your local data directory, for example:
   ```text
   data/local/agmarknet_punjab_2024.csv
   ```
3. Verify file permissions and check that column headers match either the **Canonical** or **Agmarknet** format.
4. Run the ingestion pipeline in `--dry-run` mode first to inspect the data quality report before writing to the database.

---

## 3. Ingestion CLI Usage

The AgriClutch pipeline CLI validates and processes datasets from the terminal:

### Dry-Run Validation Only (No Database Write)
```bash
python -m pipeline.cli --input data/samples/synthetic_test_mandi_prices.csv --format canonical --dry-run
```

### Full Ingestion into Local Database
```bash
python -m pipeline.cli --input data/local/agmarknet_punjab_2024.csv --source AGMARKNET --format agmarknet
```

### Saving Validation Report to JSON
```bash
python -m pipeline.cli --input data/samples/synthetic_test_mandi_prices.csv --output-report report.json --dry-run
```

---

## 4. Synthetic Test Fixtures

The accompanying file `synthetic_test_mandi_prices.csv` is a **100% synthetic fixture** generated exclusively for automated unit testing and developer validation.

> [!WARNING]
> `synthetic_test_mandi_prices.csv` is explicitly labeled:  
> `# SYNTHETIC TEST FIXTURE — NOT REAL MARKET DATA`  
> Never cite or evaluate these values as genuine agricultural market observations.
