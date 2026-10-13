"""FastAPI REST routes for simulation persistence, run comparison, and data exports.

Adheres strictly to GLOBAL-INSTRUCTIONS.md, phase-12, and phase-08A:
- Persistent history retrieval and run comparisons.
- Standardized CSV and JSON exports with units, timestamps, and provenance.
- Clean error responses and route validation.
"""

from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.app.db.database import get_db, init_db
from backend.app.db.service import (
    compare_runs,
    delete_simulation_run,
    export_runs_to_csv,
    export_runs_to_json,
    get_simulation_run,
    list_simulation_runs,
    record_simulation_run,
)

# Ensure database tables exist
init_db()

router = APIRouter(prefix="/history", tags=["History & Persistence"])


class SaveRunRequest(BaseModel):
    """Payload for manually archiving a simulation or fit result."""

    run_type: str = Field(description="Run category: 'steady_state', 'dynamic', 'sweep', 'ml_forecast'")
    name: Optional[str] = Field(default=None, description="Human-readable run name")
    parameters: dict[str, Any] = Field(description="Operating parameters")
    results_summary: dict[str, Any] = Field(description="Summary metrics or steady-state outputs")
    time_series: Optional[dict[str, Any]] = Field(default=None, description="Time series coordinates")
    provenance: str = Field(default="SIMULATED", description="Data provenance label")
    metadata: Optional[dict[str, Any]] = Field(default=None, description="Additional context")


class CompareRunsRequest(BaseModel):
    """Payload specifying runs to compare side-by-side."""

    run_ids: list[str] = Field(min_length=2, description="List of at least two run IDs to compare")


@router.get("/runs")
def get_runs(
    run_type: Optional[str] = Query(None, description="Filter by run category"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    """Retrieve historical simulation runs sorted by most recent."""
    runs = list_simulation_runs(db, run_type=run_type, limit=limit, offset=offset)
    return [
        {
            "id": r.id,
            "name": r.name,
            "run_type": r.run_type,
            "created_at": r.created_at.isoformat(),
            "provenance": r.provenance,
            "parameters": r.get_parameters(),
            "results_summary": r.get_results_summary(),
        }
        for r in runs
    ]


@router.post("/runs", status_code=status.HTTP_201_CREATED)
def create_run(
    req: SaveRunRequest,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Persist a new simulation run to the SQLite database."""
    record = record_simulation_run(
        db=db,
        run_type=req.run_type,
        name=req.name,
        parameters=req.parameters,
        results_summary=req.results_summary,
        time_series=req.time_series,
        provenance=req.provenance,
        metadata=req.metadata,
    )
    return {
        "id": record.id,
        "name": record.name,
        "run_type": record.run_type,
        "created_at": record.created_at.isoformat(),
        "provenance": record.provenance,
    }


@router.get("/runs/{run_id}")
def get_run(
    run_id: str,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Retrieve full details of a specific historical simulation run."""
    record = get_simulation_run(db, run_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run '{run_id}' not found.",
        )
    return {
        "id": record.id,
        "name": record.name,
        "run_type": record.run_type,
        "created_at": record.created_at.isoformat(),
        "provenance": record.provenance,
        "parameters": record.get_parameters(),
        "results_summary": record.get_results_summary(),
        "time_series": record.get_time_series(),
        "metadata": record.get_metadata(),
    }


@router.delete("/runs/{run_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_run(
    run_id: str,
    db: Session = Depends(get_db),
) -> None:
    """Delete a simulation run from the database."""
    deleted = delete_simulation_run(db, run_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run '{run_id}' not found.",
        )


@router.post("/compare")
def compare_history_runs(
    req: CompareRunsRequest,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Compare multiple historical simulation runs side-by-side."""
    try:
        return compare_runs(db, req.run_ids)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/export")
def export_history(
    format: str = Query("json", pattern="^(json|csv)$", description="Export format: 'json' or 'csv'"),
    run_ids: Optional[list[str]] = Query(None, description="Optional specific run IDs to export"),
    db: Session = Depends(get_db),
) -> Response:
    """Export historical simulation runs in CSV or JSON format."""
    if format == "csv":
        content = export_runs_to_csv(db, run_ids)
        return Response(
            content=content,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=cstr_simulation_history.csv"},
        )
    else:
        content = export_runs_to_json(db, run_ids)
        return Response(
            content=content,
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=cstr_simulation_history.json"},
        )
