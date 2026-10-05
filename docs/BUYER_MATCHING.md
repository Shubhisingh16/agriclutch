# AgriClutch: Buyer Matching Engine Specification

> **Subsystem**: Multi-Dimensional Candidate Compatibility Engine  
> **Module Path**: `ml/buyer/compatibility.py` & `backend/app/services/buyer_service.py`  
> **Status**: Verified Clean-Room Implementation  

---

## 1. Mathematical Formulation

Let a farmer produce lot supply be denoted by the tuple:
$$S = \langle c, v, q, g, [t_{s,\text{avail}}, t_{e,\text{avail}}], \mathbf{x}_{\text{origin}}, \text{storage} \rangle$$
where:
- $c \in \mathcal{C}$: Commodity identifier (e.g., `tomato`, `onion`, `potato`)
- $v$: Variety designation or `null`
- $q \in \mathbb{R}^+$: Available quantity in kilograms
- $g \in \{\text{GRADE\_A}, \text{GRADE\_B}, \text{GRADE\_C}, \text{FAQ}\}$: Quality grade
- $[t_{s,\text{avail}}, t_{e,\text{avail}}]$: Calendar availability window
- $\mathbf{x}_{\text{origin}} = (\phi_{\text{origin}}, \lambda_{\text{origin}})$: Farmgate GPS latitude and longitude

Let a commercial buyer requirement specification be denoted by:
$$B_j = \langle c_j, \mathcal{V}_j, [q_{\min, j}, q_{\max, j}], g_{\text{pref}, j}, \mathcal{G}_{\text{acc}, j}, [t_{s, j}, t_{e, j}], d_{\text{mode}, j}, \mathbf{x}_{\text{deliv}, j}, R_{\max, j}, P_j, T_j \rangle$$

The candidate compatibility indicator is a boolean conjunction over six independent dimensional evaluations:
$$\text{IsCompatible}(S, B_j) = E_{\text{commodity}} \land E_{\text{variety}} \land E_{\text{quality}} \land E_{\text{quantity}} \land E_{\text{temporal}} \land E_{\text{spatial}}$$

---

## 2. Dimensional Evaluation Functions

### 2.1 Commodity & Variety Compatibility
- **Commodity Constraint**:
  $$E_{\text{commodity}} = \mathbb{I}(c = c_j)$$
- **Variety Constraint**:
  $$E_{\text{variety}} = \mathbb{I}\left(v_j \text{ is } \text{null} \lor v = v_j \lor v \in \mathcal{V}_j\right)$$

### 2.2 Quality Grade Compatibility
A buyer specifies a preferred grade $g_{\text{pref}}$ and a non-empty set of acceptable grades $\mathcal{G}_{\text{acc}}$:
$$E_{\text{quality}} = \mathbb{I}\left(g \in \mathcal{G}_{\text{acc}, j} \lor g = g_{\text{pref}, j}\right)$$

### 2.3 Quantity Boundary Evaluation & Partitioning
Unlike binary filters, AgriClutch partitions lot volume into compatible and unmatched segments:
$$\text{QuantityStatus}(q, B_j) = \begin{cases}
\text{BELOW\_MINIMUM} & \text{if } q < q_{\min, j} \\
\text{FULLY\_SATISFIES} & \text{if } q_{\min, j} \le q \le q_{\max, j} \\
\text{EXCEEDS\_MAXIMUM\_PARTIAL} & \text{if } q > q_{\max, j}
\end{cases}$$

- **Compatible Quantity**:
  $$q_{\text{compat}} = \begin{cases}
  0 & \text{if } q < q_{\min, j} \\
  \min(q, q_{\max, j}) & \text{if } q \ge q_{\min, j}
  \end{cases}$$
- **Unmatched Residual Supply**:
  $$q_{\text{unmatched}} = \max(0, q - q_{\text{compat}})$$
- **Feasibility Indicator**:
  $$E_{\text{quantity}} = \mathbb{I}(q_{\text{compat}} > 0)$$

