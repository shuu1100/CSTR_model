# CSTR Lab — Data Governance & Candidate Datasets Protocol

## 1. Governance Principles & Folder Segmentation

To maintain complete scientific reproducibility and prevent data contamination, files are strictly segregated into explicit lifecycle tiers:

| Directory | Purpose | Mutability |
|---|---|---|
| `data/raw/` | Pristine source candidate files, vendor exports, original workbooks. | **Read-Only** (Immutable) |
| `data/interim/` | Intermediate cleaning steps, parsed tabular extractions. | Disposable / Reproducible |
| `data/processed/` | Standardized, verified, and unit-harmonized datasets. | Versioned |
| `data/generated/` | Mechanistically simulated synthetic data, LHS trajectories, benchmarks. | Fully reproducible from code & seed |
| `artifacts/models/` | Trained machine learning model weights, encoders, scalers. | Versioned with metadata |
| `reports/` | Automated dataset audits, data cards, and quality reports. | Versioned Markdown |

---

## 2. Candidate Dataset Audit & Cryptographic Verification

All candidate files in the workspace have been cryptographically hashed and inspected:

### 2.1 Candidate Files Manifest

| Filename | SHA-256 Digest | Size | Verified Schema / Content | Governance Status |
|---|---|---|---|---|
| `data/raw/cstr_rawdata.npy` | `9a0ec1115e8b2e947487c2688c924e3f0382a6ee1bfea39e8dd652542ee9c4e9` | 32,123,648 B (~30.6 MB) | Shape: (2860, 1404), dtype: `float64`, Range: [-30.54, 566.66]. Mean: 240.09. Zero NaNs. **No headers, no units, unknown signal mapping.** | **QUARANTINED** |
| `data/raw/CSTR_24aug_PRBS_dataset.xlsx` | `0e42ce8af6e05cdcd3c8a39eb1e0d54c9478a9623475d1bc64408e3c23d3d3bd` | 297,991 B (~291 KB) | 3 sheets: `CSTR Dataset` (3132 rows × 9 cols), `Input Plots` (empty), `Output plots` (empty). Contains PRBS feed flows & RTD temperature sensor values. **Zero concentration measurements.** | **PRESERVED FOR THERMAL CALIBRATION (PHASE 13)** |

### 2.2 Quarantine & Usage Policies
1. **Quarantine of `cstr_rawdata.npy`:** In strict compliance with `GLOBAL-INSTRUCTIONS.md`, guessing column semantics or inferring labels is prohibited. This dataset is quarantined until laboratory documentation is supplied. It shall not be used for model training or benchmark validation.
2. **Compatibility Scope of `CSTR_24aug_PRBS_dataset.xlsx`:** Because the workbook contains temperature and flow signals but no chemical concentration readings ($C_A$), it is **incompatible** with isothermal concentration validation (Phases 1–12). It is preserved read-only in `data/raw/` as candidate data for Phase 13 non-isothermal thermal energy balance calibration.

---

## 3. Data Splitting & Leakage Prevention Protocol

To guarantee unbiased machine learning evaluation, the following rules are enforced:

### 3.1 Partition Strategy
- **Synthetic Mechanistic Data:** 70% Train / 15% Validation / 15% Test.
- **Split Unit:** Partitioning is performed strictly by **independent trajectory ID** or parameter run ID, never by individual time step rows.
- **Disjoint Guarantee:** An automated programmatic assertion (`partition.assert_disjoint()`) verifies that $\text{Train} \cap \text{Val} = \emptyset$, $\text{Train} \cap \text{Test} = \emptyset$, and $\text{Val} \cap \text{Test} = \emptyset$.

### 3.2 Feature Preprocessing & Transformation Fitting
- **Train-Only Fitting:** Scalers (e.g. `StandardScaler`, `MinMaxScaler`), imputers, and dimensionality reduction models are fit **strictly** on the training partition.
- **Transform Application:** Fitted transformers are applied to validation and test partitions without re-estimating parameters.
- **Holdout Locking:** The test set is locked until model architecture and hyperparameters are finalized. Test data is never used for hyperparameter tuning.

### 3.3 Audit Trail & Provenance
Every generated dataset and model artifact records:
- Git/Code version (`CODE_VERSION`).
- Random seeds used for generation and splitting.
- Explicit `provenance` tags (`SYNTHETIC_MECHANISTIC_SOLVER`, `EXPERIMENTAL_OBSERVED`).
- SHA-256 hash of source configurations and underlying datasets.
