# Phase 12 Technical Report — Persistence, History, Run Comparison, and Exports

## 1. Executive Summary

Phase 12 delivers the enterprise-grade persistence, historical audit tracking, multi-run comparison, and standardized export layer for CSTR Lab, adhering strictly to `GLOBAL-INSTRUCTIONS.md`, `phase-12-history-export.md`, and the Phase 08A protocol.

All data persistence is 100% offline and file-based using SQLite and SQLAlchemy 2.0 ORM with zero external cloud dependencies.

### Key Capabilities Delivered:
1. **SQLite + SQLAlchemy 2.0 ORM Persistence:**
   - Database: `data/cstr_lab.db` (and isolated disk fixtures during automated testing).
   - Models: `SimulationRunRecord`, `DatasetRecord`, `TrainingJobRecord`.
   - Extended Schema: `schema_version` (default `"1.0"`), `artifact_ref`, `seed`, and `split_id` columns with lightweight automatic SQLite migration via `PRAGMA table_info` and `ALTER TABLE ... ADD COLUMN` in `backend/app/db/database.py`.
2. **Metadata Round-Trip & Provenance:**
   - Full JSON serialization of input parameters, steady-state metrics, time-series coordinates ($t, C_A$), model artifact references, stochastic random seeds, dataset split IDs, and provenance badges (`SIMULATED`, `SYNTHETIC`, `BENCHMARK`, `EXPERIMENTAL`).
   - Verified 100% round-trip fidelity across engine shutdown and reconnection.
3. **Multi-Run Side-by-Side Comparison:**
   - Endpoint: `POST /api/v1/history/compare` accepting $\ge 2$ run IDs.
   - Produces structured comparative payload detailing parameter variations and performance summary metrics.
4. **Standardized Multi-Format Exports:**
   - **JSON (`GET /api/v1/history/export?format=json`):** Hierarchical export with canonical units ($V$: L, $Q$: L/min, $k$: $\text{min}^{-1}$, $C_A$: mol/L, $t$: min), ISO-8601 UTC timestamps, full parameter dictionaries, and time-series arrays.
   - **CSV (`GET /api/v1/history/export?format=csv`):** Flattened tabular dataset with prefixes `param_*` and `result_*`, suitable for R, Python pandas, and external spreadsheets.
   - **XLSX (`GET /api/v1/history/export?format=xlsx`):** Professional multi-sheet Excel workbook powered by `openpyxl`:
     - **Sheet 1 (`Runs_Overview`):** High-level run metadata, provenance, seed, split ID, and key metrics.
     - **Sheet 2 (`Parameters`):** Detailed parameter breakdowns per run.
     - **Sheet 3 (`Time_Series`):** Full continuous trajectory data with canonical unit headers (`Time t [min]`, `Concentration C_A [mol/L]`).
5. **Filtering & Automated Data Retention:**
   - Query filters by `run_type` (`steady_state`, `dynamic`, `sweep`, `ml_forecast`, `estimation`), `run_ids`, and date ranges (`date_from`, `date_to`).
   - Retention policy service (`apply_retention_policy`) and administrative route (`POST /api/v1/history/retention/apply`) enforcing maximum run limits (`max_runs`) and aging cutoffs (`retention_days`).

---

## 2. Architecture & Data Model

### SQLAlchemy 2.0 Model Specification (`SimulationRunRecord`)
```python
class SimulationRunRecord(Base):
    __tablename__ = "simulation_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    run_type: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    provenance: Mapped[str] = mapped_column(String(50), default="SIMULATED")
    schema_version: Mapped[str] = mapped_column(String(20), default="1.0")
    artifact_ref: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    seed: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    split_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    parameters_json: Mapped[str] = mapped_column(Text, nullable=False)
    results_summary_json: Mapped[str] = mapped_column(Text, nullable=False)
    time_series_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[str] = mapped_column(Text, nullable=False)
```

---

## 3. REST API Surface

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/history/runs` | List historical runs, sorted by descending timestamp, filterable by `run_type`, pagination via `limit`/`offset` |
| `POST` | `/api/v1/history/runs` | Archive simulation run with schema version, artifact ref, seed, and split ID |
| `GET` | `/api/v1/history/runs/{run_id}` | Retrieve complete run details including time series and metadata |
| `DELETE` | `/api/v1/history/runs/{run_id}` | Permanently remove a specific run |
| `POST` | `/api/v1/history/compare` | Compare 2 or more historical runs side-by-side |
| `GET` | `/api/v1/history/export` | Download archive in `json`, `csv`, or `xlsx` formats with filters (`run_type`, `date_from`, `date_to`) |
| `POST` | `/api/v1/history/retention/apply` | Apply retention policy to purge runs beyond `max_runs` or older than `retention_days` |

---

## 4. Test Verification & Results

16 dedicated tests verify persistence, export, comparison, and retention integrity:

```
backend\tests\test_persistence_and_export.py::TestDatabaseCRUD::test_record_and_get_simulation_run PASSED
backend\tests\test_persistence_and_export.py::TestDatabaseCRUD::test_list_and_filter_runs PASSED
backend\tests\test_persistence_and_export.py::TestDatabaseCRUD::test_delete_run PASSED
backend\tests\test_persistence_and_export.py::TestRunComparisonAndExports::test_compare_two_runs PASSED
backend\tests\test_persistence_and_export.py::TestRunComparisonAndExports::test_compare_single_run_raises PASSED
backend\tests\test_persistence_and_export.py::TestRunComparisonAndExports::test_export_json_valid_schema PASSED
backend\tests\test_persistence_and_export.py::TestRunComparisonAndExports::test_export_csv_valid_columns PASSED
backend\tests\test_persistence_and_export.py::TestHistoryAPIEndpoints::test_api_create_get_delete_cycle PASSED
backend\tests\test_persistence_and_export.py::TestHistoryAPIEndpoints::test_api_compare_runs PASSED
backend\tests\test_persistence_and_export.py::TestHistoryAPIEndpoints::test_api_export_csv_and_json PASSED
backend\tests\test_persistence_and_export.py::TestHistoryAPIEndpoints::test_api_export_xlsx PASSED
backend\tests\test_persistence_and_export.py::TestHistoryAPIEndpoints::test_api_retention_endpoint PASSED
backend\tests\test_persistence_and_export.py::TestPersistencePhase12Advanced::test_sqlite_disk_persistence_across_restart PASSED
backend\tests\test_persistence_and_export.py::TestPersistencePhase12Advanced::test_export_runs_to_xlsx_multisheet PASSED
backend\tests\test_persistence_and_export.py::TestPersistencePhase12Advanced::test_export_filtering_by_type_and_date PASSED
backend\tests\test_persistence_and_export.py::TestPersistencePhase12Advanced::test_apply_retention_policy_limits PASSED
```

### Full Test Suite Summary
- **Backend Test Suite:** 228 passed in 56.41s (100% pass rate).
- **Frontend Test Suite:** 4 passed in 0.38s (100% pass rate).
