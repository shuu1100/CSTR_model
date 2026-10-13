"""Database CRUD and export services for CSTR simulation history.

Adheres strictly to GLOBAL-INSTRUCTIONS.md, phase-12, and phase-08A:
- Stores simulation, fit, and model metadata with timestamps and provenance.
- Implements side-by-side run comparisons.
- Implements standardized CSV and JSON exports with explicit units and schema versions.
"""

from datetime import datetime, timezone
import io
import json
import uuid
from typing import Any, Optional, Sequence
import pandas as pd
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from backend.app.db.models import SimulationRunRecord


def record_simulation_run(
    db: Session,
    run_type: str,
    parameters: dict[str, Any],
    results_summary: dict[str, Any],
    name: Optional[str] = None,
    time_series: Optional[dict[str, Any]] = None,
    provenance: str = "SIMULATED",
    metadata: Optional[dict[str, Any]] = None,
    schema_version: str = "1.0",
    artifact_ref: Optional[str] = None,
    seed: Optional[int] = None,
    split_id: Optional[str] = None,
) -> SimulationRunRecord:
    """Persist a simulation or analysis run to the SQLite database."""
    run_id = f"run-{uuid.uuid4().hex[:10]}"
    if not name:
        name = f"{run_type.replace('_', ' ').title()} ({datetime.now(timezone.utc).strftime('%H:%M:%S')})"

    record = SimulationRunRecord(
        id=run_id,
        run_type=run_type,
        name=name,
        created_at=datetime.now(timezone.utc),
        provenance=provenance,
        schema_version=schema_version,
        artifact_ref=artifact_ref,
        seed=seed,
        split_id=split_id,
    )
    record.set_parameters(parameters)
    record.set_results_summary(results_summary)
    record.set_time_series(time_series)
    record.set_metadata(metadata or {"version": "0.1.0", "units": "canonical"})

    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def list_simulation_runs(
    db: Session,
    run_type: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> list[SimulationRunRecord]:
    """Retrieve historical simulation runs sorted by most recent."""
    query = select(SimulationRunRecord).order_by(desc(SimulationRunRecord.created_at))
    if run_type:
        query = query.where(SimulationRunRecord.run_type == run_type)
    query = query.offset(offset).limit(limit)
    return list(db.scalars(query).all())


def get_simulation_run(db: Session, run_id: str) -> Optional[SimulationRunRecord]:
    """Retrieve specific simulation run by UUID."""
    return db.scalar(select(SimulationRunRecord).where(SimulationRunRecord.id == run_id))


def delete_simulation_run(db: Session, run_id: str) -> bool:
    """Delete a simulation run from the history database."""
    record = get_simulation_run(db, run_id)
    if not record:
        return False
    db.delete(record)
    db.commit()
    return True


def compare_runs(
    db: Session,
    run_ids: Sequence[str],
) -> dict[str, Any]:
    """Compare multiple historical runs side-by-side."""
    runs = list(db.scalars(select(SimulationRunRecord).where(SimulationRunRecord.id.in_(run_ids))).all())
    if len(runs) < 2:
        raise ValueError("At least 2 valid run IDs are required for side-by-side comparison.")

    comparison_items = []
    for r in runs:
        comparison_items.append({
            "run_id": r.id,
            "name": r.name,
            "run_type": r.run_type,
            "created_at": r.created_at.isoformat(),
            "provenance": r.provenance,
            "schema_version": getattr(r, "schema_version", "1.0"),
            "artifact_ref": getattr(r, "artifact_ref", None),
            "seed": getattr(r, "seed", None),
            "split_id": getattr(r, "split_id", None),
            "parameters": r.get_parameters(),
            "results_summary": r.get_results_summary(),
        })

    return {
        "compared_runs_count": len(comparison_items),
        "runs": comparison_items,
    }


def export_runs_to_json(
    db: Session,
    run_ids: Optional[Sequence[str]] = None,
    run_type: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
) -> str:
    """Export historical simulation runs as standardized JSON with metadata and units."""
    query = select(SimulationRunRecord).order_by(desc(SimulationRunRecord.created_at))
    if run_ids:
        query = query.where(SimulationRunRecord.id.in_(run_ids))
    if run_type:
        query = query.where(SimulationRunRecord.run_type == run_type)
    if date_from:
        query = query.where(SimulationRunRecord.created_at >= date_from)
    if date_to:
        query = query.where(SimulationRunRecord.created_at <= date_to)

    records = list(db.scalars(query).all())
    export_data = {
        "export_timestamp": datetime.now(timezone.utc).isoformat(),
        "schema_version": "1.0",
        "units": {
            "volume": "L",
            "flow_rate": "L/min",
            "rate_constant": "min^-1",
            "concentration": "mol/L",
            "time": "min",
        },
        "total_runs": len(records),
        "runs": [
            {
                "id": r.id,
                "run_type": r.run_type,
                "name": r.name,
                "created_at": r.created_at.isoformat(),
                "provenance": r.provenance,
                "schema_version": getattr(r, "schema_version", "1.0"),
                "artifact_ref": getattr(r, "artifact_ref", None),
                "seed": getattr(r, "seed", None),
                "split_id": getattr(r, "split_id", None),
                "parameters": r.get_parameters(),
                "results_summary": r.get_results_summary(),
                "time_series": r.get_time_series(),
                "metadata": r.get_metadata(),
            }
            for r in records
        ],
    }
    return json.dumps(export_data, indent=2)


def export_runs_to_csv(
    db: Session,
    run_ids: Optional[Sequence[str]] = None,
    run_type: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
) -> str:
    """Export historical simulation runs as tabular CSV."""
    query = select(SimulationRunRecord).order_by(desc(SimulationRunRecord.created_at))
    if run_ids:
        query = query.where(SimulationRunRecord.id.in_(run_ids))
    if run_type:
        query = query.where(SimulationRunRecord.run_type == run_type)
    if date_from:
        query = query.where(SimulationRunRecord.created_at >= date_from)
    if date_to:
        query = query.where(SimulationRunRecord.created_at <= date_to)

    records = list(db.scalars(query).all())
    flat_rows = []

    for r in records:
        params = r.get_parameters()
        results = r.get_results_summary()

        row: dict[str, Any] = {
            "run_id": r.id,
            "name": r.name,
            "run_type": r.run_type,
            "created_at": r.created_at.isoformat(),
            "provenance": r.provenance,
            "schema_version": getattr(r, "schema_version", "1.0"),
            "artifact_ref": getattr(r, "artifact_ref", None),
            "seed": getattr(r, "seed", None),
            "split_id": getattr(r, "split_id", None),
        }
        for k, v in params.items():
            if isinstance(v, (int, float, str, bool)):
                row[f"param_{k}"] = v
        for k, v in results.items():
            if isinstance(v, (int, float, str, bool)):
                row[f"result_{k}"] = v

        flat_rows.append(row)

    df = pd.DataFrame(flat_rows)
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    return buf.getvalue()


def export_runs_to_xlsx(
    db: Session,
    run_ids: Optional[Sequence[str]] = None,
    run_type: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
) -> bytes:
    """Export historical simulation runs as multi-sheet XLSX workbook."""
    query = select(SimulationRunRecord).order_by(desc(SimulationRunRecord.created_at))
    if run_ids:
        query = query.where(SimulationRunRecord.id.in_(run_ids))
    if run_type:
        query = query.where(SimulationRunRecord.run_type == run_type)
    if date_from:
        query = query.where(SimulationRunRecord.created_at >= date_from)
    if date_to:
        query = query.where(SimulationRunRecord.created_at <= date_to)

    records = list(db.scalars(query).all())

    overview_rows = []
    param_rows = []
    ts_rows = []

    for r in records:
        params = r.get_parameters()
        results = r.get_results_summary()
        ts = r.get_time_series()

        o_row: dict[str, Any] = {
            "Run ID": r.id,
            "Name": r.name,
            "Type": r.run_type,
            "Timestamp (UTC)": r.created_at.isoformat(),
            "Provenance": r.provenance,
            "Schema Version": getattr(r, "schema_version", "1.0"),
            "Artifact Ref": getattr(r, "artifact_ref", None),
            "Seed": getattr(r, "seed", None),
            "Split ID": getattr(r, "split_id", None),
        }
        for k, v in results.items():
            if isinstance(v, (int, float, str, bool)):
                o_row[f"Result {k}"] = v
        overview_rows.append(o_row)

        for pk, pv in params.items():
            param_rows.append({
                "Run ID": r.id,
                "Run Name": r.name,
                "Parameter": pk,
                "Value": str(pv),
            })

        if ts and "t" in ts and "C_A" in ts:
            t_list = ts["t"]
            c_list = ts["C_A"]
            for t_val, c_val in zip(t_list, c_list):
                ts_rows.append({
                    "Run ID": r.id,
                    "Time t [min]": float(t_val),
                    "Concentration C_A [mol/L]": float(c_val),
                })

    df_overview = pd.DataFrame(overview_rows) if overview_rows else pd.DataFrame([{"Notice": "No runs found"}])
    df_params = pd.DataFrame(param_rows) if param_rows else pd.DataFrame([{"Notice": "No parameters"}])
    df_ts = pd.DataFrame(ts_rows) if ts_rows else pd.DataFrame([{"Notice": "No time series"}])

    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df_overview.to_excel(writer, sheet_name="Runs_Overview", index=False)
        df_params.to_excel(writer, sheet_name="Parameters", index=False)
        df_ts.to_excel(writer, sheet_name="Time_Series", index=False)

    return buf.getvalue()


def apply_retention_policy(
    db: Session,
    max_runs: int = 500,
    retention_days: Optional[int] = None,
) -> int:
    """Enforce data retention rules by purging oldest runs beyond limit or age."""
    purged_count = 0
    now = datetime.now(timezone.utc)

    if retention_days is not None and retention_days > 0:
        cutoff = now - pd.Timedelta(days=retention_days)
        old_records = list(db.scalars(
            select(SimulationRunRecord).where(SimulationRunRecord.created_at < cutoff)
        ).all())
        for r in old_records:
            db.delete(r)
            purged_count += 1
        db.commit()

    all_runs = list(db.scalars(select(SimulationRunRecord).order_by(SimulationRunRecord.created_at.desc())).all())
    if len(all_runs) > max_runs:
        to_delete = all_runs[max_runs:]
        for r in to_delete:
            db.delete(r)
            purged_count += 1
        db.commit()

    return purged_count
