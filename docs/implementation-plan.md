# CSTR Lab — Implementation Plan & Phase Tracking

This document is the single source of truth for progress, architectural decisions, environment audits, and validation records across all phases of **CSTR Lab**.

---

## 1. Workspace Audit

- **Date of Audit:** 2026-10-12
- **Operating System:** Windows 11 (win32 10.0.26100)
- **Primary Python Runtime:** Python 3.14.6 (`C:\Users\Asus\AppData\Local\Programs\Python\Python314\python.exe`)
- **Alternative Python Runtime:** Python 3.13.9 (`C:\local_disc_D\New folder\python.exe`)
- **Package Manager:** `pip` version 26.1.2
- **Node.js Runtime:** Node.js v24.20.0
- **Frontend Package Manager:** `npm` version 11.19.0
- **Key Installed Scientific Packages:**
  - NumPy: 2.5.2
  - SciPy: 1.18.1
  - Pandas: 3.0.5
  - Scikit-learn: 1.9.0
  - PyTorch: 2.13.0
  - FastAPI: 0.141.1
  - Pydantic: 2.13.4
  - SQLAlchemy: 2.1.3
  - Alembic: 1.20.0
  - Pytest: 9.1.1
  - HTTPX: 0.28.1
- **Missing / Optional Dependencies:**
  - `openpyxl`: Needed in Phase 6 for `.xlsx` ingestion (will be installed before Phase 6).
- **Network / API Key Status:**
  - No external API keys or cloud services required. Local SQLite, local solvers, and self-contained models only.

---

## 2. Directory Structure

```
c:/local_disc_D/CSTR_model/
├── .env.example
├── .gitignore
├── GLOBAL-INSTRUCTIONS.md
├── README.md
├── docs/
│   └── implementation-plan.md
├── backend/
│   ├── pyproject.toml
│   ├── requirements.txt
│   ├── app/
│   │   ├── __init__.py
│   │   ├── core/         # Scientific equations, kinetics, ODE solvers, units
│   │   │   └── __init__.py
│   │   ├── schemas/      # Pydantic schemas for requests, responses, models
│   │   │   └── __init__.py
│   │   └── api/          # FastAPI routers and route handlers
│   │       └── __init__.py
│   └── tests/            # Pytest test suite (analytic solutions, validation oracles)
│       └── __init__.py
└── frontend/
    ├── package.json
    └── src/              # UI components, simulator pages, dashboard, Plotly graphs
```

---

## 3. Scientific Baseline & Governing Equations

Ideal, perfectly mixed, constant-volume, constant-density, isothermal Continuous Stirred-Tank Reactor (CSTR) with reactant $A$:

1. **Transient Material Balance:**
   $$\frac{dC_A}{dt} = \frac{Q}{V}(C_{A,\text{in}} - C_A) + r_A$$
2. **Residence Time:**
   $$\tau = \frac{V}{Q}$$
3. **First-Order Irreversible Kinetics:**
   $$r_A = -k C_A$$
4. **First-Order Steady-State Analytical Solution:**
   $$C_{A,\text{ss}} = \frac{\frac{Q}{V} C_{A,\text{in}}}{\frac{Q}{V} + k} = \frac{C_{A,\text{in}}}{1 + k\tau}$$
5. **Steady-State Conversion:**
   $$X_A = \frac{C_{A,\text{in}} - C_{A,\text{ss}}}{C_{A,\text{in}}} = \frac{k\tau}{1 + k\tau} \quad (\text{for } C_{A,\text{in}} > 0)$$
6. **Analytical Dynamic Solution:**
   $$C_A(t) = C_{A,\text{ss}} + \left(C_A(0) - C_{A,\text{ss}}\right) \exp\left(-\left(\frac{Q}{V} + k\right)t\right)$$
7. **Canonical Validation Oracle:**
   - $V = 10\text{ L}$, $Q = 1\text{ L/min}$, $k = 0.15\text{ min}^{-1}$, $C_{A,\text{in}} > 0$
   - $\tau = 10\text{ min}$
   - $X_A = 0.60$ ($60\%$)
   - $C_{A,\text{ss}} / C_{A,\text{in}} = 0.40$ ($40\%$)

---

## 4. Phase Tracking

