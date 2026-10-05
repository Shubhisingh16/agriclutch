# AgriClutch Buyer Intelligence & Matching: Research Foundation & Clean-Room IP Audit

> **Problem Statement**: SIH26132 — Strengthening Market Linkages and Price Discovery for Farmers  
> **Platform**: AgriClutch — AI-Powered Agricultural Market Intelligence & Optimal Selling Platform  
> **Milestone**: STEP 12 — Buyer Matching & Demand Aggregation Engine  
> **Status**: Verified Clean-Room Research Specification

---

## 1. Clean-Room Legal & Architectural Protocol

AgriClutch enforces an absolute **Clean-Room Intellectual Property Firewall**:
- **Zero Code Contamination**: No code, schemas, variable definitions, or raw files are copied from external or unlicensed research repositories (including `references/`).
- **First-Principles Implementation**: All algorithms, matching logic, aggregation metrics, and reliability models are formulated and implemented from public academic, statistical, and microeconomic literature.
- **Modern Standards**: All Python implementations use Python 3.11+, typed dataclasses, Pydantic v2, and SQLAlchemy 2.0 async paradigms.

---

## 2. Core Algorithmic & Domain Concepts

### 2.1 Bipartite Produce-Buyer Compatibility & Multi-Dimensional Filtering

#### Concept & Purpose
In fragmented agricultural markets (e.g. Indian APMC and direct farm-gate corridors), matching producer supplies to commercial buyers requires evaluating multi-dimensional feasibility across:
1. Commodity & Variety
2. Quality Grade & Assay Tolerance
3. Quantity Feasibility (batch minimums and maximum capacity)
4. Temporal Availability Windows
5. Geographic Transit Proximity

#### Mathematical Formulation
Let a producer supply lot be represented by tuple:
$$S = (c_s, v_s, g_s, Q_s, [t_s^{\text{start}}, t_s^{\text{end}}], L_s)$$
Where:
- $c_s$: Commodity identifier
- $v_s$: Crop variety
- $g_s$: Physical quality grade
- $Q_s$: Available quantity in kilograms ($Q_s > 0$)
- $[t_s^{\text{start}}, t_s^{\text{end}}]$: Producer availability window
- $L_s = (\text{lat}_s, \text{lon}_s)$: Supply origin coordinates

Let a buyer requirement be represented by tuple:
$$R = (c_r, v_r, G_r, Q_r^{\min}, Q_r^{\max}, [t_r^{\text{start}}, t_r^{\text{end}}], L_r)$$
Where:
- $c_r$: Requested commodity
- $v_r$: Requested variety (or `ANY` if unrestricted)
- $G_r$: Acceptable quality grade set, e.g. $\{\text{Grade\_A}, \text{FAQ}\}$
- $[Q_r^{\min}, Q_r^{\max}]$: Quantity constraints in kilograms
- $[t_r^{\text{start}}, t_r^{\text{end}}]$: Required procurement window
- $L_r = (\text{lat}_r, \text{lon}_r)$: Delivery destination coordinates

Compatibility predicates:
1. **Commodity Predicate**:
   $$\Phi_{\text{comm}}(S, R) = \mathbb{I}(c_s = c_r)$$
2. **Variety Predicate**:
   $$\Phi_{\text{var}}(S, R) = \mathbb{I}(v_r = \text{ANY} \lor v_s = v_r)$$
3. **Quality Predicate**:
   $$\Phi_{\text{qual}}(S, R) = \mathbb{I}(g_s \in G_r)$$
4. **Temporal Overlap Predicate**:
   $$[t_{\text{overlap}}^{\text{start}}, t_{\text{overlap}}^{\text{end}}] = \left[\max(t_s^{\text{start}}, t_r^{\text{start}}), \min(t_s^{\text{end}}, t_r^{\text{end}})\right]$$
   $$\Phi_{\text{time}}(S, R) = \mathbb{I}(t_{\text{overlap}}^{\text{start}} \le t_{\text{overlap}}^{\text{end}})$$
5. **Quantity Matching**:
   $$Q_{\text{compat}} = \begin{cases} 
   \min(Q_s, Q_r^{\max}) & \text{if } Q_s \ge Q_r^{\min} \text{ and } \Phi_{\text{comm}} \land \Phi_{\text{qual}} \land \Phi_{\text{time}} \\
   0 & \text{otherwise}
   \end{cases}$$
   $$Q_{\text{unmatched\_supply}} = \max(0, Q_s - Q_{\text{compat}})$$
   $$Q_{\text{unmatched\_demand}} = \max(0, Q_r^{\max} - Q_{\text{compat}})$$

