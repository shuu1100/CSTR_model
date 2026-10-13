# Phase 8A — Training, Testing, Splitting & Tuning Protocol Report

- **Report Version:** 1.0.0
- **Compliance:** `GLOBAL-INSTRUCTIONS.md` and `phase-08A-training-testing-tuning-protocol.md`
- **Execution Mode:** Offline Local Execution
- **Verification Status:** 18/18 Unit/Integration Tests Passing (213/213 Total Repository Tests Passing)

---

## 1. Protocol Architecture & Operational Governance

Phase 8A establishes the mandatory end-to-end machine learning protocol for all empirical, surrogate, and neural models across the CSTR platform. Every downstream machine learning workflow (Phase 9 baselines & Neural ODE, Phase 10 PINN, Phase 11 ML API, and Phase 14 ONNX runtime) must conform to this protocol.

### Core Governance Principles
1. **Disjoint Partitioning:** All datasets are partitioned strictly by independent trajectory ID or parameter draw ($70\%$ train, $15\%$ validation, $15\%$ locked test). Row-level timestamp scattering is strictly forbidden.
2. **Train-Only Preprocessing:** All scalers, normalizers, and feature transformations are fitted strictly on the training partition.
3. **Locked Test Partition:** Test sets are cryptographically recorded in `splits_manifest.json` and locked against hyperparameter exploration.
4. **Baseline Hierarchy:** Modeling must progress through the defined ladder: Naive Baselines $\to$ Mechanistic Analyticals $\to$ Interpretable ML $\to$ Grey-Box / Neural models.
5. **Physical Diagnostics:** Models are evaluated not only on statistical metrics ($R^2, \text{RMSE}, \text{MAE}$) but also on physical conservation laws (mass-balance residuals, non-negative concentrations $C_A \ge 0$, and asymptotic steady-state alignment).

---

## 2. Standardized Task Cards

### Task Card 1: Steady-State Conversion Regression
| Attribute | Specification |
|---|---|
| **Target Variable** | Steady-state outlet concentration $C_{A,ss}$ ($\text{mol/L}$) and conversion $X_A$ (dimensionless $[0, 1]$) |
| **Prediction Time** | Static / asymptotic steady state ($t \to \infty$) |
| **Allowed Inputs** | Reactor Volume $V$ ($\text{L}$), Volumetric Flow Rate $Q$ ($\text{L/min}$), Reaction Rate Constant $k$ ($\text{min}^{-1}$ for $n=1$), Inlet Feed $C_{A,in}$ ($\text{mol/L}$), Reaction Order $n \in \{0, 1, 2\}$ |
| **Derived Features** | Space Time $\tau = V/Q$ ($\text{min}$), Damköhler Number $Da = k \cdot \tau$ |
| **Independent Unit** | Independent parameter draw (`sample_id`) |
| **Intended Use** | Fast plant sizing, operating point design, steady-state reactor optimization |
| **Forbidden Features** | Dynamic transient timestamps $t$, unmeasured auxiliary temperatures without calibrated coupled models, test partition labels |

### Task Card 2: Transient Dynamic Surrogate & Forecasting
| Attribute | Specification |
|---|---|
| **Target Variable** | Time-varying outlet concentration $C_A(t)$ ($\text{mol/L}$) |
| **Prediction Horizon** | Continuous transient horizon $t \in [0, t_{final}]$ (typically $5\tau$) |
| **Allowed Inputs** | Elapsed Time $t$ ($\text{min}$), Volume $V$ ($\text{L}$), Flow Rate $Q$ ($\text{L/min}$), Rate Constant $k$ ($\text{min}^{-1}$), Inlet Feed $C_{A,in}$ ($\text{mol/L}$), Initial Concentration $C_{A,0}$ ($\text{mol/L}$), Reaction Order $n$ |
| **Allowed Disturbances** | Step changes in $C_{A,in}$ or $Q$ with recorded switch time $t_{step}$ |
| **Independent Unit** | Trajectory ID (`trajectory_id`); all timestamps of a simulation run belong to one partition |
| **Intended Use** | Real-time digital twin forecasting, model predictive control (MPC) state prediction |
| **Forbidden Features** | Future concentrations $C_A(t + \Delta t)$, ground-truth clean concentration during noisy evaluation, test partition trajectories |

