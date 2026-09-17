# AgriClutch Net Realizable Value (NRV) Engine Specification

> **Problem Statement**: SIH26132 — Strengthening Market Linkages and Price Discovery for Farmers  
> **Subsystem**: Decision Intelligence & Net Realizable Value (NRV) Engine (Step 11)  
> **Status**: Verified Clean-Room Implementation  

---

## 1. Prime Economic Directives & Conceptual Boundaries

The AgriClutch Net Realizable Value (NRV) Engine represents the foundational economic layer positioned between probabilistic time-series forecasting (Step 10) and downstream decision optimization (Step 14).

### The Core Economic Problem
Farmers frequently encounter misleading headline price signals:
- Mandi $A$ (250 km away) quotes ₹31.50/kg.
- Mandi $B$ (12 km away) quotes ₹28.00/kg.

Selling to Mandi $A$ might appear optimal based on quoted rates, but long-haul freight, terminal market loading, higher APMC cess, and transit spoilage degrade realization below ₹25.00/kg. Mandi $B$, despite the lower headline price, yields ₹26.50/kg net realization.

$$\text{MANDI PRICE} \neq \text{FARMER REALIZATION}$$

### Strict Architectural Boundary
The Step 11 NRV Engine performs **pure economic realization modeling, scenario comparison, and sensitivity analysis**.
- It **does calculate**: Gross revenue distributions, itemized friction costs, effective marketable quantities, break-even prices, cross-market comparisons, time horizon holding scenarios, and sensitivity matrices.
- It **does NOT calculate or emit**: `SELL NOW`, `HOLD`, `BUY`, `STORE`, `BEST MARKET`, `WINNER`, `RECOMMENDED ACTION`, buyer matching, buyer ranking, route optimization, or automated execution.

---

## 2. Mathematical Formulation

### 2.1 Core Net Realizable Value Equation
For commodity $c$, candidate market $m$, initial harvest quantity $Q_0$ (normalized to kg), quality profile $g$, and storage horizon $t$ (days):

$$\text{NRV}(c, m, t, Q_0) = \text{GrossRevenue}(c, m, t, Q_0) - \sum \text{FrictionCosts}(m, t, Q_0) - C_{\text{loss}}(t, Q_0) - C_{\text{risk}}(m, t)$$

Expanded term-by-term:

$$\text{NRV}(m, t) = Q_{\text{effective}}(t) \cdot P_{\text{adjusted}}(m, t) - C_{\text{transport}}(m, Q_0) - C_{\text{storage}}(t, Q_0) - C_{\text{handling}}(Q_0) - C_{\text{market}}(m, t) - C_{\text{other}}(Q_0) - C_{\text{loss}}(t) - C_{\text{risk}}(m, t)$$

Where all values are denominated strictly in Indian Rupees (INR, ₹).

---

### 2.2 Physical Perishability & Effective Quantity
Harvested agricultural commodities experience physical weight loss, moisture shrinkage, and biological spoilage during holding and transit.

$$Q_{\text{effective}}(t) = Q_0 \cdot \exp\left(-\delta_{\text{decay}}(\text{crop}, \text{storage\_type}) \cdot t\right)$$

- $Q_0$: Initial harvest volume in kilograms ($Q_0 > 0$).
- $t$: Storage duration in days ($t \ge 0$).
- $\delta_{\text{decay}}$: Physical decay rate per day ($\text{day}^{-1}$), constrained by storage infrastructure (`ambient` vs `cold_storage`).
- $r_{\text{loss}}(t)$: Expected physical loss fraction:
  $$r_{\text{loss}}(t) = 1 - \frac{Q_{\text{effective}}(t)}{Q_0} = 1 - \exp(-\delta_{\text{decay}} \cdot t), \quad 0 \le r_{\text{loss}} < 1$$
- $Q_{\text{lost}}(t)$: Mass of spoiled or degraded produce:
  $$Q_{\text{lost}}(t) = Q_0 - Q_{\text{effective}}(t) = Q_0 \cdot r_{\text{loss}}(t)$$

---

### 2.3 Quality-Adjusted Price
Forecast prices reflect Fair Average Quality (FAQ) standard specifications. Produce varying in grade or subjected to prolonged ambient storage receives quality adjustments:

$$P_{\text{adjusted}}(q) = P_{\text{forecast}}(q) \cdot F_{\text{quality}}$$

