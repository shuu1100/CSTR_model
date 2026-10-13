# CSTR Lab — Digital Twin & Scientific Machine Learning Platform

CSTR Lab is an offline-capable, high-fidelity scientific computing, simulation, and machine learning platform for Continuous Stirred-Tank Reactors (CSTR). It combines first-principles mechanistic differential equation solvers, non-isothermal thermal dynamics, non-linear parameter estimation, interactive telemetry, and scientific ML architectures (Grey-Box Neural ODEs and Physics-Informed Neural Networks).

---

## 1. Canonical Stack & Engineering Principles

- **Backend:** Python 3.10+ (tested on Python 3.14) with FastAPI, Pydantic v2, and SQLite with SQLAlchemy 2.x ORM.
- **Frontend:** React 18, TypeScript, Vite, Tailwind CSS, Lucide icons, and Plotly.js interactive visualization.
- **Scientific Computing:** NumPy, SciPy (`solve_ivp`, `optimize.least_squares`, `stats.qmc`), Pandas, OpenPyXL.
- **Scientific Machine Learning:** PyTorch (RK4 numerical integration, automatic differentiation collocation loss), scikit-learn.
- **Testing & Quality Assurance:** pytest (238 backend tests), Vitest (frontend unit tests), TypeScript strict mode (0 errors).
- **Strict Offline Guarantee:** Zero paid services, zero cloud APIs, zero external telemetry, and zero Redis/Celery dependencies. The complete numerical simulation, surrogate training, and data persistence pipeline runs 100% locally and offline.

---

## 2. Scientific Core & Governing Equations

### 2.1 Isothermal Mass Balance
For an ideal, constant-volume CSTR with reaction $A \rightarrow \text{Products}$:

$$\frac{dC_A}{dt} = \frac{Q}{V}\left(C_{A,\text{in}} - C_A\right) + r_A(C_A) = \frac{1}{\tau}\left(C_{A,\text{in}} - C_A\right) + r_A(C_A)$$

where:
- $V$: Reactor volume [$\text{L}$]
- $Q$: Volumetric flow rate [$\text{L/min}$]
- $\tau = V/Q$: Space time / residence time [$\text{min}$]
- $C_{A,\text{in}}, C_A$: Inlet and reactor reactant concentrations [$\text{mol/L}$]
- $r_A(C_A) = -k C_A^n$: Reaction rate [$\text{mol/(L}\cdot\text{min)}$] for order $n \in \{0, 1, 2\}$

### 2.2 Canonical Validation Oracle
For a first-order reaction ($r_A = -k C_A$) at steady state:
$$C_{A,\text{ss}} = \frac{C_{A,\text{in}}}{1 + k\tau}, \quad X_A = \frac{k\tau}{1 + k\tau} = \frac{\text{Da}}{1 + \text{Da}} \quad (C_{A,\text{in}} > 0)$$

**Standard Oracle Reference:**
- $V = 10.0\text{ L}$, $Q = 1.0\text{ L/min} \implies \tau = 10.0\text{ min}$
- $k = 0.15\text{ min}^{-1} \implies \text{Da} = 1.50$
- $C_{A,\text{in}} = 1.0\text{ mol/L} \implies C_{A,\text{ss}} = 0.40\text{ mol/L}, \quad X_A = 0.60\text{ (60\%)}$
- $C_{A,\text{in}} = 2.0\text{ mol/L} \implies C_{A,\text{ss}} = 0.80\text{ mol/L}, \quad X_A = 0.60\text{ (60\%)}$

### 2.3 Non-Isothermal & Thermal Jacket Dynamics
Coupled mass, reactor energy, and jacket cooling balances:

$$\frac{dC_A}{dt} = \frac{Q}{V}(C_{A,\text{in}} - C_A) - k(T)C_A^n$$
$$\frac{dT}{dt} = \frac{Q}{V}(T_{\text{in}} - T) + \frac{(-\Delta H_{\text{rxn}})}{\rho C_p} k(T) C_A^n - \frac{U A}{V \rho C_p}(T - T_j)$$
$$\frac{dT_j}{dt} = \frac{Q_j}{V_j}(T_{j,\text{in}} - T_j) + \frac{U A}{V_j \rho_j C_{pj}}(T - T_j)$$

