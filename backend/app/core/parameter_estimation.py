"""Conventional kinetic parameter estimation for isothermal CSTR using SciPy optimization.

Supports:
1. Dynamic parameter estimation: Solves the CSTR transient ODE for candidate k
   and minimizes the sum of squared residuals between observed and predicted C_A(t).
2. Steady-state parameter estimation: Solves algebraic steady-state equations
   across multiple operating points (varying residence times or flow rates).
"""

from dataclasses import dataclass, field
import math
from typing import Any, Literal, Optional, Sequence
import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import least_squares
from scipy.stats import t as student_t

from backend.app.core.dynamic_solver import cstr_ode_rhs, solve_dynamic_cstr
from backend.app.core.isothermal_first_order import (
    validate_finite_nonnegative,
    validate_finite_positive,
)
from backend.app.core.kinetics import RATE_CONSTANT_CANONICAL_UNITS, KineticModel
from backend.app.core.steady_state import solve_steady_state


@dataclass
class ParameterConfidenceInterval:
    """Statistical confidence interval for an estimated parameter."""

    param_name: str
    estimate: float
    std_error: float
    confidence_level: float  # e.g., 0.95
    ci_lower: float
    ci_upper: float
    degrees_of_freedom: int
    t_critical: float


@dataclass
class KineticFitResult:
    """Complete diagnostic results of a kinetic parameter estimation."""

    model_type: Literal["dynamic", "steady_state"]
    reaction_order: int
    fitted_k: float
    k_unit: str
    initial_k_guess: float
    k_bounds: tuple[float, float]

    # Goodness of fit metrics
    n_points: int
    degrees_of_freedom: int
    ssr: float  # Sum of squared residuals
    rmse: float  # Root mean squared error
    mae: float  # Mean absolute error
    r_squared: float  # Coefficient of determination

    # Optimizer diagnostics
    optimizer_success: bool
    optimizer_status: int
    optimizer_message: str
    n_fev: int

    # Series for plotting
    time_series: list[float]
    observed_C_A: list[float]
    predicted_C_A: list[float]
    residuals: list[float]

    # Optional estimates and diagnostics
    fitted_C_A_0: Optional[float] = None
    confidence_interval_k: Optional[ParameterConfidenceInterval] = None
    uncertainty_note: Optional[str] = None
    condition_number: Optional[float] = None
    parameter_correlation: Optional[dict[str, float]] = None
    warnings: list[str] = field(default_factory=list)
    provenance_label: str = (
        "FITTED ESTIMATE: The reported kinetic parameters are mathematical estimates "
        "derived from numerical optimization and model assumptions. They are not direct laboratory measurements."
    )


def compute_r_squared(observed: np.ndarray, predicted: np.ndarray) -> float:
    """Calculate the coefficient of determination R^2."""
    ss_res = float(np.sum((observed - predicted) ** 2))
    ss_tot = float(np.sum((observed - np.mean(observed)) ** 2))
    if ss_tot <= 1e-14:
        return 0.0 if ss_res > 1e-14 else 1.0
    r2 = 1.0 - (ss_res / ss_tot)
    return float(max(-10.0, min(1.0, r2)))


def validate_data_compatibility_for_kinetics(
    has_concentration: bool = True,
    has_temperature_only: bool = False,
    dataset_split: Optional[str] = None,
) -> None:
    """Enforce Phase 7 scientific compatibility guidelines.

    1. Rejects temperature-only signals: kinetic parameters cannot be fitted without
       measured reactant concentrations or a fully coupled mass & energy balance model.
    2. Enforces split leakage prevention: test split data must never be used for parameter fitting.
    """
    if has_temperature_only or not has_concentration:
        raise ValueError(
            "Cannot infer reaction kinetics from temperature-only signals without measured "
            "concentration C_A or a calibrated coupled thermo-kinetic energy model."
        )
    if dataset_split is not None and dataset_split.strip().lower() == "test":
        raise ValueError(
            "Test partition data must NOT be used for parameter fitting to prevent data leakage. "
            "Fit parameters on the training split only."
        )