| Phase | Description | Status | Verification & Deliverables |
|---|---|---|---|
| **Phase 0** | Workspace audit, plan, and safe scaffold | **PASS** | Audited environment; created directory scaffold, dependency manifests, `.gitignore`, `.env.example`, README, and plan. Verified Python 3.14 & Node v24 runtimes. |
| **Phase 1** | Scientific core, units, first-order steady state, and analytic tests | **PASS** | Pure Python scientific core implemented with canonical unit enforcement. Validated against canonical oracle (tau=10 min, C_A,ss/C_in=0.40, X_A=0.60) and independent residual check. 29/29 tests pass. |
| **Phase 2** | Dynamic solver and reaction-order support | **PASS** | SciPy solve_ivp ODE integrator implemented with support for orders n=0, 1, 2, piecewise step-changes, depletion boundaries, and exact analytical trajectory comparisons. 43/43 tests pass. |
| **Phase 3** | Backend API and schemas | **PASS** | FastAPI app with versioned REST routes (/health, /models, /simulations/steady-state, /simulations/dynamic), Pydantic schemas, input unit conversion, computational safety limits, and local CORS. 53/53 tests pass. |
| **Phase 4** | Frontend simulator and engineering dashboard | **PASS** | React + TypeScript + Vite dashboard with Plotly charts, scientific form presets (canonical oracle, fast kinetics, step disturbance), KPI metrics, assumptions panel, and typed API client connected to backend. Build & integration tests pass. |
| **Phase 5** | Parameter sweeps and sensitivity analysis | **PASS** | 1D parameter sweeps ($k, V, Q, C_{A,\text{in}}$) and 2D surface grid maps implemented. Local sensitivity measures (tangent derivative & normalized elasticity) and dynamic trend interpretation computed. 65/65 tests pass. |
| **Phase 6** | CSV/Excel ingestion and experimental data analysis | **PASS** | Multipart upload for CSV/TSV/Excel, security guards (10MB, 50k rows, 50 cols), column mapping, conversion boundary checks, optional Savitzky–Golay smoothing, Isolation Forest anomaly flags, non-destructive data integrity, frontend UI with Plotly comparison plots. 85/85 tests pass. |
| **Phase 7** | Conventional kinetic parameter estimation | **PASS** | Nonlinear least-squares optimization (`scipy.optimize.least_squares` with TRF algorithm) for dynamic ODE and multi-condition steady-state runs. Ground-truth synthetic parameter recovery verified across orders n=0, 1, 2. Student's t asymptotic confidence intervals, residual analysis, diagnostic warnings, labeled as FITTED ESTIMATE. 95/95 tests pass. |
| **Phase 8** | Synthetic training dataset generation | **NOT STARTED** | Controlled synthetic dataset generation with labelled noise, Latin hypercube / Sobol sampling, train/val/test splits. |
| **Phase 9** | Grey-box Neural ODE | **NOT STARTED** | PyTorch hybrid model combining known mass balance physics with neural net for missing reaction kinetics $r_A(C_A)$. |
| **Phase 10** | Physics-Informed Neural Network (PINN) | **NOT STARTED** | Collocation points, residual loss penalizing deviation from governing ODE $\frac{dC_A}{dt} - f(C_A) = 0$. |
| **Phase 11** | ML API, task status, and ML interface | **NOT STARTED** | Asynchronous training worker/status tracking, ML inference endpoints, frontend training visualizer. |
| **Phase 12** | SQLite history, comparisons, and exports | **NOT STARTED** | SQLAlchemy run persistence, simulation run comparison, CSV/JSON/PDF-ready data exports. |
| **Phase 13** | Arrhenius temperature dependence and optional energy balance | **NOT STARTED** | $k(T) = A \exp(-E_a / RT)$, non-isothermal CSTR with jacket cooling/heating, thermal stability/runaway regimes. |
| **Phase 14** | Optional ONNX inference acceleration | **NOT STARTED** | ONNX export and runtime benchmarking for trained neural kinetic models. |
| **Phase 15** | Scientific QA, security, documentation, and release | **NOT STARTED** | End-to-end integration tests, edge case verification, scientific documentation, architecture diagrams. |

---

## 5. Phase 0 Detailed Execution Log