- **Arrhenius Kinetics:** $k(T) = A \exp\left(-\frac{E_a}{R T}\right)$ with strict Kelvin enforcement ($T > 0\text{ K}$) and numerical exponent safeguards.
- **Selectable Isothermal Mode:** Setting `isothermal=True` holds $T \equiv T_{\text{in}}$, identically recovering pure isothermal dynamics.
- **Thermal Runaway Detection:** Automatic diagnostic warning triggered when $T_{\text{peak}} - T_{\text{in}} > 50\text{ K}$.

---

## 3. Platform Capabilities & Architecture

```
CSTR_model/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # REST endpoints (simulations, ml, history, analysis, datasets)
│   │   ├── core/            # Solvers (analytical, dynamic ODE, thermal, sweeps, PRBS audit)
│   │   ├── db/              # SQLAlchemy 2.0 persistence, SQLite migrations & export services
│   │   ├── ml/              # Grey-Box Neural ODE, PINN, baselines, latency benchmarking
│   │   ├── schemas/         # Strongly-typed Pydantic schemas with canonical units
│   │   └── main.py          # FastAPI application root & middleware
│   └── tests/               # 238 comprehensive unit and integration pytest tests
├── frontend/
│   ├── src/
│   │   ├── api/             # Typed API client with full error handling
│   │   ├── components/      # Modular telemetry panels, parameter controls & Plotly charts
│   │   ├── pages/           # Dashboard, Dynamic Simulation, Machine Learning, Sweeps, Data
│   │   └── types/           # TypeScript domain interfaces
│   └── package.json         # React 18, Vite, TypeScript, Vitest
├── data/
│   ├── raw/                 # Immutable candidate datasets & cryptographic manifest.json
│   ├── interim/             # Cleaned intermediate files
│   ├── processed/           # Standardized modeling datasets
│   └── generated/           # Synthetic Latin Hypercube trajectories & split manifests
├── artifacts/
│   └── models/              # Checkpoints, scalers, and parameter states
├── docs/                    # Technical architecture, scientific specifications & phase roadmaps
├── reports/                 # Formal verification audits, dataset cards & benchmark logs
└── README.md
```

### Key Modules:
1. **Dynamic ODE Solver (`backend/app/core/dynamic_solver.py`):** Multi-order kinetics ($n \in \{0, 1, 2\}$), arbitrary step changes in $Q, C_{A,\text{in}}, k$, stiff ODE solvers (Radau, BDF), and smooth zero-order depletion regularization.
2. **Sensitivity & Sweeps (`backend/app/core/sweeps.py`):** 1D OFAT sweeps, 2D meshgrid parameter sweeps, Latin Hypercube Sampling (SciPy QMC), and local finite-difference elasticity calculation.
3. **Parameter Estimation (`backend/app/core/parameter_estimation.py`):** Non-linear least-squares optimization (`scipy.optimize.least_squares`) recovering rate constants ($k$) and initial concentrations ($C_0$) with asymptotic 95% confidence intervals from Jacobian covariance.
4. **Data Ingestion & Filtering (`backend/app/core/ingestion.py`):** Multi-format CSV/Excel parser, column mapping, Savitzky-Golay polynomial smoothing, and isolation forest anomaly detection.
5. **Grey-Box Neural ODE (`backend/app/ml/neural_ode.py`):** Hybrid physics-ML model using PyTorch RK4 numerical integration that embeds known macroscopic mass balances while learning constitutive reaction kinetics $r_A(C_A)$.
6. **Physics-Informed Neural Network (`backend/app/ml/pinn.py`):** Neural surrogate trained with autograd collocation loss minimizing the continuous CSTR mole balance residual, guaranteed non-negative projection ($C_A \ge 0$), and multi-seed benchmarking.
7. **ML Management & Training UI (`backend/app/api/v1/ml.py`):** Thread-pooled asynchronous model training, real-time loss tracking, job cancellation, inference with 95% epistemic confidence intervals, and full 4-tab interactive frontend telemetry.
8. **Persistence, History & Multi-Sheet Exports (`backend/app/db/`):** SQLite persistence with schema versioning (`schema_version`), artifact tracking, random seed, and split ID. Automatic database migration, side-by-side run comparisons, and multi-sheet **XLSX** (`openpyxl`), CSV, and JSON exports with canonical units. Automated retention policy enforcement (`max_runs`, `retention_days`).
9. **Arrhenius & Non-Isothermal CSTR (`backend/app/core/thermal.py`):** Coupled energy balance for fluid and jacket, thermal runaway detection, and PRBS experimental workbook compatibility audit (`backend/app/core/prbs_thermal.py`) with blocked chronological calibration and locked test evaluation.
10. **ONNX Feasibility & Fallback Engine (`backend/app/ml/onnx_optimization.py`):** Latency, throughput, and memory benchmarking, Normal/Edge/OOD regime stability audit, and zero-crash transparent native PyTorch fallback preserving an external zero-dependency architecture.