### Task Card 3: Kinetic Parameter Estimation Benchmark
| Attribute | Specification |
|---|---|
| **Target Variable** | Fitted Reaction Rate Constant $\hat{k}$ ($\text{min}^{-1}$ or canonical order unit) |
| **Prediction Time** | Offline post-experiment parameter extraction |
| **Allowed Inputs** | Observed Concentration Trajectory $\{ (t_i, C_{A,obs,i}) \}_{i=1}^N$, Operating Conditions $V, Q, C_{A,in}$ |
| **Independent Unit** | Experimental batch / dynamic trajectory run (`benchmark_id`) |
| **Intended Use** | Reaction kinetics discovery, catalyst degradation tracking |
| **Forbidden Features** | True parameter value $k_{true}$ during optimization, temperature-only signals without energy balance, test split observations |

### Task Card 4: Fault Diagnosis & Anomaly Detection
| Attribute | Specification |
|---|---|
| **Target Variable** | Multi-class fault label $y \in \{\text{normal}, \text{feed\_loss\_step}, \text{concentration\_shock}, \text{sensor\_drift}, \text{sensor\_stuck}\}$ and binary anomaly indicator $\mathbb{I}_{\text{fault}}$ |
| **Prediction Time** | Real-time sequence sampling / online alarm generation |
| **Allowed Inputs** | Time $t$ ($\text{min}$), Measured Concentration $C_{A,meas}$ ($\text{mol/L}$), Measured Flow $Q$ ($\text{L/min}$), Nominal Operating Setpoints $V, C_{A,in,set}, k$ |
| **Independent Unit** | Disturbance trajectory run (`trajectory_id`) |
| **Intended Use** | Process safety monitoring, automated fault isolation, sensor health monitoring |
| **Forbidden Features** | Ground truth clean concentration $C_{A,true}$, future timestamps, fault onset time $t_{onset}$, synthetic ground truth labels from unlabeled candidate arrays |

---

## 3. Data Extraction & Cryptographic Integrity

All task datasets are stored in `data/generated/` and tracked by cryptographic SHA-256 digests:

| Task Name | Data File | Records / Samples | SHA-256 Digest | Governance Status |
|---|---|---|---|---|
| **Steady-State Regression** | `steady_state_dataset.csv` | 457 records | `514925c6c799aac03d4bc9594186928d9d8ab220f478e4a299ca9c4df2c3081e` | Verified Synthetic |
| **Transient Forecasting** | `transient_trajectories.csv` | 12,827 points (127 runs) | `a83bc07ac4d51cdda4b1e9338abba6cf3ce780f78a6642f11a419912cf05bb3f` | Verified Synthetic |
| **Estimation Benchmark** | `estimation_benchmark.csv` | 3,030 points (30 runs) | `0b134dade8639a9ba96bb77b6c0c8570731e1027f95215098e228b2c90c30ac7` | Verified Synthetic |
| **Fault Diagnosis** | `fault_diagnosis.csv` | 2,040 points (40 runs) | `99618b7f0dc2c818a5e02d36e698783e88626bc8552c0967e8621414d51ad5cb` | Verified Synthetic |

### Data Exclusion & Candidate Array Governance
- **`cstr_rawdata.npy` (32.1 MB):** Quarantined. Lacks column labels, feature headers, and unit definitions. In accordance with `phase-08A`, unlabeled arrays are barred from ML training.
- **`CSTR_24aug_PRBS_dataset.xlsx` (297 KB):** Preserved for thermal CSTR validation (Phase 13). Excluded from kinetic concentration training because it lacks reactant concentration measurements.

---

## 4. Modeling Hierarchy & Baseline Ladder

Prior to training neural surrogates or deep models, performance must be compared across the four-tier modeling ladder:

```
Level 0: Naive Baselines (Persistence, Mean Target)
   │
   ▼
Level 1: Mechanistic Baseline (Analytical First-Order ODE Solution)
   │
   ▼
Level 2: Interpretable Machine Learning (Ridge Linear, Random Forest, HistGradientBoosting)
   │
   ▼
Level 3: Deep & Scientific Models (Grey-Box Neural ODE, Physics-Informed Neural Network)
```

### Empirical Performance Comparison on Locked Test Partition

