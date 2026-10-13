# Phase 7 — Experimental Analysis and Parameter Estimation Report

- **Report Version:** 1.0.0
- **Compliance:** `GLOBAL-INSTRUCTIONS.md` and `phase-07-parameter-estimation.md`
- **Execution Mode:** Offline Local Execution
- **Verification Status:** 15/15 Phase 7 Unit & Integration Tests Passing (205/205 Repository Tests Passing)

---

## 1. Overview & Objectives

In accordance with `phase-07-parameter-estimation.md`, conventional least-squares optimization and identifiability diagnostics must be established prior to neural surrogate and physics-informed machine learning.

This phase implements and validates:
1. **Dynamic Transient Parameter Estimation:** Non-linear least-squares (NLLS) optimization fitting reaction rate constant $\hat{k}$ (and optionally initial concentration $\hat{C}_{A,0}$) against transient concentration trajectories $C_A(t)$ solved via SciPy `solve_ivp` (RK45 / Radau) and `least_squares` (Trust Region Reflective algorithm).
2. **Steady-State Parameter Estimation:** Multi-operating-point NLLS fitting rate constant $\hat{k}$ across varying space times $\tau = V / Q$.
3. **Statistical Uncertainty & Asymptotic Confidence Intervals:** Analytical evaluation of parameter covariance $\mathbf{\Sigma} = s^2 (\mathbf{J}^T \mathbf{J})^{-1}$ and Student's $t$ confidence bounds $[k_{lower}, k_{upper}]$ at specified confidence levels (default 95%).
4. **Identifiability & Collinearity Diagnostics:** Information matrix condition number $\kappa(\mathbf{J}^T \mathbf{J})$ and pairwise parameter correlation $\rho(k, C_{A,0})$ to detect overparameterization and ill-conditioned excitation.
5. **Data Compatibility & Temperature-Only Signal Rejection:** Explicit enforcement barring temperature-only datasets (e.g. `CSTR_24aug_PRBS_dataset.xlsx`) from kinetic rate estimation without a calibrated coupled thermo-chemical energy model.
6. **Strict Split Leakage Prevention:** Guardrails preventing test partition data from entering the fitting pipeline, coupled with out-of-sample evaluation on held-out test splits.

---

## 2. Mathematical Formulation

### 2.1 Transient Dynamic Objective Function
For an isothermal continuous stirred-tank reactor with reaction rate $r_A = -k C_A^n$:
$$\frac{dC_A}{dt} = \frac{Q}{V}(C_{A,in} - C_A) - k C_A^n$$

Given discrete observed concentration measurements $\{ (t_i, C_{A,obs,i}) \}_{i=1}^N$, the parameter optimization solves:
$$\min_{\boldsymbol{\theta} \in [\boldsymbol{\theta}_{min}, \boldsymbol{\theta}_{max}]} \frac{1}{2} \sum_{i=1}^N \left( C_A(t_i; \boldsymbol{\theta}) - C_{A,obs,i} \right)^2$$
where $\boldsymbol{\theta} = [k]$ or $\boldsymbol{\theta} = [k, C_{A,0}]$.

### 2.2 Optimization Method & Trust Region Constraints
The optimization is executed using SciPy's Trust Region Reflective (`trf`) algorithm:
- Initial rate constant guess: $k_{init} > 0$ (default $0.10 \text{ min}^{-1}$).
- Strict physical bounds: $k \in [k_{min}, k_{max}]$, typically $[10^{-6}, 50.0] \text{ min}^{-1}$.
- Convergence criteria: Function tolerance $\text{ftol} = 10^{-7}$, step tolerance $\text{xtol} = 10^{-7}$, gradient tolerance $\text{gtol} = 10^{-7}$.

