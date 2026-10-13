# Phase 6 — Data Extraction, Ingestion & Data Quality Report

- **Report Version:** 1.0.0
- **Compliance:** `GLOBAL-INSTRUCTIONS.md` and `phase-06-data-extraction-quality.md`
- **Execution Mode:** Offline Local Execution

---

## 1. Candidate Files & Cryptographic Fingerprints

All candidate files in the workspace are hashed, verified, and inventoried:

| Filename | File Path | File Format | SHA-256 Digest | Size (Bytes) | Governance Classification |
|---|---|---|---|---|---|
| `cstr_rawdata.npy` | `data/raw/quarantine/cstr_rawdata.npy` | NumPy binary (.npy) | `9a0ec1115e8b2e947487c2688c924e3f0382a6ee1bfea39e8dd652542ee9c4e9` | 32,123,648 | **QUARANTINED** (Undocumented columns) |
| `CSTR_24aug_PRBS_dataset.xlsx` | `data/raw/CSTR_24aug_PRBS_dataset.xlsx` | OpenPyXL (.xlsx) | `0e42ce8af6e05cdcd3c8a39eb1e0d54c9478a9623475d1bc64408e3c23d3d3bd` | 297,991 | **PRESERVED** (Thermal RTD sensor data only) |

---

## 2. Binary Array Audit: `cstr_rawdata.npy`

### 2.1 Safe Loading Verification
Loaded strictly with `allow_pickle=False` via NumPy:
- **Array Shape:** $(2860, 1404)$ (2,860 rows × 1,404 columns)
- **Data Type:** `float64`
- **Pickle Security:** Verified safe (`allow_pickle=False` loads without unpickling arbitrary objects)
- **Numerical Integrity:**
  - Minimum value: $-30.5445$
  - Maximum value: $566.6622$
  - Arithmetic mean: $240.0905$
  - Missing values (NaN / null): $0$
  - Non-finite values ($\pm \infty$): $0$

### 2.2 Quarantine & Risk Governance
The file contains an unlabeled matrix without column headers, timestamps, units, or feature definitions. Guessing column assignments is strictly forbidden by `GLOBAL-INSTRUCTIONS.md`. The dataset is quarantined and excluded from all concentration and kinetic modeling.

---

## 3. Spreadsheet Workbook Audit: `CSTR_24aug_PRBS_dataset.xlsx`

### 3.1 Sheet Inspection
The workbook was inspected via `openpyxl`:
- **Sheets Present:**
  1. `CSTR Dataset` (Primary data sheet, 3,132 rows × 9 columns)
  2. `Input Plots` (Embedded chart sheet, 0 data rows)
  3. `Output plots` (Embedded chart sheet, 0 data rows)

### 3.2 Structure & Column Profiling (`CSTR Dataset`)
- **Row Count:** 3,132
- **Column Count:** 9
- **Header Structure:** Multi-level header structure indicating:
  - PRBS input signals (manipulated flow / voltage signals)
  - Measured RTD temperature sensor values (jacket, tank, bath)
- **Concentration Analysis:**
  - $C_A$ / concentration measurements: **ABSENT**
  - Chemical reactant units (e.g. $\text{mol/L}$, $\text{kmol/m}^3$): **ABSENT**
- **Assessment:** Contains thermal telemetry suitable for Phase 13 non-isothermal energy balances, but **cannot validate chemical concentration or reaction kinetics**.

---

## 4. Scientific Column Dictionary & Units Mapping

The ingestion engine maps arbitrary user and laboratory datasets into canonical engineering units:

| Canonical Variable | Symbol | Canonical Unit | Supported Input Units | Conversion Factor to Canonical | Notes |
|---|---|---|---|---|---|
| **Time** | $t$ | $\text{min}$ | $\text{min}, \text{s}, \text{h}$ | $1.0$, $1/60$, $60.0$ | Verified for monotonic increase; chronologically reordered if required. |
| **Effluent Concentration** | $C_{A,\text{out}}$ | $\text{mol/L}$ | $\text{mol/L}, \text{kmol/m}^3, \text{mol/m}^3, \text{mmol/L}$ | $1.0$, $1.0$, $10^{-3}$, $10^{-3}$ | Main observation series for dynamic fitting. |
| **Inlet Concentration** | $C_{A,\text{in}}$ | $\text{mol/L}$ | $\text{mol/L}, \text{kmol/m}^3, \text{mol/m}^3, \text{mmol/L}$ | $1.0$, $1.0$, $10^{-3}$, $10^{-3}$ | Can be variable time series or constant operating feed. |
| **Reactor Volume** | $V$ | $\text{L}$ | $\text{L}, \text{m}^3, \text{cm}^3, \text{mL}$ | $1.0$, $1000.0$, $10^{-3}$, $10^{-3}$ | Used with flow rate to calculate $\tau = V/Q$. |
| **Volumetric Flow** | $Q$ | $\text{L/min}$ | $\text{L/min}, \text{m}^3/\text{h}, \text{L/h}, \text{mL/min}$ | $1.0$, $1000/60$, $1/60$, $10^{-3}$ | Denominator of residence time. |
| **Fractional Conversion** | $X_A$ | dimensionless | fraction $[0, 1]$ | — | Calculated as $(C_{\text{in}} - C_{\text{out}})/C_{\text{in}}$ when $C_{\text{in}} > 0$. |

---

## 5. Ingestion Engine & Quality Filters

### 5.1 Savitzky–Golay Polynomial Smoothing
- Formulated as local unweighted polynomial least-squares smoothing via `scipy.signal.savgol_filter`.
- **Preconditions Enforced:** Window length $w$ must be an odd positive integer ($w \ge 3$) and polynomial order $p < w$.
- **Transient Preservation Notice:** Raw and filtered series are preserved simultaneously; step-change rounding warnings are presented to the engineer.

### 5.2 Isolation Forest Non-Destructive Anomaly Detection
- Formulated using `sklearn.ensemble.IsolationForest` on feature vector $[t, C_{A,\text{out}}]$.
- **Contamination Parameter:** User-controllable proportion $\alpha \in [0.01, 0.25]$.
- **Non-Destructive Guarantee:** Suspected anomalous rows are flagged with `is_anomaly = True` and scored, but **never deleted or silently dropped**, ensuring strict auditability.

---

## 6. Dataset-Task Compatibility Matrix

| Project Task / Phase | `cstr_rawdata.npy` | `CSTR_24aug_PRBS_dataset.xlsx` | Synthetic Mechanistic Benchmarks |
|---|---|---|---|
| **Phase 1–5: Isothermal CSTR Core** | Incompatible (Undocumented) | Incompatible (No concentration) | **Compatible & Verified** |
| **Phase 7: Parameter Estimation** | Incompatible | Incompatible | **Compatible & Verified** |
| **Phase 8–11: Scientific ML (Neural ODE / PINN)** | Incompatible | Incompatible | **Compatible & Verified** |
| **Phase 12: Persistent History & Export** | Incompatible | Incompatible | **Compatible & Verified** |
| **Phase 13: Coupled Thermal CSTR** | Incompatible | **Compatible (Thermal RTD telemetry)** | **Compatible & Verified** |
| **Phase 15: Release Regression Suite** | Incompatible (Quarantine Locked) | Audited Candidate Reference | **Compatible & Verified** |
