# Phase 13 — Arrhenius and Optional Thermal CSTR

Add Arrhenius `k(T)=A exp(-Ea/(R T))` with Kelvin, explicit units and numerical safeguards. Add energy/jacket balances only with documented heat capacity, density, heat transfer, enthalpy and assumptions; keep isothermal mode selectable. Use PRBS workbook only after compatibility review; identify signal mappings rather than guessing. Check timestamps, delays, missingness and identifiability. Split by run or blocked chronology; fit on calibration, select on validation, report locked test and physical residuals. Temperature-only data cannot validate concentration.

## Global compliance
Follow `GLOBAL-INSTRUCTIONS.md` and preserve the existing Phase 0–15 architecture. Inspect prior work before editing, add tests, run checks, and report actual results.
