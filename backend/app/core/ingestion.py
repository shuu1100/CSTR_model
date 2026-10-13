"""Data ingestion, validation, column mapping, smoothing, and anomaly detection for experimental datasets."""

from dataclasses import dataclass, field
import io
import math
from typing import Any, Literal, Optional
import numpy as np
import pandas as pd
from scipy.signal import savgol_filter
from sklearn.ensemble import IsolationForest

from backend.app.core.units import (
    ConcentrationUnit,
    FlowRateUnit,
    TimeUnit,
    VolumeUnit,
    convert_concentration,
    convert_flow_rate,
    convert_time,
    convert_volume,
)

MAX_UPLOAD_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB
MAX_UPLOAD_ROWS = 50_000
MAX_UPLOAD_COLS = 50


@dataclass
class DatasetInspection:
    """Inspection and metadata of an uploaded experimental dataset."""

    filename: str
    file_type: str
    total_rows: int
    total_columns: int
    columns: list[str]
    column_types: dict[str, str]
    missing_counts: dict[str, int]
    duplicate_rows_count: int
    preview_data: list[dict[str, Any]]
    warnings: list[str] = field(default_factory=list)


@dataclass
class ProcessedSeries:
    """Individual processed physical time-series."""

    time: list[float]
    time_unit: str
    C_A_out_raw: list[float]
    C_A_out_smoothed: Optional[list[float]] = None
    C_A_in: list[float] = field(default_factory=list)
    conversion: Optional[list[Optional[float]]] = None
    anomaly_scores: Optional[list[float]] = None
    is_anomaly: Optional[list[bool]] = None
    tau: Optional[list[float]] = None


@dataclass
class ProcessedDatasetResult:
    """Complete analyzed experimental dataset result."""

    dataset_summary: dict[str, Any]
    series: ProcessedSeries
    column_mapping: dict[str, Optional[str]]
    smoothing_applied: bool
    smoothing_settings: Optional[dict[str, Any]]
    anomaly_detection_applied: bool
    anomaly_count: int
    data_quality_warnings: list[str]
    provenance_note: str = (
        "USER-PROVIDED DATA: This dataset was uploaded by the user. "
        "Its authenticity, experimental accuracy, and provenance are unverified."
    )


def parse_dataset_bytes(
    file_bytes: bytes,
    filename: str,
    max_size: int = MAX_UPLOAD_SIZE_BYTES,
    max_rows: int = MAX_UPLOAD_ROWS,
    max_cols: int = MAX_UPLOAD_COLS,
) -> pd.DataFrame:
    """Safely validate and parse uploaded CSV or Excel bytes into a Pandas DataFrame."""
    if len(file_bytes) == 0:
        raise ValueError("Uploaded file is empty (0 bytes).")
    if len(file_bytes) > max_size:
        raise ValueError(
            f"File size ({len(file_bytes) / 1024 / 1024:.2f} MB) exceeds maximum allowed limit of {max_size / 1024 / 1024:.1f} MB."
        )

    fn_lower = filename.lower()
    if fn_lower.endswith(".csv") or fn_lower.endswith(".txt") or fn_lower.endswith(".tsv"):
        sep = "\t" if fn_lower.endswith(".tsv") else ","
        try:
            df = pd.read_csv(io.BytesIO(file_bytes), sep=sep, encoding="utf-8")
        except UnicodeDecodeError:
            df = pd.read_csv(io.BytesIO(file_bytes), sep=sep, encoding="latin1")
        except Exception as exc:
            raise ValueError(f"Failed to parse CSV file: {str(exc)}") from exc
    elif fn_lower.endswith(".xlsx") or fn_lower.endswith(".xls"):
        try:
            df = pd.read_excel(io.BytesIO(file_bytes), engine="openpyxl")
        except Exception as exc:
            raise ValueError(f"Failed to parse Excel file: {str(exc)}") from exc
    else:
        raise ValueError(
            f"Unsupported file format '{filename}'. Allowed formats are .csv, .tsv, .xlsx, .xls."
        )

    if df.shape[1] == 0:
        raise ValueError("Dataset contains no columns.")
    if df.shape[0] == 0:
        raise ValueError("Dataset contains no rows of data.")

    if df.shape[1] > max_cols:
        raise ValueError(
            f"Dataset column count ({df.shape[1]}) exceeds maximum allowed limit of {max_cols} columns."
        )
    if df.shape[0] > max_rows:
        raise ValueError(
            f"Dataset row count ({df.shape[0]}) exceeds maximum allowed limit of {max_rows} rows."
        )

    return df