### 2.4 Temporal Delivery Overlap
Let the date intersection between availability and demand be $[t_{\text{start}}, t_{\text{end}}]$:
$$t_{\text{start}} = \max(t_{s,\text{avail}}, t_{s, j}), \quad t_{\text{end}} = \min(t_{e,\text{avail}}, t_{e, j})$$
$$\Delta t_{\text{overlap}} = \max\left(0, \lfloor t_{\text{end}} - t_{\text{start}} \rfloor + 1\right)$$

$$\text{TemporalStatus} = \begin{cases}
\text{COMPLETE\_OVERLAP} & \text{if } t_{s,j} \ge t_{s,\text{avail}} \land t_{e,j} \le t_{e,\text{avail}} \\
\text{PARTIAL\_OVERLAP} & \text{if } \Delta t_{\text{overlap}} > 0 \land \neg \text{COMPLETE\_OVERLAP} \\
\text{NO\_OVERLAP} & \text{if } \Delta t_{\text{overlap}} = 0
\end{cases}$$

$$E_{\text{temporal}} = \mathbb{I}(\Delta t_{\text{overlap}} > 0)$$

### 2.5 Geospatial Distance & Transit Feasibility
Let the great-circle geodesic distance between $\mathbf{x}_{\text{origin}} = (\phi_1, \lambda_1)$ and $\mathbf{x}_{\text{deliv}} = (\phi_2, \lambda_2)$ be computed via the spherical Haversine formula:
$$\Delta \phi = \frac{\pi}{180} (\phi_2 - \phi_1), \quad \Delta \lambda = \frac{\pi}{180} (\lambda_2 - \lambda_1)$$
$$a = \sin^2\left(\frac{\Delta \phi}{2}\right) + \cos\left(\frac{\pi}{180}\phi_1\right) \cos\left(\frac{\pi}{180}\phi_2\right) \sin^2\left(\frac{\Delta \lambda}{2}\right)$$
$$d_{\text{km}}(\mathbf{x}_{\text{origin}}, \mathbf{x}_{\text{deliv}}) = 2 R_{\text{earth}} \arctan_2\left(\sqrt{a}, \sqrt{1-a}\right), \quad R_{\text{earth}} = 6371.0\text{ km}$$

$$\text{DistanceStatus} = \begin{cases}
\text{DISTANCE\_DIRECT} & \text{if coordinates present and within } R_{\max} \\
\text{DISTANCE\_UNAVAILABLE} & \text{if coordinates absent (fails open with warning if radius unconstrained)}
\end{cases}$$

$$E_{\text{spatial}} = \mathbb{I}\left(d_{\text{km}} \le R_{\max} \lor R_{\max} \text{ is } \infty\right)$$

---

## 3. Explanations & Additive Justifications

For every match evaluated, the engine returns a list of human-readable, auditable bullet points:
- Positive fulfillment facts:
  - `Quality Grade A matches requirement [Grade A, Grade B]`
  - `Quantity 2,500 kg satisfies requirement range [1,000 - 5,000 kg]`
  - `Temporal overlap of 8 days (2026-10-02 to 2026-10-10)`
  - `Distance 18.4 km within delivery radius 40.0 km`
  - `Payment terms: IMMEDIATE_CASH; Price basis: FIXED_QUOTE (₹28.50/kg)`
- Negative constraint facts:
  - `Produce quantity 500 kg is below buyer minimum requirement of 1,000 kg`
  - `Zero calendar day overlap between availability and buyer demand window`
  - `Delivery distance 120.4 km exceeds maximum radius 50.0 km`

---

## 4. Non-Normative Principle

Matching output objects strictly omit any composite scoring (e.g. `score = 87/100`), preference ranking, or recommendations. The downstream split optimization solver (Step 13) is responsible for optimizing allocation fractions based on Net Realizable Value, risk preferences, and portfolio diversification.
