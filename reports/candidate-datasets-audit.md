# Candidate Datasets Audit & Compatibility Matrix

- **Audit Date:** 2026-10-13
- **Audit Policy:** Strictly adhering to GLOBAL-INSTRUCTIONS.md

## 1. Candidate Files & Cryptographic Hashes

| Filename | SHA-256 Hash | Size (Bytes) | Status |
|---|---|---|---|
| `cstr_rawdata.npy` | `9a0ec1115e8b2e947487c2688c924e3f0382a6ee1bfea39e8dd652542ee9c4e9` | 32,123,648 | **QUARANTINED** |
| `CSTR_24aug_PRBS_dataset.xlsx` | `0e42ce8af6e05cdcd3c8a39eb1e0d54c9478a9623475d1bc64408e3c23d3d3bd` | 297,991 | **AUDITED / THERMAL ONLY** |

## 2. Array Analysis: `cstr_rawdata.npy`

- **Dimensions:** 2860 rows × 1404 columns
- **Data Type:** `float64`
- **Numerical Range:** [-30.5445, 566.6622]
- **Mean:** 240.0905
- **Missing Values (NaN):** 0
- **Inf Values:** 0
- **Assessment:** Unlabeled multi-dimensional floating-point array with no feature dictionary or timestamp definitions. In accordance with GLOBAL-INSTRUCTIONS.md, this dataset is **quarantined** and will not be used for supervised model training.

## 3. Workbook Analysis: `CSTR_24aug_PRBS_dataset.xlsx`

- **Sheets Found:** CSTR Dataset, Input Plots, Output plots

### Sheet: `CSTR Dataset`
- Rows: 3132, Columns: 9
- Columns: `Unnamed: 0, PRBS Input Signals (Scaled from Multilevel PRBS to actual values), Unnamed: 2, Unnamed: 3, Unnamed: 4, Measure RTD Sensor values, Unnamed: 6, Unnamed: 7, Unnamed: 8`

### Sheet: `Input Plots`
- Rows: 0, Columns: 0
- Columns: ``

### Sheet: `Output plots`
- Rows: 0, Columns: 0
- Columns: ``

## 4. Dataset-Task Compatibility Matrix

| Task / Phase | `cstr_rawdata.npy` | `CSTR_24aug_PRBS_dataset.xlsx` | Rationale |
|---|---|---|---|
| **Phase 1–5: Isothermal Steady/Dynamic Core** | Incompatible | Incompatible | Both candidate files do not contain verified reactant concentrations. |
| **Phase 7: Kinetic Parameter Estimation** | Incompatible | Incompatible | Kinetic estimation requires concentration time series $C_A(t)$ or conversion $X_A$. |
| **Phase 8: Synthetic Data & Splits** | N/A | N/A | Generated from the tested mechanistic ODE solver. |
| **Phase 9–11: Neural ODE & PINN Kinetic Modeling** | Incompatible | Incompatible | Cannot fit reaction kinetics $r_A(C_A)$ without measured concentration. |
| **Phase 13: Arrhenius & Thermal CSTR** | Incompatible | **Candidate Match** | Contains reactor/jacket/bath temperatures and feed flow rates for thermal energy balance. |
