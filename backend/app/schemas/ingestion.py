"""Pydantic schemas for experimental dataset ingestion, validation, and processing."""

from typing import Any, Literal, Optional
from pydantic import BaseModel, Field

from backend.app.core.units import ConcentrationUnit, FlowRateUnit, TimeUnit, VolumeUnit


class DatasetInspectionResponse(BaseModel):
    """Schema returned after initial inspection of uploaded CSV/Excel file."""

    filename: str
    file_type: str
    total_rows: int
    total_columns: int
    columns: list[str]
    column_types: dict[str, str]
    missing_counts: dict[str, int]
    duplicate_rows_count: int
    preview_data: list[dict[str, Any]]
    raw_records: list[dict[str, Any]] = Field(
        ...,
        description="Complete list of records parsed from file for client-side state preservation.",
    )
    warnings: list[str] = Field(default_factory=list)


class ProcessDatasetRequest(BaseModel):
    """Configuration for mapping columns, units, and applying smoothing/anomaly detection."""

    records: list[dict[str, Any]] = Field(
        ...,
        description="Dataset rows to process.",
    )
    time_col: str = Field(..., description="Column containing reaction or residence time.")
    c_out_col: str = Field(..., description="Column containing outlet reactant concentration C_A,out.")
    c_in_col: Optional[str] = Field(None, description="Column containing inlet concentration C_A,in.")
    constant_c_in: Optional[float] = Field(
        None, ge=0.0, description="Constant inlet concentration C_A,in if not given in column."
    )
    flow_col: Optional[str] = Field(None, description="Column containing volumetric flow rate Q.")
    constant_flow: Optional[float] = Field(
        None, gt=0.0, description="Constant volumetric flow rate Q if not given in column."
    )
    volume_col: Optional[str] = Field(None, description="Column containing reactor volume V.")
    constant_volume: Optional[float] = Field(
        None, gt=0.0, description="Constant reactor volume V if not given in column."
    )

    time_unit: TimeUnit = Field("min", description="Unit of time column.")
    conc_unit: ConcentrationUnit = Field("mol/L", description="Unit of concentration columns.")
    flow_unit: FlowRateUnit = Field("L/min", description="Unit of flow rate column.")
    vol_unit: VolumeUnit = Field("L", description="Unit of volume column.")

    apply_smoothing: bool = Field(False, description="Whether to apply Savitzky-Golay filter to C_A,out.")
    savgol_window: int = Field(5, ge=3, description="Savitzky-Golay window length (must be odd).")
    savgol_poly: int = Field(2, ge=1, description="Savitzky-Golay polynomial order (must be < window).")

    apply_anomaly_detection: bool = Field(False, description="Whether to run Isolation Forest anomaly detection.")
    contamination: float = Field(0.05, ge=0.01, le=0.25, description="Expected proportion of outliers.")


class ProcessedSeriesSchema(BaseModel):
    """Processed physical time-series."""

    time: list[float]
    time_unit: str = "min"
    C_A_out_raw: list[float]
    C_A_out_smoothed: Optional[list[float]] = None
    C_A_in: list[float]
    conversion: Optional[list[Optional[float]]] = None
    anomaly_scores: Optional[list[float]] = None
    is_anomaly: Optional[list[bool]] = None
    tau: Optional[list[float]] = None


class ProcessedDatasetResponse(BaseModel):
    """Response containing processed dataset, series, mappings, and warnings."""

    dataset_summary: dict[str, Any]
    series: ProcessedSeriesSchema
    column_mapping: dict[str, Optional[str]]
    smoothing_applied: bool
    smoothing_settings: Optional[dict[str, Any]] = None
    anomaly_detection_applied: bool
    anomaly_count: int = 0
    data_quality_warnings: list[str] = Field(default_factory=list)
    provenance_note: str = (
        "USER-PROVIDED DATA: This dataset was uploaded by the user. "
        "Its authenticity, experimental accuracy, and provenance are unverified."
    )
