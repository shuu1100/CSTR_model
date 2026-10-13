"""Parameter sweeps and local sensitivity analysis for CSTR steady-state operation."""

from dataclasses import dataclass, field
from enum import Enum
import math
from typing import Any, Literal, Optional
import numpy as np
from scipy.stats import qmc

from backend.app.core.kinetics import RATE_CONSTANT_CANONICAL_UNITS, KineticModel
from backend.app.core.steady_state import solve_steady_state


class SweepVariable(str, Enum):
    """Supported independent variables for parameter sweeps."""
    VOLUME = "V"
    FLOW_RATE = "Q"
    RATE_CONSTANT = "k"
    INLET_CONCENTRATION = "C_A_in"


SWEEP_VARIABLE_LABELS = {
    SweepVariable.VOLUME: "Reactor Volume (V)",
    SweepVariable.FLOW_RATE: "Volumetric Flow Rate (Q)",
    SweepVariable.RATE_CONSTANT: "Rate Constant (k)",
    SweepVariable.INLET_CONCENTRATION: "Inlet Concentration (C_A,in)",
}


@dataclass(frozen=True)
class SweepPoint1D:
    """Calculated steady-state metrics for a single sweep evaluation point."""

    param_value: float
    tau: float
    C_A_ss: float
    conversion: Optional[float]
    reaction_rate_ss: float
    residual: float
    status: Literal["ok", "failed"] = "ok"
    warning: Optional[str] = None


@dataclass
class Sweep1DResult:
    """Result of a 1-dimensional parameter sweep."""

    variable: str
    variable_label: str
    variable_unit: str
    baseline_param_value: float
    fixed_parameters: dict[str, float]
    order: int
    points: list[SweepPoint1D]
    baseline_metrics: dict[str, Any]
    local_sensitivity: Optional[dict[str, float]]
    trend_summary: str
    units: dict[str, str] = field(default_factory=dict)


@dataclass
class Sweep2DResult:
    """Result of a 2-dimensional parameter sweep for contour / surface mapping."""

    var_x: str
    var_x_label: str
    var_x_unit: str
    x_values: list[float]

    var_y: str
    var_y_label: str
    var_y_unit: str
    y_values: list[float]

    fixed_parameters: dict[str, float]
    order: int

    # 2D matrices: [len(y_values)][len(x_values)]
    conversion_grid: list[list[Optional[float]]]
    concentration_grid: list[list[float]]
    tau_grid: list[list[float]]

    baseline_point: dict[str, float]
    trend_summary: str
    units: dict[str, str] = field(default_factory=dict)