- **Files Created:**
  - `backend/app/__init__.py`
  - `backend/app/core/__init__.py`
  - `backend/app/schemas/__init__.py`
  - `backend/app/api/__init__.py`
  - `backend/tests/__init__.py`
  - `backend/requirements.txt`
  - `backend/pyproject.toml`
  - `frontend/package.json`
  - `.gitignore`
  - `.env.example`
  - `docs/implementation-plan.md`
  - `README.md`
- **Commands Executed:**
  - `python --version` (Python 3.14.6)
  - `node -v` (v24.20.0)
  - `npm -v` (11.19.0)
  - `python -m pip list` (confirmed installed: numpy, scipy, pandas, scikit-learn, torch, fastapi, pydantic, sqlalchemy, alembic, pytest, httpx)
  - Scaffold creation via PowerShell `New-Item`
- **Acceptance Gate Verification:**
  - [x] Existing files inspected before any changes.
  - [x] Plan lists every phase (Phase 0 to Phase 15) in strict sequential order.
  - [x] No secrets, API keys, or external service credentials introduced.
  - [x] Runtime environments validated and ready for Phase 1.

---

## 6. Phase 1 Detailed Execution Log

- **Files Created / Modified:**
  - `backend/app/core/units.py`: Canonical unit definitions, conversions, and dimensional checks.
  - `backend/app/core/isothermal_first_order.py`: Pure scientific core for residence time, reaction kinetics, analytical steady state, conversion, material-balance residual check, and diagnostics.
  - `backend/app/core/__init__.py`: Clean public interface export.
  - `backend/tests/test_scientific_core.py`: Comprehensive test suite for analytic formulas, canonical oracle, edge cases, input validation, and unit conversions.
  - `docs/scientific-baseline.md`: Mathematical derivations, assumptions, and validation oracle documentation.
  - `docs/implementation-plan.md`: Updated Phase 1 status to PASS.
- **Commands Executed:**
  - `python -m pytest backend/tests -v`
- **Test Outcomes:**
  - 29 tests collected, 29 passed in 0.47s.
  - Canonical Oracle: $V=10\text{ L}$, $Q=1\text{ L/min}$, $k=0.15\text{ min}^{-1}$, $C_{A,\text{in}}=2.0\text{ mol/L} \implies \tau=10.0\text{ min}$, $C_{A,\text{ss}}=0.80\text{ mol/L}$, $C_{A,\text{ss}}/C_{A,\text{in}}=0.40$, $X_A=0.60$, residual $< 10^{-14}\text{ mol/(L}\cdot\text{min)}$.
  - Boundary cases: $C_{A,\text{in}} = 0 \implies C_{A,\text{ss}} = 0$, conversion is `None`, residual $= 0$.
  - Rate limits: $k = 0 \implies X_A = 0$, $k \to \infty \implies X_A \to 1.0$.
  - Validation: Non-positive volumes, negative rates, negative concentrations, NaNs, infinities strictly raise `ValueError` / `TypeError`.
- **Phase 1 Acceptance Gate:** **PASS**

---

## 7. Phase 2 Detailed Execution Log

- **Files Created / Modified:**
  - `backend/app/core/kinetics.py`: Reaction orders $n=0, 1, 2$, rate expressions, rate-constant canonical units, and zero-order depletion boundaries.
  - `backend/app/core/analytical.py`: First-order exact dynamic trajectory and steady-state reference solutions.
  - `backend/app/core/steady_state.py`: Unified analytical and numerical steady-state solver across all reaction orders ($n=0, 1, 2$) with material-balance closure checks.
  - `backend/app/core/dynamic_solver.py`: Dynamic ODE simulation engine using `scipy.integrate.solve_ivp`, supporting continuous operation, non-negativity protection, analytical comparison diagnostics, and piecewise step changes for $C_{A,\text{in}}$ and $Q$.
  - `backend/app/core/__init__.py`: Exported all new modules and classes while preserving Phase 1 interfaces.
  - `backend/tests/test_dynamic_solver.py`: Pytest suite for kinetics, steady states, analytical trajectory agreement, zero initial/inlet conditions, piecewise step changes, and input error handling.
  - `docs/dynamic-solver.md`: Documentation for dynamic equations, solver methods, tolerances, and step-change mechanics.
  - `docs/implementation-plan.md`: Updated Phase 2 status to PASS.
- **Commands Executed:**
  - `python -m pytest backend/tests -v`
