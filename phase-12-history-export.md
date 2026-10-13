# Phase 12 — Persistence, History and Exports

Use SQLite + SQLAlchemy 2.x as planned; migrations only as needed. Store simulation, fit, dataset, split, training, model and metric metadata with schema/version and artifact references. Implement run comparison and CSV/JSON/XLSX exports with units, provenance, seeds, split IDs and timestamps. Validate paths and export filters; preserve privacy and retention rules. Test persistence across restart, migrations and round-trip metadata.

## Global compliance
Follow `GLOBAL-INSTRUCTIONS.md` and preserve the existing Phase 0–15 architecture. Inspect prior work before editing, add tests, run checks, and report actual results.
