"""Analytical solutions for first-order isothermal CSTR benchmark comparisons.

Transient solution for constant inputs:
    dC_A/dt = (Q/V)*(C_A_in - C_A) - k*C_A
    Let lambda = Q/V + k = 1/tau + k
    dC_A/dt + lambda * C_A = (Q/V) * C_A_in
    Integrating factor: exp(lambda * t)
    C_A(t) = C_A_ss + (C_A_0 - C_A_ss) * exp(-lambda * t)
"""

import math
from typing import Sequence, Union
import numpy as np


def first_order_steady_state_analytical(V: float, Q: float, C_A_in: float, k: float) -> float:
    """Exact analytical steady-state concentration for first-order isothermal CSTR."""
    if V <= 0.0 or Q <= 0.0:
        raise ValueError("V and Q must be strictly positive.")
    if C_A_in < 0.0 or k < 0.0:
        raise ValueError("C_A_in and k must be non-negative.")

    tau = V / Q
    return C_A_in / (1.0 + k * tau)


def first_order_dynamic_analytical_point(
    t: float,
    C_A_0: float,
    V: float,
    Q: float,
    C_A_in: float,
    k: float,
) -> float:
    """Exact analytical concentration at time t >= 0 for constant inputs."""
    if t < 0.0:
        raise ValueError(f"Time t must be non-negative, got {t}.")
    if C_A_0 < 0.0:
        raise ValueError(f"Initial concentration C_A_0 must be non-negative, got {C_A_0}.")

    c_ss = first_order_steady_state_analytical(V, Q, C_A_in, k)
    lam = (Q / V) + k
    return c_ss + (C_A_0 - c_ss) * math.exp(-lam * t)


def first_order_dynamic_analytical_trajectory(
    t_points: Union[Sequence[float], np.ndarray],
    C_A_0: float,
    V: float,
    Q: float,
    C_A_in: float,
    k: float,
) -> np.ndarray:
    """Calculate exact analytical concentration trajectory across an array of time points."""
    t_arr = np.asarray(t_points, dtype=np.float64)
    if np.any(t_arr < 0.0):
        raise ValueError("All time points in t_points must be non-negative.")

    c_ss = first_order_steady_state_analytical(V, Q, C_A_in, k)
    lam = (Q / V) + k
    return c_ss + (C_A_0 - c_ss) * np.exp(-lam * t_arr)
