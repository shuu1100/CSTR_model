"""Dynamic ODE solver for isothermal CSTR with arbitrary reaction orders and step changes.

Solves the transient mole balance ODE:
    dC_A/dt = (Q / V) * (C_A_in - C_A) + r_A(C_A)
using scipy.integrate.solve_ivp.
"""

from dataclasses import dataclass, field
import math
from typing import Any, Optional, Sequence, Union
import numpy as np
from scipy.integrate import solve_ivp

from backend.app.core.analytical import first_order_dynamic_analytical_trajectory
from backend.app.core.isothermal_first_order import validate_finite_nonnegative, validate_finite_positive
from backend.app.core.kinetics import KineticModel, RATE_CONSTANT_CANONICAL_UNITS
from backend.app.core.steady_state import solve_steady_state


@dataclass(frozen=True)
class StepChange:
    """Specification of a single parameter step change during dynamic simulation."""

    time: float  # Time at which step change occurs (0 < time < t_final)
    C_A_in_new: Optional[float] = None  # New inlet concentration [mol/L]
    Q_new: Optional[float] = None  # New volumetric flow rate [L/min]

    def __post_init__(self) -> None:
        if not isinstance(self.time, (int, float)) or not math.isfinite(self.time) or self.time <= 0.0:
            raise ValueError(f"Step change time must be positive and finite, got {self.time}.")
        if self.C_A_in_new is not None:
            validate_finite_nonnegative("C_A_in_new", self.C_A_in_new)
        if self.Q_new is not None:
            validate_finite_positive("Q_new", self.Q_new)
        if self.C_A_in_new is None and self.Q_new is None:
            raise ValueError("At least one parameter (C_A_in_new or Q_new) must be specified for a step change.")


@dataclass
class DynamicSimulationResult:
    """Results container for dynamic CSTR simulation."""

    t: list[float]
    C_A: list[float]
    conversion: Optional[list[float]]
    reaction_rate: list[float]
    order: int
    k: float
    k_unit: str
    tau_initial: float
    C_A_ss_initial: float
    solver_method: str
    success: bool
    status: int
    message: str
    tolerances: dict[str, float]
    units: dict[str, str]
    analytical_comparison: Optional[dict[str, float]] = None
    step_change_applied: Optional[dict[str, Any]] = None
    warnings: list[str] = field(default_factory=list)


def cstr_ode_rhs(
    t: float,
    y: np.ndarray,
    V: float,
    Q: float,
    C_A_in: float,
    kinetic_model: KineticModel,
) -> np.ndarray:
    """Right-hand side of CSTR dynamic mole balance: dC_A/dt = (Q/V)*(C_in - C_A) + r_A."""
    c_val = y[0]
    # Enforce non-negativity in evaluation of rate
    r_A = kinetic_model.reaction_rate(c_val)
    convection = (Q / V) * (C_A_in - c_val)
    return np.array([convection + r_A], dtype=np.float64)


