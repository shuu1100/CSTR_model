# Phase 9 — Baseline ML and Grey-Box Neural ODE

First compare naive and mechanistic baselines with suitable scikit-learn models. Explicitly define features/targets and forbid future-data leakage or unrealistic hidden-parameter shortcuts. Use grouped/blocked splits; tune on validation only; test once after freezing. Log all trials and save preprocessing/model/metadata. Then optionally implement a PyTorch Grey-box Neural ODE that preserves known mass-balance structure and learns only justified unknown terms. Add seed control, early stopping, checkpoints, gradient controls, training curves, physical residuals and edge/OOD tests. Compare on identical holdout; do not replace trusted solver without evidence.

## Global compliance
Follow `GLOBAL-INSTRUCTIONS.md` and preserve the existing Phase 0–15 architecture. Inspect prior work before editing, add tests, run checks, and report actual results.
