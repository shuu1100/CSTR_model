# Phase 11 — ML API, Training Tasks and UI

Integrate dataset preview/validation, training/evaluation, job status/cancellation if needed, model listing and inference into existing FastAPI/UI. Do not add Redis/Celery/cloud unless canonical plan requires it. Keep long tasks from blocking simulation. Validate feature schema, units, ranges and model version; return provenance/warnings and uncertainty if supported. UI shows split summary, model selection, tuning config, curves, validation/test metrics and comparison to mechanistic baseline. Keep final test metrics out of iterative tuning.

## Global compliance
Follow `GLOBAL-INSTRUCTIONS.md` and preserve the existing Phase 0–15 architecture. Inspect prior work before editing, add tests, run checks, and report actual results.
