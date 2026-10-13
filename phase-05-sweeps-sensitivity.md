# Phase 5 — Parameter Sweeps and Sensitivity

Add reproducible parameter sweeps and sensitivity for V, Q, k, CAin and other supported parameters. Start with grid/one-factor-at-a-time; use Latin Hypercube Sampling (SciPy QMC) for coverage where useful. Use validated core for all cases. Show trends, failed cases, ranges, units and metadata; fixed seeds for randomized designs. Test known first-order monotonic trends and report failed simulations instead of silently dropping them.

## Global compliance
Follow `GLOBAL-INSTRUCTIONS.md` and preserve the existing Phase 0–15 architecture. Inspect prior work before editing, add tests, run checks, and report actual results.
