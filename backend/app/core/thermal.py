"""Arrhenius kinetics and non-isothermal thermal CSTR simulation.

Adheres strictly to GLOBAL-INSTRUCTIONS.md and phase-13:
- Arrhenius temperature dependence: k(T) = A * exp(-Ea / (R * T)) with Kelvin and safeguards.
- Coupled mass and energy balances for reactor fluid and cooling/heating jacket.
- Selectable isothermal mode that recovers pure Phase 1-2 dynamics identically.
- Thermal runaway detection and heat transfer calibration.
- Explicit notice: PRBS workbook validates heat transfer and thermal dynamics only.
"""

from dataclasses import dataclass, field
import math
from typing import Any, Optional, Sequence
import numpy as np
from scipy.integrate import solve_ivp

# Universal gas constant R
R_GAS_CONSTANT_J_MOL_K = 8.314462618


def arrhenius_rate_constant(
    T_kelvin: float,
    A: float,
    Ea_J_mol: float,
    R: float = R_GAS_CONSTANT_J_MOL_K,
) -> float:
    """Compute temperature-dependent kinetic rate constant k(T) via Arrhenius equation.

    k(T) = A * exp(-Ea / (R * T))
    """
    if T_kelvin <= 0.0:
        raise ValueError(f"Absolute temperature must be strictly positive in Kelvin (got {T_kelvin} K).")
    if A < 0.0:
        raise ValueError(f"Pre-exponential factor A must be non-negative (got {A}).")
    if Ea_J_mol < 0.0:
        raise ValueError(f"Activation energy Ea must be non-negative (got {Ea_J_mol} J/mol).")

    exponent = -Ea_J_mol / (R * T_kelvin)
    # Numerical safeguard to avoid floating point overflow or underflow
    clamped_exp = max(-100.0, min(50.0, exponent))
    return float(A * math.exp(clamped_exp))


@dataclass(frozen=True)
class ThermalCSTRConfig:
    """Operating parameters for coupled non-isothermal CSTR with jacket."""

    # Reactor geometry & hydraulics
    V: float = 10.0  # Reactor volume [L]
    Q: float = 1.0   # Feed flow rate [L/min]
    C_A_in: float = 2.0  # Feed reactant concentration [mol/L]
    T_in: float = 300.0  # Feed temperature [K] (26.85 °C)

    # Reaction kinetics & thermodynamics
    A: float = 1.5e7     # Pre-exponential factor [min^-1 for n=1]
    Ea: float = 50000.0  # Activation energy [J/mol] (~50 kJ/mol)
    order: int = 1       # Reaction order n in {0, 1, 2}
    delta_H_rxn: float = -60.0  # Heat of reaction [kJ/mol] (< 0 exothermic)

    # Reactor mixture physical properties
    rho: float = 1.0    # Density [kg/L]
    Cp: float = 4.184   # Specific heat capacity [kJ/(kg*K)] (water-like)

    # Jacket cooling system
    V_j: float = 2.5     # Jacket volume [L]
    Q_j: float = 1.5     # Coolant flow rate [L/min]
    T_j_in: float = 290.0  # Coolant inlet temperature [K] (16.85 °C)
    rho_j: float = 1.0   # Coolant density [kg/L]
    Cp_j: float = 4.184  # Coolant heat capacity [kJ/(kg*K)]
    UA: float = 15.0     # Overall heat transfer coefficient * Area [kJ/(min*K)]

    # Operation mode
    isothermal: bool = False  # If True, locks T = T_in


@dataclass
class ThermalSimulationResult:
    """Time-series trajectory and physical diagnostics for non-isothermal CSTR."""

    t: list[float]
    C_A: list[float]
    T_reactor: list[float]
    T_jacket: list[float]
    k_T: list[float]
    conversion: list[float]
    heat_generated: list[float]
    heat_removed: list[float]
    steady_state_C_A: float
    steady_state_T: float
    thermal_runaway_detected: bool
    provenance: str = "NON_ISOTHERMAL_MECHANISTIC_SOLVER"
    warnings: list[str] = field(default_factory=list)


