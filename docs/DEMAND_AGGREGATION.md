# AgriClutch: Regional Demand & Market Concentration Specification

> **Subsystem**: Regional Demand Aggregation & Market Depth Engine  
> **Module Path**: `ml/buyer/aggregation.py` & `backend/app/services/buyer_service.py`  
> **Status**: Verified Clean-Room Implementation  

---

## 1. Mathematical Formulation

Let $\mathcal{D} = \{d_1, d_2, \dots, d_K\}$ be the set of active commercial buyer requirements and spot procurement demands for a given commodity $c$ in region $\mathcal{R}$.

Each demand observation is defined by:
$$d_k = \langle b_k, c, g_k, \tau_k, q_k, p_k \rangle$$
where $b_k$ is the purchasing entity, $g_k$ is the quality grade requirement, $\tau_k$ is the buyer channel category, and $q_k$ is the demanded volume in kilograms.

### 1.1 Total Regional Stated Demand
$$Q_{\text{total}} = \sum_{k=1}^K q_k$$

If $Q_{\text{total}} = 0$ or $K = 0$, all aggregate metrics return neutral nulls or zeros, failing closed to prevent misleading liquidity signals.

### 1.2 Channel & Quality Stratification
- **Quality Grade Stratification**:
  $$Q(g) = \sum_{k: g_k = g} q_k, \quad \forall g \in \{\text{GRADE\_A}, \text{GRADE\_B}, \text{GRADE\_C}, \text{FAQ}\}$$
- **Channel Stratification**:
  $$Q(\tau) = \sum_{k: \tau_k = \tau} q_k, \quad \forall \tau \in \mathcal{T}$$

---

## 2. Market Power & Structural Concentration

In regional agricultural corridors, purchasing power is frequently concentrated among a small number of large institutional aggregators or agro-processors. To measure market depth and exposure risk without issuing subjective opinions, AgriClutch computes two formal structural metrics:

### 2.1 Herfindahl-Hirschman Index (HHI)
Let $M$ be the number of distinct commercial buyer entities ($M \le K$). Let $q^{(b)}$ be the total volume demanded by entity $b$:
$$q^{(b)} = \sum_{k: b_k = b} q_k$$
The market share of buyer $b$ is:
$$s_b = \frac{q^{(b)}}{Q_{\text{total}}}$$

The Herfindahl-Hirschman Index is computed as:
$$HHI = 10,000 \times \sum_{b=1}^M s_b^2$$

#### Regulatory & Structural Thresholds (Provenance: CONFIGURED)
The market concentration interpretive thresholds used in AgriClutch are classified as:
- **`provenance_status = CONFIGURED`**
- **Source Lineage**: Adapted convention based on the 1982/2010 U.S. Department of Justice & Federal Trade Commission (DOJ/FTC) Horizontal Merger Guidelines.
- **Methodological Disclosure**: These thresholds are **NOT** an empirical agricultural truth, an econometric standard, or an objective economic judgment. They are provided solely as a configured descriptive benchmark:
  - **$HHI < 1,500$ (Unconcentrated benchmark band)**: Purchasing volume distributed across multiple commercial entities.
  - **$1,500 \le HHI \le 2,500$ (Moderately concentrated benchmark band)**: Moderate volume consolidation among entities.
  - **$HHI > 2,500$ (Concentrated benchmark band)**: Stated procurement demand concentrated in fewer entities.

In the user interface, numeric HHI is prioritized directly, and categorical interpretation is explicitly labeled as a `CONFIGURED (DOJ/FTC CONVENTION)`.

### 2.2 Top Buyer Share Percentage
$$S_{\text{top}} = \left(\max_{b \in \{1,\dots,M\}} s_b\right) \times 100\%$$

---

## 3. Order Size Distribution & Sample-Size Gating ($N \ge 3$)

To understand commercial lot sizing (e.g., whether buyers expect bulk 10-tonne truckloads or smaller 500-kg crates), the engine computes descriptive order size quantiles.

### 3.1 Sample-Size Gating Protocol (Provenance: CONFIGURED)
- **`provenance_status = CONFIGURED`**
- **Definition**: *"Minimum descriptive sample-size gate used to suppress extremely small sample summaries."*
- **Methodological Disclosure**:
  - The threshold $N \ge 3$ is **NOT** described as statistically significant, universally sufficient, or an econometric standard.
  - It is a conservative heuristic gate designed to prevent displaying misleading parametric or quantile summaries (e.g. P10, Median, P90) from 1 or 2 observations.

$$\text{DistributionStatus} = \begin{cases}
\text{VALID} & \text{if } K \ge 3 \quad (\text{Configured gate satisfied}) \\
\text{INSUFFICIENT\_DATA} & \text{if } K < 3 \quad (\text{Quantiles suppressed})
\end{cases}$$

When status is `INSUFFICIENT_DATA`:
- `min_kg = null`
- `median_kg = null`
- `max_kg = null`
- All quantile estimates (`p10`, `p25`, `p50`, `p75`, `p90`) are withheld (`null`).

### 3.2 Quantile Estimation (when $K \ge 3$)
Using the standard continuous linear interpolation formulation (NumPy/SciPy method 7):
$$\min \le P_{10} \le P_{25} \le P_{50} (\text{Median}) \le P_{75} \le P_{90} \le \max$$
Arithmetic mean is also provided:
$$\mu_{\text{order}} = \frac{1}{K} \sum_{k=1}^K q_k$$

---

## 4. Non-Normative Transparency & Demo Disclosure

- **Demo Fixture Notice**: In demo mode, all demand aggregation and order distribution metrics are derived from synthetic demand orders representing 6 synthetic demo buyer entities representing commercial buyer archetypes (`provenance_status = DEMO`, `is_demo = true`).
- **Zero Recommendation Policy**: All demand statistics represent factual aggregation of procurement postings. AgriClutch does not endorse any specific order, rank buyers, or advise selling into any specific volume pocket in Step 12.

