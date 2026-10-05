# AgriClutch Crop Perishability & Shelf-Life Decay Engine

> **Subsystem**: Step 13 — Logistics + Storage + Perishability Feasibility Engine  
> **Problem Statement**: SIH26132 — Strengthening Market Linkages and Price Discovery for Farmers  
> **Platform Vision**: Mathematical modeling of time-dependent produce mass shrinkage and quality grade degradation.

---

## 1. Decoupled Deterioration Mathematical Formulations

Perishability in AgriClutch is decoupled into two independent biological processes:
1. **Physical Quantity Loss (Mass/Spoilage Shrinkage)**: Moisture respiration, rot, and physical culling.
2. **Quality Grade Decay (Commercial Assay Discount)**: Color fade, firmness reduction, and blemish progression that downgrade the commercial realization tier.

### 1.1 Physical Mass Survival Equation

The proportion of physical produce surviving at time $t$ (days) is modeled as:

$$S(t) = \exp(-\delta \cdot t)$$

The effective delivered quantity $Q_{\text{effective}}(t)$ is:

$$Q_{\text{effective}}(t) = Q_{\text{initial}} \times S(t) = Q_{\text{initial}} \cdot \exp(-\delta \cdot t)$$

Physical quantity loss $\Delta Q(t)$ is:

$$\Delta Q(t) = Q_{\text{initial}} - Q_{\text{effective}}(t) = Q_{\text{initial}} \cdot (1 - \exp(-\delta \cdot t))$$

### 1.2 Quality Grade Decay Equation

Commercial quality retention factor $F_{\text{quality}}(t) \in [0, 1]$ deteriorates according to:

$$F_{\text{quality}}(t) = \max\left(0.0, \min\left(1.0, F_0 \cdot \exp(-\beta \cdot t)\right)\right)$$

where $F_0$ is the initial harvest assay factor ($1.0$ for Grade A standard).

---

## 2. Configured/Demo Crop Perishability Parameters

All parameters are explicitly categorized as **CONFIGURED/DEMO ASSUMPTIONS** with `calibration_status = "NOT_CALIBRATED"`, `is_demo = true`, and `provenance_status = "DEMO"`:

> [!NOTE]
> **No Empirical Calibration Claim**: These values represent configured indicative regional shelf-life benchmarks for scenario demonstration. They are **NOT** certified empirical laboratory constants.

| Commodity | Storage Regime | Daily Mass Loss Rate ($\delta$) | Daily Quality Loss Rate ($\beta$) | Half-Life ($t_{1/2}$) | Maximum Horizon | Calibration Status | Provenance Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Tomato** | Ambient Farm Gate | $0.035 \text{ day}^{-1}$ (~3.5%/d) | $0.050 \text{ day}^{-1}$ (~5.0%/d) | ~19.8 days | 10 days | `NOT_CALIBRATED` | `DEMO` |
| **Tomato** | Cold Chain Hub | $0.008 \text{ day}^{-1}$ (~0.8%/d) | $0.015 \text{ day}^{-1}$ (~1.5%/d) | ~86.6 days | 28 days | `NOT_CALIBRATED` | `DEMO` |
| **Onion** | Ambient Ventilated | $0.005 \text{ day}^{-1}$ (~0.5%/d) | $0.008 \text{ day}^{-1}$ (~0.8%/d) | ~138.6 days | 60 days | `NOT_CALIBRATED` | `DEMO` |
| **Onion** | Cold Storage Hub | $0.0015 \text{ day}^{-1}$ (~0.15%/d) | $0.003 \text{ day}^{-1}$ (~0.3%/d) | ~462.1 days | 180 days | `NOT_CALIBRATED` | `DEMO` |
| **Potato** | Ambient Heap | $0.004 \text{ day}^{-1}$ (~0.4%/d) | $0.006 \text{ day}^{-1}$ (~0.6%/d) | ~173.3 days | 90 days | `NOT_CALIBRATED` | `DEMO` |
| **Potato** | Industrial Cold Store | $0.0008 \text{ day}^{-1}$ (~0.08%/d) | $0.0015 \text{ day}^{-1}$ (~0.15%/d) | ~866.4 days | 240 days | `NOT_CALIBRATED` | `DEMO` |

---

## 3. Unsupported Commodity Fail-Closed Behavior

If a query specifies an unsupported crop or an uncalibrated storage environment:
- The engine **FAILS CLOSED** to `status = "LOSS_MODEL_UNAVAILABLE"`.
- `model_spec` is returned as `null`.
- Final quantity remains identical to initial quantity ($Q_{\text{final}} = Q_{\text{initial}}$); the system **never fabricates decay numbers**.
- Provenance status is tagged as `UNAVAILABLE` with an explicit notice:
  ```json
  {
    "source_name": "PERISHABILITY_ENGINE",
    "status": "UNAVAILABLE",
    "is_demo": false,
    "justification": "No verified loss model available for crop 'X' under storage 'Y'."
  }
  ```
