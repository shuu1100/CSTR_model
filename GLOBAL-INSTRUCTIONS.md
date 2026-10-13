# GLOBAL INSTRUCTIONS — CSTR LAB / ANTIGRAVITY

These prompts extend the existing CSTR Lab roadmap Phase 0–15; they do not replace it. Preserve working code, existing architecture, APIs, frontend/backend contracts, and implementation order. Before each phase, inspect the repository, prior phase reports, current tests, and available datasets. Do not rebuild the project from scratch if it already exists.

## Canonical stack
Frontend: React + TypeScript + Vite, Tailwind/shadcn where already configured, Plotly charts. Backend: Python + FastAPI + Pydantic. Scientific: NumPy, SciPy (`solve_ivp`, optimization), Pandas, OpenPyXL. ML: scikit-learn and PyTorch; `torchdiffeq` and ONNX Runtime only if justified. Persistence: SQLite + SQLAlchemy 2.x; Alembic if migrations are needed. Testing: pytest, HTTPX/TestClient, existing frontend test runner. Do not introduce paid services, API keys, Redis, cloud infrastructure, or new infrastructure unless the existing master plan requires it. Core simulation must work offline.

## Scientific oracle
For ideal constant-volume, well-mixed, isothermal first-order CSTR A → products:
`dCA/dt = (Q/V)(CAin − CA) − k CA`; `tau=V/Q`; `CA_ss=((Q/V)*CAin)/((Q/V)+k)`; `X=(CAin−CA_ss)/CAin=k*tau/(1+k*tau)` only if CAin>0. Oracle: V=10 L, Q=1 L/min, k=0.15 min⁻¹, CAin=1 mol/L => tau=10 min, CA_ss=0.4 mol/L, X=0.6. Explicitly track units; never silently mix seconds/minutes, L/m³, mol/L/mol/m³, or °C/K.

## Candidate data — inspect, never assume
- `CSTR_24aug_PRBS_dataset.xlsx` or suffix duplicates: reportedly includes reactor/jacket temperatures, feed A/B flows, hot-oil circulation, bath temperature and feed temperatures. Verify actual workbook/sheets/columns/units/timestamps first. May support thermal calibration only if compatible. If concentration is not measured, it cannot validate concentration predictions.
- `cstr_rawdata.npy`: reportedly ~2860×1404 with unknown semantics. Load with `allow_pickle=False`; record shape/dtype/ranges. Do not infer labels, units, or column meanings and do not use for supervised training until documented.
- Search the workspace, compute SHA-256 hashes, identify duplicates, preserve raw files read-only, and create a data manifest. Separate `data/raw`, `data/interim`, `data/processed`, `data/generated`, `artifacts/models`, and `reports`.
- Unknown schema means quarantine/metadata request, not guessing. Produce a compatibility matrix for each dataset and task.

## Data splitting and leakage prevention
- Synthetic data: default 70/15/15 train/validation/test split by independent trajectory or parameter draw, never by individual time row.
- Experimental data: split by complete run/experiment. If only one run exists, use chronological blocked windows (with gap/embargo if appropriate) and state the generalization limitation.
- Keep windows from the same run/trajectory in one split. Fit imputers, scalers, encoders, feature selection and dimensionality reduction on training only.
- Validation is for tuning; lock test until model and preprocessing are frozen. If test results influence decisions, mark it as development data and create a new holdout if possible.
- Record seeds, source hashes, trajectory/run IDs, split IDs, timestamps, code version, transforms, exclusions, and parameter ranges.

## Training and evaluation standards
Define each task and prediction-time inputs before training. Compare naive and mechanistic baselines to simple ML before neural methods. Tune only on training/validation; log all trials, failures, hyperparameters, seeds, versions and runtime. Use at least 3 seeds for stochastic neural models where compute permits. Report MAE, RMSE, R² when meaningful, relative error with near-zero safeguards, per-trajectory/horizon errors, steady-state error, physical residuals, runtime, and uncertainty/seed variation when available. For classification report per-class precision/recall/F1, macro-F1, confusion matrix, false alarms and missed detections. Never rely on R² alone. Check residuals, physical plausibility, OOD ranges, solver failures and worst cases. Synthetic performance is not proof of real-world validity.

## Required workflow for every phase
Inspect current state → state plan/files → implement smallest coherent increment → add tests/docs → run relevant tests/lint/type/build checks → report actual results and blockers → update `docs/phase-status.md`. Do not claim tests passed unless actually run. Keep app runnable after each phase. UI/API must show units, assumptions, data provenance, model version and limitations; label measured, simulated, estimated and ML-predicted values distinctly. Validate uploads and numerical inputs; no secrets in source control.