Where:
$$F_{\text{quality}} = F_{\text{grade}} \cdot (1 - \kappa_{\text{downgrade}}(t))$$
- $F_{\text{grade}}$: Relative value factor for initial produce grade:
  - `Grade_A` / Premium: $1.08$
  - `FAQ` / Fair Average Quality: $1.00$
  - `Grade_B` / Undergrade: $0.85$
- $\kappa_{\text{downgrade}}(t)$: Quality downgrade penalty triggered when ambient holding exceeds the safe holding threshold $T_{\text{ambient\_max}}$:
  $$\kappa_{\text{downgrade}}(t) = \begin{cases} 0.15 & \text{if } \text{storage\_type} = \text{ambient and } t > T_{\text{downgrade}} \\ 0.00 & \text{otherwise} \end{cases}$$

---

### 2.4 Quantile Gross Revenue Distribution
Gross revenue is calculated over the entire forecast distribution from Step 10 ($q \in \{10, 20, 50, 80, 90\}$):

$$\text{GrossRevenue}_q = Q_{\text{effective}}(t) \cdot P_{\text{adjusted}}(q)$$

This ensures that downside price risks ($P_{10}$) and upside opportunities ($P_{90}$) propagate directly into top-line revenue estimates.

---

### 2.5 Itemized Economic Deductions

Every deduction is maintained as an auditable, separate component:

#### 1. Transport Cost ($C_{\text{transport}}$)
Freight charges between the production cluster / farm gate and the target APMC mandi:
$$C_{\text{transport}}(m, Q_0) = F_{\text{base}} + \left( D_m \cdot R_{\text{km/ton}} \cdot \frac{Q_0}{1000} \right)$$
- $F_{\text{base}}$: Fixed dispatch / booking fee (₹).
- $D_m$: Road transit distance to mandi $m$ (km).
- $R_{\text{km/ton}}$: Freight rate per road kilometer per metric tonne (₹/km/tonne).
- $Q_0 / 1000$: Produce tonnage.