### 2.3 Uncertainty & Covariance Matrix
At the converged optimal point $\hat{\boldsymbol{\theta}}$, the Jacobian matrix $\mathbf{J} \in \mathbb{R}^{N \times p}$ contains sensitivity derivatives $J_{ij} = \frac{\partial C_A(t_i)}{\partial \theta_j}$.
The unbiased residual variance estimator is:
$$s^2 = \frac{\sum_{i=1}^N \left( C_{A,obs,i} - C_A(t_i; \hat{\boldsymbol{\theta}}) \right)^2}{N - p}$$
where degrees of freedom $\nu = N - p$.

The parameter covariance matrix is computed as:
$$\mathbf{\Sigma}_{\boldsymbol{\theta}} = s^2 (\mathbf{J}^T \mathbf{J})^{-1}$$
For rate constant $\hat{k}$, the asymptotic standard error is $\text{SE}(\hat{k}) = \sqrt{\mathbf{\Sigma}_{1,1}}$.
The two-sided $100(1 - \alpha)\%$ confidence interval is:
$$\text{CI}_{1-\alpha}(\hat{k}) = \left[ \max\left(0, \hat{k} - t_{1-\alpha/2, \nu} \cdot \text{SE}(\hat{k})\right), \quad \hat{k} + t_{1-\alpha/2, \nu} \cdot \text{SE}(\hat{k}) \right]$$

### 2.4 Identifiability & Collinearity Criteria
1. **Condition Number:** The condition number of the Fisher information matrix is:
   $$\kappa(\mathbf{J}^T \mathbf{J}) = \frac{\lambda_{max}(\mathbf{J}^T \mathbf{J})}{\lambda_{min}(\mathbf{J}^T \mathbf{J})}$$
   If $\kappa > 10^4$, the information matrix is ill-conditioned, and an explicit warning is raised.
2. **Parameter Correlation:** When co-estimating $[k, C_{A,0}]$, the correlation coefficient is:
   $$\rho(k, C_{A,0}) = \frac{\mathbf{\Sigma}_{1,2}}{\sqrt{\mathbf{\Sigma}_{1,1} \cdot \mathbf{\Sigma}_{2,2}}}$$
   If $|\rho| > 0.90$, collinearity between initial concentration and kinetics is flagged.

---

## 3. Synthetic Benchmark Ground-Truth Recovery

All parameter estimation routines were verified against synthetic datasets with known ground truth:

| Test Case | Reaction Order ($n$) | True Rate Constant ($k_{true}$) | Initial Guess ($k_{init}$) | Fitted Rate Constant ($\hat{k}$) | $R^2$ Metric | RMSE ($\text{mol/L}$) | Confidence Interval (95%) | Status |
|---|---|---|---|---|---|---|---|---|
| **Clean Oracle Dynamic** | $n=1$ | $0.1500 \text{ min}^{-1}$ | $0.4500$ | $0.1500$ | $1.00000$ | $< 10^{-4}$ | $[0.1498, 0.1502]$ | **PASSED** |
| **Noisy Sensor Dynamic** | $n=1$ | $0.1500 \text{ min}^{-1}$ | $0.0500$ | $0.1488$ | $0.98412$ | $0.0092$ | $[0.1441, 0.1535]$ | **PASSED** |
| **Second-Order Dynamic** | $n=2$ | $0.2500 \text{ L/(mol}\cdot\text{min)}$ | $0.1000$ | $0.2499$ | $0.99998$ | $< 10^{-3}$ | $[0.2482, 0.2516]$ | **PASSED** |
| **Zero-Order Dynamic** | $n=0$ | $0.0400 \text{ mol/(L}\cdot\text{min)}$ | $0.1000$ | $0.0400$ | $0.99999$ | $< 10^{-4}$ | $[0.0397, 0.0403]$ | **PASSED** |
| **Steady-State Multi-$\tau$** | $n=1$ | $0.1500 \text{ min}^{-1}$ | $0.5000$ | $0.1500$ | $1.00000$ | $< 10^{-4}$ | $[0.1499, 0.1501]$ | **PASSED** |

---

## 4. Generalization & Zero-Leakage Test Split Validation

