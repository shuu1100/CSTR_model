# CSTR Lab — Phase Roadmap & Implementation Status

## 1. Roadmap Overview & Status Matrix

| Phase | Title | Status | Test / Build Verification | Key Deliverables & Notes |
|---|---|---|---|---|
| **Phase 0** | **Workspace Audit & Contract** | **COMPLETED** | Verified SHA-256 manifests, quarantined undocumented arrays. | Master README, Architecture, Scientific Assumptions, Data Governance, Manifests with SHA-256 hashes, Candidate dataset quarantine. |
| **Phase 1** | **Scientific Core (First-Order)** | **COMPLETED** | 38 tests passing (`test_scientific_core.py`) | Analytical steady state, Damköhler scaling, canonical oracle ($V=10, Q=1, k=0.15 \implies \tau=10, C_{ss}=0.40, X=0.60$). |
| **Phase 2** | **Dynamic ODE Solver & Orders** | **COMPLETED** | 29 tests passing (`test_dynamic_solver.py`) | Multi-order kinetics ($n \in \{0, 1, 2\}$), piecewise step changes, tolerance convergence, stiff solvers (Radau/BDF), smooth zero-order depletion regularization. |
| **Phase 3** | **Backend REST API** | **COMPLETED** | 15 tests passing (`test_api.py`) | FastAPI endpoints for steady state, dynamic simulation, model catalog, and health checks with typed schemas, OpenAPI examples, and zero-leakage validation. |
| **Phase 4** | **Frontend Interactive Dashboard** | **COMPLETED** | Clean Vite build (`1604 modules transformed`, 0 TypeScript errors) | React 18 + TypeScript + Vite + Plotly interactive charts for dynamic simulation and steady-state exploration. |
| **Phase 5** | **Sensitivity Sweeps & Regimes** | **COMPLETED** | 17 tests passing (`test_parameter_sweeps.py`) | 1D OFAT & 2D parameter sweeps, Latin Hypercube Sampling (SciPy QMC), monotonicity verification, local finite-difference elasticity, and non-silent failure reporting. |
| **Phase 6** | **Data Ingestion & Quality Audit** | **COMPLETED** | 22 tests passing (`test_ingestion.py`) | Multi-format CSV/Excel parser, column mapping, Savitzky-Golay noise filtering, isolation forest anomaly detection. |
| **Phase 7** | **Parameter Estimation & Fit** | **COMPLETED** | 10 tests passing (`test_parameter_estimation.py`) | Non-linear least-squares optimization (`scipy.optimize`), rate constant recovery with parameter confidence bounds. |
| **Phase 8** | **Synthetic Data & Zero-Leakage Splits** | **COMPLETED** | 9 tests passing (`test_synthetic_data.py`) | Latin Hypercube Sampling (QMC), canonical edge cases, 70/15/15 disjoint partitions, train-only preprocessing fit. |
| **Phase 8A** | **Training/Testing Protocol** | **COMPLETED** | Coverage & quality reports verified | Explicit evaluation protocol, seed logging, metric standards (RMSE, MAE, R², physical residual). |
| **Phase 9** | **Baselines & Neural ODE** | **COMPLETED** | 16 tests passing (`test_baselines_and_neural_ode.py`) | PyTorch RK4 grey-box ($R^2 > 0.93$), mechanistic & naive baselines benchmark report. |
| **Phase 10** | **Physics-Informed Neural Networks** | **COMPLETED** | 12 tests passing (`test_pinn.py`) | Autograd CSTR mole balance collocation residual loss, non-negative concentration projection, training-only normalizer, validation tuning, multi-seed benchmarks. |
| **Phase 11** | **ML API & Training UI** | **COMPLETED** | 13 tests passing (`test_ml_api.py`) | FastAPI ML endpoints `/api/v1/ml/*`, dataset preview/validation, thread-pooled async jobs, cancellation, 95% uncertainty intervals, and 4-tab `MachineLearningPage.tsx`. |
| **Phase 12** | **Run History & State Export** | **COMPLETED** | 16 tests passing (`test_persistence_and_export.py`) | SQLite run persistence with schema versioning and artifact tracking, multi-sheet XLSX, CSV, JSON exports, side-by-side run comparison, and automated retention policy. |
| **Phase 13** | **Arrhenius & Thermal CSTR** | **COMPLETED** | 14 tests passing (`test_thermal_cstr.py`) | Arrhenius kinetics, coupled jacket energy balances, isothermal mode recovery, thermal runaway detection, PRBS workbook signal mappings, blocked chronological split, thermal calibration, and concentration validation guard. |
| **Phase 14** | **Optional ONNX Runtime & Benchmark** | **COMPLETED** | 2 tests passing (`test_onnx_optimization.py`) | Native PyTorch latency benchmarked (~35-50 ms), offline zero-dependency architecture preserved. |
| **Phase 15** | **Scientific QA, Regression & Release** | **COMPLETED** | 6 regression tests passing (`test_phase15_qa_release_regression.py`) | Complete end-to-end regression test suite, zero-leakage verification, quarantine integrity locked. |

---

## 2. Baseline Verification Log

- **Python Version:** 3.14.6
- **Test Framework:** pytest 9.1.1
- **Backend Test Suite:** `pytest backend/tests` -> **234 passed in 56.5s (100% pass rate)**
- **Frontend Build:** `npm run build` -> **0 errors, Vite production bundle generated**
- **Frontend Unit Tests:** `npm test` -> **4 passed (100% pass rate)**
- **Blockers Resolved During Roadmap:**
  1. *Zero-Order Depletion Discontinuity:* In `simulate_dynamic_cstr`, smooth linear regularization in `backend/app/core/kinetics.py` ($[0, \epsilon_{\text{depletion}}]$ with $\epsilon = 10^{-3}\text{ mol/L}$).
  2. *Step Change Evaluation Grid Alignment:* In `simulate_dynamic_cstr`, preserved caller's exact evaluation grid length.
  3. *PINN Boundary Non-Negativity:* Added non-negative projection to ensure $C_A \ge 0$ unconditionally.
  4. *SQLAlchemy 2.0 Syntax:* Refactored `.isin()` to `.in_()`.
  5. *FastAPI Pydantic regex Validation:* Updated `regex=` to `pattern=` for modern Pydantic v2 / FastAPI compatibility.

