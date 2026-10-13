# Phase 10 — Physics-Informed Neural Network

Implement PINN as optional research model. Define ODE residual, observation loss where compatible measurements exist, initial-condition loss and constraints; document loss weights and track each loss. Fit normalizers on training only. Tune architecture, collocation points, weights and optimizer on validation only. Compare with analytical/numerical solution and prior baselines using trajectory/steady-state error, residuals, positivity violations, runtime and multiple seeds. If only synthetic data is available, state that clearly; no claims of experimental validation.

## Global compliance
Follow `GLOBAL-INSTRUCTIONS.md` and preserve the existing Phase 0–15 architecture. Inspect prior work before editing, add tests, run checks, and report actual results.