def simulate_dynamic_cstr(
    C_A_0: float,
    C_A_in: float,
    V: float,
    Q: float,
    order: int,
    k: float,
    t_final: float,
    n_points: int = 101,
    t_eval: Optional[Union[Sequence[float], np.ndarray]] = None,
    method: str = "RK45",
    rtol: float = 1e-6,
    atol: float = 1e-9,
    step_change: Optional[StepChange] = None,
) -> DynamicSimulationResult:
    """Simulate transient concentration trajectory for an isothermal CSTR.

    Parameters:
        C_A_0: Initial concentration inside the reactor [mol/L] (>= 0).
        C_A_in: Inlet feed concentration [mol/L] (>= 0).
        V: Reactor volume [L] (> 0).
        Q: Volumetric flow rate [L/min] (> 0).
        order: Reaction order (0, 1, or 2).
        k: Reaction rate constant in canonical units (>= 0).
        t_final: Total simulation horizon in minutes (> 0).
        n_points: Number of uniformly spaced evaluation points (if t_eval not given).
        t_eval: Explicit time points to record trajectory at.
        method: ODE solver method supported by solve_ivp (RK45, Radau, BDF, etc.).
        rtol: Relative error tolerance.
        atol: Absolute error tolerance.
        step_change: Optional StepChange instance applied at t_step.

    Returns:
        DynamicSimulationResult with trajectory data, diagnostics, and units.
    """
    validate_finite_nonnegative("C_A_0", C_A_0)
    validate_finite_nonnegative("C_A_in", C_A_in)
    validate_finite_positive("V", V)
    validate_finite_positive("Q", Q)
    validate_finite_positive("t_final", t_final)

    if n_points < 2:
        raise ValueError(f"Requested output count n_points must be at least 2, got {n_points}.")
    if n_points > 100_000:
        raise ValueError(f"Requested output count n_points is excessively large ({n_points}). Maximum is 100,000.")

    kinetic_model = KineticModel(order=order, k=k)
    tau_init = V / Q
    ss_init = solve_steady_state(V, Q, C_A_in, order, k)

    tolerances = {"rtol": rtol, "atol": atol}
    units = {
        "t": "min",
        "C_A": "mol/L",
        "conversion": "fraction [0, 1]",
        "reaction_rate": "mol/(L*min)",
        "V": "L",
        "Q": "L/min",
        "k": kinetic_model.k_unit,
    }

    warnings: list[str] = []

    # Handle evaluation grid
    if t_eval is not None:
        eval_points = np.asarray(t_eval, dtype=np.float64)
        if len(eval_points) < 2:
            raise ValueError("t_eval must contain at least 2 points.")
        if eval_points[0] < 0.0 or eval_points[-1] > t_final:
            raise ValueError(f"t_eval must lie within [0, t_final={t_final}].")
        if not np.all(np.diff(eval_points) > 0):
            raise ValueError("t_eval must be strictly monotonically increasing.")
    else:
        eval_points = np.linspace(0.0, t_final, n_points, dtype=np.float64)

    # Validate step change time if provided
    if step_change is not None:
        if step_change.time >= t_final:
            warnings.append(
                f"Step change time ({step_change.time} min) is >= t_final ({t_final} min); step change will not occur."
            )
            step_change = None

    # Piecewise integration if step change occurs
    if step_change is not None:
        t_step = step_change.time
        # Segment 1: [0, t_step]
        eval_seg1 = eval_points[eval_points <= t_step]
        added_t_step_to_seg1 = False
        if len(eval_seg1) == 0 or eval_seg1[-1] < t_step:
            eval_seg1_with_step = np.append(eval_seg1, t_step)
            added_t_step_to_seg1 = True
        else:
            eval_seg1_with_step = eval_seg1

        sol1 = solve_ivp(
            fun=lambda t, y: cstr_ode_rhs(t, y, V, Q, C_A_in, kinetic_model),
            t_span=(0.0, t_step),
            y0=[C_A_0],
            t_eval=eval_seg1_with_step,
            method=method,
            rtol=rtol,
            atol=atol,
        )

        if not sol1.success:
            warnings.append(f"Solver segment 1 failed: {sol1.message}")

        c_at_step = float(sol1.y[0, -1])

        # New operating conditions
        c_in_seg2 = step_change.C_A_in_new if step_change.C_A_in_new is not None else C_A_in
        q_seg2 = step_change.Q_new if step_change.Q_new is not None else Q

        # Segment 2: [t_step, t_final]
        eval_seg2 = eval_points[eval_points > t_step]
        # Prepend t_step to segment 2 for clean continuity
        eval_seg2_with_start = np.insert(eval_seg2, 0, t_step)

        sol2 = solve_ivp(
            fun=lambda t, y: cstr_ode_rhs(t, y, V, q_seg2, c_in_seg2, kinetic_model),
            t_span=(t_step, t_final),
            y0=[c_at_step],
            t_eval=eval_seg2_with_start,
            method=method,
            rtol=rtol,
            atol=atol,
        )

        if not sol2.success:
            warnings.append(f"Solver segment 2 failed: {sol2.message}")

        # Combine results: omit duplicated t_step and preserve exact eval_points length
        sol1_t = sol1.t[:-1] if added_t_step_to_seg1 else sol1.t
        sol1_c = sol1.y[0, :-1] if added_t_step_to_seg1 else sol1.y[0]
        t_arr = np.concatenate([sol1_t, sol2.t[1:]])
        c_arr = np.concatenate([sol1_c, sol2.y[0][1:]])
        success = sol1.success and sol2.success
        status = sol1.status if not sol1.success else sol2.status
        message = sol2.message if sol1.success else sol1.message

        step_applied_info = {
            "time": step_change.time,
            "C_A_in_initial": C_A_in,
            "C_A_in_new": c_in_seg2,
            "Q_initial": Q,
            "Q_new": q_seg2,
            "C_A_at_step": c_at_step,
        }
    else:
        # Single continuous interval
        sol = solve_ivp(
            fun=lambda t, y: cstr_ode_rhs(t, y, V, Q, C_A_in, kinetic_model),
            t_span=(0.0, t_final),
            y0=[C_A_0],
            t_eval=eval_points,
            method=method,
            rtol=rtol,
            atol=atol,
        )
        t_arr = sol.t
        c_arr = sol.y[0]
        success = sol.success
        status = sol.status
        message = sol.message
        step_applied_info = None

    # Numerical post-processing & non-negativity safety
    # Check if any concentration was slightly negative due to solver tolerances
    min_c = float(np.min(c_arr))
    if min_c < -1e-8:
        warnings.append(f"Concentration dropped below 0 to {min_c:.3e} (beyond numerical tolerance).")
    # Project to strictly non-negative
    c_arr = np.maximum(0.0, c_arr)

    # Conversion trajectory where inlet concentration > 0
    conv_list: Optional[list[float]] = None
    if step_change is None:
        if C_A_in > 0.0:
            conv_arr = np.clip((C_A_in - c_arr) / C_A_in, 0.0, 1.0)
            conv_list = [float(x) for x in conv_arr]
    else:
        # With step change, compute conversion piecewise based on active inlet concentration
        t_step_val = step_change.time
        conv_list = []
        for t_val, c_val in zip(t_arr, c_arr):
            curr_c_in = step_change.C_A_in_new if (step_change.C_A_in_new is not None and t_val >= t_step_val) else C_A_in
            if curr_c_in > 0.0:
                conv_list.append(float(max(0.0, min(1.0, (curr_c_in - c_val) / curr_c_in))))
            else:
                conv_list.append(float("nan"))

    # Reaction rate trajectory
    rates = [kinetic_model.reaction_rate(c) for c in c_arr]

    # Analytical comparison for first-order without step changes
    analytical_comparison: Optional[dict[str, float]] = None
    if order == 1 and step_change is None:
        c_analytical = first_order_dynamic_analytical_trajectory(t_arr, C_A_0, V, Q, C_A_in, k)
        abs_err = np.abs(c_arr - c_analytical)
        denom = np.maximum(c_analytical, 1e-12)
        rel_err = abs_err / denom
        analytical_comparison = {
            "max_absolute_error": float(np.max(abs_err)),
            "mean_absolute_error": float(np.mean(abs_err)),
            "max_relative_error": float(np.max(rel_err)),
            "rmse": float(np.sqrt(np.mean(abs_err ** 2))),
        }

    return DynamicSimulationResult(
        t=[float(x) for x in t_arr],
        C_A=[float(x) for x in c_arr],
        conversion=conv_list,
        reaction_rate=rates,
        order=order,
        k=k,
        k_unit=kinetic_model.k_unit,
        tau_initial=tau_init,
        C_A_ss_initial=ss_init.C_A_ss,
        solver_method=method,
        success=success,
        status=status,
        message=message,
        tolerances=tolerances,
        units=units,
        analytical_comparison=analytical_comparison,
        step_change_applied=step_applied_info,
        warnings=warnings,
    )


# Alias for compatibility with estimation / solvers
solve_dynamic_cstr = simulate_dynamic_cstr
