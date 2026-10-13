# Phase 2 — Dynamic ODE Solver

Implement transient CSTR with SciPy `solve_ivp`, configurable initial state, parameters, time span, output sampling, solver method/tolerances, and supported rate law. Start with first order; add other orders only with explicit equations and safeguards. Support time-varying feeds only with documented interpolation/hold behavior. Return trajectory and solver diagnostics. Compare to analytical transient/steady state; test tolerance convergence, stiff cases, non-finite inputs and solver failures. Never silently clip bad states.

## Global compliance
Follow `GLOBAL-INSTRUCTIONS.md` and preserve the existing Phase 0–15 architecture. Inspect prior work before editing, add tests, run checks, and report actual results.