def compute_1d_parameter_sweep(
    variable: SweepVariable,
    min_val: float,
    max_val: float,
    n_points: int,
    baseline_V: float,
    baseline_Q: float,
    baseline_C_in: float,
    baseline_k: float,
    order: int = 1,
) -> Sweep1DResult:
    """Compute steady-state outcomes across a range of an independent parameter."""
    if n_points < 2:
        raise ValueError(f"Number of sweep points must be at least 2, got {n_points}.")
    if n_points > 1000:
        raise ValueError(f"Number of sweep points exceeds maximum limit of 1000, got {n_points}.")
    if min_val >= max_val:
        raise ValueError(f"min_val ({min_val}) must be strictly less than max_val ({max_val}).")

    # Validate bounds
    if variable in (SweepVariable.VOLUME, SweepVariable.FLOW_RATE) and min_val <= 0.0:
        raise ValueError(f"Parameter '{variable.value}' must be strictly positive (> 0). min_val is {min_val}.")
    if min_val < 0.0:
        raise ValueError(f"Parameter '{variable.value}' cannot be negative. min_val is {min_val}.")

    k_unit = RATE_CONSTANT_CANONICAL_UNITS.get(order, "min^-1")
    unit_map = {
        "V": "L",
        "Q": "L/min",
        "C_A_in": "mol/L",
        "k": k_unit,
        "tau": "min",
        "C_A_ss": "mol/L",
        "conversion": "fraction [0, 1]",
        "reaction_rate_ss": "mol/(L*min)",
    }

    grid_values = np.linspace(min_val, max_val, n_points)
    points: list[SweepPoint1D] = []

    # Map baseline parameter value
    baseline_val_map = {
        SweepVariable.VOLUME: baseline_V,
        SweepVariable.FLOW_RATE: baseline_Q,
        SweepVariable.RATE_CONSTANT: baseline_k,
        SweepVariable.INLET_CONCENTRATION: baseline_C_in,
    }
    baseline_param_val = baseline_val_map[variable]

    # Evaluate sweep points
    for val in grid_values:
        curr_V = float(val) if variable == SweepVariable.VOLUME else baseline_V
        curr_Q = float(val) if variable == SweepVariable.FLOW_RATE else baseline_Q
        curr_k = float(val) if variable == SweepVariable.RATE_CONSTANT else baseline_k
        curr_C_in = float(val) if variable == SweepVariable.INLET_CONCENTRATION else baseline_C_in

        try:
            res = solve_steady_state(curr_V, curr_Q, curr_C_in, order, curr_k)
            points.append(
                SweepPoint1D(
                    param_value=float(val),
                    tau=res.tau,
                    C_A_ss=res.C_A_ss,
                    conversion=res.conversion,
                    reaction_rate_ss=res.reaction_rate_ss,
                    residual=res.residual,
                    status="ok",
                )
            )
        except Exception as exc:
            points.append(
                SweepPoint1D(
                    param_value=float(val),
                    tau=0.0,
                    C_A_ss=0.0,
                    conversion=None,
                    reaction_rate_ss=0.0,
                    residual=0.0,
                    status="failed",
                    warning=str(exc),
                )
            )

    # Evaluate baseline point
    baseline_res = solve_steady_state(baseline_V, baseline_Q, baseline_C_in, order, baseline_k)
    baseline_metrics = {
        "tau": baseline_res.tau,
        "C_A_ss": baseline_res.C_A_ss,
        "conversion": baseline_res.conversion,
        "reaction_rate_ss": baseline_res.reaction_rate_ss,
        "residual": baseline_res.residual,
    }

    # Calculate local finite-difference sensitivity at baseline
    local_sens: Optional[dict[str, float]] = None
    if baseline_res.conversion is not None and baseline_param_val > 0.0:
        h = max(1e-5, baseline_param_val * 1e-4)
        val_plus = baseline_param_val + h
        val_minus = max(1e-6, baseline_param_val - h)

        def eval_conv(v_eval: float) -> Optional[float]:
            v_V = v_eval if variable == SweepVariable.VOLUME else baseline_V
            v_Q = v_eval if variable == SweepVariable.FLOW_RATE else baseline_Q
            v_k = v_eval if variable == SweepVariable.RATE_CONSTANT else baseline_k
            v_C = v_eval if variable == SweepVariable.INLET_CONCENTRATION else baseline_C_in
            return solve_steady_state(v_V, v_Q, v_C, order, v_k).conversion

        c_plus = eval_conv(val_plus)
        c_minus = eval_conv(val_minus)

        if c_plus is not None and c_minus is not None:
            dX_dp = (c_plus - c_minus) / (val_plus - val_minus)
            # Normalized elasticity: (dX/X) / (dp/p)
            elasticity = (dX_dp * baseline_param_val / baseline_res.conversion) if baseline_res.conversion > 1e-6 else 0.0
            local_sens = {
                "derivative_dX_dp": float(dX_dp),
                "normalized_elasticity": float(elasticity),
            }

    # Generate trend interpretation summary
    valid_pts = [p for p in points if p.status == "ok"]
    if len(valid_pts) >= 2:
        conv_start = valid_pts[0].conversion
        conv_end = valid_pts[-1].conversion
        if conv_start is not None and conv_end is not None:
            delta_conv = (conv_end - conv_start) * 100.0
            direction = "increases" if delta_conv > 0.0 else "decreases"
            trend_summary = (
                f"As {SWEEP_VARIABLE_LABELS[variable]} increases from {min_val:.2f} to {max_val:.2f} {unit_map[variable.value]}, "
                f"fractional conversion {direction} from {conv_start*100:.1f}% to {conv_end*100:.1f}% "
                f"(Δ = {delta_conv:+.1f}%)."
            )
        else:
            trend_summary = (
                f"Steady-state concentration shifts from {valid_pts[0].C_A_ss:.3f} to {valid_pts[-1].C_A_ss:.3f} mol/L."
            )
    else:
        trend_summary = "Insufficient valid points to compute trend."

    fixed_params = {
        "V": baseline_V,
        "Q": baseline_Q,
        "k": baseline_k,
        "C_A_in": baseline_C_in,
    }
    # Remove the swept variable from fixed
    fixed_params.pop(variable.value, None)

    return Sweep1DResult(
        variable=variable.value,
        variable_label=SWEEP_VARIABLE_LABELS[variable],
        variable_unit=unit_map[variable.value],
        baseline_param_value=baseline_param_val,
        fixed_parameters=fixed_params,
        order=order,
        points=points,
        baseline_metrics=baseline_metrics,
        local_sensitivity=local_sens,
        trend_summary=trend_summary,
        units=unit_map,
    )


