"""SQLAlchemy 2.0 ORM models for simulation history, training jobs, and dataset tracking.

Adheres strictly to GLOBAL-INSTRUCTIONS.md, phase-12, and phase-08A:
- Explicit schemas, units, provenance, and timestamps.
- JSON-encoded parameters and metric summaries for flexible schema evolution.
- Foreign keys and indexing on run_type and timestamps for fast history filtering.
"""

from datetime import datetime, timezone
import json
from typing import Any, Optional
from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.database import Base


class SimulationRunRecord(Base):
    """Persistent record of a simulation, sweep, estimation, or ML forecast run."""

    __tablename__ = "simulation_runs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, index=True)
    run_type: Mapped[str] = mapped_column(String(64), index=True)  # steady_state, dynamic, sweep, ml_forecast, estimation
    name: Mapped[str] = mapped_column(String(128), default="Simulation Run")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )
    provenance: Mapped[str] = mapped_column(String(64), default="SIMULATED")
    schema_version: Mapped[str] = mapped_column(String(16), default="1.0")
    artifact_ref: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    seed: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    split_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    # JSON-encoded blobs
    parameters_json: Mapped[str] = mapped_column(Text, default="{}")
    results_summary_json: Mapped[str] = mapped_column(Text, default="{}")
    time_series_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[str] = mapped_column(Text, default="{}")

    def get_parameters(self) -> dict[str, Any]:
        return json.loads(self.parameters_json)

    def set_parameters(self, val: dict[str, Any]) -> None:
        self.parameters_json = json.dumps(val)

    def get_results_summary(self) -> dict[str, Any]:
        return json.loads(self.results_summary_json)

    def set_results_summary(self, val: dict[str, Any]) -> None:
        self.results_summary_json = json.dumps(val)

    def get_time_series(self) -> Optional[dict[str, Any]]:
        return json.loads(self.time_series_json) if self.time_series_json else None

    def set_time_series(self, val: Optional[dict[str, Any]]) -> None:
        self.time_series_json = json.dumps(val) if val is not None else None

    def get_metadata(self) -> dict[str, Any]:
        return json.loads(self.metadata_json)

    def set_metadata(self, val: dict[str, Any]) -> None:
        self.metadata_json = json.dumps(val)


class DatasetRecord(Base):
    """Persistent catalog record for uploaded and interim datasets."""

    __tablename__ = "dataset_records"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, index=True)
    filename: Mapped[str] = mapped_column(String(256))
    file_sha256: Mapped[str] = mapped_column(String(64), index=True)
    row_count: Mapped[int] = mapped_column(Integer)
    column_count: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    columns_json: Mapped[str] = mapped_column(Text, default="[]")
    provenance: Mapped[str] = mapped_column(String(64), default="UPLOADED_EXPERIMENTAL")


class TrainingJobRecord(Base):
    """Persistent log of neural model training trials and hyperparameter tuning."""

    __tablename__ = "training_jobs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, index=True)
    model_type: Mapped[str] = mapped_column(String(64), index=True)
    epochs: Mapped[int] = mapped_column(Integer)
    learning_rate: Mapped[float] = mapped_column(Float)
    best_val_loss: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    test_rmse: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    test_r2: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    provenance: Mapped[str] = mapped_column(String(64), default="TRAINED_ML_MODEL")
    artifact_path: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
