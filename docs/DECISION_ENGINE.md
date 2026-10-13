# AgriClutch Step 14: Decision Intelligence, Mathematical Optimization & Risk Audit

## 1. Overview & Architectural Role
Step 14 is the foundational decision-support engine authorized to answer:
$$\text{Optimal Selling Plan} = f(\text{Crop}, \text{Quantity}, \text{Quality}, \text{Location}, \text{Storage}, \text{Liquidity}, \text{Risk})$$

It integrates the validated factual layers from earlier subsystems:
- **Step 10**: Price forecast distributions ($P_{10}, P_{50}, P_{90}$).
- **Step 11**: Net Realizable Value (NRV) after itemized friction deductions.
- **Step 12**: Buyer compatibility, documented buyer demand/capacity, and payment horizons.
- **Step 13**: Logistics routing, haulage costs, storage limits, and perishability decay curves.

Step 14 translates these factual inputs into a deterministic **SciPy HiGHS Dual Simplex Linear Program** to recommend explicit, verifiable allocation splits across markets, commercial buyers, and storage horizons.

---

## 2. Mathematical Optimization Formulation

### Objective Function
$$\text{Maximize } Z = \sum_{i \in \mathcal{C}} c_i x_i$$
where $x_i$ is the allocated produce harvest quantity (kg) for candidate pathway $i$, and $c_i$ is the linear risk-adjusted economic realization coefficient:
$$c_i = \text{ExpectedNRV}_i - \lambda \cdot \text{DownsideSpread}_i$$
$$\text{DownsideSpread}_i = \max(0, \text{ExpectedNRV}_i - \text{NRV}_{p10, i})$$

### Mathematical Meaning of Objective Terms
1. **$x_i$**: Decision variable representing allocated produce harvest volume (kg) committed to pathway $i$.
2. **$\text{ExpectedNRV}_i$**: Expected net realizable value per kg in pathway $i$ based on the forecast median and physical/logistics deductions.
3. **$\text{NRV}_{p10, i}$**: Conservative 10th-percentile net realizable value per kg under adverse price/decay scenarios.
4. **$\text{DownsideSpread}_i$**: The parametric lower-quantile downside spread (dispersion between the central expectation and the 10th percentile conservative realization). It measures channel uncertainty and downside exposure.
5. **$\lambda \in [0.0, 1.0]$**: The farmer risk penalty weighting parameter.
   - `RISK_NEUTRAL`: $\lambda = 0.0$ (Optimizes pure expected economic realization; zero downside spread penalty).
   - `RISK_AWARE`: $\lambda = 0.5$ (Configured policy weighting balancing expected gain with lower quantile spread).
   - `RISK_AVERSE`: $\lambda = 1.0$ (Full 1:1 deduction of lower quantile spread to safeguard farmer floor realization).
   - **Provenance Status of $\lambda$**: `CONFIGURED` (system policy parameters, not empirically estimated farmer utility curves).

---

## 3. Optimization Risk vs Post-Solve Evaluation Risk

### A. Optimization Risk Formulation (In LP Matrix)
The risk term actually optimized within the LP objective function is:
$$\text{Penalty}_{\text{LP}} = \lambda \sum_{i \in \mathcal{C}} \max(0, \text{ExpectedNRV}_i - \text{NRV}_{p10, i}) \cdot x_i$$
This is strictly linear in $x_i$, preserving exact linear programming structure and enabling deterministic solution via SciPy HiGHS Dual Simplex without heuristic non-linear approximations.

### B. Post-Solve Risk Evaluation (Computed After Optimization)
Once the optimal allocation vector $\mathbf{x}^*$ is identified, the engine computes summary portfolio risk statistics:
1. **Portfolio Value at Risk ($\text{VaR}_{95}$)**:
   $$\text{VaR}_{95} = \max\left(0, \sum_i x_i^* \cdot \text{NRV}_{p50, i} - \sum_i x_i^* \cdot \text{NRV}_{p10, i}\right)$$
   Represents maximum expected loss relative to median at the 10th percentile lower quantile.
