"""Scientific core for ideal, isothermal, first-order CSTR calculations.

Assumptions:
- Continuous Stirred-Tank Reactor (CSTR) operated at steady state.
- Perfectly mixed liquid volume (uniform concentration throughout the tank).
- Constant fluid volume and constant fluid density.
- Isothermal operation (heat effects neglected).
- Single reactant A undergoing irreversible first-order reaction: A -> Products.
- Reaction kinetics: r_A = -k * C_A.

Canonical units:
- Volume (V): Liters (L)
- Volumetric flow rate (Q): Liters per minute (L/min)
- Inlet concentration (C_A_in): mol/L
- First-order rate constant (k): 1/min (min^-1)
- Residence time (tau): minutes (min)
- Steady-state concentration (C_A_ss): mol/L
- Conversion (X_A): dimensionless fraction [0, 1]
- Reaction rate (r_A): mol/(L*min)
"""

from dataclasses import dataclass, field
import math
from typing import Optional


@dataclass(frozen=True)
class SteadyStateFirstOrderResult:
    """Scientific result container for steady-state first-order CSTR calculation."""

    tau: float
    C_A_ss: float
    conversion: Optional[float]
    reaction_rate_ss: float
    residual: float
    model_identifier: str = "ideal_isothermal_cstr_first_order"
    units: dict[str, str] = field(
        default_factory=lambda: {
            "V": "L",
            "Q": "L/min",
            "C_A_in": "mol/L",
            "k": "min^-1",
            "tau": "min",
            "C_A_ss": "mol/L",
            "conversion": "dimensionless (fraction)",
            "reaction_rate_ss": "mol/(L*min)",
            "residual": "mol/(L*min)",
        }
    )
    assumptions: list[str] = field(
        default_factory=lambda: [
            "Ideal continuous stirred-tank reactor (perfect mixing)",
            "Constant reaction volume (d closed liquid level)",
            "Constant fluid density",
            "Isothermal operation",
            "First-order irreversible reaction: r_A = -k * C_A",
            "Single inlet and single outlet stream with identical volumetric flow rates",
        ]
    )
    diagnostics: dict[str, object] = field(default_factory=dict)


def validate_finite_positive(name: str, value: float) -> None:
    """Validate that a numerical input is finite and strictly positive (> 0)."""
    if not isinstance(value, (int, float)):
        raise TypeError(f"Parameter '{name}' must be a numerical value, got {type(value).__name__}.")
    if not math.isfinite(value):
        raise ValueError(f"Parameter '{name}' must be finite, got {value}.")
    if value <= 0.0:
        raise ValueError(f"Parameter '{name}' must be strictly positive (> 0), got {value}.")


def validate_finite_nonnegative(name: str, value: float) -> None:
    """Validate that a numerical input is finite and non-negative (>= 0)."""
    if not isinstance(value, (int, float)):
        raise TypeError(f"Parameter '{name}' must be a numerical value, got {type(value).__name__}.")
    if not math.isfinite(value):
        raise ValueError(f"Parameter '{name}' must be finite, got {value}.")
    if value < 0.0:
        raise ValueError(f"Parameter '{name}' must be non-negative (>= 0), got {value}.")


def residence_time(V: float, Q: float) -> float:
    """Calculate space time / residence time tau = V / Q.

    Parameters:
        V: Reactor volume [L], must be finite and > 0.
        Q: Volumetric flow rate [L/min], must be finite and > 0.

    Returns:
        tau: Mean residence time [min].
    """
    validate_finite_positive("V", V)
    validate_finite_positive("Q", Q)
    return V / Q


def reaction_rate_first_order(k: float, C_A: float) -> float:
    """Calculate first-order reaction rate r_A = -k * C_A.

    Parameters:
        k: Rate constant [min^-1], must be finite and >= 0.
        C_A: Reactant concentration [mol/L], must be finite and >= 0.

    Returns:
        r_A: Reaction rate of A [mol/(L*min)]. Negative for consumption.
    """
    validate_finite_nonnegative("k", k)
    validate_finite_nonnegative("C_A", C_A)
    return -k * C_A