- **Test Outcomes:**
  - 43 tests collected, 43 passed in 0.78s across `test_scaffold.py`, `test_scientific_core.py`, and `test_dynamic_solver.py`.
  - Numerical vs analytical agreement: First-order dynamic trajectory simulated via `solve_ivp` matches the analytical formula with max absolute error $< 10^{-5}\text{ mol/L}$ and RMSE $< 10^{-5}\text{ mol/L}$.
  - Depletion boundary: Zero-order kinetics stops reactant consumption at $C_A \le 0$ without producing negative concentrations.
  - Step changes: Piecewise ODE integration verified for disturbance in feed concentration $C_{A,\text{in}}$ and flow rate $Q$, correctly reaching new post-step steady states.
- **Phase 2 Acceptance Gate:** **PASS**

---

## 8. Phase 3 Detailed Execution Log

- **Files Created / Modified:**
  - `backend/app/config.py`: Application settings (host, port, restricted local CORS origins, computation bounds).
  - `backend/app/schemas/simulation.py`: Pydantic request and response models for `/health`, `/models`, `/simulations/steady-state`, and `/simulations/dynamic`.
  - `backend/app/schemas/__init__.py`: Clean public exports.
  - `backend/app/api/v1/health.py`: Health check route.
  - `backend/app/api/v1/models.py`: Model catalog route.
  - `backend/app/api/v1/simulations.py`: Thin REST route controllers delegating to core scientific solvers.
  - `backend/app/api/v1/router.py`: API v1 router aggregator.
  - `backend/app/api/__init__.py`: API package export.
  - `backend/app/main.py`: FastAPI app initialization with local CORS middleware and root route.
  - `backend/tests/test_api.py`: Comprehensive API test suite using FastAPI `TestClient`.
  - `docs/api-specification.md`: API v1 documentation with example requests, responses, and startup commands.
  - `docs/implementation-plan.md`: Updated Phase 3 status to PASS.
- **Commands Executed:**
  - `python -m pytest backend/tests -v`
- **Test Outcomes:**
  - 53 tests collected, 53 passed in 1.08s.
  - `GET /api/v1/health`: Returns HTTP 200 with real operational health status.
  - `GET /api/v1/models`: Returns supported models, reaction orders, canonical units, and assumptions.
  - `POST /api/v1/simulations/steady-state`: Computes exact canonical oracle ($V=10\text{ L}, Q=1\text{ L/min}, k=0.15\text{ min}^{-1} \implies \tau=10\text{ min}, C_{A,\text{ss}}=0.80\text{ mol/L}, X_A=0.60$), supports arbitrary input units (e.g. mL, L/h), and validates orders $n=0, 1, 2$.
  - `POST /api/v1/simulations/dynamic`: Solves transient trajectory, verifies analytical agreement, and integrates step disturbances piecewise.
  - Guardrails & Error Handling: Negative values, non-numeric inputs, horizon $> 10000\text{ min}$, or points $> 10000$ return HTTP 422 with structured validation messages.
- **Phase 3 Acceptance Gate:** **PASS**

---

## 9. Phase 4 Detailed Execution Log

- **Files Created / Modified:**
  - `frontend/package.json`: Frontend dependencies (React 18, Vite, TypeScript, Tailwind CSS, Lucide icons, Plotly.js, types).
  - `frontend/vite.config.ts`: Vite build configuration with `/api` proxy to `http://127.0.0.1:8000`.
  - `frontend/tsconfig.json` & `frontend/tsconfig.node.json`: TypeScript configuration.
  - `frontend/tailwind.config.js` & `frontend/postcss.config.js`: Tailwind styling configuration.
  - `frontend/index.html`: Entry HTML with Inter & JetBrains Mono fonts.
  - `frontend/src/index.css`: Styling tokens, smooth scrollbars, and Tailwind directives.
  - `frontend/src/vite-env.d.ts`: Vite client environment types.
  - `frontend/src/api/types.ts`: TypeScript interfaces matching backend models.
  - `frontend/src/api/client.ts`: Typed API client with custom `ApiError` class and configurable `VITE_API_BASE_URL`.
  - `frontend/src/components/Header.tsx`: Navigation header with live engine status pulse and planned feature badges.
  - `frontend/src/components/SimulationForm.tsx`: Scientific parameter input form with unit dropdowns, reaction order selector, dynamic solver settings, disturbance step toggles, and instant presets (Canonical Oracle, Fast Kinetics, Step Disturbance, 2nd Order, 0th Order).
  - `frontend/src/components/ResultsPanel.tsx`: Key engineering metrics ($\tau, C_{A,\text{ss}}, X_A, r_A$), material-balance residual closure verification, and analytical benchmark RMSE badge.
  - `frontend/src/components/PlotlyChart.tsx`: High-performance Plotly charts for $C_A(t)$ with steady-state asymptote, step change marker, $X_A(t)$ conversion trajectory, and reaction rate $r_A(t)$.
  - `frontend/src/components/AssumptionsPanel.tsx`: Transparent display of scientific assumptions, normalized canonical inputs, and engineering disclaimer.
  - `frontend/src/components/ErrorBanner.tsx`: User-friendly recovery banner for API and validation errors.
  - `frontend/src/pages/OverviewPage.tsx`: Theory guide with CSTR mole balance equations and canonical oracle test case.
  - `frontend/src/pages/SimulatorPage.tsx`: Main simulator dashboard integrating form, live API solver calls, and Plotly visualization.
  - `frontend/src/App.tsx` & `frontend/src/main.tsx`: Main application entry and root mounting.
  - `docs/implementation-plan.md`: Updated Phase 4 status to PASS.
