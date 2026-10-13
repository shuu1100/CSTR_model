"""API endpoints for experimental dataset upload, inspection, column mapping, and analysis."""

from typing import Any
from fastapi import APIRouter, File, HTTPException, UploadFile, status
import numpy as np
import pandas as pd

from backend.app.core.ingestion import (
    MAX_UPLOAD_SIZE_BYTES,
    inspect_dataset,
    parse_dataset_bytes,
    process_mapped_dataset,
)
from backend.app.schemas.ingestion import (
    DatasetInspectionResponse,
    ProcessDatasetRequest,
    ProcessedDatasetResponse,
    ProcessedSeriesSchema,
)

router = APIRouter(prefix="/datasets", tags=["Datasets"])


@router.post(
    "/upload",
    response_model=DatasetInspectionResponse,
    status_code=status.HTTP_200_OK,
    summary="Upload and inspect an experimental CSV or Excel dataset",
)
async def upload_dataset(file: UploadFile = File(...)) -> DatasetInspectionResponse:
    """Read uploaded file, enforce size/dimension security limits, inspect columns, and return metadata."""
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is missing or empty.",
        )

    # Read file content safely
    try:
        content = await file.read()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read uploaded file: {str(exc)}",
        ) from exc

    if len(content) > MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum upload limit of {MAX_UPLOAD_SIZE_BYTES / (1024 * 1024):.1f} MB.",
        )

    try:
        df = parse_dataset_bytes(content, filename=file.filename)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc

    inspection = inspect_dataset(df, filename=file.filename)

    # Convert full records to serializable dicts (replacing NaN with None)
    clean_records = df.replace({np.nan: None}).to_dict(orient="records")

    return DatasetInspectionResponse(
        filename=inspection.filename,
        file_type=inspection.file_type,
        total_rows=inspection.total_rows,
        total_columns=inspection.total_columns,
        columns=inspection.columns,
        column_types=inspection.column_types,
        missing_counts=inspection.missing_counts,
        duplicate_rows_count=inspection.duplicate_rows_count,
        preview_data=inspection.preview_data,
        raw_records=clean_records,
        warnings=inspection.warnings,
    )


@router.post(
    "/process",
    response_model=ProcessedDatasetResponse,
    status_code=status.HTTP_200_OK,
    summary="Process and validate mapped experimental columns",
)
def process_dataset(request: ProcessDatasetRequest) -> ProcessedDatasetResponse:
    """Transform uploaded records into engineering variables, compute conversion, and apply smoothing/anomaly flags."""
    if not request.records:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No dataset records provided in request.",
        )

    df = pd.DataFrame(request.records)

    try:
        result = process_mapped_dataset(
            df=df,
            time_col=request.time_col,
            c_out_col=request.c_out_col,
            c_in_col=request.c_in_col,
            constant_c_in=request.constant_c_in,
            flow_col=request.flow_col,
            constant_flow=request.constant_flow,
            volume_col=request.volume_col,
            constant_volume=request.constant_volume,
            time_unit=request.time_unit,
            conc_unit=request.conc_unit,
            flow_unit=request.flow_unit,
            vol_unit=request.vol_unit,
            apply_smoothing=request.apply_smoothing,
            savgol_window=request.savgol_window,
            savgol_poly=request.savgol_poly,
            apply_anomaly_detection=request.apply_anomaly_detection,
            contamination=request.contamination,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc

    return ProcessedDatasetResponse(
        dataset_summary=result.dataset_summary,
        series=ProcessedSeriesSchema(
            time=result.series.time,
            time_unit=result.series.time_unit,
            C_A_out_raw=result.series.C_A_out_raw,
            C_A_out_smoothed=result.series.C_A_out_smoothed,
            C_A_in=result.series.C_A_in,
            conversion=result.series.conversion,
            anomaly_scores=result.series.anomaly_scores,
            is_anomaly=result.series.is_anomaly,
            tau=result.series.tau,
        ),
        column_mapping=result.column_mapping,
        smoothing_applied=result.smoothing_applied,
        smoothing_settings=result.smoothing_settings,
        anomaly_detection_applied=result.anomaly_detection_applied,
        anomaly_count=result.anomaly_count,
        data_quality_warnings=result.data_quality_warnings,
        provenance_note=result.provenance_note,
    )


@router.get(
    "/sample-dataset",
    response_model=DatasetInspectionResponse,
    summary="Generate a synthetic experimental run for instant UI testing",
)
def get_sample_dataset() -> DatasetInspectionResponse:
    """Generate a realistic noisy dynamic CSTR run with synthetic step change and single outlier spike."""
    np.random.seed(42)
    time = np.linspace(0.0, 50.0, 101)  # 0 to 50 min, dt=0.5 min
    # Flow Q = 1.0 L/min, V = 10.0 L, tau = 10 min
    # Inlet: C_A,in starts at 1.0 mol/L, steps to 2.0 mol/L at t=20 min
    # Exact analytical dynamic response:
    c_in = np.where(time < 20.0, 1.0, 2.0)
    # k = 0.15 min^-1 -> denom = 1 + k*tau = 1 + 1.5 = 2.5
    # C_ss1 = 1.0 / 2.5 = 0.40 mol/L
    # C_ss2 = 2.0 / 2.5 = 0.80 mol/L
    c_out_clean = np.zeros_like(time)
    for i, t in enumerate(time):
        if t < 20.0:
            # from initial C_A(0)=0.1 up to 0.40
            c_out_clean[i] = 0.40 - (0.40 - 0.10) * np.exp(-t * 0.25)
        else:
            # step change relaxation toward 0.80
            c_at_20 = 0.40 - (0.40 - 0.10) * np.exp(-20.0 * 0.25)
            c_out_clean[i] = 0.80 - (0.80 - c_at_20) * np.exp(-(t - 20.0) * 0.25)

    # Add Gaussian noise
    noise = np.random.normal(0.0, 0.015, size=len(time))
    c_out_noisy = np.maximum(0.0, c_out_clean + noise)

    # Add intentional outlier sensor spike at index 65
    c_out_noisy[65] += 0.35

    df = pd.DataFrame(
        {
            "time_min": np.round(time, 2),
            "C_A_inlet_mol_L": np.round(c_in, 2),
            "C_A_outlet_mol_L": np.round(c_out_noisy, 4),
            "flow_rate_L_min": [1.0] * len(time),
            "volume_L": [10.0] * len(time),
        }
    )

    filename = "synthetic_cstr_dynamic_experiment.csv"
    inspection = inspect_dataset(df, filename=filename)
    clean_records = df.to_dict(orient="records")

    return DatasetInspectionResponse(
        filename=filename,
        file_type="csv",
        total_rows=inspection.total_rows,
        total_columns=inspection.total_columns,
        columns=inspection.columns,
        column_types=inspection.column_types,
        missing_counts=inspection.missing_counts,
        duplicate_rows_count=inspection.duplicate_rows_count,
        preview_data=inspection.preview_data,
        raw_records=clean_records,
        warnings=[
            "SYNTHETIC BENCHMARK DATA: Generated purely for demonstration and verification purposes."
        ],
    )