#### 2. Storage Rental Cost ($C_{\text{storage}}$)
Holding charges dependent on storage type and elapsed days:
$$C_{\text{storage}}(t, Q_0) = Q_0 \cdot t \cdot S_{\text{daily\_rate}}(\text{storage\_type})$$
- On-farm ambient shed: $S_{\text{daily\_rate}} = \text{₹}0.00/\text{kg/day}$ (farmer's existing ambient infrastructure).
- Commercial cold storage warehouse: $S_{\text{daily\_rate}} = \text{₹}0.20/\text{kg/day}$ (standard commercial tariff for horticulture in Northern India).

#### 3. Handling Cost ($C_{\text{handling}}$)
Physical labor fees for loading at farm gate and unloading at the APMC yard:
$$C_{\text{handling}}(Q_0) = Q_0 \cdot (C_{\text{loading}} + C_{\text{unloading}})$$
- $C_{\text{loading}}$: ₹0.30/kg
- $C_{\text{unloading}}$: ₹0.30/kg
- Total handling: ₹0.60/kg.

#### 4. Statutory APMC Market Charges ($C_{\text{market}}$)
Statutory mandi fees and rural development cess enacted under state APMC regulations. Calculated as an ad-valorem percentage $\mu_{\text{APMC}}$ of gross realized sales:
$$C_{\text{market}, q} = \mu_{\text{APMC}}(m) \cdot \text{GrossRevenue}_q$$
Typical statutory rates:
- Chandigarh APMC: $1.50\%$
- Haryana (Panchkula, Kalka): $2.00\%$
- Punjab (Patiala): $2.00\%$
- Delhi Azadpur Terminal: $1.00\%$

#### 5. Other Documented Costs ($C_{\text{other}}$)
Certified weighbridge fee and packing material amortization (reusable plastic crates or gunny bags):
$$C_{\text{other}}(Q_0) = Q_0 \cdot C_{\text{packaging\_weighment}}$$
- Benchmark: ₹0.40/kg.

#### 6. Spoilage Disposal / Culling Cost ($C_{\text{loss}}$)
Direct labor and municipal fee for sorting, culling, and disposing of spoiled produce:
$$C_{\text{loss}}(t) = Q_{\text{lost}}(t) \cdot C_{\text{culling\_per\_kg}}$$
- Benchmark: ₹0.10/kg of spoiled produce.

#### 7. Risk Adjustment ($C_{\text{risk}}$)
Accounts for operational uncertainty. If no separately calibrated behavioral or transit risk model is active, this value is strictly set to `0.0` with explicit status `NOT_MODELED`. Missing risk models are never conflated with "zero risk".

---

### 2.6 Total Deductions and Quantile NRV
$$\text{TotalCost}_q = C_{\text{transport}} + C_{\text{storage}} + C_{\text{handling}} + C_{\text{market}, q} + C_{\text{other}} + C_{\text{loss}} + C_{\text{risk}}$$
$$\text{NRV}_q = \text{GrossRevenue}_q - \text{TotalCost}_q$$
$$\text{NRV\_per\_kg}_q = \frac{\text{NRV}_q}{Q_0}$$

Because $\text{GrossRevenue}_q = Q_{\text{effective}} \cdot P_{\text{adjusted}}(q)$, we can write:
$$\text{NRV}_q = \text{GrossRevenue}_q \cdot (1 - \mu_{\text{APMC}}) - \text{FixedCostComponent} - C_{\text{risk}}$$
Given $P_{10} \le P_{20} \le P_{50} \le P_{80} \le P_{90}$ and $(1 - \mu_{\text{APMC}}) > 0$, quantile monotonicity is strictly preserved:
$$\text{NRV}_{P10} \le \text{NRV}_{P20} \le \text{NRV}_{P50} \le \text{NRV}_{P80} \le \text{NRV}_{P90}$$

---

### 2.7 Break-Even Price Derivation & Zero-Margin Proof
The break-even price $P_{\text{BE}}$ is the minimum quoted mandi market price (₹/kg) required for the farmer to achieve exactly zero net realization ($\text{NRV} = 0$).

#### 1. Unambiguous Mathematical Formulation:
```
P_BE =
C_non_market /
(Q_effective(t) × F_quality × (1 - μ_APMC))
```

In standard LaTeX notation:
$$P_{\text{BE}} = \frac{C_{\text{non\_market}}}{Q_{\text{effective}}(t) \times F_{\text{quality}} \times (1 - \mu_{\text{APMC}})}$$

Where:
- $C_{\text{non\_market}} = C_{\text{transport}} + C_{\text{storage}} + C_{\text{handling}} + C_{\text{other}} + C_{\text{loss}} + C_{\text{risk}}$
- $Q_{\text{effective}}(t)$: Surviving marketable produce quantity in kg after perishability decay at holding day $t$ ($Q_{\text{effective}}(t) = Q_0 \cdot e^{-\delta t}$).
- $F_{\text{quality}}$: Effective quality factor ($F_{\text{grade}} \cdot (1 - \kappa_{\text{downgrade}})$).
- $\mu_{\text{APMC}}$: Statutory ad-valorem APMC market cess fraction (e.g., $0.015$ for $1.5\%$).

> [!NOTE]
> **Implementation Note on Arithmetic Operator:**
> The calculation in [`ml/decision/nrv.py`](file:///c:/Users/shubh/OneDrive/Documents/agriclutch/ml/decision/nrv.py) strictly uses **division**, not multiplication:
> ```python
> be_denom = effective_qty_kg * quality_factor * (1.0 - apmc_fee_fraction)
> be_price = fixed_deductions / be_denom  # Strict division by the combined effective denominator
> ```

#### 2. First-Principles Derivation from $\text{NRV} = 0$:
By definition, at the break-even quoted price $P_{\text{BE}}$:
$$\text{NRV}(P_{\text{BE}}) = \text{GrossRevenue}(P_{\text{BE}}) - \text{TotalCost}(P_{\text{BE}}) = 0$$

1. Decompose $\text{TotalCost}$ into statutory ad-valorem market charges and non-market deductions:
   $$\text{TotalCost}(P_{\text{BE}}) = C_{\text{market}}(P_{\text{BE}}) + C_{\text{non\_market}}$$
2. Express statutory APMC market cess as a fraction $\mu_{\text{APMC}}$ of gross realized sales:
   $$C_{\text{market}}(P_{\text{BE}}) = \mu_{\text{APMC}} \cdot \text{GrossRevenue}(P_{\text{BE}})$$
3. Substitute back into the zero-margin condition:
   $$\text{GrossRevenue}(P_{\text{BE}}) - \left[ \mu_{\text{APMC}} \cdot \text{GrossRevenue}(P_{\text{BE}}) + C_{\text{non\_market}} \right] = 0$$
   $$\text{GrossRevenue}(P_{\text{BE}}) \cdot (1 - \mu_{\text{APMC}}) = C_{\text{non\_market}}$$
4. Expand gross revenue in terms of surviving physical quantity, quality adjustment factor, and break-even quoted price:
   $$\text{GrossRevenue}(P_{\text{BE}}) = Q_{\text{effective}}(t) \cdot F_{\text{quality}} \cdot P_{\text{BE}}$$
5. Factor out $P_{\text{BE}}$:
   $$P_{\text{BE}} \cdot \left[ Q_{\text{effective}}(t) \cdot F_{\text{quality}} \cdot (1 - \mu_{\text{APMC}}) \right] = C_{\text{non\_market}}$$
6. Solve analytically for $P_{\text{BE}}$ by dividing both sides by the bracketed denominator:
   $$P_{\text{BE}} = \frac{C_{\text{non\_market}}}{Q_{\text{effective}}(t) \times F_{\text{quality}} \times (1 - \mu_{\text{APMC}})}$$

#### 3. Analytical & Numerical Verification ($|\text{NRV}(P_{\text{BE}})| < 10^{-10}$):
To prove that substituting $P_{\text{BE}}$ guarantees net zero realization:
1. Calculate gross revenue at $P_{\text{BE}}$:
   $$\text{GrossRevenue}(P_{\text{BE}}) = Q_{\text{effective}} \cdot F_{\text{quality}} \cdot \frac{C_{\text{non\_market}}}{Q_{\text{effective}} \cdot F_{\text{quality}} \cdot (1 - \mu_{\text{APMC}})} = \frac{C_{\text{non\_market}}}{1 - \mu_{\text{APMC}}}$$
2. Calculate total deductions:
   $$\text{TotalCost}(P_{\text{BE}}) = \mu_{\text{APMC}} \cdot \left(\frac{C_{\text{non\_market}}}{1 - \mu_{\text{APMC}}}\right) + C_{\text{non\_market}} = C_{\text{non\_market}} \cdot \left[ \frac{\mu_{\text{APMC}} + 1 - \mu_{\text{APMC}}}{1 - \mu_{\text{APMC}}} \right] = \frac{C_{\text{non\_market}}}{1 - \mu_{\text{APMC}}}$$
3. Net Realizable Value:
   $$\text{NRV}(P_{\text{BE}}) = \text{GrossRevenue}(P_{\text{BE}}) - \text{TotalCost}(P_{\text{BE}}) = \frac{C_{\text{non\_market}}}{1 - \mu_{\text{APMC}}} - \frac{C_{\text{non\_market}}}{1 - \mu_{\text{APMC}}} \equiv 0.00$$
4. In numerical evaluation, standard IEEE 754 64-bit floating point arithmetic yields:
   $$|\text{NRV}(P_{\text{BE}})| < 10^{-10} \approx 0.00\text{ INR}$$
   This is verified by automated unit tests in [`backend/tests/test_nrv_calculation.py`](file:///c:/Users/shubh/OneDrive/Documents/agriclutch/backend/tests/test_nrv_calculation.py) and [`frontend/tests/nrv_ui.test.mjs`](file:///c:/Users/shubh/OneDrive/Documents/agriclutch/frontend/tests/nrv_ui.test.mjs).

If $Q_{\text{effective}} = 0$ or $(1 - \mu_{\text{APMC}}) \le 0$ or any required cost parameter is unavailable, the engine returns `is_available = False` with `break_even_price = None` (`BREAK_EVEN_UNAVAILABLE`) rather than dividing by zero or inventing numbers.

---

## 3. Provenance & Data Architecture

Every economic parameter used in calculations must declare a typed `ProvenanceStatus`:
1. `EMPIRICAL`: Observed from authorized empirical market transaction datasets.
2. `OFFICIAL`: Derived from an authoritative regulatory schedule (e.g., State APMC Acts).
3. `RESEARCH`: Derived from published scientific agricultural studies (e.g., ICAR-CIPHET post-harvest loss reports).
4. `CONFIGURED`: Explicitly configured by the system administrator or user.
5. `DEMO`: Benchmark assumption used for demonstration/testing.
6. `UNAVAILABLE`: Parameter not defensibly established.

All demo parameters must be rendered with an explicit `DEMO ASSUMPTION` badge and must never be represented as real-time or verified APMC rates.