def fit_dynamic_kinetics(
    time: Sequence[float],
    C_A_obs: Sequence[float],
    V: float,
    Q: float,
    C_A_in: float,
    order: int = 1,
    C_A_0: Optional[float] = None,
    fit_initial_conc: bool = False,
    k_init: float = 0.1,
    k_min: float = 1e-6,
    k_max: float = 50.0,
    confidence_level: float = 0.95,
    dataset_split: Optional[str] = None,
    has_temperature_only: bool = False,
) -> KineticFitResult:
    """Fit kinetic rate constant k from transient dynamic concentration data."""
    validate_data_compatibility_for_kinetics(
        has_concentration=True,
        has_temperature_only=has_temperature_only,
        dataset_split=dataset_split,
    )

    t_arr = np.asarray(time, dtype=np.float64)
    y_obs = np.asarray(C_A_obs, dtype=np.float64)

    warnings: list[str] = []

    # 1. Input hygiene & validation
    if len(t_arr) != len(y_obs):
        raise ValueError(f"Length mismatch: time ({len(t_arr)}) and C_A_obs ({len(y_obs)}) must match.")
    if len(t_arr) < 3:
        raise ValueError(f"Parameter estimation requires at least 3 data points, got {len(t_arr)}.")
    if order not in (0, 1, 2):
        raise ValueError(f"Reaction order must be 0, 1, or 2, got {order}.")

    validate_finite_positive("V", V)
    validate_finite_positive("Q", Q)
    validate_finite_nonnegative("C_A_in", C_A_in)
    validate_finite_positive("k_init", k_init)
    if k_min >= k_max:
        raise ValueError(f"k_min ({k_min}) must be strictly less than k_max ({k_max}).")

    # Sort chronologically if needed
    if not np.all(np.diff(t_arr) >= 0):
        sort_idx = np.argsort(t_arr)
        t_arr = t_arr[sort_idx]
        y_obs = y_obs[sort_idx]
        warnings.append("Time vector was re-sorted chronologically.")

    # Excitation & Identifiability Checks
    t_span_total = float(t_arr[-1] - t_arr[0])
    if t_span_total < 1e-4:
        warnings.append("Experimental time span is virtually zero (< 1e-4 min). Poor dynamic identifiability.")

    obs_std = float(np.std(y_obs))
    if obs_std < 1e-5:
        warnings.append(
            "Observed concentration variance is virtually zero. Dynamic excitation is insufficient to identify kinetics."
        )

    # Initial condition C_A(0)
    c0_fixed = float(y_obs[0]) if C_A_0 is None else float(C_A_0)
    if c0_fixed < 0:
        c0_fixed = 0.0
        warnings.append("Initial concentration C_A(0) was clamped to 0.0.")

    t_eval = t_arr - t_arr[0]  # Normalize time so t starts at 0.0
    t_final = float(t_eval[-1])
    if t_final <= 0:
        t_final = 1.0

    # 2. Define ODE simulation for candidate parameter vector
    # params = [k] or [k, C_A_0]
    p_names = ["k"]
    lower_bounds = [k_min]
    upper_bounds = [k_max]
    p_init = [max(k_min, min(k_max, k_init))]

    if fit_initial_conc:
        p_names.append("C_A_0")
        lower_bounds.append(0.0)
        upper_bounds.append(max(5.0 * max(y_obs), 10.0))
        p_init.append(c0_fixed)

    def simulate_model(params: np.ndarray) -> np.ndarray:
        cand_k = float(params[0])
        cand_c0 = float(params[1]) if fit_initial_conc else c0_fixed

        k_model = KineticModel(order=order, k=cand_k)
        # Solve ODE
        sol = solve_ivp(
            fun=lambda t, y: cstr_ode_rhs(t, y, V, Q, C_A_in, k_model),
            t_span=(0.0, t_final),
            y0=[cand_c0],
            t_eval=t_eval,
            method="Radau" if order == 0 else "RK45",
            rtol=1e-5,
            atol=1e-7,
        )
        if not sol.success or len(sol.y[0]) != len(t_eval):
            # Fallback interpolation if solver terminated early
            return np.full_like(y_obs, fill_value=cand_c0)
        return np.maximum(0.0, sol.y[0])

    def residuals_fn(params: np.ndarray) -> np.ndarray:
        pred = simulate_model(params)
        return pred - y_obs

    # 3. Nonlinear Least-Squares Optimization
    res = least_squares(
        fun=residuals_fn,
        x0=p_init,
        bounds=(lower_bounds, upper_bounds),
        method="trf",
        loss="linear",
        ftol=1e-7,
        xtol=1e-7,
        gtol=1e-7,
        max_nfev=200,
    )

    fitted_k = float(res.x[0])
    fitted_c0 = float(res.x[1]) if fit_initial_conc else c0_fixed

    # Check bound collision
    if math.isclose(fitted_k, k_min, rel_tol=1e-3, abs_tol=1e-5):
        warnings.append(f"Fitted rate constant hit lower bound ({k_min}). Check kinetics or units.")
    elif math.isclose(fitted_k, k_max, rel_tol=1e-3, abs_tol=1e-5):
        warnings.append(f"Fitted rate constant hit upper bound ({k_max}). Rate may be instantaneous or mass-transfer limited.")

    # 4. Residuals & Metrics
    y_pred = simulate_model(res.x)
    residual_vec = y_obs - y_pred

    n_pts = len(y_obs)
    n_params = len(p_init)
    dof = n_pts - n_params

    ssr = float(np.sum(residual_vec ** 2))
    rmse = float(np.sqrt(ssr / n_pts))
    mae = float(np.mean(np.abs(residual_vec)))
    r2 = compute_r_squared(y_obs, y_pred)

    # 5. Statistical Uncertainty & Confidence Intervals
    ci_k: Optional[ParameterConfidenceInterval] = None
    uncertainty_note: Optional[str] = None
    condition_number: Optional[float] = None
    parameter_correlation: Optional[dict[str, float]] = None

    if dof > 0 and res.success:
        try:
            # Jacobian J from least_squares (N x p)
            J = res.jac
            jt_j = J.T @ J
            cond_val = float(np.linalg.cond(jt_j))
            condition_number = cond_val
            if cond_val > 1e4:
                warnings.append(
                    f"Information matrix J^T J is ill-conditioned (condition number {cond_val:.1e}). "
                    "Parameters may have high collinearity or poor identifiability."
                )

            # Residual variance s^2
            s_sq = ssr / dof
            cov = s_sq * np.linalg.inv(jt_j)
            var_k = cov[0, 0]
            if var_k > 0 and math.isfinite(var_k):
                se_k = float(np.sqrt(var_k))
                t_crit = float(student_t.ppf((1.0 + confidence_level) / 2.0, df=dof))
                ci_k = ParameterConfidenceInterval(
                    param_name="k",
                    estimate=fitted_k,
                    std_error=se_k,
                    confidence_level=confidence_level,
                    ci_lower=max(0.0, fitted_k - t_crit * se_k),
                    ci_upper=fitted_k + t_crit * se_k,
                    degrees_of_freedom=dof,
                    t_critical=t_crit,
                )
            else:
                uncertainty_note = "Variance of k is non-positive or singular. Uncertainty was not estimated."

            # Correlation diagnostics when multiple parameters are co-estimated
            if cov.shape[0] > 1:
                var_c0 = cov[1, 1]
                if var_k > 0 and var_c0 > 0:
                    corr_val = float(cov[0, 1] / np.sqrt(var_k * var_c0))
                    parameter_correlation = {"k_C_A_0": corr_val}
                    if abs(corr_val) > 0.90:
                        warnings.append(
                            f"High parameter correlation detected (rho(k, C_A_0) = {corr_val:.3f}). "
                            "Initial concentration and rate constant are strongly collinear in this dynamic window."
                        )
        except np.linalg.LinAlgError:
            uncertainty_note = "Jacobian (J^T J) is singular. Parameter uncertainty could not be estimated."
    else:
        uncertainty_note = f"Insufficient degrees of freedom (N={n_pts}, params={n_params}, df={dof}). Uncertainty was not estimated."

    k_unit = RATE_CONSTANT_CANONICAL_UNITS.get(order, "min^-1")

    return KineticFitResult(
        model_type="dynamic",
        reaction_order=order,
        fitted_k=fitted_k,
        k_unit=k_unit,
        initial_k_guess=k_init,
        k_bounds=(k_min, k_max),
        fitted_C_A_0=fitted_c0,
        confidence_interval_k=ci_k,
        uncertainty_note=uncertainty_note,
        condition_number=condition_number,
        parameter_correlation=parameter_correlation,
        n_points=n_pts,
        degrees_of_freedom=dof,
        ssr=ssr,
        rmse=rmse,
        mae=mae,
        r_squared=r2,
        optimizer_success=bool(res.success),
        optimizer_status=int(res.status),
        optimizer_message=str(res.message),
        n_fev=int(res.nfev),
        time_series=[float(x) for x in t_arr],
        observed_C_A=[float(x) for x in y_obs],
        predicted_C_A=[float(x) for x in y_pred],
        residuals=[float(x) for x in residual_vec],
        warnings=warnings,
    )


