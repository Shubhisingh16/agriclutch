# AgriClutch: Forecasting Model Specification — Amazon Chronos-2

> **Document**: Technical Specification & Architecture Manual  
> **Subsystem**: AgriClutch Forecasting Intelligence Engine (STEP 10)  
> **Problem Statement**: SIH26132 — Strengthening Market Linkages and Price Discovery for Farmers  
> **Platform**: AgriClutch — AI-Powered Agricultural Market Intelligence & Optimal Selling Platform  
> **Version**: 1.0.0  

---

## 1. Executive Summary

This document specifies the primary foundation model architecture integrated into the **AgriClutch Forecasting Intelligence Engine**: **Amazon Chronos-2**.

Chronos-2 is a pretrained time-series foundation model developed by Amazon Science. In AgriClutch, Chronos-2 is deployed strictly for **zero-shot probabilistic price distribution forecasting**:

$$\mathcal{P}(y_{t+1:t+H} \mid x_{\le t})$$

The engine estimates future price distributions across configurable horizons ($H \in \{7, 14, 28\}$ days) without fine-tuning, generating probabilistic quantiles ($P_{10}, P_{20}, P_{50}, P_{80}, P_{90}$) to quantify market downside and upside risk.

---

## 2. Authoritative Model Specifications (Amazon Science / Hugging Face)

| Specification Parameter | Official Fact / Specification | Source / Verification |
| :--- | :--- | :--- |
| **Model Identifier** | `amazon/chronos-2` | Hugging Face Model Hub / Amazon Science |
| **Release Date** | October 2025 | Amazon Science Technical Report (arXiv:2510.15821) |
| **Architecture Family** | Encoder-only Transformer with Group Attention | Amazon Science / GluonTS |
| **Parameter Count** | ~120 Million Parameters (120M) | Official Model Checkpoint Metadata |
| **Pretrained Modality** | Multi-domain Time-Series Foundation Model | Pretrained on Chronos Benchmark II / GIFT-Eval |
| **Supported Tasks** | Univariate, Multivariate, Covariate-informed | Native Chronos2Pipeline |
| **Max Context Length** | **8,192 time steps** | Model Architecture Limit |
| **Max Model Prediction Horizon**| Arbitrary autoregressive / patch rollout | Universal Rollout Capability |
| **Probabilistic Outputs** | Monte Carlo trajectories / Analytic Quantiles | $P_{10}, P_{20}, P_{50}, P_{80}, P_{90}$ |
| **Supported Dtypes** | `torch.float32`, `torch.bfloat16`, `torch.float16` | PyTorch runtime |
| **Inference Hardware** | CPU (x86_64, ARM64) and GPU (CUDA, ROCm) | Single CPU core ~50ms; A10G >300 series/sec |
| **License** | **Apache 2.0** | Amazon Open Source License |
| **Official Library** | `chronos-forecasting >= 2.0.0` | PyPI package |

---

## 3. Model Capabilities vs. AgriClutch Application Constraints

To ensure scientific honesty and product usability, AgriClutch strictly distinguishes the theoretical limits of Chronos-2 from application-level business constraints:

| Dimension | Native Chronos-2 Capability | AgriClutch Application Policy & Constraint |
| :--- | :--- | :--- |
| **Prediction Horizon** | Unbounded sequence rollout | Configurable short-to-medium horizons: **7, 14, and 28 days**. Longer horizons are disfavored in agricultural spot markets due to weather and policy shocks. |
| **Context Window** | Up to 8,192 observations | Minimum **30 trading sessions** required for forecast generation. Default context window utilizes the most recent **90 to 365 daily sessions**. |
| **Covariates** | Past-only and known future covariates | In Step 10, strictly past-observed price and arrival series are fed. No unverified future covariates (e.g. unverified weather forecasts) are injected. |
| **Fine-Tuning** | Task-specific LoRA / Full fine-tuning | **Zero-shot inference only**. We do not fine-tune weights on small local datasets to prevent catastrophic overfitting or memorization. |
| **Execution Path** | GPU cluster / SageMaker JumpStart | **Local CPU-compatible development path** (`device="cpu"`, `torch_dtype=torch.float32`), with automatic CUDA acceleration if an NVIDIA GPU is detected. |

---

## 4. Probabilistic Quantile Forecasting

Agricultural price series exhibit volatility clustering, extreme supply shocks, and fat-tailed distributions. A single point forecast (e.g., *₹28.50/kg*) provides false certainty to farmers.

Chronos-2 emits probabilistic forecasts sampled across Monte Carlo trajectories, which AgriClutch projects into 5 canonical quantiles:

1. **$P_{10}$ (10th Percentile / Downside Tail)**: 90% probability that market price will exceed this floor. Critical for risk-averse farmers evaluating distress sales.
2. **$P_{20}$ (20th Percentile)**: Lower boundary of the central 60% probability corridor.
3. **$P_{50}$ (Median Forecast)**: The median expectation of future price. Used as the central scenario.
4. **$P_{80}$ (80th Percentile)**: Upper boundary of the central 60% probability corridor.
5. **$P_{90}$ (90th Percentile / Upside Tail)**: 10% probability of exceeding this level under high supply crunch.

### Quantile Monotonicity Invariant:
For every forecast horizon step $h \in \{1 \dots H\}$:
$$P_{10}(t+h) \le P_{20}(t+h) \le P_{50}(t+h) \le P_{80}(t+h) \le P_{90}(t+h)$$

Any model prediction exhibiting quantile crossing is rectified via monotonic isotonic rearrangement before egress.

---

## 5. Critical Anti-Fabrication Protocol

In strict adherence to AgriClutch Prime Directives:

1. **Zero Hallucinated Numbers**: If the Chronos-2 model cannot be loaded (e.g., offline host without pre-cached weights, insufficient memory, or missing runtime), the system **MUST NOT**:
   - Fabricate synthetic numbers and label them as Chronos-2 predictions.
   - Silently run a baseline model (such as Naive or Holt) while mislabeling it as Chronos-2.
   - Output arbitrary confidence scores.
2. **Explicit Typed Error Handling**:
   When Chronos-2 is unavailable or encounters an unrecoverable inference error, the engine raises:
   ```json
   {
     "status": "MODEL_UNAVAILABLE",
     "model_name": "chronos-2",
     "detail": "Chronos-2 pipeline weights could not be loaded on host. Model inference is unavailable."
   }
   ```
3. **Deterministic Seed Fixture Isolation**:
   Synthetic benchmark data is reserved exclusively for unit tests and UI layout validation. It is never presented to users as genuine model performance.

---

## 6. Model Lifecycle & Memory Architecture

- **Lazy Initialization**: Model weights (~480 MB in float32) are loaded into memory only on the first forecast request.
- **In-Memory Caching**: Once initialized, the `Chronos2Pipeline` instance is retained in the process singleton `ForecastModelRegistry` to eliminate reload latency on repeated requests.
- **CPU Resource Safety**: Inference utilizes `torch.set_grad_enabled(False)` and single-batch CPU evaluation to maintain memory footprints below 1 GB RAM.

---
*Authoritative Documentation: docs/FORECASTING_MODEL.md*
