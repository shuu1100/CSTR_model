"""Unified steady-state calculation and validation for arbitrary reaction orders (0, 1, 2)."""

from dataclasses import dataclass, field
import math
from typing import Optional
from scipy.optimize import root_scalar

from backend.app.core.kinetics import KineticModel, RATE_CONSTANT_CANONICAL_UNITS
from backend.app.core.isothermal_first_order import validate_finite_nonnegative, validate_finite_positive


@dataclass(frozen=True)
class SteadyStateResult:
    """General steady-state result container for any supported reaction order."""

    order: int
    k: float
    k_unit: str
    tau: float
    C_A_ss: float
    conversion: Optional[float]
    reaction_rate_ss: float
    residual: float
    model_identifier: str
    units: dict[str, str] = field(
        default_factory=lambda: {
            "V": "L",
            "Q": "L/min",
            "C_A_in": "mol/L",
            "tau": "min",
            "C_A_ss": "mol/L",
            "conversion": "fraction [0, 1]",
            "reaction_rate_ss": "mol/(L*min)",
            "residual": "mol/(L*min)",
        }
    )
    diagnostics: dict[str, object] = field(default_factory=dict)


def calculate_steady_state_zero_order(V: float, Q: float, C_A_in: float, k: float) -> float:
    """Analytical steady-state concentration for zero-order kinetics."""
    validate_finite_positive("V", V)
    validate_finite_positive("Q", Q)
    validate_finite_nonnegative("C_A_in", C_A_in)
    validate_finite_nonnegative("k", k)

    tau = V / Q
    # If reactant is consumed faster than supplied, C_A drops to 0
    c_ss = C_A_in - k * tau
    return max(0.0, c_ss)


def calculate_steady_state_second_order(V: float, Q: float, C_A_in: float, k: float) -> float:
    """Analytical physically admissible steady-state concentration for second-order kinetics."""
    validate_finite_positive("V", V)
    validate_finite_positive("Q", Q)
    validate_finite_nonnegative("C_A_in", C_A_in)
    validate_finite_nonnegative("k", k)

    if k == 0.0:
        return C_A_in

    tau = V / Q
    # Quadratic equation: k * tau * C_ss^2 + C_ss - C_in = 0
    # Roots: (-1 +/- sqrt(1 + 4 * k * tau * C_in)) / (2 * k * tau)
    discriminant = 1.0 + 4.0 * k * tau * C_A_in
    c_ss = (-1.0 + math.sqrt(discriminant)) / (2.0 * k * tau)
    return max(0.0, c_ss)


def calculate_material_balance_residual(
    V: float, Q: float, C_A_in: float, C_A_val: float, kinetic_model: KineticModel
) -> float:
    """Material balance residual: (Q/V)*(C_A_in - C_A_val) + r_A(C_A_val)."""
    rate = kinetic_model.reaction_rate(C_A_val)
    convection = (Q / V) * (C_A_in - C_A_val)
    return convection + rate


def solve_steady_state(
    V: float,
    Q: float,
    C_A_in: float,
    order: int,
    k: float,
    residual_tolerance: float = 1e-9,
) -> SteadyStateResult:
    """Solve steady state for zero, first, or second-order CSTR reaction."""
    validate_finite_positive("V", V)
    validate_finite_positive("Q", Q)
    validate_finite_nonnegative("C_A_in", C_A_in)
    validate_finite_nonnegative("k", k)

    kinetic_model = KineticModel(order=order, k=k)
    tau = V / Q

    if order == 0:
        c_ss = calculate_steady_state_zero_order(V, Q, C_A_in, k)
    elif order == 1:
        c_ss = C_A_in / (1.0 + k * tau)
    elif order == 2:
        c_ss = calculate_steady_state_second_order(V, Q, C_A_in, k)
    else:
        raise ValueError(f"Unsupported reaction order: {order}")

    # Conversion
    if C_A_in > 0.0:
        conversion = max(0.0, min(1.0, (C_A_in - c_ss) / C_A_in))
    else:
        conversion = None

    rate_ss = kinetic_model.reaction_rate(c_ss)
    residual = calculate_material_balance_residual(V, Q, C_A_in, c_ss, kinetic_model)

    diagnostics = {
        "material_balance_closed": abs(residual) <= residual_tolerance,
        "residual_absolute": abs(residual),
        "residual_tolerance": residual_tolerance,
    }

    units = {
        "V": "L",
        "Q": "L/min",
        "C_A_in": "mol/L",
        "k": kinetic_model.k_unit,
        "tau": "min",
        "C_A_ss": "mol/L",
        "conversion": "fraction [0, 1]",
        "reaction_rate_ss": "mol/(L*min)",
        "residual": "mol/(L*min)",
    }

    return SteadyStateResult(
        order=order,
        k=k,
        k_unit=kinetic_model.k_unit,
        tau=tau,
        C_A_ss=c_ss,
        conversion=conversion,
        reaction_rate_ss=rate_ss,
        residual=residual,
        model_identifier=f"isothermal_cstr_order_{order}",
        units=units,
        diagnostics=diagnostics,
    )
