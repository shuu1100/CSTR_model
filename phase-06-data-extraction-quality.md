# Phase 6 — Data Extraction, Ingestion and Quality

Discover files; hash/deduplicate; inspect Excel sheets, dimensions, headers, units rows, formulas, timestamps, duplicates, missingness, sampling interval, ranges and outliers. Preserve raw sources; write derived extracts only to interim/processed. Load NPY safely with `allow_pickle=False`, report shape/dtype/ranges and keep semantics unknown until documented. Produce column dictionary, data quality report, data card and dataset-task compatibility matrix. PRBS workbook can only support thermal tasks if columns/units/physics match; no concentration validation without concentration measurement. Do not force incompatible data into training.

## Global compliance
Follow `GLOBAL-INSTRUCTIONS.md` and preserve the existing Phase 0–15 architecture. Inspect prior work before editing, add tests, run checks, and report actual results.
