# Phase 1 — Scientific Core and Analytical Oracles

Implement pure typed functions for first-order isothermal CSTR steady-state, conversion, residence time and units. Validate finite and physically allowed values, including CAin=0 conversion guard. Use the oracle in GLOBAL INSTRUCTIONS and parameterized tests, dimensional checks and mass-balance residual checks. Keep scientific code independent of API/UI. Acceptance: oracle matches documented tolerance; invalid inputs fail safely; no network needed.

## Global compliance
Follow `GLOBAL-INSTRUCTIONS.md` and preserve the existing Phase 0–15 architecture. Inspect prior work before editing, add tests, run checks, and report actual results.
