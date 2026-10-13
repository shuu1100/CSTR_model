# Phase 8 — Synthetic Training Data, Extraction and Splitting

Generate reproducible trajectories from the tested mechanistic solver. Sample V,Q,k,CAin,CA0, supported reaction order and forcing profiles using bounded ranges and LHS where appropriate; include edge cases. Record every parameter, unit, seed, solver setting, trajectory ID, source/code version and noise configuration. Separate datasets by task: steady-state regression, transient surrogate/forecasting, parameter estimation and optional fault diagnosis. Default 70/15/15 split by trajectory/parameter draw. Persist split manifest and assert disjoint IDs; keep test locked; fit transforms on train only. Create dataset card, coverage/quality report, failed-case log and reproducible command. Label as synthetic.

## Global compliance
Follow `GLOBAL-INSTRUCTIONS.md` and preserve the existing Phase 0–15 architecture. Inspect prior work before editing, add tests, run checks, and report actual results.