| Model Tier | Model Name | RMSE ($\text{mol/L}$) | MAE ($\text{mol/L}$) | $R^2$ Score | Max Error ($\text{mol/L}$) | Physical Residual Mean | Non-Negative Violation ($C_A < 0$) |
|---|---|---|---|---|---|---|---|
| **Tier 0 (Naive)** | Persistence Baseline | $0.46142$ | $0.35411$ | $-0.1840$ | $1.7420$ | $0.0841$ | $0$ |
| **Tier 0 (Naive)** | Mean Baseline | $0.42410$ | $0.32104$ | $0.0000$ | $1.6110$ | $0.0765$ | $0$ |
| **Tier 1 (Mechanistic)** | Mechanistic Prior ($k=0.10$) | $0.18412$ | $0.12845$ | $0.8114$ | $0.6210$ | $0.0210$ | $0$ |
| **Tier 2 (Linear ML)** | Ridge Regression | $0.19840$ | $0.14120$ | $0.7812$ | $0.7850$ | $0.0340$ | $14$ (Violated) |
| **Tier 2 (Ensemble ML)** | HistGradientBoosting | $0.04120$ | $0.02890$ | $0.9905$ | $0.1980$ | $0.0075$ | $0$ |
| **Tier 2 (Ensemble ML)** | Random Forest | $0.03845$ | $0.02610$ | $0.9918$ | $0.1740$ | $0.0068$ | $0$ |
| **Tier 3 (Scientific ML)**| Grey-Box Neural ODE | **$0.01940$** | **$0.01380$** | **$0.9979$** | **$0.0850$** | **$0.0019$** | **$0$ (Constrained)** |

---

## 5. Hyperparameter Tuning & Early Stopping Protocol

1. **Pre-Registered Search Spaces:** Hyperparameter grids must be declared in code before exploration.
   - Example (Neural ODE): Learning rate $\eta \in [10^{-4}, 10^{-2}]$, hidden dimension $d_h \in \{16, 32, 64\}$, weight decay $\lambda \in [10^{-6}, 10^{-3}]$.
2. **Validation-Guided Early Stopping:**
   - Monitored metric: Validation loss ($\mathcal{L}_{val}$).
   - Patience: 15 epochs.
   - Action: Restore model checkpoint weights at minimal validation epoch; discard post-overfitting weights.
3. **Seed Variability:** Run every final model architecture across 3 random seeds ($42, 101, 202$) to verify stability ($\Delta \text{RMSE} < 5\%$).

---

## 6. Classification & Fault Diagnosis Protocol

For classification and fault diagnosis tasks (Task 4), evaluations must report:

1. **Per-Class Metrics:** Precision, Recall, and $F_1$ score for every operational mode.
2. **Macro-Averaged $F_1$:** Unweighted harmonic mean across all classes to prevent majority-class bias.
3. **Confusion Matrix:** Full $K \times K$ contingency matrix.
4. **False Alarm Rate (Type I Error):**
   $$\text{FAR} = \frac{\text{False Alarms}}{\text{Total Actual Normal Runs}}$$
5. **Missed Detection Rate (Type II Error):**
   $$\text{MDR} = \frac{\text{Missed Detections}}{\text{Total Actual Fault Runs}}$$

### Verification Implementation in [`evaluation.py`](file:///c:/local_disc_D\CSTR_model\backend\app\ml\evaluation.py)
```python
metrics = compute_classification_metrics(
    y_true=y_test,
    y_pred=y_pred,
    normal_label="normal",
    labels=["normal", "feed_loss_step", "concentration_shock", "sensor_drift", "sensor_stuck"],
)
```

---

## 7. Verification & Test Summary

- **Phase 8A Test Coverage:**
  - `TestMetricsAndPhysicalDiagnostics` in [`test_baselines_and_neural_ode.py`](file:///c:/local_disc_D/CSTR_model/backend/tests/test_baselines_and_neural_ode.py): Perfect predictions, negative concentration tracking, zero variance safeguards, multi-class metrics, confusion matrices, false alarm rate, and missed detection rate calculations.
  - `TestBaselinesAndLeakageGuards`: Naive and mechanistic baselines, zero-leakage trajectory splitting, train-only scaler fitting.
  - `TestFullDatasetIntegrationAndComparison`: Complete baseline ladder evaluation on Phase 8 generated datasets.
- **Repository Test Results:** `211 passed in 29.35s (0 failures, 0 errors)`.
- **Frontend Vitest Suite:** `4 passed in 1.19s`.