#### Clean-Room Interpretation
The engine outputs explicit boolean flags and compatible volumes. It **never** assigns a hidden subjective score or rank. Every compatibility evaluation is accompanied by deterministic, additive string explanations.

---

### 2.2 Geodesic Transit Distance (Haversine Formulation)

#### Concept & Purpose
To evaluate delivery feasibility without making unsupported assumptions about road network topology or live traffic conditions, the system computes the great-circle geodesic distance between supply origin and buyer destination coordinates.

#### Mathematical Formulation
Given coordinates $(\phi_1, \lambda_1)$ and $(\phi_2, \lambda_2)$ in radians:
$$\Delta\phi = \phi_2 - \phi_1, \quad \Delta\lambda = \lambda_2 - \lambda_1$$
$$a = \sin^2\left(\frac{\Delta\phi}{2}\right) + \cos(\phi_1)\cos(\phi_2)\sin^2\left(\frac{\Delta\lambda}{2}\right)$$
$$c = 2 \cdot \text{atan2}\left(\sqrt{a}, \sqrt{1-a}\right)$$
$$D_{\text{geodesic}} = R_{\text{earth}} \cdot c$$
Where $R_{\text{earth}} \approx 6371.0\text{ km}$.

#### Clean-Room Interpretation
- Output is explicitly labeled `distance_type = "DISTANCE_GEODESIC"`.
- If either coordinate pair is null or uncalibrated, the status is strictly set to `DISTANCE_UNAVAILABLE`. Road route distance is never fabricated.

---

### 2.3 Regional Demand Aggregation & Market Depth

#### Concept & Purpose
Agricultural cooperatives and FPOs aggregate farm output to negotiate with institutional buyers. Symmetrically, understanding the aggregate documented buyer demand landscape in a regional corridor helps assess true market depth.

#### Mathematical Formulation
For commodity $c$, quality grade $g$, and regional market scope $\Omega$:
$$D_{\text{total}}(c, g, \Omega) = \sum_{b \in B(c, g, \Omega)} Q_{\text{demand}}(b)$$
Where $B(c, g, \Omega)$ is the set of active buyer requirements within the scope.

Demand breakdown by provenance:
$$D_{\text{total}} = D_{\text{confirmed}} + D_{\text{quoted}} + D_{\text{estimated}} + D_{\text{demo}}$$
The system preserves the distinction across all levels of aggregation.

---

### 2.4 Demand Distribution & Sample-Size Gating (`provenance_status = CONFIGURED`)

#### Concept & Purpose
Descriptive order size statistics (minimum, maximum, mean, median, interquartile range) provide transparency on buyer order sizes.

#### Mathematical Formulation & Gating Rule
Given $N$ active buyer demand observations $\{d_1, d_2, \dots, d_N\}$ sorted in non-decreasing order:
- **Sample-Size Gate (`provenance_status = CONFIGURED`)**: Minimum descriptive sample-size gate used to suppress extremely small sample summaries.
  - This is a conservative heuristic gate designed to prevent displaying misleading quantiles from 1 or 2 observations; it is **NOT** described as statistically significant, universally sufficient, or an econometric standard.
- If $N < 3$: The engine returns:
  $$\text{distribution\_status} = \text{"INSUFFICIENT\_DATA"}$$
  Point metrics and quantiles are set to `None`.
- If $N \ge 3$:
  $$\mu = \frac{1}{N}\sum_{i=1}^N d_i, \quad \text{Med} = \begin{cases} d_{(N+1)/2} & N \text{ odd} \\ \frac{1}{2}(d_{N/2} + d_{N/2+1}) & N \text{ even} \end{cases}$$
  Quantiles $P_{10}, P_{25}, P_{50}, P_{75}, P_{90}$ are calculated using standard linear interpolation.

---

### 2.5 Regional Buyer Demand Concentration (Herfindahl-Hirschman Index)

#### Concept & Purpose
To characterize the distribution of demand across buyers in a regional market corridor, the platform calculates market concentration metrics.

