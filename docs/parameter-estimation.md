# Conventional Kinetic Parameter Estimation

This document details the mathematical framework, optimization algorithms, statistical uncertainty calculations, and identifiability safeguards used for conventional kinetic parameter estimation in **CSTR Lab**.

---

## 1. Problem Formulation

Conventional parameter estimation determines unknown chemical kinetic parameters (e.g. rate constant $k$) by minimizing discrepancies between experimental observations and deterministic CSTR model predictions.

### A. Dynamic Parameter Estimation
Given transient observations $(t_i, C_{A,\text{obs}, i})$ for $i = 1, \dots, N$:

$$\min_{k \in [k_{\min}, k_{\max}]} \Phi(k) = \sum_{i=1}^N \left( C_{A,\text{obs}, i} - C_A(t_i; k) \right)^2$$

where $C_A(t; k)$ is computed by numerically solving the CSTR transient mole balance:

$$\frac{dC_A}{dt} = \frac{Q}{V}\left(C_{A,\text{in}} - C_A\right) - k C_A^n, \quad C_A(0) = C_{A,0}$$

Optionally, initial concentration $C_{A,0}$ can be simultaneously co-estimated if initial sensor readings contain substantial measurement noise.

### B. Multi-Condition Steady-State Parameter Estimation
Given steady-state concentration measurements under $M$ distinct operating residence times $\tau_j = V / Q_j$:

$$\min_{k \in [k_{\min}, k_{\max}]} \Phi(k) = \sum_{j=1}^M \left( C_{A,\text{obs}, j} - C_{A,\text{ss}}(\tau_j; k) \right)^2$$

where $C_{A,\text{ss}}(\tau; k)$ is solved analytically:
- **First-Order ($n=1$):**
  $$C_{A,\text{ss}} = \frac{C_{A,\text{in}}}{1 + k\tau}$$
- **Second-Order ($n=2$):**
  $$C_{A,\text{ss}} = \frac{-1 + \sqrt{1 + 4 k \tau C_{A,\text{in}}}}{2 k \tau}$$
- **Zero-Order ($n=0$):**
  $$C_{A,\text{ss}} = \max\left(0, C_{A,\text{in}} - k\tau\right)$$

---

## 2. Optimization Algorithm: SciPy Least Squares

Optimization is executed using `scipy.optimize.least_squares` with the **Trust Region Reflective (`trf`)** algorithm:
- Enforces strict box constraints: $k \in [k_{\min}, k_{\max}]$ (default $[10^{-6}, 50.0]$).
- Computes the exact forward Jacobian matrix $J \in \mathbb{R}^{N \times p}$ at the optimal solution:
  $$J_{ij} = \frac{\partial \hat{y}_i}{\partial \theta_j}$$
- Tolerances: `ftol=1e-7`, `xtol=1e-7`, `gtol=1e-7`.

---

## 3. Goodness of Fit & Statistical Metrics

1. **Sum of Squared Residuals ($SSR$):**
   $$SSR = \sum_{i=1}^N e_i^2 = \sum_{i=1}^N \left(C_{A,\text{obs}, i} - C_{A,\text{pred}, i}\right)^2$$
2. **Root Mean Squared Error ($RMSE$):**
   $$RMSE = \sqrt{\frac{SSR}{N}}$$
3. **Mean Absolute Error ($MAE$):**
   $$MAE = \frac{1}{N} \sum_{i=1}^N |e_i|$$
4. **Coefficient of Determination ($R^2$):**
   $$R^2 = 1 - \frac{\sum_{i=1}^N (C_{A,\text{obs}, i} - C_{A,\text{pred}, i})^2}{\sum_{i=1}^N (C_{A,\text{obs}, i} - \bar{C}_{A,\text{obs}})^2}$$

---

## 4. Parameter Uncertainty & Confidence Intervals

Parameter variance and covariance are derived from the linearized asymptotic covariance matrix:

$$\text{Cov}(\hat{\boldsymbol{\theta}}) \approx s^2 \left( J^T J \right)^{-1}$$

where the sample residual variance $s^2$ is evaluated over degrees of freedom $\nu = N - p$:

$$s^2 = \frac{SSR}{N - p}$$

- **Standard Error ($SE$):**
  $$SE(k) = \sqrt{\text{Cov}_{11}}$$
- **Student's $t$ Confidence Interval:**
  $$\text{CI}_{100(1-\alpha)\%} = \left[ \hat{k} - t_{\alpha/2, \nu} SE(k), \; \hat{k} + t_{\alpha/2, \nu} SE(k) \right]$$
  where $t_{\alpha/2, \nu}$ is the critical two-tailed Student's $t$ value with $\nu = N - p$ degrees of freedom (`scipy.stats.t.ppf`).

### Scientific Uncertainty Guardrails:
If the Jacobian matrix $J^T J$ is singular or ill-conditioned, or if $N \le p$ (insufficient degrees of freedom), **no fabricated uncertainty is reported**. Instead, `confidence_interval_k` is explicitly set to `None` with an explanatory note: *"Uncertainty was not estimated (singular Jacobian or insufficient degrees of freedom)."*

---

## 5. Identifiability Checks & Diagnostic Warnings

The optimizer systematically verifies:
1. **Sample Size:** At least $N \ge 3$ points required.
2. **Dynamic Excitation:** Warns if $\text{std}(C_{A,\text{obs}}) < 10^{-5}\text{ mol/L}$ or total time span $\Delta t < 10^{-4}\text{ min}$.
3. **Repeated Steady States:** Warns if $\text{std}(\tau) < 10^{-4}\text{ min}$ across rows.
4. **Bound Collisions:** Warns if fitted $\hat{k}$ converges within $0.1\%$ of $k_{\min}$ or $k_{\max}$.

---

## 6. Provenance & Engineering Labeling

In adherence to scientific guidelines, all estimates returned by `POST /api/v1/analysis/fit-kinetics` carry the immutable label:

> **FITTED ESTIMATE: The reported kinetic parameters are mathematical estimates derived from numerical optimization and model assumptions. They are not direct laboratory measurements.**