def compute_2d_parameter_sweep(
    var_x: SweepVariable,
    x_min: float,
    x_max: float,
    n_x: int,
    var_y: SweepVariable,
    y_min: float,
    y_max: float,
    n_y: int,
    baseline_V: float,
    baseline_Q: float,
    baseline_C_in: float,
    baseline_k: float,
    order: int = 1,
) -> Sweep2DResult:
    """Compute 2D steady-state parameter matrix for heatmap and contour surfaces."""
    if var_x == var_y:
        raise ValueError("var_x and var_y must be different independent variables.")
    if n_x < 2 or n_y < 2:
        raise ValueError("Grid resolution n_x and n_y must each be at least 2.")
    if n_x * n_y > 2500:
        raise ValueError(f"2D grid total points ({n_x * n_y}) exceeds maximum limit of 2500.")
    if x_min >= x_max or y_min >= y_max:
        raise ValueError("Min bound must be strictly less than max bound for each axis.")

    k_unit = RATE_CONSTANT_CANONICAL_UNITS.get(order, "min^-1")
    unit_map = {
        "V": "L",
        "Q": "L/min",
        "C_A_in": "mol/L",
        "k": k_unit,
        "tau": "min",
        "C_A_ss": "mol/L",
        "conversion": "fraction [0, 1]",
    }

    x_grid = np.linspace(x_min, x_max, n_x)
    y_grid = np.linspace(y_min, y_max, n_y)

    conv_matrix: list[list[Optional[float]]] = []
    conc_matrix: list[list[float]] = []
    tau_matrix: list[list[float]] = []

    for y_val in y_grid:
        conv_row: list[Optional[float]] = []
        conc_row: list[float] = []
        tau_row: list[float] = []

        for x_val in x_grid:
            param_dict = {
                "V": baseline_V,
                "Q": baseline_Q,
                "k": baseline_k,
                "C_A_in": baseline_C_in,
            }
            param_dict[var_x.value] = float(x_val)
            param_dict[var_y.value] = float(y_val)

            res = solve_steady_state(
                param_dict["V"], param_dict["Q"], param_dict["C_A_in"], order, param_dict["k"]
            )
            conv_row.append(res.conversion)
            conc_row.append(res.C_A_ss)
            tau_row.append(res.tau)

        conv_matrix.append(conv_row)
        conc_matrix.append(conc_row)
        tau_matrix.append(tau_row)

    fixed_params = {
        "V": baseline_V,
        "Q": baseline_Q,
        "k": baseline_k,
        "C_A_in": baseline_C_in,
    }
    fixed_params.pop(var_x.value, None)
    fixed_params.pop(var_y.value, None)

    trend_summary = (
        f"2D surface mapped over {SWEEP_VARIABLE_LABELS[var_x]} ({x_min:.2f} to {x_max:.2f}) "
        f"and {SWEEP_VARIABLE_LABELS[var_y]} ({y_min:.2f} to {y_max:.2f})."
    )

    return Sweep2DResult(
        var_x=var_x.value,
        var_x_label=SWEEP_VARIABLE_LABELS[var_x],
        var_x_unit=unit_map[var_x.value],
        x_values=[float(x) for x in x_grid],
        var_y=var_y.value,
        var_y_label=SWEEP_VARIABLE_LABELS[var_y],
        var_y_unit=unit_map[var_y.value],
        y_values=[float(y) for y in y_grid],
        fixed_parameters=fixed_params,
        order=order,
        conversion_grid=conv_matrix,
        concentration_grid=conc_matrix,
        tau_grid=tau_matrix,
        baseline_point={"x": baseline_V if var_x == SweepVariable.VOLUME else (baseline_Q if var_x == SweepVariable.FLOW_RATE else (baseline_k if var_x == SweepVariable.RATE_CONSTANT else baseline_C_in)),
                        "y": baseline_V if var_y == SweepVariable.VOLUME else (baseline_Q if var_y == SweepVariable.FLOW_RATE else (baseline_k if var_y == SweepVariable.RATE_CONSTANT else baseline_C_in))},
        trend_summary=trend_summary,
        units=unit_map,
    )


@dataclass(frozen=True)
class SweepLHSPoint:
    """Calculated steady-state metrics for a single LHS parameter draw."""

    sample_index: int
    V: float
    Q: float
    k: float
    C_A_in: float
    tau: float
    C_A_ss: float
    conversion: Optional[float]
    reaction_rate_ss: float
    residual: float
    status: Literal["ok", "failed"] = "ok"
    warning: Optional[str] = None


