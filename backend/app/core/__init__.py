"""Scientific core: kinetics, solvers, unit conversions, balances."""

from backend.app.core.analytical import (
    first_order_dynamic_analytical_point,
    first_order_dynamic_analytical_trajectory,
    first_order_steady_state_analytical,
)
from backend.app.core.dynamic_solver import (
    DynamicSimulationResult,
    StepChange,
    cstr_ode_rhs,
    simulate_dynamic_cstr,
)
from backend.app.core.isothermal_first_order import (
    SteadyStateFirstOrderResult,
    material_balance_residual,
    reaction_rate_first_order,
    residence_time,
    solve_isothermal_first_order_steady_state,
    steady_state_concentration,
    steady_state_conversion,
    steady_state_material_balance_residual,
)
from backend.app.core.kinetics import (
    RATE_CONSTANT_CANONICAL_UNITS,
    KineticModel,
    ReactionOrder,
    calculate_reaction_rate,
)
from backend.app.core.steady_state import (
    SteadyStateResult,
    calculate_steady_state_second_order,
    calculate_steady_state_zero_order,
    solve_steady_state,
)
from backend.app.core.units import (
    convert_concentration,
    convert_first_order_rate_constant,
    convert_flow_rate,
    convert_time,
    convert_volume,
)

from backend.app.core.sweeps import (
    SWEEP_VARIABLE_LABELS,
    Sweep1DResult,
    Sweep2DResult,
    SweepPoint1D,
    SweepVariable,
    compute_1d_parameter_sweep,
    compute_2d_parameter_sweep,
)
from backend.app.core.parameter_estimation import (
    KineticFitResult,
    ParameterConfidenceInterval,
    fit_dynamic_kinetics,
    fit_steady_state_kinetics,
)
from backend.app.core.synthetic_data import (
    DynamicTrajectoryData,
    DynamicTrajectoryMetadata,
    ParameterBounds,
    SteadyStateSample,
    generate_dynamic_trajectories,
    generate_edge_cases,
    generate_steady_state_dataset,
    sample_parameters_lhs,
)
from backend.app.core.splitting import (
    SplitPartition,
    build_split_manifest,
    fit_scaler_train_only,
    split_trajectories_by_id,
)
from backend.app.core.thermal import (
    ThermalCSTRConfig,
    ThermalSimulationResult,
    arrhenius_rate_constant,
    simulate_thermal_cstr,
)

__all__ = [
    # Units
    "convert_volume",
    "convert_flow_rate",
    "convert_concentration",
    "convert_time",
    "convert_first_order_rate_constant",
    # Phase 1 First-Order Core
    "SteadyStateFirstOrderResult",
    "residence_time",
    "reaction_rate_first_order",
    "steady_state_concentration",
    "steady_state_conversion",
    "steady_state_material_balance_residual",
    "material_balance_residual",
    "solve_isothermal_first_order_steady_state",
    # Kinetics
    "ReactionOrder",
    "KineticModel",
    "RATE_CONSTANT_CANONICAL_UNITS",
    "calculate_reaction_rate",
    # Analytical References
    "first_order_steady_state_analytical",
    "first_order_dynamic_analytical_point",
    "first_order_dynamic_analytical_trajectory",
    # Unified Steady State
    "SteadyStateResult",
    "calculate_steady_state_zero_order",
    "calculate_steady_state_second_order",
    "solve_steady_state",
    # Dynamic ODE Solver
    "StepChange",
    "DynamicSimulationResult",
    "cstr_ode_rhs",
    "simulate_dynamic_cstr",
    # Parameter Sweeps & Sensitivity
    "SweepVariable",
    "SWEEP_VARIABLE_LABELS",
    "SweepPoint1D",
    "Sweep1DResult",
    "Sweep2DResult",
    "compute_1d_parameter_sweep",
    "compute_2d_parameter_sweep",
    # Parameter Estimation
    "KineticFitResult",
    "ParameterConfidenceInterval",
    "fit_dynamic_kinetics",
    "fit_steady_state_kinetics",
    # Synthetic Data & Splitting
    "ParameterBounds",
    "SteadyStateSample",
    "DynamicTrajectoryMetadata",
    "DynamicTrajectoryData",
    "sample_parameters_lhs",
    "generate_edge_cases",
    "generate_steady_state_dataset",
    "SplitPartition",
    "split_trajectories_by_id",
    "fit_scaler_train_only",
    "build_split_manifest",
    # Thermal & Arrhenius Core
    "arrhenius_rate_constant",
    "ThermalCSTRConfig",
    "ThermalSimulationResult",
    "simulate_thermal_cstr",
]