#### Mathematical Formulation
Let $s_i$ be the percentage share of buyer $i$ in total regional demand:
$$s_i = \left( \frac{D_i}{D_{\text{total}}} \right) \times 100\%$$
The Herfindahl-Hirschman Index is:
$$\text{HHI} = \sum_{i=1}^N s_i^2 = \sum_{i=1}^N \left( \frac{D_i}{D_{\text{total}}} \times 100 \right)^2 \in (0, 10000]$$

Top-Buyer Share:
$$\text{CR}_1 = \max_{i} s_i, \quad \text{CR}_3 = \sum_{i \in \text{top 3}} s_i$$

#### Clean-Room Interpretation & Neutrality Mandate (`provenance_status = CONFIGURED`)
- Interpretive bands (<1500 unconcentrated, 1500–2500 moderately concentrated, >2500 concentrated) are classified as `provenance_status = CONFIGURED`, adapted from the 1982/2010 U.S. DOJ/FTC Horizontal Merger Guidelines.
- They are **NOT** presented as empirical agricultural truths or objective economic judgments, but strictly as a configured descriptive benchmark.
- Categorical labels are not presented as normative verdicts.

---

### 2.6 Empirical Buyer Reliability Metrics

#### Concept & Purpose
Rather than relying on opaque, subjective "reputation scores" (e.g. 84/100), commercial reliability is computed transparently from immutable historical transaction records.

#### Mathematical Formulations
1. **Order Fulfillment Rate**:
   $$\text{FR} = \frac{N_{\text{fulfilled}}}{N_{\text{confirmed}}}$$
2. **Order Cancellation Rate**:
   $$\text{CR} = \frac{N_{\text{cancelled}}}{N_{\text{confirmed}}}$$
3. **Quantity Fulfillment Ratio**:
   $$\text{QFR} = \frac{1}{N_{\text{delivered}}} \sum_{j=1}^{N_{\text{delivered}}} \min\left(1.0, \frac{Q_{\text{delivered}, j}}{Q_{\text{contracted}, j}}\right)$$
4. **Average Payment Delay (Days)**:
   $$\bar{\Delta}_{\text{payment}} = \frac{1}{N_{\text{dated}}} \sum_{k=1}^{N_{\text{dated}}} \max(0, \text{Date}_{\text{actual\_payment}, k} - \text{Date}_{\text{agreed\_due}, k})$$
   - **Missing-Data Treatment**: Missing payment dates are strictly distinguished from zero delay and never silently converted to zero.
   - Only records with both valid `actual_payment_date` and `agreed_payment_due_date` enter the denominator $N_{\text{dated}}$.
   - If $N_{\text{dated}} = 0$, the metric returns `None`.
5. **Dispute Rate**:
   $$\text{DR} = \frac{N_{\text{disputed}}}{N_{\text{confirmed}}}$$

#### Sufficiency & Fail-Closed Rules
- If $N_{\text{confirmed}} = 0$: `reliability_status = "UNAVAILABLE"`.
- If $N_{\text{confirmed}} < 3$: `reliability_status = "INSUFFICIENT_HISTORY"` (`provenance_status = CONFIGURED` sample-size gate).
- All outputs include the exact numerator, denominator, sample size $N$, and time horizon. Default scores are strictly forbidden.
- Demo fixtures represent **6 synthetic demo buyer entities representing commercial buyer archetypes** (`provenance_status = DEMO`, `is_demo = true`). Never described as verified real commercial buyers.

---

## 3. Summary of Implementation Contracts

| Concept | File Location | Key Guarantees |
| :--- | :--- | :--- |
| **Contracts & Enums** | `ml/buyer/contracts.py` | Strict typed dataclasses, UUID identifiers, explicit units (`KG`, `INR_PER_KG`). |
| **Compatibility Engine** | `ml/buyer/compatibility.py` | Deterministic boolean predicates, interval intersection, Haversine distance, additive string explanations. |
| **Aggregation Engine** | `ml/buyer/aggregation.py` | Total volume, provenance breakdown, $N \ge 3$ distribution gating, descriptive HHI. |
| **Reliability Analyzer** | `ml/buyer/reliability.py` | Immutable transaction accounting, $N \ge 3$ sample gating, zero magic scores. |
| **Smoke Test** | `ml/buyer/smoke_test.py` | 16-stage verification script ensuring math precision and zero recommendation leakage. |

---
*End of docs/BUYER_INTELLIGENCE_RESEARCH.md*