def steady_state_concentration(V: float, Q: float, C_A_in: float, k: float) -> float:
    """Calculate analytical steady-state concentration for first-order CSTR.

    Material balance at steady state:
        0 = (Q/V) * (C_A_in - C_A_ss) - k * C_A_ss
        C_A_ss * ((Q/V) + k) = (Q/V) * C_A_in
        C_A_ss = (Q/V) * C_A_in / ((Q/V) + k) = C_A_in / (1 + k * tau)

    Parameters:
        V: Reactor volume [L], must be > 0.
        Q: Volumetric flow rate [L/min], must be > 0.
        C_A_in: Inlet concentration [mol/L], must be >= 0.
        k: First-order rate constant [min^-1], must be >= 0.

    Returns:
        C_A_ss: Steady-state reactant concentration [mol/L].
    """
    validate_finite_positive("V", V)
    validate_finite_positive("Q", Q)
    validate_finite_nonnegative("C_A_in", C_A_in)
    validate_finite_nonnegative("k", k)

    tau = V / Q
    denom = 1.0 + k * tau
    return C_A_in / denom


def steady_state_conversion(C_A_in: float, C_A_ss: float) -> Optional[float]:
    """Calculate fractional conversion of reactant A at steady state.

    X_A = (C_A_in - C_A_ss) / C_A_in

    Parameters:
        C_A_in: Inlet concentration [mol/L].
        C_A_ss: Steady-state concentration [mol/L].

    Returns:
        X_A: Fractional conversion [0.0, 1.0], or None if C_A_in == 0.0.
    """
    validate_finite_nonnegative("C_A_in", C_A_in)
    validate_finite_nonnegative("C_A_ss", C_A_ss)

    if C_A_in == 0.0:
        return None

    # Numerically clip to [0.0, 1.0] to prevent precision roundoff beyond bounds
    conv = (C_A_in - C_A_ss) / C_A_in
    return max(0.0, min(1.0, conv))


def steady_state_material_balance_residual(
    V: float, Q: float, C_A_in: float, C_A_ss: float, k: float
) -> float:
    """Calculate the transient material balance residual dC_A/dt evaluated at steady state.

    dC_A/dt = (Q / V) * (C_A_in - C_A) + r_A

    At exact steady state, this residual must equal zero.

    Parameters:
        V: Reactor volume [L], must be > 0.
        Q: Volumetric flow rate [L/min], must be > 0.
        C_A_in: Inlet concentration [mol/L], must be >= 0.
        C_A_ss: Evaluated concentration [mol/L], must be >= 0.
        k: Rate constant [min^-1], must be >= 0.

    Returns:
        residual: Material balance residual [mol/(L*min)].
    """
    validate_finite_positive("V", V)
    validate_finite_positive("Q", Q)
    validate_finite_nonnegative("C_A_in", C_A_in)
    validate_finite_nonnegative("C_A_ss", C_A_ss)
    validate_finite_nonnegative("k", k)

    rate = reaction_rate_first_order(k, C_A_ss)
    convection = (Q / V) * (C_A_in - C_A_ss)
    return convection + rate


material_balance_residual = steady_state_material_balance_residual


def solve_isothermal_first_order_steady_state(
    V: float, Q: float, C_A_in: float, k: float, residual_tolerance: float = 1e-12
) -> SteadyStateFirstOrderResult:
    """Execute complete steady-state solution and validation diagnostics.

    Parameters:
        V: Reactor volume [L].
        Q: Volumetric flow rate [L/min].
        C_A_in: Inlet concentration [mol/L].
        k: Rate constant [min^-1].
        residual_tolerance: Acceptable absolute tolerance for balance closure.

    Returns:
        SteadyStateFirstOrderResult containing calculated values, diagnostics, and metadata.
    """
    tau = residence_time(V, Q)
    c_ss = steady_state_concentration(V, Q, C_A_in, k)
    conv = steady_state_conversion(C_A_in, c_ss)
    rate_ss = reaction_rate_first_order(k, c_ss)
    res = steady_state_material_balance_residual(V, Q, C_A_in, c_ss, k)

    balance_closed = abs(res) <= residual_tolerance

    diagnostics = {
        "material_balance_closed": balance_closed,
        "residual_absolute": abs(res),
        "residual_tolerance": residual_tolerance,
        "damkohler_number": k * tau,
    }

    return SteadyStateFirstOrderResult(
        tau=tau,
        C_A_ss=c_ss,
        conversion=conv,
        reaction_rate_ss=rate_ss,
        residual=res,
        diagnostics=diagnostics,
    )
