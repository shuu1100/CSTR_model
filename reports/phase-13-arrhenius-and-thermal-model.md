# Phase 13 Technical Report — Arrhenius Kinetics, Non-Isothermal CSTR, and PRBS Thermal Governance

## 1. Executive Summary & Physics Foundation

Phase 13 establishes the non-isothermal mechanistic modeling, Arrhenius kinetic framework, and PRBS experimental thermal calibration for CSTR Lab, adhering strictly to `GLOBAL-INSTRUCTIONS.md`, `phase-13-arrhenius-thermal-model.md`, and the candidate dataset audit protocol.

### Key Capabilities Delivered:
1. **Arrhenius Temperature Dependence:**
   $$k(T) = A \exp\left(-\frac{E_a}{R T}\right)$$
   - Strict absolute Kelvin validation ($T > 0\text{ K}$, rejecting $T \le 0\text{ K}$).
   - Parameter constraints: $A \ge 0$, $E_a \ge 0$, $R = 8.314462618\text{ J/(mol}\cdot\text{K)}$.
   - Numerical safeguard: exponent clamping $\max(-100.0, \min(50.0, -E_a / (RT)))$ preventing numerical underflow and floating-point overflow.
2. **Coupled Non-Isothermal Mass & Energy Balances:**
   $$\frac{dC_A}{dt} = \frac{Q}{V}(C_{A,\text{in}} - C_A) - k(T)C_A^n$$
   $$\frac{dT}{dt} = \frac{Q}{V}(T_{\text{in}} - T) + \frac{(-\Delta H_{\text{rxn}})}{\rho C_p} k(T) C_A^n - \frac{U A}{V \rho C_p}(T - T_j)$$
   $$\frac{dT_j}{dt} = \frac{Q_j}{V_j}(T_{j,\text{in}} - T_j) + \frac{U A}{V_j \rho_j C_{pj}}(T - T_j)$$
   - Complete documented physical properties:
     - Fluid densities $\rho, \rho_j$ [kg/L]
     - Specific heat capacities $C_p, C_{pj}$ [kJ/(kg·K)]
     - Overall heat transfer conductance $UA$ [kJ/(min·K)]
     - Reaction enthalpy $\Delta H_{\text{rxn}}$ [kJ/mol] ($< 0$ exothermic, $> 0$ endothermic)
3. **Selectable Isothermal Mode:**
   - Setting `isothermal=True` locks $T(t) \equiv T_{\text{in}}$, holding $dT/dt = 0$ and $dT_j/dt = 0$, identically recovering the Phase 1–2 isothermal ODE trajectories.
4. **Automated Thermal Runaway Detection:**
   - Evaluates trajectory peak temperature $T_{\text{peak}}$. If $T_{\text{peak}} - T_{\text{in}} > 50\text{ K}$, activates `thermal_runaway_detected=True` and issues descriptive warnings.
5. **Experimental PRBS Workbook Compatibility, Audit & Thermal Calibration:**
   - Audited workbook: `data/raw/CSTR_24aug_PRBS_dataset.xlsx`.
   - Identified explicit signal mappings without guesswork.
   - Audited uniform sampling ($\Delta t = 0.5\text{ s}$), zero missingness ($0\text{ NaNs}$), and excitation identifiability.
   - Blocked chronological partitioning: 60% Calibration (train), 20% Validation (tune), 20% Locked Test.
   - Calibrated jacket-to-reactor thermal conductance and evaluated held-out physical residuals.
6. **Strict Scientific Data Governance Guard:**
   - Confirmed that `CSTR_24aug_PRBS_dataset.xlsx` measures RTD sensor temperatures and flow rates only, with **zero concentration assays**.
   - Guarded constraint: **Temperature-only data cannot validate concentration**. Any attempt to validate concentration predictions on this dataset raises a scientific error.

---

## 2. Experimental PRBS Dataset Audit & Signal Mappings

| Workbook Column Header | Canonical Signal Mapping | Units | Description & Physical Role |
| :--- | :--- | :--- | :--- |
| `'Time (s)'` | `time_s` | s | Continuous elapsed time ($\Delta t = 0.5\text{ s}$) |
| `'Hot oil circulation'` | `hot_oil_flow` | arb / mL/min | Multi-level PRBS excitation signal |
| `' Feed A Flowrate(ml/min)'` | `feed_a_flow_ml_min` | mL/min | Reactant A hydraulic feed rate |
| `' Feed B Flowrate(ml/min)'` | `feed_b_flow_ml_min` | mL/min | Reactant B hydraulic feed rate |
| `'Hot Oil bath(for Feed A and Feed  B )'` | `oil_bath_temp_c` | °C | Preheating bath RTD temperature |
| `'Reactor Temp. Tr (°C)'` | `reactor_temp_k` | K | Reactor fluid core temperature ($T_r [^\circ\text{C}] + 273.15$) |
| `'Jacket Temp. Tj (°C)'` | `jacket_temp_k` | K | Cooling/heating jacket temperature ($T_j [^\circ\text{C}] + 273.15$) |
| `'FeedA Temp. (°C)'`, `'FeedB Temp. (°C)'` | `feed_inlet_temp_k` | K | Flow-weighted feed inlet temperature |