def fit_steady_state_kinetics(
    tau_or_flow: Sequence[float],
    C_A_obs: Sequence[float],
    C_A_in: float,
    V: float = 10.0,
    is_flow_rate: bool = False,
    order: int = 1,
    k_init: float = 0.1,
    k_min: float = 1e-6,
    k_max: float = 50.0,
    confidence_level: float = 0.95,
    dataset_split: Optional[str] = None,
    has_temperature_only: bool = False,
) -> KineticFitResult:
    """Fit rate constant k from steady-state concentration data across multiple operating points."""
    validate_data_compatibility_for_kinetics(
        has_concentration=True,
        has_temperature_only=has_temperature_only,
        dataset_split=dataset_split,
    )

    x_input = np.asarray(tau_or_flow, dtype=np.float64)
    y_obs = np.asarray(C_A_obs, dtype=np.float64)

    warnings: list[str] = []

    if len(x_input) != len(y_obs):
        raise ValueError("Length mismatch between input operating conditions and observed concentrations.")
    if len(x_input) < 2:
        raise ValueError("Steady-state parameter estimation requires at least 2 distinct operating points.")
    if order not in (0, 1, 2):
        raise ValueError(f"Reaction order must be 0, 1, or 2, got {order}.")

    validate_finite_positive("V", V)
    validate_finite_nonnegative("C_A_in", C_A_in)

    # Compute residence times tau
    if is_flow_rate:
        # x_input is Q [L/min]
        if np.any(x_input <= 0):
            raise ValueError("All volumetric flow rates must be strictly positive.")
        tau_arr = V / x_input
    else:
        # x_input is tau [min]
        if np.any(x_input <= 0):
            raise ValueError("All residence times must be strictly positive.")
        tau_arr = x_input

    # Check for identical repeated conditions
    if float(np.std(tau_arr)) < 1e-4:
        warnings.append(
            "Residence times are virtually identical across all data rows. "
            "Steady-state data must vary flow rate or residence time to identify kinetics."
        )

    def model_fn(cand_k: float) -> np.ndarray:
        preds = []
        for tau in tau_arr:
            q_equiv = V / tau
            res = solve_steady_state(V=V, Q=q_equiv, C_A_in=C_A_in, order=order, k=cand_k)
            preds.append(res.C_A_ss)
        return np.asarray(preds, dtype=np.float64)

    def residuals_fn(p: np.ndarray) -> np.ndarray:
        cand_k = float(p[0])
        return model_fn(cand_k) - y_obs

    res = least_squares(
        fun=residuals_fn,
        x0=[max(k_min, min(k_max, k_init))],
        bounds=([k_min], [k_max]),
        method="trf",
        max_nfev=150,
    )

    fitted_k = float(res.x[0])
    y_pred = model_fn(fitted_k)
    residual_vec = y_obs - y_pred

    n_pts = len(y_obs)
    dof = n_pts - 1
    ssr = float(np.sum(residual_vec ** 2))
    rmse = float(np.sqrt(ssr / n_pts))
    mae = float(np.mean(np.abs(residual_vec)))
    r2 = compute_r_squared(y_obs, y_pred)

    ci_k: Optional[ParameterConfidenceInterval] = None
    uncertainty_note: Optional[str] = None

    if dof > 0 and res.success:
        try:
            J = res.jac
            jt_j_val = (J.T @ J).item() if hasattr(J.T @ J, "item") else float(J.T @ J)
            if jt_j_val > 1e-12:
                s_sq = ssr / dof
                se_k = float(np.sqrt(max(0.0, s_sq / jt_j_val)))
                t_crit = float(student_t.ppf((1.0 + confidence_level) / 2.0, df=dof))
                ci_k = ParameterConfidenceInterval(
                    param_name="k",
                    estimate=fitted_k,
                    std_error=se_k,
                    confidence_level=confidence_level,
                    ci_lower=max(0.0, fitted_k - t_crit * se_k),
                    ci_upper=fitted_k + t_crit * se_k,
                    degrees_of_freedom=dof,
                    t_critical=t_crit,
                )
            else:
                uncertainty_note = "Jacobian information is singular. Uncertainty was not estimated."
        except Exception as exc:
            uncertainty_note = f"Could not compute confidence interval: {str(exc)}"
    else:
        uncertainty_note = f"Insufficient degrees of freedom (N={n_pts}, df={dof}). Uncertainty was not estimated."

    k_unit = RATE_CONSTANT_CANONICAL_UNITS.get(order, "min^-1")

    return KineticFitResult(
        model_type="steady_state",
        reaction_order=order,
        fitted_k=fitted_k,
        k_unit=k_unit,
        initial_k_guess=k_init,
        k_bounds=(k_min, k_max),
        confidence_interval_k=ci_k,
        uncertainty_note=uncertainty_note,
        condition_number=1.0,
        parameter_correlation=None,
        n_points=n_pts,
        degrees_of_freedom=dof,
        ssr=ssr,
        rmse=rmse,
        mae=mae,
        r_squared=r2,
        optimizer_success=bool(res.success),
        optimizer_status=int(res.status),
        optimizer_message=str(res.message),
        n_fev=int(res.nfev),
        time_series=[float(x) for x in tau_arr],
        observed_C_A=[float(x) for x in y_obs],
        predicted_C_A=[float(x) for x in y_pred],
        residuals=[float(x) for x in residual_vec],
        warnings=warnings,
    )