To guarantee strict compliance with `GLOBAL-INSTRUCTIONS.md` (no test split data used during model fitting):
1. **Training Split:** Dynamic trajectory evaluated from $t \in [0, 20] \text{ min}$ with initial concentration $C_{A}(0) = 0.10 \text{ mol/L}$.
   - Optimizer converged to $\hat{k} = 0.1500 \text{ min}^{-1}$ in 8 evaluations.
2. **Held-Out Test Split:** Completely independent dynamic trajectory evaluated from $t \in [0, 25] \text{ min}$ with initial concentration $C_{A}(0) = 1.20 \text{ mol/L}$ (unseen operating regime).
   - Test evaluation results:
     - Test points: $N_{test} = 26$
     - Test $R^2$: $0.99999$
     - Test RMSE: $1.24 \times 10^{-4} \text{ mol/L}$
     - Test MAE: $9.81 \times 10^{-5} \text{ mol/L}$
3. **Leakage Enforcement:** Passing `dataset_split="test"` to the estimation API or core function raises `ValueError: Test partition data must NOT be used for parameter fitting to prevent data leakage. Fit parameters on the training split only.` with HTTP 422 Unprocessable Content.

---

## 5. Candidate Data Compatibility & Temperature-Only Governance

In compliance with the Phase 6 data audit and Phase 7 instructions:
- **`cstr_rawdata.npy`:** Quarantined. Unlabeled column array with no concentration labels. Cannot be used for parameter estimation.
- **`CSTR_24aug_PRBS_dataset.xlsx`:** Contains RTD temperature readings ($T_{jacket}, T_{tank}, T_{bath}$) and volumetric flow rates, but **no chemical concentration signals**.
- **Governance Rule:** Inferring reaction kinetics from temperature-only measurements without a calibrated coupled thermo-kinetic energy balance is mathematically non-identifiable and scientifically invalid.
- **System Safeguard:** `validate_data_compatibility_for_kinetics` strictly rejects temperature-only datasets:
  ```python
  if has_temperature_only or not has_concentration:
      raise ValueError(
          "Cannot infer reaction kinetics from temperature-only signals without measured "
          "concentration C_A or a calibrated coupled thermo-kinetic energy model."
      )
  ```

---

## 6. Frontend Visualizations & User Interface

The estimation interface (`/estimation`) provides:
1. **Preset Benchmarks:** One-click loading of Canonical First-Order Oracle ($k=0.15 \text{ min}^{-1}$), Second-Order Nonlinear Dynamics, and Steady-State Residence Time series.
2. **Interactive Controls:** Reaction order selector ($0, 1, 2$), operating parameter inputs ($V, Q, C_{A,in}$), and optimizer bounds ($k_{min}, k_{max}, k_{init}$).
3. **Diagnostic Metrics:**
   - Coefficient $R^2$, RMSE, MAE, Sum of Squared Residuals (SSR).
   - Condition number $\kappa(\mathbf{J}^T \mathbf{J})$ and parameter correlation $\rho(k, C_{A,0})$.
   - Asymptotic 95% Confidence Interval with Student's $t$ critical threshold.
4. **Interactive Plots:**
   - Observed Data Points vs Fitted Mechanistic Model Trajectory.
   - Residual Distribution vs Time / Fitted Concentration with zero-residual reference line.
5. **Provenance Transparency:** Luminous badge confirming:
   > *"FITTED ESTIMATE: The reported kinetic parameters are mathematical estimates derived from numerical optimization and model assumptions. They are not direct laboratory measurements."*

---

## 7. Verification & Test Summary

```powershell
pytest backend/tests/test_parameter_estimation.py
```
- **Passed:** 15 / 15 tests (100%) in 6.08s.
- **Coverage:** Synthetic parameter recovery (orders 0, 1, 2), noisy sensor robustness, steady-state multi-condition fits, identifiability warnings (zero variance, zero time span, bound collisions), parameter correlation diagnostics, condition number tracking, test split leakage prevention, temperature-only data rejection, and API contracts.
