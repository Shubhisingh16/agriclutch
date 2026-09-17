# AgriClutch: Time-Series Model Evaluation & Benchmarking Protocol

> **Document**: Evaluation Methodology & Benchmark Specification  
> **Subsystem**: AgriClutch Forecasting Intelligence Engine (STEP 10)  
> **Problem Statement**: SIH26132 — Strengthening Market Linkages and Price Discovery for Farmers  
> **Version**: 1.0.0  

---

## 1. Rolling-Origin Temporal Cross-Validation

Standard $k$-fold cross-validation or random train/test splitting is strictly invalid for time series because it shuffles temporal order, leaking future price information into training folds.

AgriClutch implements **Rolling-Origin (Walk-Forward) Temporal Evaluation**:

```
Series: [-----------------------------------------------------------------]
Fold 1: [--- Train Window T1 ---] [ Test Window H ]
Fold 2: [----- Train Window T2 -----] [ Test Window H ]
Fold 3: [------- Train Window T3 -------] [ Test Window H ]
Fold K: [--------- Train Window Tk ---------] [ Test Window H ]
```

### Protocol Mechanics:
1. **Initial Training Window**: Minimum $N_{\text{init}} = 30$ trading sessions.
2. **Forecast Horizon**: $H \in \{7, 14, 28\}$ days.
3. **Roll Step**: Step size $S \in \{7, 14\}$ sessions forward.
4. **Strict Isolation**: At each origin $T_k$, models are calibrated solely on $y_{1:T_k}$. Forecasts $\hat{y}_{T_k+1:T_k+H}$ are generated and compared strictly against ground-truth held-out observations $y_{T_k+1:T_k+H}$.

---

## 2. Quantitative Evaluation Metrics

AgriClutch evaluates both **point accuracy** (central tendency) and **probabilistic calibration** (uncertainty).

### 2.1 Point Forecast Metrics (P50 Median)

1. **Mean Absolute Error (MAE)**:
   $$\text{MAE} = \frac{1}{H} \sum_{h=1}^H |y_{t+h} - \hat{y}_{t+h}|$$
   Measures expected absolute error in canonical units ($\text{INR/kg}$).

2. **Root Mean Squared Error (RMSE)**:
   $$\text{RMSE} = \sqrt{\frac{1}{H} \sum_{h=1}^H (y_{t+h} - \hat{y}_{t+h})^2}$$
   Penalizes large outlier misses heavily.

3. **Symmetric Mean Absolute Percentage Error (sMAPE)**:
   $$\text{sMAPE} = \frac{100\%}{H} \sum_{h=1}^H \frac{2 |y_{t+h} - \hat{y}_{t+h}|}{|y_{t+h}| + |\hat{y}_{t+h}|}$$
   Bounded in $[0\%, 200\%]$, symmetric to over- and under-forecasting.

4. **Mean Absolute Scaled Error (MASE)**:
   $$\text{MASE} = \frac{\text{MAE}}{\frac{1}{N-1} \sum_{i=2}^N |y_i - y_{i-1}|}$$
   Compares the model's MAE against the in-sample 1-step Naive persistence forecast.
   - $\text{MASE} < 1.0$: Model outperforms naive random walk.
   - $\text{MASE} > 1.0$: Model performs worse than simply copying yesterday's price.

### 2.2 Probabilistic / Quantile Metrics

1. **Pinball Loss (Quantile Loss)**:
   For target quantile $q \in (0, 1)$ and prediction $\hat{y}_q$:
   $$\mathcal{L}_q(y, \hat{y}_q) = \begin{cases} q(y - \hat{y}_q) & \text{if } y \ge \hat{y}_q \\ (1-q)(\hat{y}_q - y) & \text{if } y < \hat{y}_q \end{cases}$$
   Evaluates calibration of asymmetric risk bounds.

2. **Weighted Quantile Loss (WQL)**:
   Aggregated across canonical quantiles $Q = \{0.1, 0.2, 0.5, 0.8, 0.9\}$:
   $$\text{WQL} = \frac{2 \sum_{q \in Q} \sum_{h=1}^H \mathcal{L}_q(y_{t+h}, \hat{y}_{q, t+h})}{|Q| \sum_{h=1}^H |y_{t+h}|}$$

3. **Empirical Prediction Interval Coverage (PIC)**:
   Percentage of held-out actual prices that fall within the $[P_{10}, P_{90}]$ 80% interval:
   $$\text{PIC}_{80} = \frac{1}{H} \sum_{h=1}^H \mathbb{I}(P_{10}(t+h) \le y_{t+h} \le P_{90}(t+h))$$
   A well-calibrated 80% interval should achieve $\text{PIC}_{80} \approx 0.80$.

---

## 3. Evaluated Model Benchmarks

AgriClutch evaluates 5 distinct modeling paradigms under identical temporal splits:

| Model ID | Architecture | Strengths & Trade-offs |
| :--- | :--- | :--- |
| **`naive`** | Persistence ($y_{t+h} = y_t$) with historical residual variance | Foundational baseline; zero training cost; non-stationary benchmark. |
| **`seasonal_naive`** | Seasonal lag repeat ($y_{t+h} = y_{t+h-m}$, $m=7$) | Captures weekly APMC auction cycles; requires $\ge 14$ sessions. |
| **`statistical`** | Holt Exponential Smoothing (Level + Damped Additive Trend) | Captures local momentum; fast closed-form optimization. |
| **`gradient_boosting`** | Multi-quantile `HistGradientBoostingRegressor` | Non-linear regression on 28-day lags and rolling statistics. |
| **`chronos-2`** | Amazon Chronos-2 Transformer (120M parameters) | Deep in-context sequence learning; zero-shot probabilistic distributions. |

---

## 4. Anti-Bias & No "Winner Badge" Policy

AgriClutch adheres to strict scientific objectivity:
- **No Preset Superiority**: Foundation models like Chronos-2 are **not** assumed to beat simple baselines. In erratic spot markets, Naive or Holt models frequently achieve lower MAE than complex neural networks.
- **No Arbitrary Ranking**: Evaluation reports display actual measured numbers. The system never injects subjective "Best Choice" or "Winner" tags.
- **Auditable Results**: All metrics are calculated by executable code on real held-out data.

---
*Authoritative Documentation: docs/FORECASTING_EVALUATION.md*
