# Experimental Data Ingestion and Analysis

This document describes the engineering architecture, mathematical processing, data hygiene constraints, and validation protocols for experimental and user-provided datasets in **CSTR Lab**.

---

## 1. Safety and Ingestion Limits

Uploaded datasets are never trusted blindly or executed. Raw bytes are parsed in memory using **Pandas** and **OpenPyXL** under explicit security guards:

| Parameter | Limit | Description / Rationale |
| :--- | :--- | :--- |
| **Max File Size** | 10 MB | Guards backend memory against out-of-memory DoS vectors. |
| **Max Rows** | 50,000 rows | Sufficient for high-frequency laboratory transient runs (e.g. 10 Hz over 80 min). |
| **Max Columns** | 50 columns | Blocks wide or malformed spreadsheet matrices. |
| **Allowed Formats** | `.csv`, `.tsv`, `.xlsx`, `.xls` | Disallows executable, binary, or script extensions. |

### Column & Missing-Value Profiling
Upon file upload via `POST /api/v1/datasets/upload`:
- Header names and data types are extracted.
- Missing (NaN/null) values per column are tabulated.
- Duplicate row counts are calculated.
- The top 10 preview rows are returned for immediate inspection.

---

## 2. Scientific Column Mapping & Canonical Normalization

Users map arbitrary dataset columns to physical CSTR variables:
- **Time ($t$)**: Mapped to canonical unit $\text{min}$ from $\text{min}, \text{s}, \text{h}$. Monotonicity is verified; non-monotonic timestamps trigger chronological re-sorting and warning notices.
- **Outlet Concentration ($C_{A,\text{out}}$)**: Mapped to canonical unit $\text{mol/L}$ from $\text{mol/L}, \text{kmol/m}^3, \text{mol/m}^3, \text{mmol/L}$.
- **Inlet Feed ($C_{A,\text{in}}$)**: Can be mapped to a variable time-series column or fixed as an operating constant.
- **Reactor Volume ($V$) & Volumetric Flow Rate ($Q$)**: Optional columns or operating constants used to determine residence time $\tau = V / Q$.

---

## 3. Measured Conversion Formulation & Boundary Checks

The fractional conversion of reactant A is calculated strictly when inlet concentration is strictly positive ($C_{A,\text{in}} > 0$):

$$X_A = \frac{C_{A,\text{in}} - C_{A,\text{out}}}{C_{A,\text{in}}}$$

### Mathematical Boundary Handling:
- If $C_{A,\text{in}} \le 0$ or is missing, conversion is assigned `None` / `null` (never divided by zero or producing infinite residuals).
- If measurement noise causes $C_{A,\text{out}} > C_{A,\text{in}}$ ($X_A < 0$) or $C_{A,\text{out}} < 0$ ($X_A > 1$), **data points are preserved**. Out-of-bound occurrences are flagged in `data_quality_warnings` rather than silently deleted.

---

## 4. Digital Filtering: Savitzky–Golay Smoothing

High-frequency sensor noise (e.g. optical absorbance fluctuation, conductivity jitter) can be optionally smoothed using a **Savitzky–Golay digital filter** (`scipy.signal.savgol_filter`).

### Filter Formulation:
For a local window of $2m+1$ points centered at index $i$:

$$\hat{y}_i = \sum_{j=-m}^{m} c_j y_{i+j}$$

where coefficients $c_j$ are determined via local unweighted least-squares polynomial fitting of order $p$.

### Constraints & Warnings:
1. **Odd Window Requirement**: Window size $w$ must be an odd positive integer ($w \in \{3, 5, 7, \dots\}$).
2. **Degree Constraint**: Polynomial order $p$ must satisfy $1 \le p < w < N$.
3. **Transient Attenuation Warning**: Savitzky–Golay filters preserve peak area and lower-order moments, but high-order step changes (e.g. instantaneous feed disturbances) can be smoothed or rounded. Both raw and smoothed time-series are preserved and plotted side-by-side.

---

## 5. Non-Destructive Anomaly Detection: Isolation Forest

Potential sensor glitches, bubble passes, or communication spikes are identified using an **Isolation Forest** unsupervised ensemble model (`sklearn.ensemble.IsolationForest`).

- **Feature Space**: $\mathbf{x} = [t, C_{A,\text{out}}]$.
- **Contamination**: User-selectable expected outlier proportion $\alpha \in [0.01, 0.25]$ (default 5%).
- **Non-Deletion Guarantee**: Outlier points receive an anomaly score and boolean flag `is_anomaly`. They are highlighted as distinct visual diamond markers. **No point is automatically pruned or discarded**, ensuring complete experimental auditability.

---

## 6. Provenance Disclosure

Every processed dataset carries the immutable provenance banner:

> **USER-PROVIDED DATA: This dataset was uploaded by the user. Its authenticity, experimental accuracy, and provenance are unverified.**