---

## 4. Candidate Datasets & Data Governance

All candidate files are cryptographically verified in `data/raw/manifest.json`:
- **`cstr_rawdata.npy`** (SHA-256: `9a0ec1115e8b2e947487c2688c924e3f0382a6ee1bfea39e8dd652542ee9c4e9`): Shape $(2860, 1404)$, unlabeled floating-point array with no feature documentation. **Status: QUARANTINED**. Guessing feature meanings is strictly prohibited.
- **`CSTR_24aug_PRBS_dataset.xlsx`** (SHA-256: `0e42ce8af6e05cdcd3c8a39eb1e0d54c9478a9623475d1bc64408e3c23d3d3bd`): Contains RTD temperature and flow measurements across 3,131 samples ($\Delta t = 0.5\text{ s}$). **Status: AUDITED FOR THERMAL DYNAMICS ONLY**.
  - **Scientific Constraint:** **Temperature-only data cannot validate concentration**. ZERO concentration assays exist in this workbook; any attempt to infer concentration validation is guarded and rejected.

---

## 5. Setup & Quickstart

### 5.1 Backend Setup
```bash
# From workspace root
cd backend

# Install dependencies (Python 3.10+)
pip install -r requirements.txt

# Run backend development server on port 8001
uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
```
Interactive API documentation is available at:
- **Swagger UI:** [http://127.0.0.1:8001/docs](http://127.0.0.1:8001/docs)
- **ReDoc:** [http://127.0.0.1:8001/redoc](http://127.0.0.1:8001/redoc)
- **OpenAPI Schema:** [http://127.0.0.1:8001/openapi.json](http://127.0.0.1:8001/openapi.json)

### 5.2 Frontend Setup
```bash
# From workspace root
cd frontend

# Install dependencies
npm install

# Start development server on port 5173
npm run dev
```
Access the interactive web telemetry dashboard at [http://localhost:5173](http://localhost:5173).

---

## 6. Complete REST API Route Directory (30 Endpoints)

| Category | Method | Endpoint | Description |
| :--- | :--- | :--- | :--- |
| **Simulations** | `POST` | `/api/v1/simulations/steady-state` | Isothermal analytical steady-state solution & conversion |
| | `POST` | `/api/v1/simulations/dynamic` | Transient dynamic ODE solver with step changes |
| | `POST` | `/api/v1/simulations/parameter-sweep` | 1D & 2D parameter sweeps and local elasticity sensitivity |
| | `POST` | `/api/v1/simulations/parameter-sweep/lhs` | Latin Hypercube Sampling (SciPy QMC) parameter exploration |
| | `POST` | `/api/v1/simulations/thermal` | Coupled non-isothermal CSTR mass & energy balances with jacket cooling |
| | `GET` | `/api/v1/simulations/thermal/prbs-audit` | Experimental PRBS dataset signal mapping & governance audit |
| | `POST` | `/api/v1/simulations/thermal/prbs-calibration` | Thermal parameter calibration on 60% partition & locked test evaluation |
| **Machine Learning** | `GET` | `/api/v1/ml/models` | List registered surrogate models (Grey-Box Neural ODE, PINN, baselines) |
| | `GET` | `/api/v1/ml/dataset/preview` | Preview candidate synthetic dataset with split distributions |
| | `POST` | `/api/v1/ml/dataset/validate` | Assert zero-leakage partition disjointness & schema integrity |
| | `POST` | `/api/v1/ml/train` | Asynchronous training job dispatch with custom seed & hyperparameters |
| | `GET` | `/api/v1/ml/jobs` | List all historical background training jobs |
| | `GET` | `/api/v1/ml/jobs/{job_id}` | Poll asynchronous job status, epoch progress, and loss metrics |
| | `POST` | `/api/v1/ml/jobs/{job_id}/cancel` | Gracefully cancel a running training task |
| | `POST` | `/api/v1/ml/predict` | Surrogate inference with 95% epistemic confidence intervals |
| | `GET` | `/api/v1/ml/baselines/benchmark` | Mechanistic vs. naive baseline comparison benchmark table |
| | `GET` | `/api/v1/ml/optimization/audit` | Latency benchmark, Normal/Edge/OOD regime stability, & fallback status |
| | `POST` | `/api/v1/ml/optimization/benchmark` | Dynamic CPU latency & throughput benchmarking tool |
| **Parameter Estimation** | `POST` | `/api/v1/analysis/fit-kinetics` | Non-linear least-squares rate constant estimation with confidence bounds |
| **Data Ingestion** | `POST` | `/api/v1/datasets/upload` | Upload & audit user CSV/Excel time series |
| | `POST` | `/api/v1/datasets/process` | Savitzky-Golay noise filtering & isolation forest anomaly detection |
| | `GET` | `/api/v1/datasets/sample-dataset` | Download bundled canonical calibration dataset |
| **History & Export** | `GET` | `/api/v1/history/runs` | List persisted simulation runs with pagination & category filters |
| | `POST` | `/api/v1/history/runs` | Manually archive a simulation run with provenance, seed, & split ID |
| | `GET` | `/api/v1/history/runs/{run_id}` | Retrieve full run history with full continuous time series |
| | `DELETE` | `/api/v1/history/runs/{run_id}` | Permanently delete a simulation run record |
| | `POST` | `/api/v1/history/compare` | Side-by-side comparative inspection across $\ge 2$ historical runs |
| | `GET` | `/api/v1/history/export` | Download session history archive in `json`, `csv`, or multi-sheet `xlsx` formats |
| | `POST` | `/api/v1/history/retention/apply` | Apply automated data retention policy (`max_runs`, `retention_days`) |
| **System** | `GET` | `/api/v1/health` | System health check, database status, and version info |
| | `GET` | `/api/v1/models` | Analytical model parameter bounds and metadata catalog |
| | `GET` | `/` | Root API welcome message |

---

## 7. Verification & Automated Test Suite

### Run Backend Pytest Suite (238 Tests)
```bash
python -m pytest backend/tests -v
```
*Current Status:* **238 passed in ~74 seconds (100% pass rate).**

### Run Frontend Vitest Unit Tests
```bash
npm --prefix frontend test
```
*Current Status:* **4 passed in ~0.37 seconds (100% pass rate).**

### Build Production Frontend Bundle
```bash
npm --prefix frontend run build
```
*Current Status:* **0 TypeScript errors, clean production bundle generated.**

---

## 8. Technical Reports Index

- [Phase 06: Data Ingestion & Quality Audit Report](file:///c:/local_disc_D/CSTR_model/reports/phase-06-data-quality-report.md)
- [Phase 07: Non-Linear Parameter Estimation Report](file:///c:/local_disc_D/CSTR_model/reports/phase-07-parameter-estimation.md)
- [Phase 08: Synthetic Coverage & Splits Report](file:///c:/local_disc_D/CSTR_model/reports/phase-08-coverage-quality-report.md)
- [Phase 08A: Training, Testing & Tuning Protocol](file:///c:/local_disc_D/CSTR_model/reports/phase-08A-training-testing-tuning-protocol.md)
- [Phase 09: Baselines & Grey-Box Neural ODE Benchmark](file:///c:/local_disc_D/CSTR_model/reports/phase-09-baselines-and-neural-ode.md)
- [Phase 10: Physics-Informed Neural Network (PINN) Report](file:///c:/local_disc_D/CSTR_model/reports/phase-10-pinn-research-model.md)
- [Phase 11: Machine Learning API & Training UI Report](file:///c:/local_disc_D/CSTR_model/reports/phase-11-ml-api-training-ui.md)
- [Phase 12: Run History, Persistence & Multi-Format Exports](file:///c:/local_disc_D/CSTR_model/reports/phase-12-persistence-and-exports.md)
- [Phase 13: Arrhenius Kinetics & Thermal Non-Isothermal CSTR](file:///c:/local_disc_D/CSTR_model/reports/phase-13-arrhenius-and-thermal-model.md)
- [Phase 14: Latency Benchmarking & ONNX Fallback Audit](file:///c:/local_disc_D/CSTR_model/reports/phase-14-onnx-optimization-audit.md)
- [Roadmap Implementation Status & Baseline Matrix](file:///c:/local_disc_D/CSTR_model/docs/phase-status.md)
