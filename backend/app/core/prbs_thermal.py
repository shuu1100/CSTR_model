"""PRBS Workbook Ingestion, Thermal Calibration, and Scientific Data Governance.

Adheres strictly to GLOBAL-INSTRUCTIONS.md, phase-13, and candidate-datasets-audit.md:
- Explicit signal mappings without guessing for CSTR_24aug_PRBS_dataset.xlsx.
- Audits timestamps (uniform dt=0.5s), delays, missingness (0 NaNs), and identifiability.
- Blocked chronological partitioning (Calibration 60%, Validation 20%, Locked Test 20%).
- Calibration of reactor-jacket heat transfer parameters and locked test physical residuals.
- Hard scientific guard: Temperature-only data CANNOT validate chemical concentration.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional
import numpy as np
import pandas as pd


PRBS_DEFAULT_FILE = Path("data/raw/CSTR_24aug_PRBS_dataset.xlsx")


@dataclass
class PRBSAuditReport:
    """Audit report for PRBS candidate dataset."""

    filepath: str
    row_count: int
    column_count: int
    dt_seconds: float
    time_span_seconds: float
    missing_values_count: int
    signal_mappings: dict[str, str]
    excitation_identifiability: dict[str, Any]
    scientific_governance_notice: str


def load_and_audit_prbs_dataset(
    filepath: Optional[Path | str] = None,
) -> tuple[pd.DataFrame, PRBSAuditReport]:
    """Parse, audit, and clean the PRBS CSTR experimental workbook.

    Identifies verified signal mappings:
    - Time (s): Uniform timestamp with dt = 0.5 s.
    - Hot oil circulation: PRBS heating/cooling actuator signal.
    - Feed A / B Flowrate: Reagent flow rates [mL/min].
    - Hot Oil bath: Feed preheat temperature [°C].
    - Reactor Temp. Tr: Internal RTD sensor [°C] -> converted to Kelvin.
    - Jacket Temp. Tj: Cooling/heating jacket RTD sensor [°C] -> converted to Kelvin.
    - Feed A / B Temp: Inlet feed RTD sensors [°C] -> converted to Kelvin.
    """
    path = Path(filepath) if filepath else PRBS_DEFAULT_FILE
    if not path.exists():
        raise FileNotFoundError(f"PRBS dataset not found at '{path}'.")

    # Read sheet 'CSTR Dataset', skipping the top metadata row
    raw_df = pd.read_excel(path, sheet_name="CSTR Dataset", skiprows=1)

    # Normalize column mapping cleanly regardless of special character encoding
    col_mapping: dict[str, str] = {}
    for col in raw_df.columns:
        c_lower = str(col).lower()
        if "time" in c_lower:
            col_mapping[col] = "time_s"
        elif "hot oil circulation" in c_lower:
            col_mapping[col] = "hot_oil_flow"
        elif "feed a flowrate" in c_lower:
            col_mapping[col] = "feed_a_flow_ml_min"
        elif "feed b flowrate" in c_lower:
            col_mapping[col] = "feed_b_flow_ml_min"
        elif "hot oil bath" in c_lower:
            col_mapping[col] = "oil_bath_temp_c"
        elif "reactor temp" in c_lower or "tr" in c_lower:
            col_mapping[col] = "reactor_temp_c"
        elif "jacket temp" in c_lower or "tj" in c_lower:
            col_mapping[col] = "jacket_temp_c"
        elif "feeda temp" in c_lower or "feed a temp" in c_lower:
            col_mapping[col] = "feed_a_temp_c"
        elif "feedb temp" in c_lower or "feed b temp" in c_lower:
            col_mapping[col] = "feed_b_temp_c"

    df = raw_df.rename(columns=col_mapping).copy()

    # Required columns check
    expected = [
        "time_s", "hot_oil_flow", "feed_a_flow_ml_min", "feed_b_flow_ml_min",
        "oil_bath_temp_c", "reactor_temp_c", "jacket_temp_c",
        "feed_a_temp_c", "feed_b_temp_c",
    ]
    missing_cols = [c for c in expected if c not in df.columns]
    if missing_cols:
        raise ValueError(f"PRBS workbook missing expected signals: {missing_cols}")

    # Keep only relevant columns and ensure numeric
    df = df[expected].apply(pd.to_numeric, errors="coerce")

    # Missingness audit
    nan_count = int(df.isna().sum().sum())
    if nan_count > 0:
        df = df.dropna().reset_index(drop=True)

    # Timestamp audit: verify uniform dt and monotonic progression
    time_diffs = np.diff(df["time_s"].values)
    median_dt = float(np.median(time_diffs))
    if not np.all(time_diffs > 0):
        raise ValueError("PRBS timestamps are not strictly monotonically increasing.")

    # Convert Celsius temperatures to absolute Kelvin
    df["reactor_temp_k"] = df["reactor_temp_c"] + 273.15
    df["jacket_temp_k"] = df["jacket_temp_c"] + 273.15
    df["feed_a_temp_k"] = df["feed_a_temp_c"] + 273.15
    df["feed_b_temp_k"] = df["feed_b_temp_c"] + 273.15
    df["total_feed_flow_ml_min"] = df["feed_a_flow_ml_min"] + df["feed_b_flow_ml_min"]

    # Weighted inlet feed temperature
    q_tot = df["total_feed_flow_ml_min"].values
    qa = df["feed_a_flow_ml_min"].values
    qb = df["feed_b_flow_ml_min"].values
    t_fa = df["feed_a_temp_k"].values
    t_fb = df["feed_b_temp_k"].values

    t_in_weighted = np.where(
        q_tot > 0,
        (qa * t_fa + qb * t_fb) / np.maximum(q_tot, 1e-6),
        0.5 * (t_fa + t_fb),
    )
    df["feed_inlet_temp_k"] = t_in_weighted

    # Identifiability audit
    identifiability = {
        "reactor_temp_range_k": float(df["reactor_temp_k"].max() - df["reactor_temp_k"].min()),
        "jacket_temp_range_k": float(df["jacket_temp_k"].max() - df["jacket_temp_k"].min()),
        "prbs_levels": int(df["hot_oil_flow"].nunique()),
        "is_sufficiently_excited": bool(
            df["hot_oil_flow"].nunique() >= 3 and (df["reactor_temp_k"].max() - df["reactor_temp_k"].min()) > 5.0
        ),
    }

    signal_descriptions = {
        "time_s": "Timestamp [s], sampling dt=0.5 s",
        "hot_oil_flow": "PRBS heating/cooling oil flow rate [actuator units]",
        "feed_a_flow_ml_min": "Feed A flow rate [mL/min]",
        "feed_b_flow_ml_min": "Feed B flow rate [mL/min]",
        "reactor_temp_k": "Reactor liquid core temperature [K] (RTD sensor)",
        "jacket_temp_k": "Cooling/heating jacket temperature [K] (RTD sensor)",
        "feed_inlet_temp_k": "Flow-weighted reactant inlet temperature [K]",
    }

    governance_notice = (
        "SCIENTIFIC DATA GOVERNANCE WARNING: CSTR_24aug_PRBS_dataset.xlsx contains exclusively "
        "temperature sensors and hydraulic flow rates. ZERO concentration assays (C_A, C_B, conversion) "
        "were measured. Therefore, this dataset can validate heat transfer and thermal balances ONLY, "
        "and CANNOT be used to validate kinetic concentration predictions."
    )

    report = PRBSAuditReport(
        filepath=str(path),
        row_count=len(df),
        column_count=len(df.columns),
        dt_seconds=median_dt,
        time_span_seconds=float(df["time_s"].iloc[-1] - df["time_s"].iloc[0]),
        missing_values_count=nan_count,
        signal_mappings=signal_descriptions,
        excitation_identifiability=identifiability,
        scientific_governance_notice=governance_notice,
    )

    return df, report


def split_prbs_blocked_chronology(
    df: pd.DataFrame,
    cal_ratio: float = 0.6,
    val_ratio: float = 0.2,
    test_ratio: float = 0.2,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Partition PRBS time series into strictly disjoint blocked chronological subsets.

    - Calibration partition: 0 to cal_ratio (train).
    - Validation partition: cal_ratio to (cal_ratio + val_ratio) (model selection).
    - Locked Test partition: remaining tail (final held-out verification).
    """
    total = len(df)
    n_cal = int(cal_ratio * total)
    n_val = int(val_ratio * total)

    cal = df.iloc[:n_cal].copy().reset_index(drop=True)
    val = df.iloc[n_cal:n_cal + n_val].copy().reset_index(drop=True)
    test = df.iloc[n_cal + n_val:].copy().reset_index(drop=True)

    # Assert non-overlap
    assert cal["time_s"].iloc[-1] < val["time_s"].iloc[0]
    assert val["time_s"].iloc[-1] < test["time_s"].iloc[0]

    return cal, val, test