@dataclass
class SweepLHSResult:
    """Result of Latin Hypercube Sampling (SciPy QMC) parameter sweep."""

    n_samples: int
    seed: int
    order: int
    bounds: dict[str, tuple[float, float]]
    points: list[SweepLHSPoint]
    summary_statistics: dict[str, Any]
    failed_count: int
    units: dict[str, str] = field(default_factory=dict)


def compute_lhs_parameter_sweep(
    bounds: dict[str, tuple[float, float]],
    n_samples: int = 50,
    seed: int = 42,
    order: int = 1,
) -> SweepLHSResult:
    """Execute Latin Hypercube Sampling across CSTR parameter space using SciPy QMC."""
    if n_samples < 2:
        raise ValueError(f"Number of LHS samples must be at least 2, got {n_samples}.")
    if n_samples > 10000:
        raise ValueError(f"Number of LHS samples exceeds maximum limit of 10000, got {n_samples}.")

    param_keys = ["V", "Q", "k", "C_A_in"]
    lower_bounds: list[float] = []
    upper_bounds: list[float] = []

    for key in param_keys:
        if key not in bounds:
            raise ValueError(f"Missing bounds for required parameter '{key}'.")
        low, high = bounds[key]
        if low >= high:
            raise ValueError(f"Lower bound for '{key}' ({low}) must be strictly less than upper bound ({high}).")
        if key in ("V", "Q") and low <= 0.0:
            raise ValueError(f"Lower bound for '{key}' must be strictly positive (> 0), got {low}.")
        if low < 0.0:
            raise ValueError(f"Lower bound for '{key}' cannot be negative, got {low}.")
        lower_bounds.append(float(low))
        upper_bounds.append(float(high))

    sampler = qmc.LatinHypercube(d=4, seed=seed)
    raw_samples = sampler.random(n=n_samples)
    scaled_samples = qmc.scale(raw_samples, lower_bounds, upper_bounds)

    points: list[SweepLHSPoint] = []
    failed_count = 0
    conversions: list[float] = []
    taus: list[float] = []

    k_unit = RATE_CONSTANT_CANONICAL_UNITS.get(order, "min^-1")
    unit_map = {
        "V": "L",
        "Q": "L/min",
        "C_A_in": "mol/L",
        "k": k_unit,
        "tau": "min",
        "C_A_ss": "mol/L",
        "conversion": "fraction [0, 1]",
        "reaction_rate": "mol/(L*min)",
        "residual": "mol/(L*min)",
    }

    for idx, sample in enumerate(scaled_samples):
        v_val, q_val, k_val, cin_val = float(sample[0]), float(sample[1]), float(sample[2]), float(sample[3])
        try:
            res = solve_steady_state(v_val, q_val, cin_val, order, k_val)
            tau_val = res.tau
            css_val = res.C_A_ss
            conv_val = res.conversion
            rate_val = res.reaction_rate_ss
            res_val = res.residual
            status_val: Literal["ok", "failed"] = "ok"
            warn_val = None
            if conv_val is not None:
                conversions.append(conv_val)
            taus.append(tau_val)
        except Exception as exc:
            failed_count += 1
            tau_val = v_val / q_val if q_val > 0 else 0.0
            css_val = float("nan")
            conv_val = None
            rate_val = float("nan")
            res_val = float("nan")
            status_val = "failed"
            warn_val = str(exc)

        points.append(
            SweepLHSPoint(
                sample_index=idx,
                V=v_val,
                Q=q_val,
                k=k_val,
                C_A_in=cin_val,
                tau=tau_val,
                C_A_ss=css_val,
                conversion=conv_val,
                reaction_rate_ss=rate_val,
                residual=res_val,
                status=status_val,
                warning=warn_val,
            )
        )

    summary_stats = {
        "total_evaluations": n_samples,
        "successful_evaluations": n_samples - failed_count,
        "failed_evaluations": failed_count,
        "mean_conversion": float(np.mean(conversions)) if conversions else None,
        "min_conversion": float(np.min(conversions)) if conversions else None,
        "max_conversion": float(np.max(conversions)) if conversions else None,
        "mean_residence_time": float(np.mean(taus)) if taus else None,
    }

    return SweepLHSResult(
        n_samples=n_samples,
        seed=seed,
        order=order,
        bounds=bounds,
        points=points,
        summary_statistics=summary_stats,
        failed_count=failed_count,
        units=unit_map,
    )
