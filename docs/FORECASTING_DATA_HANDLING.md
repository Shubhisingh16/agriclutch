# AgriClutch: Time-Series Data Handling & Temporal Integrity Protocol

> **Document**: Engineering Specification & Data Quality Protocol  
> **Subsystem**: AgriClutch Forecasting Intelligence Engine (STEP 10)  
> **Problem Statement**: SIH26132 — Strengthening Market Linkages and Price Discovery for Farmers  
> **Version**: 1.0.0  

---

## 1. Trading Sessions vs. Calendar Days

Physical agricultural mandis do not trade 365 days continuously. Mandi operations feature regular non-trading days (Sunday weekly closures, regional holidays, APMC strikes).

AgriClutch explicitly distinguishes between two categories of missing calendar dates:
1. **Expected Calendar Gaps**:
   - Friday $\to$ Monday intervals (weekend APMC closures).
   - Gazetted national or state holidays (e.g. Republic Day, Diwali).
   - These are natural gaps in trading activity where no physical auctions took place.
2. **Unexpected Missing Observations**:
   - Consecutive regular trading weekdays (e.g., Tuesday missing between Monday and Wednesday without an APMC holiday).
   - These represent reporting gaps, recording delays, or missing data submissions.

---

## 2. Zero Silent Interpolation Policy

A common failure mode in naive machine learning pipelines is silently interpolating or forward-filling missing commodity prices (e.g., calling `df.interpolate()` or `df.ffill()`).

### Why Silent Imputation Fails in Agriculture:
- Mandi prices reflect real supply-demand auction clearing. If a mandi closed for 3 days due to flash floods, the subsequent reopening price may spike by 40%. Imputing a smooth linear ramp fabricates artificial stability that never existed in the physical market.
- Forward-filling underestimates price volatility and produces artificially tight prediction intervals.

### The AgriClutch Protocol:
- **Raw Physical Sequence**: Time series models operate on the actual sequential trading sessions:
  $$(y_1, t_1), (y_2, t_2), \dots, (y_N, t_N) \quad \text{where } t_i < t_{i+1}$$
- **Explicit Gap Logging**: If calendar gaps exceed 3 business days, the dataset pipeline flags the interval:
  ```python
  {"gap_start": "2024-08-12", "gap_end": "2024-08-16", "days_missing": 4, "type": "UNEXPECTED_REPORTING_GAP"}
  ```
- **Auditable Provenance**: Every observation in the context window preserves its `source_record_id` and raw observation timestamp.

---

## 3. Data Sufficiency Gate (`INSUFFICIENT_HISTORY`)

### Rationale:
Time-series forecasting models, particularly autoregressive transformers and gradient-boosted trees with 28-day lag features, require sufficient historical context to establish baseline price levels, volatility scales, and local trend directions. Running inference on sparse series (e.g., 5 observations) produces wild, uncalibrated distributions.

### Policy & Defaults:
- **Default Minimum History Threshold**: **30 valid trading sessions** ($\sim 6$ to 8 calendar weeks of trading activity).
- **Seasonal Models**: Require $\ge 2 \times m$ observations (where $m=7$ requires $\ge 14$ sessions).
- **Configurable Control**: The threshold is defined as `MIN_OBSERVATIONS_THRESHOLD = 30` in application settings.

### Failure Contract:
If a requested commodity-mandi pair contains fewer than 30 observations, the pipeline halts immediately and emits a typed error:
```json
{
  "status": "INSUFFICIENT_HISTORY",
  "commodity_id": "tomato",
  "market_id": "mandi_xyz",
  "available_records": 14,
  "required_minimum": 30,
  "detail": "Historical trading history (14 sessions) is insufficient for reliable probabilistic forecasting. Minimum 30 sessions required."
}
```
The platform **never** outputs a fake forecast to mask data scarcity.

---

## 4. Strict Temporal Integrity & Leakage Prevention

In time-series forecasting, data leakage can silently invalidate benchmarks. AgriClutch enforces strict temporal firewalls:

1. **Origin Date Cutoff ($t_0$)**:
   - At forecast origin $t_0$, only information with timestamp $t \le t_0$ is accessible.
   - Any feature requiring future information ($t > t_0$) is strictly prohibited.
2. **Shifted Feature Construction**:
   - Rolling statistics (e.g. 7-day rolling mean, 14-day rolling std) are computed strictly on past observations:
     $$\bar{y}_{t}^{(7)} = \frac{1}{7} \sum_{k=1}^{7} y_{t-k}$$
     Notice that the current observation $y_t$ is not included in the feature vector for predicting $y_t$, and future values are inaccessible.
3. **Walk-Forward Preprocessing**:
   - Min-max scaling, standardization, or residual standard deviations are estimated **only** within the training window of the current rolling fold.

---
*Authoritative Documentation: docs/FORECASTING_DATA_HANDLING.md*
