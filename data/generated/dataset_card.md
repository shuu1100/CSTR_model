# CSTR Lab — Synthetic Dataset Card (Phase 8)

## 1. Dataset Summary

Synthetically generated training, validation, and test datasets for continuous stirred-tank reactor (CSTR) machine learning models. Built strictly using the validated mechanistic ODE solver with Quasi-Monte Carlo Latin Hypercube Sampling (SciPy QMC) and physical edge cases.

- **Provenance:** Mechanistic SciPy IVP Solver (`SYNTHETIC_MECHANISTIC_SOLVER`)
- **Code Version:** `0.1.0-phase08`
- **Primary Canonical Units:** $V$ [L], $Q$ [L/min], $k$ [min⁻¹ for n=1], $C_A$ [mol/L], $t$ [min]
- **Splitting Policy:** 70/15/15 by independent trajectory / parameter draw (disjoint IDs, zero row-level leakage)

## 2. Tasks & Data Files

| Task | File | Total Items | Train (70%) | Val (15%) | Locked Test (15%) | SHA-256 |
|---|---|---|---|---|---|---|
| **Steady-State Regression** | `steady_state_dataset.csv` | 457 draws | 320 | 69 | 68 | `514925c6c799aac03d4bc9594186928d9d8ab220f478e4a299ca9c4df2c3081e` |
| **Dynamic Transient Forecasting** | `transient_trajectories.csv` | 127 trajectories (12,827 rows) | 89 | 19 | 19 | `a83bc07ac4d51cdda4b1e9338abba6cf3ce780f78a6642f11a419912cf05bb3f` |
| **Kinetic Estimation Benchmark** | `estimation_benchmark.csv` | 30 runs (3,030 rows) | 21 | 4 | 5 | `0b134dade8639a9ba96bb77b6c0c8570731e1027f95215098e228b2c90c30ac7` |
| **Fault Diagnosis & Anomaly** | `fault_diagnosis.csv` | 40 runs (2,040 rows) | 28 | 6 | 6 | `99618b7f0dc2c818a5e02d36e698783e88626bc8552c0967e8621414d51ad5cb` |

## 3. Parameter Ranges Covered

- Volume $V$: $[1.0, 50.0]\text{ L}$
- Flow Rate $Q$: $[0.1, 5.0]\text{ L/min}$
- Rate Constant $k$:
  - $n=0$: $[0.005, 0.20]\text{ mol/(L}\cdot\text{min)}$
  - $n=1$: $[0.01, 2.00]\text{ min}^{-1}$
  - $n=2$: $[0.01, 1.00]\text{ L/(mol}\cdot\text{min)}$
- Inlet Concentration $C_{A,\text{in}}$: $[0.1, 5.0]\text{ mol/L}$
- Initial Concentration $C_{A,0}$: $[0.0, 5.0]\text{ mol/L}$
- Measurement Noise: Gaussian additive $\sigma = 0.015\text{ mol/L}$ with strictly non-negative projection

## 4. Edge Cases Represented

1. **Canonical Validation Oracle:** $V=10, Q=1, k=0.15, C_{A,\text{in}}=2.0 \implies \tau=10, C_{A,\text{ss}}=0.80, X_A=60\%$
2. **Zero Inlet Concentration:** $C_{A,\text{in}}=0 \implies C_{A,\text{ss}}=0$, conversion is `None`
3. **Zero Initial Charge:** $C_{A,0}=0 \implies$ transient filling trajectory
4. **Fast Kinetics ($k\tau \gg 1$):** Conversion exceeds $99\%$
5. **Slow Kinetics ($k\tau \ll 1$):** Conversion below $1\%$
6. **Zero-Order Complete Depletion:** Reactant reaches zero and consumption shuts off cleanly
7. **Step Disturbances:** Piecewise parameter step jumps in feed or flow rate

## 5. Usage & Reproduction

To regenerate these exact files deterministically, run:
```bash
python scripts/generate_phase08_datasets.py
```