- **Commands Executed:**
  - `npm install` (installed 369 packages in 37s)
  - `npm run build` (`tsc -b && vite build` built production bundle in 1m 3s with zero errors)
  - `python -m pytest backend/tests` (53/53 tests pass in 1.17s)
  - Backend daemon verification: `http://127.0.0.1:8000/api/v1/health` returned HTTP 200 `ok`; `POST /api/v1/simulations/dynamic` returned exact canonical solution $C_A(50) = 0.7999988\text{ mol/L}$.
  - Frontend server verification: `http://127.0.0.1:5173/` returned HTTP 200.
- **Phase 4 Acceptance Gate:** **PASS**

---

## 10. Phase 5 Detailed Execution Log

- **Files Created / Modified:**
  - `backend/app/core/sweeps.py`: Core computational routines for 1D parameter sweeps (`compute_1d_parameter_sweep`), 2D contour grid sweeps (`compute_2d_parameter_sweep`), local finite-difference sensitivity measures ($dX_A / dp$, normalized elasticity), and physical trend generation.
  - `backend/app/core/__init__.py`: Clean export of parameter sweeps interfaces.
  - `backend/app/schemas/sweep.py`: Pydantic request and response schemas for 1D and 2D sweeps with bound validations.
  - `backend/app/schemas/__init__.py`: Schema package export.
  - `backend/app/api/v1/simulations.py`: Added `POST /api/v1/simulations/parameter-sweep` endpoint.
  - `backend/tests/test_parameter_sweeps.py`: Comprehensive test suite for 1D sweeps ($k, V, Q, C_{A,\text{in}}$), monotonicity checks, 2D grid generation, bounds validation, and API integration.
  - `frontend/src/api/types.ts` & `frontend/src/api/client.ts`: Added `ParameterSweepRequest`, `Sweep1DResponse`, `Sweep2DResponse`, and `api.runParameterSweep()`.
  - `frontend/src/pages/SweepsPage.tsx`: Interactive parameter sweeps page supporting 1D sweeps, 2D contour maps with baseline marker dots, calculated trend interpretations, and local sensitivity elasticity cards.
  - `frontend/src/components/Header.tsx` & `frontend/src/App.tsx`: Enabled the "Parameter Sweeps" navigation tab and integrated the page.
  - `docs/parameter-sweeps.md`: Technical documentation of sweep calculations, monotonicity properties, and sensitivity definitions.
  - `docs/implementation-plan.md`: Updated Phase 5 status to PASS.
- **Commands Executed:**
  - `python -m pytest backend/tests` (65/65 passed in 1.07s)
  - `npm run build` in `frontend/` (`tsc -b && vite build` built production bundle in 24.46s with zero errors)
- **Scientific Verifications:**
  - Monotonicity verified: $\frac{\partial X_A}{\partial k} > 0$, $\frac{\partial X_A}{\partial V} > 0$, $\frac{\partial X_A}{\partial Q} < 0$.
  - First-order conversion invariance to inlet concentration verified: $\frac{\partial X_A}{\partial C_{A,\text{in}}} = 0$.
  - Local baseline derivative verified: $\left.\frac{\partial X_A}{\partial k}\right|_{\text{baseline}} = 1.60\text{ min}$ (matches exact analytical $\frac{\tau}{(1+k\tau)^2} = \frac{10}{2.5^2} = 1.60$).