def inspect_dataset(df: pd.DataFrame, filename: str) -> DatasetInspection:
    """Extract metadata, column types, missing value tallies, duplicate counts, and preview."""
    total_rows, total_cols = df.shape
    cols = [str(c) for c in df.columns]

    col_types = {str(c): str(df[c].dtype) for c in df.columns}
    missing_counts = {str(c): int(df[c].isna().sum()) for c in df.columns}
    dup_rows = int(df.duplicated().sum())

    preview_df = df.head(10).replace({np.nan: None})
    preview_data = preview_df.to_dict(orient="records")

    warnings = []
    total_missing = sum(missing_counts.values())
    if total_missing > 0:
        warnings.append(f"Dataset contains {total_missing} missing (NaN/null) values across columns.")
    if dup_rows > 0:
        warnings.append(f"Dataset contains {dup_rows} duplicate rows.")

    ext = filename.split(".")[-1].lower() if "." in filename else "unknown"

    return DatasetInspection(
        filename=filename,
        file_type=ext,
        total_rows=total_rows,
        total_columns=total_cols,
        columns=cols,
        column_types=col_types,
        missing_counts=missing_counts,
        duplicate_rows_count=dup_rows,
        preview_data=preview_data,
        warnings=warnings,
    )


def process_mapped_dataset(
    df: pd.DataFrame,
    time_col: str,
    c_out_col: str,
    c_in_col: Optional[str] = None,
    constant_c_in: Optional[float] = None,
    flow_col: Optional[str] = None,
    constant_flow: Optional[float] = None,
    volume_col: Optional[str] = None,
    constant_volume: Optional[float] = None,
    time_unit: TimeUnit = "min",
    conc_unit: ConcentrationUnit = "mol/L",
    flow_unit: FlowRateUnit = "L/min",
    vol_unit: VolumeUnit = "L",
    apply_smoothing: bool = False,
    savgol_window: int = 5,
    savgol_poly: int = 2,
    apply_anomaly_detection: bool = False,
    contamination: float = 0.05,
) -> ProcessedDatasetResult:
    """Map columns, validate values, calculate conversion, apply optional smoothing/anomaly flags."""
    warnings: list[str] = []

    # Validate mandatory columns exist
    if time_col not in df.columns:
        raise ValueError(f"Time column '{time_col}' was not found in dataset columns: {list(df.columns)}")
    if c_out_col not in df.columns:
        raise ValueError(f"Outlet concentration column '{c_out_col}' was not found in dataset.")

    # Extract time series and enforce numeric coercion
    t_raw = pd.to_numeric(df[time_col], errors="coerce")
    c_out_raw = pd.to_numeric(df[c_out_col], errors="coerce")

    # Inlet concentration
    if c_in_col is not None and c_in_col in df.columns:
        c_in_raw = pd.to_numeric(df[c_in_col], errors="coerce")
    elif constant_c_in is not None:
        c_in_raw = pd.Series([constant_c_in] * len(df))
    else:
        c_in_raw = pd.Series([float("nan")] * len(df))

    # Flow rate & Volume (for residence time tau)
    if flow_col is not None and flow_col in df.columns:
        q_raw = pd.to_numeric(df[flow_col], errors="coerce")
    elif constant_flow is not None:
        q_raw = pd.Series([constant_flow] * len(df))
    else:
        q_raw = None

    if volume_col is not None and volume_col in df.columns:
        v_raw = pd.to_numeric(df[volume_col], errors="coerce")
    elif constant_volume is not None:
        v_raw = pd.Series([constant_volume] * len(df))
    else:
        v_raw = None

    # Check for NaNs in critical columns
    nan_t = int(t_raw.isna().sum())
    nan_c = int(c_out_raw.isna().sum())
    if nan_t > 0:
        warnings.append(f"Time column contains {nan_t} non-numeric/missing rows.")
    if nan_c > 0:
        warnings.append(f"Outlet concentration column contains {nan_c} non-numeric/missing rows.")

    # Fill NaNs using linear interpolation or forward fill to avoid dropping rows
    t_clean = t_raw.interpolate(method="linear").bfill().ffill()
    c_out_clean = c_out_raw.interpolate(method="linear").bfill().ffill()
    c_in_clean = c_in_raw.interpolate(method="linear").bfill().ffill()

    # Convert to canonical units (min, mol/L, L, L/min)
    t_canon = np.array([convert_time(val, time_unit) for val in t_clean], dtype=np.float64)
    c_out_canon = np.array([convert_concentration(val, conc_unit) for val in c_out_clean], dtype=np.float64)
    c_in_canon = np.array([convert_concentration(val, conc_unit) if not np.isnan(val) else float("nan") for val in c_in_clean], dtype=np.float64)

    # Sort chronologically if time is not monotonic
    if not np.all(np.diff(t_canon) >= 0):
        warnings.append("Time vector is not monotonically increasing. Sorted data chronologically by time.")
        sort_idx = np.argsort(t_canon)
        t_canon = t_canon[sort_idx]
        c_out_canon = c_out_canon[sort_idx]
        c_in_canon = c_in_canon[sort_idx]

    # Calculate conversion: X_A = (C_in - C_out) / C_in (only if C_in > 0)
    conversions: list[Optional[float]] = []
    out_of_bounds_conv_count = 0
    for cin, cout in zip(c_in_canon, c_out_canon):
        if not np.isnan(cin) and cin > 0.0:
            x_val = (cin - cout) / cin
            if x_val < 0.0 or x_val > 1.0:
                out_of_bounds_conv_count += 1
            conversions.append(float(x_val))
        else:
            conversions.append(None)

    if out_of_bounds_conv_count > 0:
        warnings.append(
            f"{out_of_bounds_conv_count} conversion values lie outside physical range [0, 1]. "
            "Flagged as warnings; raw data retained without deletion."
        )

    # Calculate optional tau
    tau_list: Optional[list[float]] = None
    if q_raw is not None and v_raw is not None:
        q_canon = np.array([convert_flow_rate(val, flow_unit) for val in q_raw], dtype=np.float64)
        v_canon = np.array([convert_volume(val, vol_unit) for val in v_raw], dtype=np.float64)
        with np.errstate(divide="ignore", invalid="ignore"):
            tau_vals = np.where(q_canon > 0, v_canon / q_canon, np.nan)
        tau_list = [float(x) if not np.isnan(x) else 0.0 for x in tau_vals]

    # Optional Savitzky-Golay Smoothing
    c_out_smoothed: Optional[list[float]] = None
    smoothing_settings: Optional[dict[str, Any]] = None
    if apply_smoothing:
        n_pts = len(c_out_canon)
        if savgol_window % 2 == 0:
            raise ValueError(f"Savitzky-Golay window_length must be an odd integer, got {savgol_window}.")
        if savgol_window >= n_pts:
            raise ValueError(
                f"Savitzky-Golay window_length ({savgol_window}) must be strictly less than dataset size ({n_pts})."
            )
        if savgol_poly >= savgol_window:
            raise ValueError(
                f"Savitzky-Golay polyorder ({savgol_poly}) must be strictly less than window_length ({savgol_window})."
            )

        smoothed_arr = savgol_filter(c_out_canon, window_length=savgol_window, polyorder=savgol_poly)
        # Never let smoothing produce negative concentration
        smoothed_arr = np.maximum(0.0, smoothed_arr)
        c_out_smoothed = [float(x) for x in smoothed_arr]
        smoothing_settings = {
            "window_length": savgol_window,
            "polyorder": savgol_poly,
            "caution": "Savitzky-Golay filtering smooths high-frequency noise but can attenuate steep dynamic step changes.",
        }

    # Optional Isolation Forest Anomaly Detection
    anomaly_scores: Optional[list[float]] = None
    is_anomaly: Optional[list[bool]] = None
    anomaly_count = 0
    if apply_anomaly_detection:
        features = np.column_stack([t_canon, c_out_canon])
        iso_forest = IsolationForest(
            contamination=max(0.01, min(0.25, contamination)),
            random_state=42,
        )
        preds = iso_forest.fit_predict(features)  # -1 for anomaly, 1 for inlier
        scores = iso_forest.decision_function(features)

        anomaly_scores = [float(s) for s in scores]
        is_anomaly = [bool(p == -1) for p in preds]
        anomaly_count = sum(is_anomaly)
        if anomaly_count > 0:
            warnings.append(
                f"Isolation Forest flagged {anomaly_count} potential anomalies. Points are highlighted but NOT automatically removed."
            )

    series = ProcessedSeries(
        time=[float(x) for x in t_canon],
        time_unit="min",
        C_A_out_raw=[float(x) for x in c_out_canon],
        C_A_out_smoothed=c_out_smoothed,
        C_A_in=[float(x) if not np.isnan(x) else 0.0 for x in c_in_canon],
        conversion=conversions,
        anomaly_scores=anomaly_scores,
        is_anomaly=is_anomaly,
        tau=tau_list,
    )

    column_mapping = {
        "time": time_col,
        "C_A_out": c_out_col,
        "C_A_in": c_in_col if c_in_col else (f"constant={constant_c_in}" if constant_c_in is not None else None),
        "flow": flow_col if flow_col else (f"constant={constant_flow}" if constant_flow is not None else None),
        "volume": volume_col if volume_col else (f"constant={constant_volume}" if constant_volume is not None else None),
    }

    summary = {
        "row_count": len(t_canon),
        "t_min": float(np.min(t_canon)),
        "t_max": float(np.max(t_canon)),
        "c_out_min": float(np.min(c_out_canon)),
        "c_out_max": float(np.max(c_out_canon)),
    }

    return ProcessedDatasetResult(
        dataset_summary=summary,
        series=series,
        column_mapping=column_mapping,
        smoothing_applied=apply_smoothing,
        smoothing_settings=smoothing_settings,
        anomaly_detection_applied=apply_anomaly_detection,
        anomaly_count=anomaly_count,
        data_quality_warnings=warnings,
    )