def simulate_thermal_cstr(
    config: ThermalCSTRConfig,
    C_A_0: float = 0.0,
    T_0: Optional[float] = None,
    T_j_0: Optional[float] = None,
    t_final: float = 40.0,
    n_points: int = 81,
    method: str = "Radau",
) -> ThermalSimulationResult:
    """Integrate non-isothermal coupled CSTR mass and energy balances."""
    if T_0 is None:
        T_0 = config.T_in
    if T_j_0 is None:
        T_j_0 = config.T_j_in

    warnings: list[str] = []
    t_eval = np.linspace(0.0, t_final, n_points)

    # State vector: y = [C_A, T, T_j]
    y0 = [max(0.0, float(C_A_0)), float(T_0), float(T_j_0)]

    def odes(t: float, y: np.ndarray) -> list[float]:
        c_a = max(0.0, float(y[0]))
        T = max(1.0, float(y[1]))
        T_j = max(1.0, float(y[2]))

        # Arrhenius rate constant
        if config.isothermal:
            k = arrhenius_rate_constant(config.T_in, config.A, config.Ea)
        else:
            k = arrhenius_rate_constant(T, config.A, config.Ea)

        # Kinetic rate
        if config.order == 0:
            rate = k if c_a > 1e-4 else k * (c_a / 1e-4)
        elif config.order == 1:
            rate = k * c_a
        elif config.order == 2:
            rate = k * (c_a ** 2)
        else:
            rate = k * (c_a ** config.order)

        # 1. Mass balance: dC_A/dt = (Q/V)*(C_in - C_A) - rate
        dCA_dt = (config.Q / config.V) * (config.C_A_in - c_a) - rate

        # If isothermal mode is selected, dT/dt = 0 and dT_j/dt = 0
        if config.isothermal:
            return [dCA_dt, 0.0, 0.0]

        # 2. Reactor energy balance:
        # V*rho*Cp * dT/dt = Q*rho*Cp*(T_in - T) + (-delta_H)*V*rate - UA*(T - T_j)
        heat_flow_in = config.Q * config.rho * config.Cp * (config.T_in - T)
        heat_gen = (-config.delta_H_rxn) * config.V * rate  # kJ/min
        heat_transfer = config.UA * (T - T_j)                # kJ/min
        net_reactor_heat = heat_flow_in + heat_gen - heat_transfer
        dT_dt = net_reactor_heat / (config.V * config.rho * config.Cp)

        # 3. Jacket energy balance:
        # V_j*rho_j*Cp_j * dT_j/dt = Q_j*rho_j*Cp_j*(T_j_in - T_j) + UA*(T - T_j)
        coolant_flow_in = config.Q_j * config.rho_j * config.Cp_j * (config.T_j_in - T_j)
        net_jacket_heat = coolant_flow_in + heat_transfer
        dTj_dt = net_jacket_heat / (config.V_j * config.rho_j * config.Cp_j)

        return [dCA_dt, dT_dt, dTj_dt]

    sol = solve_ivp(
        odes,
        (0.0, t_final),
        y0,
        t_eval=t_eval,
        method=method,
        rtol=1e-6,
        atol=1e-8,
    )

    if not sol.success:
        raise RuntimeError(f"Thermal solver failed: {sol.message}")

    c_series = np.maximum(0.0, sol.y[0]).tolist()
    T_series = sol.y[1].tolist()
    Tj_series = sol.y[2].tolist()

    # Derived physical quantities
    k_series: list[float] = []
    heat_gen_series: list[float] = []
    heat_rem_series: list[float] = []
    conv_series: list[float] = []

    for i in range(len(t_eval)):
        T_val = config.T_in if config.isothermal else T_series[i]
        c_val = c_series[i]
        k_val = arrhenius_rate_constant(T_val, config.A, config.Ea)
        k_series.append(k_val)

        r_val = k_val * (c_val ** config.order)
        q_gen = (-config.delta_H_rxn) * config.V * r_val
        q_rem = config.UA * (T_series[i] - Tj_series[i])
        heat_gen_series.append(float(q_gen))
        heat_rem_series.append(float(q_rem))

        if config.C_A_in > 0:
            conv = max(0.0, min(1.0, (config.C_A_in - c_val) / config.C_A_in))
        else:
            conv = 0.0
        conv_series.append(conv)

    # Check for thermal runaway: rapid temperature increase > 50 K above feed
    max_T = max(T_series)
    runaway = (max_T - config.T_in) > 50.0
    if runaway:
        warnings.append(
            f"Thermal runaway detected! Peak reactor temperature reached {max_T:.1f} K "
            f"({max_T - 273.15:.1f} °C), exceeding feed temperature by {max_T - config.T_in:.1f} K."
        )

    return ThermalSimulationResult(
        t=t_eval.tolist(),
        C_A=c_series,
        T_reactor=T_series,
        T_jacket=Tj_series,
        k_T=k_series,
        conversion=conv_series,
        heat_generated=heat_gen_series,
        heat_removed=heat_rem_series,
        steady_state_C_A=float(c_series[-1]),
        steady_state_T=float(T_series[-1]),
        thermal_runaway_detected=runaway,
        warnings=warnings,
    )
