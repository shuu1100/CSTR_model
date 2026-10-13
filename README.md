# CSTR Lab — Digital Twin & Scientific Machine Learning Platform

CSTR Lab is an offline-capable, high-fidelity scientific computing and machine learning platform for Continuous Stirred-Tank Reactors (CSTR). It combines mechanistic differential equation solvers, parameter estimation, interactive web telemetry, and scientific ML architectures (Neural ODEs and PINNs).

---

## 1. Canonical Stack & Engineering Principles

- **Backend:** Python 3.10+ with FastAPI, Pydantic v2, and SQLite (SQLAlchemy 2.x).
- **Frontend:** React 18, TypeScript, Vite, Tailwind CSS, and Plotly.js interactive charts.
- **Scientific Computing:** NumPy, SciPy (`solve_ivp`, `optimize`, `stats.qmc`), Pandas, OpenPyXL.
- **Machine Learning:** PyTorch, scikit-learn.
- **Testing & Verification:** pytest, HTTPX / FastAPI TestClient, Vite/TypeScript compilation.
- **Offline Guarantee:** Zero paid services, third-party cloud APIs, or external database requirements. The complete simulation and training pipeline runs locally and offline.

---

## 2. Scientific Oracle & Governing Equations

The core reactor models an ideal, isothermal, constant-volume CSTR with reaction $A \rightarrow \text{Products}$:

$$\frac{dC_A}{dt} = \frac{Q}{V}\left(C_{A,\text{in}} - C_A\right) + r_A(C_A) = \frac{1}{\tau}\left(C_{A,\text{in}} - C_A\right) + r_A(C_A)$$

### Canonical Validation Oracle
For a first-order reaction ($r_A = -k C_A$) at steady state:
$$C_{A,\text{ss}} = \frac{C_{A,\text{in}}}{1 + k\tau}, \quad X_A = \frac{k\tau}{1 + k\tau} = \frac{\text{Da}}{1 + \text{Da}} \quad (C_{A,\text{in}} > 0)$$

**Standard Oracle Reference:**
- $V = 10.0\text{ L}$, $Q = 1.0\text{ L/min} \implies \tau = 10.0\text{ min}$
- $k = 0.15\text{ min}^{-1} \implies \text{Da} = 1.50$
- $C_{A,\text{in}} = 1.0\text{ mol/L} \implies C_{A,\text{ss}} = 0.40\text{ mol/L}, \quad X_A = 0.60\text{ (60\%)}$
- $C_{A,\text{in}} = 2.0\text{ mol/L} \implies C_{A,\text{ss}} = 0.80\text{ mol/L}, \quad X_A = 0.60\text{ (60\%)}$

---

## 3. Directory Layout & Data Governance

```
CSTR_model/
├── backend/
│   ├── app/
│   │   ├── api/             # REST endpoints (simulation, sweeps, ingestion, ml)
│   │   ├── core/            # Solvers, kinetics, parameter fitting, LHS generation
│   │   ├── schemas/         # Pydantic validation schemas
│   │   └── main.py          # FastAPI application root
│   └── tests/               # 200 comprehensive pytest tests
├── frontend/                # React + TypeScript + Vite interactive UI
├── data/
│   ├── raw/                 # Immutable source datasets + manifest.json
│   ├── interim/             # Cleaned intermediate files
│   ├── processed/           # Standardized modeling datasets
│   └── generated/           # Synthetic LHS trajectories & zero-leakage splits
├── artifacts/
│   └── models/              # Checkpoints, scalers, and ONNX weights
├── docs/                    # Architecture, Baseline, Governance, & Phase Status
├── reports/                 # Quality audits & dataset cards
├── scripts/                 # Standalone auditing and data generation tools
├── .env.example             # Local configuration placeholders (no secrets)
└── README.md
```

### Data Manifest & Candidate Data Status
All candidate files are cryptographically verified in `data/raw/manifest.json`:
- **`cstr_rawdata.npy`** (SHA-256: `9a0ec1115e8b2e947487c2688c924e3f0382a6ee1bfea39e8dd652542ee9c4e9`): Shape $(2860, 1404)$, unknown column semantics. **Status: QUARANTINED**. Guessing feature meanings is prohibited until an official schema is provided.
- **`CSTR_24aug_PRBS_dataset.xlsx`** (SHA-256: `0e42ce8af6e05cdcd3c8a39eb1e0d54c9478a9623475d1bc64408e3c23d3d3bd`): Contains RTD temperature and flow measurements, but no concentration measurements. **Status: PRESERVED FOR PHASE 13 THERMAL MODELING**. Incompatible with isothermal concentration validation.

---

## 4. Setup & Quickstart

### 4.1 Backend Setup
```bash
# From workspace root
cd backend

# Install dependencies
pip install -r requirements.txt

# Run backend development server
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
API documentation is interactively available at `http://127.0.0.1:8000/docs`.

### 4.2 Frontend Setup
```bash
# From workspace root
cd frontend

# Install dependencies
npm install

# Start development dashboard
npm run dev
```
Access the UI dashboard at `http://localhost:5173`.

---

## 5. Verification & Test Suite

### Run Backend Pytest Suite
From workspace root:
```bash
python -m pytest -v
```
*Current Baseline:* **200 passing tests in ~30 seconds.**

### Build Frontend
From `frontend/` directory:
```bash
npm run build
```
*Current Baseline:* **Clean compilation (`tsc -b && vite build`), 0 TypeScript errors.**

### Run Frontend Vitest Unit Tests
From `frontend/` directory:
```bash
npm test
```
*Current Baseline:* **4 passing unit tests (100% pass rate).**

---

## 6. Project Documentation Index

- [Architecture & Contract Specification](file:///c:/local_disc_D/CSTR_model/docs/architecture.md)
- [Scientific Assumptions & Governing Equations](file:///c:/local_disc_D/CSTR_model/docs/scientific-assumptions.md)
- [Data Governance & Candidate Datasets Protocol](file:///c:/local_disc_D/CSTR_model/docs/data-governance.md)
- [Phase Roadmap & Implementation Status](file:///c:/local_disc_D/CSTR_model/docs/phase-status.md)
- [REST API Specification](file:///c:/local_disc_D/CSTR_model/docs/api-specification.md)