- **Phase 5 Acceptance Gate:** **PASS**

---

## 11. Phase 6 Detailed Execution Log

- **Files Created / Modified:**
  - `backend/requirements.txt`: Added `openpyxl>=3.1.5`.
  - `backend/app/core/ingestion.py`: Safe parsing for CSV/TSV/Excel, size & dimension limit enforcement (10 MB, 50,000 rows, 50 columns), metadata inspection (missing counts, duplicates, data types), unit conversions, measured conversion calculation with boundary checks, optional Savitzky–Golay digital filtering (`scipy.signal.savgol_filter`), optional Isolation Forest anomaly scoring (`sklearn.ensemble.IsolationForest`), and immutable provenance note attachment.
  - `backend/app/schemas/ingestion.py`: Pydantic schemas (`DatasetInspectionResponse`, `ProcessDatasetRequest`, `ProcessedSeriesSchema`, `ProcessedDatasetResponse`).
  - `backend/app/schemas/__init__.py`: Package exports for dataset schemas.
  - `backend/app/api/v1/datasets.py`: Endpoints for `POST /api/v1/datasets/upload` (multipart/form-data), `POST /api/v1/datasets/process`, and `GET /api/v1/datasets/sample-dataset` (synthetic noisy CSTR benchmark run).
  - `backend/app/api/v1/router.py`: Registered `datasets_router`.
  - `backend/tests/test_ingestion.py`: 20 unit and integration tests covering CSV and Excel parsing, file size limits, invalid file extensions, non-monotonic time sorting, out-of-bound conversion preservation, Savitzky–Golay odd-window/polyorder validation, Isolation Forest anomaly scoring without deletion, and API routes.
  - `frontend/src/api/types.ts`: TypeScript interfaces for dataset inspection and processing requests/responses.
  - `frontend/src/api/client.ts`: API client functions (`uploadDataset`, `processDataset`, `getSampleDataset`).
  - `frontend/src/pages/IngestionPage.tsx`: Interactive dataset ingestion UI with drag-and-drop file upload, instant benchmark dataset loader, data profiling inspection summary, top-10 preview table, column mapping with physical unit selectors, Savitzky–Golay and Isolation Forest parameter controls, and dual Plotly visualizations (Raw vs Smoothed concentration comparison with anomaly overlays, measured conversion $X_A$).
  - `frontend/src/components/Header.tsx` & `frontend/src/App.tsx`: Enabled the "Data Ingestion" navigation tab and routed the page.
  - `docs/experimental-data-ingestion.md`: Full architectural and scientific documentation of data ingestion, boundary handling, filtering trade-offs, and provenance policies.
  - `docs/implementation-plan.md`: Updated Phase 6 status to PASS.
- **Commands Executed:**
  - `pip install openpyxl` (installed openpyxl 3.1.5)
  - `python -m pytest backend/tests` (85/85 passed in 2.70s with zero warnings or errors)
  - `npm run build` in `frontend/` (`tsc -b && vite build` built production bundle in 1m with zero errors)
- **Scientific Verifications:**
  - **Raw Data Preservation:** Verified that raw experimental data points are never silently deleted or mutated.
  - **Non-Destructive Outlier Handling:** Isolation Forest identifies anomalous sensor spikes and labels them with anomaly scores while retaining all points in the series.
  - **Conversion Boundary Check:** Verified that $X_A = (C_{A,\text{in}} - C_{A,\text{out}}) / C_{A,\text{in}}$ is evaluated only when $C_{A,\text{in}} > 0$. Unphysical values ($X_A \notin [0, 1]$) trigger explicit quality warnings while preserving raw points.
  - **Savitzky–Golay Validation:** Enforces odd window size $w \ge 3$ and polynomial order $p < w$. Prevents negative smoothed concentrations.
  - **Data Provenance:** Displays prominent notice: *"USER-PROVIDED DATA: This dataset was uploaded by the user. Its authenticity, experimental accuracy, and provenance are unverified."*
- **Phase 6 Acceptance Gate:** **PASS**

---

## 12. Phase 7 Detailed Execution Log