def evaluate_kinetic_model_on_test_split(
    fit_result: KineticFitResult,
    test_time: Sequence[float],
    test_C_A_obs: Sequence[float],
    V: float,
    Q: float,
    C_A_in: float,
    C_A_0: Optional[float] = None,
) -> dict[str, float]:
    """Evaluate a fitted kinetic model against an independent held-out test split.

    Ensures zero leakage: parameters were fitted strictly on train/val data, and are
    now evaluated on unseen test data to verify generalization.
    """
    t_test = np.asarray(test_time, dtype=np.float64)
    y_test = np.asarray(test_C_A_obs, dtype=np.float64)
    if len(t_test) != len(y_test):
        raise ValueError("Length mismatch between test time and test concentration.")

    k_model = KineticModel(order=fit_result.reaction_order, k=fit_result.fitted_k)
    c0 = float(y_test[0]) if C_A_0 is None else float(C_A_0)

    t_eval = t_test - t_test[0]
    t_final = float(t_eval[-1]) if t_eval[-1] > 0 else 1.0

    sol = solve_ivp(
        fun=lambda t, y: cstr_ode_rhs(t, y, V, Q, C_A_in, k_model),
        t_span=(0.0, t_final),
        y0=[c0],
        t_eval=t_eval,
        method="Radau" if fit_result.reaction_order == 0 else "RK45",
        rtol=1e-5,
        atol=1e-7,
    )

    if sol.success and len(sol.y[0]) == len(t_eval):
        y_pred = np.maximum(0.0, sol.y[0])
    else:
        y_pred = np.full_like(y_test, fill_value=c0)

    residuals = y_test - y_pred
    ssr = float(np.sum(residuals ** 2))
    rmse = float(np.sqrt(ssr / len(y_test)))
    mae = float(np.mean(np.abs(residuals)))
    r2 = compute_r_squared(y_test, y_pred)

    return {
        "test_n_points": float(len(y_test)),
        "test_ssr": ssr,
        "test_rmse": rmse,
        "test_mae": mae,
        "test_r_squared": r2,
    }