2. **Portfolio Conditional Value at Risk ($\text{CVaR}_{95}$)**:
   $$\text{CVaR}_{95} = \text{VaR}_{95} \cdot \mu_{\text{tail}}$$
   Where $\mu_{\text{tail}} = 1.25$.
   - **CRITICAL AUDIT NOTE**: $1.25\times$ is **NOT** an intrinsic mathematical constant of CVaR95. It is a **CONFIGURED parametric tail approximation multiplier** representing typical heavy-tailed commodity distribution behavior below P10.
   - **Provenance Status**: `provenance_status = CONFIGURED`, `is_demo = true`.
   - The LP solver does **NOT** directly optimize CVaR95; CVaR95 is evaluated post-solve for portfolio risk transparency.

---

## 4. Constraint System & Policy Thresholds

1. **Total Supply Conservation**:
   $$\sum_{i \in \mathcal{C}} x_i \le Q_{\text{total}}$$
2. **Liquidity Window Bounds (Minimum Immediate Day 0-1 Liquidation)**:
   - `IMMEDIATE`: $\sum_{i \in \mathcal{C}_{\text{imm}}} x_i \ge 0.60 \cdot Q_{\text{total}}$
   - `BALANCED`: $\sum_{i \in \mathcal{C}_{\text{imm}}} x_i \ge 0.30 \cdot Q_{\text{total}}$
   - `DELAY_TOLERANT`: Unconstrained minimum immediate allocation ($\ge 0$).
   - **Provenance Status**: `CONFIGURED` (policy conventions representing typical smallholder cash-flow urgency, not empirically proven universal farmer behavior).
3. **Documented Buyer Demand / Capacity Constraints**:
   $$\sum_{i \in \mathcal{C}_b} x_i \le \text{Demand}_b \quad \forall \text{ Buyer } b$$
   - Demand provenance adheres to Step 12 classifications (`DEMO_DEMAND`, `QUOTED_DEMAND`, `CONTRACTED_DEMAND`). Synthetic buyers are documented as demo entities.
4. **Storage Facility Capacity**:
   $$\sum_{i \in \mathcal{C}_s} x_i \le \text{Capacity}_s \quad \forall \text{ Facility } s$$
5. **Transport Fleet Limits**:
   $$x_i \le \text{Capacity}_{\text{veh}, i} \quad \forall i$$
6. **Non-negativity & Bounds**:
   $$0 \le x_i \le \min(Q_{\text{total}}, \text{Demand}_i, \text{Capacity}_i)$$

---

## 5. Solver Optimality Scope
When the SciPy HiGHS LP solver completes with status `OPTIMAL`:
- It provides a **mathematically guaranteed globally optimal solution to the FORMULATED LINEAR PROGRAM**.
- It does **NOT** claim global optimality of the complex real-world agricultural system, unmodeled macro risks, or external weather shocks.

---

## 6. What-If Simulator & Sensitivity Reproducibility
The `WhatIfSimulatorEngine` independently reruns the complete optimization problem for every counterfactual scenario rather than modifying baseline numbers:
- Logs `baseline_input_hash` and `counterfactual_input_hash`.
- Records `baseline_solver_status` and `new_solver_status`.
- Computes exact differential deltas:
  $$\Delta \text{NRV} = \text{NRV}_{\text{CF}} - \text{NRV}_{\text{Base}}$$
  $$\Delta \text{CVaR} = \text{CVaR}_{\text{CF}} - \text{CVaR}_{\text{Base}}$$
  $$\Delta \text{Allocation} = \mathbf{x}^*_{\text{CF}} - \mathbf{x}^*_{\text{Base}}$$
  $$\Delta \text{Feasibility} = (\text{Status}_{\text{Base}} \neq \text{Status}_{\text{CF}})$$
