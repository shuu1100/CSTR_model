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
) -> str:
    """Export historical simulation runs as standardized JSON."""
    query = select(SimulationRunRecord).order_by(desc(SimulationRunRecord.created_at))
    if run_ids:
        query = query.where(SimulationRunRecord.id.in_(run_ids))

    records = list(db.scalars(query).all())
    export_data = {
        "export_timestamp": datetime.now(timezone.utc).isoformat(),
        "schema_version": "1.0",
        "total_runs": len(records),
        "runs": [
            {
                "id": r.id,
                "run_type": r.run_type,
                "name": r.name,
                "created_at": r.created_at.isoformat(),
                "provenance": r.provenance,
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
) -> str:
    """Export historical simulation runs as tabular CSV."""
    query = select(SimulationRunRecord).order_by(desc(SimulationRunRecord.created_at))
    if run_ids:
        query = query.where(SimulationRunRecord.id.in_(run_ids))

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
        }
        # Flatten parameters with param_ prefix
        for k, v in params.items():
            if isinstance(v, (int, float, str, bool)):
                row[f"param_{k}"] = v
        # Flatten results with result_ prefix
        for k, v in results.items():
            if isinstance(v, (int, float, str, bool)):
                row[f"result_{k}"] = v

        flat_rows.append(row)

    df = pd.DataFrame(flat_rows)
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    return buf.getvalue()