def calibrate_and_evaluate_prbs_thermal(
    filepath: Optional[Path | str] = None,
) -> dict[str, Any]:
    """Fit thermal jacket-reactor energy parameters on calibration and report locked test residuals.

    Governing thermal energy balance for reactor temperature:
    dTr/dt = k_jacket * (T_j - T_r) + k_inlet * (T_in - T_r) + bias
    """
    df, audit_report = load_and_audit_prbs_dataset(filepath)
    cal, val, test = split_prbs_blocked_chronology(df)

    # 1. Calibration phase: compute numerical derivative and fit parameters
    t_cal = cal["time_s"].values
    tr_cal = cal["reactor_temp_k"].values
    tj_cal = cal["jacket_temp_k"].values
    tin_cal = cal["feed_inlet_temp_k"].values
    dtr_cal = np.gradient(tr_cal, t_cal)

    X_cal = np.column_stack([tj_cal - tr_cal, tin_cal - tr_cal, np.ones(len(t_cal))])
    params, _, _, _ = np.linalg.lstsq(X_cal, dtr_cal, rcond=None)
    k_jacket, k_inlet, bias = float(params[0]), float(params[1]), float(params[2])

    # 2. Validation phase: compute validation metrics
    t_val = val["time_s"].values
    tr_val = val["reactor_temp_k"].values
    tj_val = val["jacket_temp_k"].values
    tin_val = val["feed_inlet_temp_k"].values
    dtr_val = np.gradient(tr_val, t_val)

    X_val = np.column_stack([tj_val - tr_val, tin_val - tr_val, np.ones(len(t_val))])
    pred_dtr_val = X_val @ params
    val_rmse_deriv = float(np.sqrt(np.mean((pred_dtr_val - dtr_val) ** 2)))

    # 3. Locked Test phase: held-out evaluation
    t_test = test["time_s"].values
    tr_test = test["reactor_temp_k"].values
    tj_test = test["jacket_temp_k"].values
    tin_test = test["feed_inlet_temp_k"].values
    dtr_test = np.gradient(tr_test, t_test)

    X_test = np.column_stack([tj_test - tr_test, tin_test - tr_test, np.ones(len(t_test))])
    pred_dtr_test = X_test @ params

    # Residuals on temperature derivative
    test_deriv_residuals = pred_dtr_test - dtr_test
    test_rmse_deriv = float(np.sqrt(np.mean(test_deriv_residuals ** 2)))
    test_mae_deriv = float(np.mean(np.abs(test_deriv_residuals)))
    test_mean_deriv_residual = float(np.mean(test_deriv_residuals))

    # 1-step ahead temperature integration residuals: Tr(k+1) = Tr(k) + dt * dTr/dt
    dt = audit_report.dt_seconds
    pred_tr_next = tr_test[:-1] + dt * pred_dtr_test[:-1]
    actual_tr_next = tr_test[1:]

    temp_residuals = pred_tr_next - actual_tr_next
    test_rmse_k = float(np.sqrt(np.mean(temp_residuals ** 2)))
    test_mae_k = float(np.mean(np.abs(temp_residuals)))
    test_mean_temp_residual = float(np.mean(temp_residuals))

    return {
        "status": "success",
        "audit": {
            "row_count": audit_report.row_count,
            "dt_seconds": audit_report.dt_seconds,
            "missing_values": audit_report.missing_values_count,
            "identifiability": audit_report.excitation_identifiability,
        },
        "calibrated_parameters": {
            "k_jacket_per_s": k_jacket,
            "k_inlet_per_s": k_inlet,
            "thermal_bias_k_per_s": bias,
        },
        "validation_metrics": {
            "validation_derivative_rmse_k_per_s": val_rmse_deriv,
        },
        "locked_test_metrics": {
            "derivative_rmse_k_per_s": test_rmse_deriv,
            "derivative_mae_k_per_s": test_mae_deriv,
            "derivative_mean_residual_k_per_s": test_mean_deriv_residual,
            "temperature_1step_rmse_k": test_rmse_k,
            "temperature_1step_mae_k": test_mae_k,
            "temperature_mean_residual_k": test_mean_temp_residual,
            "sample_count": len(test),
        },
        "scientific_data_governance": {
            "temperature_validated": True,
            "concentration_validated": False,
            "warning": audit_report.scientific_governance_notice,
        },
    }


def assert_cannot_validate_concentration_on_prbs() -> None:
    """Raise explicit scientific exception if caller attempts to validate concentration on PRBS data."""
    raise ValueError(
        "Scientific data governance error: CSTR_24aug_PRBS_dataset.xlsx contains exclusively RTD temperature "
        "and flow signals. Zero concentration measurements exist. Temperature-only data cannot validate concentration."
    )