### Data Integrity & Identifiability Verification
- **Total Record Count:** 3,131 samples ($t = 0.0\text{ s}$ to $1,565.0\text{ s}$).
- **Sampling Interval:** Uniform $\Delta t = 0.500\text{ s}$ with strictly monotonic progression.
- **Missingness Audit:** Exactly $0$ NaN / null values across all 9 channels.
- **Identifiability:** Multi-level PRBS excitation drives substantial temperature variations:
  - Reactor temperature range: $\Delta T_r = 21.02\text{ K}$ ($303.81\text{ K}$ to $324.83\text{ K}$).
  - Jacket temperature range: $\Delta T_j = 25.39\text{ K}$ ($304.21\text{ K}$ to $329.60\text{ K}$).
  - Excitation levels: 5 distinct discrete operating states ($0, 110, 220, 330, 440$).

---

## 3. Blocked Chronological Partitioning & Locked Test Evaluation

Data was partitioned along the chronological axis into strictly contiguous, disjoint blocks:
1. **Calibration Partition (60%):** Rows 0 to 1,877 ($t \in [0.0, 938.5]\text{ s}$).
2. **Validation Partition (20%):** Rows 1,878 to 2,503 ($t \in [939.0, 1,251.5]\text{ s}$).
3. **Locked Test Partition (20%):** Rows 2,504 to 3,130 ($t \in [1,252.0, 1,565.0]\text{ s}$).

### Thermal Parameter Calibration
Governing energy balance on reactor fluid temperature derivative:
$$\frac{dT_r}{dt} = k_{\text{jacket}}(T_j - T_r) + k_{\text{inlet}}(T_{\text{in}} - T_r) + \beta_0$$

Calibrated parameter estimates:
- $k_{\text{jacket}} = 1.425 \times 10^{-3}\text{ s}^{-1}$ (effective heat transfer dissipation rate)
- $k_{\text{inlet}} = -6.937 \times 10^{-4}\text{ s}^{-1}$
- $\beta_0 = -9.300 \times 10^{-3}\text{ K/s}$ (ambient loss bias)

### Held-Out Evaluation on Locked Test Partition
- **Gradient RMSE:** $0.05119\text{ K/s}$
- **Gradient MAE:** $0.04094\text{ K/s}$
- **Mean Gradient Residual:** $0.00294\text{ K/s}$ (demonstrating zero unphysical systematic drift)
- **1-Step Integrated Temperature RMSE:** $0.02560\text{ K}$
- **1-Step Integrated Temperature MAE:** $0.02047\text{ K}$
- **Mean Temperature Residual:** $0.00147\text{ K}$

---

## 4. REST API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/v1/simulations/thermal` | Non-isothermal coupled CSTR dynamic simulation with jacket balances and runaway alerts |
| `GET` | `/api/v1/simulations/thermal/prbs-audit` | PRBS compatibility audit, verified signal mappings, and data governance warnings |
| `POST` | `/api/v1/simulations/thermal/prbs-calibration` | Thermal parameter estimation on 60% calibration block and locked test evaluation |

---

## 5. Test Suite Verification

14 dedicated unit and integration tests passing in `backend/tests/test_thermal_cstr.py`:
- `TestArrheniusKinetics::test_arrhenius_monotonicity_with_temperature` (PASSED)
- `TestArrheniusKinetics::test_temperature_must_be_positive_kelvin` (PASSED)
- `TestArrheniusKinetics::test_negative_parameters_raise` (PASSED)
- `TestCoupledThermalSimulation::test_baseline_thermal_simulation` (PASSED)
- `TestCoupledThermalSimulation::test_isothermal_mode_recovers_constant_temperature` (PASSED)
- `TestCoupledThermalSimulation::test_thermal_runaway_detection` (PASSED)
- `TestThermalAPIEndpoint::test_thermal_api_success` (PASSED)
- `TestThermalAPIEndpoint::test_thermal_api_invalid_volume_rejected` (PASSED)
- `TestThermalAPIEndpoint::test_thermal_api_prbs_audit` (PASSED)
- `TestThermalAPIEndpoint::test_thermal_api_prbs_calibration` (PASSED)
- `TestPRBSThermalAuditAndCalibration::test_prbs_workbook_audit_and_signal_mapping` (PASSED)
- `TestPRBSThermalAuditAndCalibration::test_prbs_blocked_chronology_split` (PASSED)
- `TestPRBSThermalAuditAndCalibration::test_prbs_thermal_calibration_and_locked_test` (PASSED)
- `TestPRBSThermalAuditAndCalibration::test_prbs_temperature_only_cannot_validate_concentration` (PASSED)

### Regression Test Suite Status
- **Backend Test Suite:** **234 passed in 56.54s (100% pass rate)**.
- **Frontend Test Suite:** **4 passed in 0.55s (100% pass rate)**.
