# Phase 11 Technical Report — ML API, Training Tasks and UI

## 1. Executive Summary

Phase 11 completes the full integration of machine learning capabilities across the backend REST API and the React frontend dashboard, conforming to `GLOBAL-INSTRUCTIONS.md`, `phase-11-ml-api-training-ui.md`, and the `phase-08A` protocol.

Key features delivered:
1. **Model Catalog & REST Endpoints:** `/api/v1/ml/models`, `/api/v1/ml/train`, `/api/v1/ml/predict`, and `/api/v1/ml/baselines/benchmark`.
2. **Interactive ML Frontend Page (`MachineLearningPage.tsx`):** Three integrated workflows:
   - *Forecast & Inference:* Dynamic trajectory simulations using PyTorch Grey-Box Neural ODE and PINN surrogates.
   - *Training Studio:* Real-time loss curves, hyperparameter tuning, and zero-leakage validation tracking.
   - *Locked Test Leaderboard:* Comprehensive metrics comparison across 19 holdout test trajectories.
3. **Physical Diagnostics & OOD Detection:** Real-time warnings for extreme Damköhler regimes and strict prevention of negative concentration artifacts ($C_A < 0$).

---

## 2. API Endpoints Overview

| Method | Endpoint | Description | Provenance / Guarantees |
|---|---|---|---|
| `GET` | `/api/v1/ml/models` | Lists available neural and baseline model architectures | Catalog metadata with units and input schemas |
| `GET` | `/api/v1/ml/baselines/benchmark` | Evaluates models across locked test split (19 trajectories) | Zero leakage, disjoint trajectory evaluation |
| `POST` | `/api/v1/ml/train` | Dispatches online training and hyperparameter optimization | Returns loss history, best epoch, and validation error |
| `POST` | `/api/v1/ml/predict` | Computes dynamic transient trajectory forecast | Differentiable RK4 / PINN inference with OOD warnings |

---

## 3. Frontend Architecture & User Experience

- **Component:** `frontend/src/pages/MachineLearningPage.tsx`
- **Navigation:** Activated "Neural ODE & PINN" tab in `Header.tsx` and routed in `App.tsx`.
- **Plotly Visualizations:**
  - Dynamic trajectory $C_A(t)$ with learned kinetic rate $r_A(t)$ secondary axis.
  - Multi-curve loss progression showing training loss and validation loss convergence.
- **Verification:**
  - `npm test` -> 4 tests passed.
  - `npm run build` -> Clean production bundle generated (1604 modules transformed, 0 TypeScript errors).