- **Files Created / Modified:**
  - `backend/app/core/parameter_estimation.py`: Nonlinear least-squares optimization (`scipy.optimize.least_squares` with TRF algorithm and box bounds) for dynamic ODE trajectories (`fit_dynamic_kinetics`) and multi-condition steady-state data (`fit_steady_state_kinetics`). Supports reaction orders $n \in \{0, 1, 2\}$, optional co-estimation of initial concentration $C_{A,0}$, forward Jacobian covariance derivation $V_{\hat{\theta}} = s^2 (J^T J)^{-1}$, Student's $t$ confidence intervals, and identifiability safeguards.
  - `backend/app/core/__init__.py`: Exported parameter estimation functions and dataclasses.
  - `backend/app/schemas/estimation.py`: Pydantic request and response schemas (`FitKineticsRequest`, `FitKineticsResponse`, `ParameterConfidenceIntervalSchema`).
  - `backend/app/schemas/__init__.py`: Package export for estimation schemas.
  - `backend/app/api/v1/analysis.py`: Created endpoint `POST /api/v1/analysis/fit-kinetics`.
  - `backend/app/api/v1/router.py`: Registered `analysis_router`.
  - `backend/tests/test_parameter_estimation.py`: 10 comprehensive unit and integration tests including ground-truth synthetic parameter recovery for first-order clean analytical data, noisy dynamic data, second-order kinetics ($n=2$), zero-order kinetics ($n=0$), multi-flow steady-state runs, identifiability warnings (poor excitation, bound collisions, insufficient points), and API routes.
  - `frontend/src/api/types.ts`: TypeScript interfaces for kinetic parameter fitting requests and responses.
  - `frontend/src/api/client.ts`: Added `api.fitKinetics(req)` client method.
  - `frontend/src/pages/EstimationPage.tsx`: Interactive parameter estimation page featuring built-in benchmark presets (First-Order Dynamic Oracle, Second-Order Dynamic, Multi-Flow Steady-State), reaction order selectors, initial guesses and bound controls, prominent parameter estimate card with confidence intervals, goodness-of-fit metrics ($R^2, RMSE, MAE, SSR$), optimizer diagnostics, Observed vs Model trajectory plot, and a dedicated Residuals plot.
  - `frontend/src/components/Header.tsx` & `frontend/src/App.tsx`: Enabled "Parameter Estimation" navigation tab and routed the page.
  - `docs/parameter-estimation.md`: Mathematical specification covering objective functions, Jacobian covariance derivation, confidence intervals, identifiability criteria, and provenance policy.
  - `docs/implementation-plan.md`: Updated Phase 7 status to PASS.
- **Commands Executed:**
  - `python -m pytest backend/tests` (95/95 tests passed in 2.92s with zero warnings or errors)
  - `npm run build` in `frontend/` (`tsc -b && vite build` built production bundle in 57.26s with zero errors)
- **Scientific Verifications:**
  - **Synthetic Parameter Recovery:**
    - Clean first-order oracle ($k_{\text{true}} = 0.1500\text{ min}^{-1}$): recovered $\hat{k} = 0.1500\text{ min}^{-1}$ ($|\hat{k} - k_{\text{true}}| < 10^{-4}$, $R^2 = 1.0000$, $RMSE < 10^{-4}$).
    - Second-order run ($k_{\text{true}} = 0.2500\text{ L/(mol}\cdot\text{min})$): recovered $\hat{k} = 0.2500$ ($R^2 > 0.999$).
    - Zero-order run ($k_{\text{true}} = 0.0400\text{ mol/(L}\cdot\text{min})$): recovered $\hat{k} = 0.0400$.
    - Steady-state multi-flow run ($\tau \in [2, 5, 10, 15, 20]\text{ min}$): recovered $\hat{k} = 0.1500$ ($R^2 = 1.0000$).
  - **Identifiability & Uncertainty Guardrails:** Verified that flat/unexcited series trigger explicit warnings, bound collisions are flagged, and singular information prevents reporting fabricated confidence intervals.
  - **Scientific Labeling:** Verified that all estimation outputs carry the label: *"FITTED ESTIMATE: The reported kinetic parameters are mathematical estimates derived from numerical optimization and model assumptions. They are not direct laboratory measurements."*
- **Phase 7 Acceptance Gate:** **PASS**
