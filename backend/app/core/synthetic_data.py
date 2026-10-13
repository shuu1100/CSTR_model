"""Mechanistic synthetic data generator for CSTR machine learning workflows.

Adheres strictly to GLOBAL-INSTRUCTIONS.md, phase-08, and phase-08A protocols:
- Bounded parameter spaces and Latin Hypercube Sampling (SciPy QMC).
- Exact recording of all parameters, units, seeds, solver settings, and noise configurations.
- Deterministic inclusion of canonical oracles and physical edge cases.
- Generation of task-separated datasets (steady-state, dynamic trajectories, parameter estimation).
- Explicit synthetic provenance labeling on every record.
"""

from dataclasses import asdict, dataclass, field
import uuid
import math
from typing import Any, Literal, Optional
import numpy as np
from scipy.stats import qmc

from backend.app.core.analytical import first_order_dynamic_analytical_trajectory
from backend.app.core.dynamic_solver import StepChange, simulate_dynamic_cstr
from backend.app.core.kinetics import RATE_CONSTANT_CANONICAL_UNITS, KineticModel
from backend.app.core.steady_state import solve_steady_state

CODE_VERSION = "0.1.0-phase08"


@dataclass(frozen=True)
class ParameterBounds:
    """Bounded operational ranges for CSTR parameters."""

    V_min: float = 1.0
    V_max: float = 50.0  # Liters
    Q_min: float = 0.1
    Q_max: float = 5.0  # L/min
    C_in_min: float = 0.1
    C_in_max: float = 5.0  # mol/L
    C_0_min: float = 0.0
    C_0_max: float = 5.0  # mol/L

    # Kinetic rate constants per order
    k_ranges: dict[int, tuple[float, float]] = field(
        default_factory=lambda: {
            0: (0.005, 0.20),  # mol/(L*min)
            1: (0.01, 2.00),   # min^-1
            2: (0.01, 1.00),   # L/(mol*min)
        }
    )


@dataclass
class SteadyStateSample:
    """Record for steady-state regression task."""

    sample_id: str
    order: int
    V: float
    Q: float
    k: float
    C_A_in: float
    tau: float
    damkohler: float
    C_A_ss: float
    conversion: Optional[float]
    reaction_rate_ss: float
    residual: float
    is_edge_case: bool
    edge_case_type: Optional[str] = None
    provenance: str = "SYNTHETIC_MECHANISTIC_SOLVER"


@dataclass
class DynamicTrajectoryMetadata:
    """Metadata describing a single transient dynamic simulation trajectory."""

    trajectory_id: str
    order: int
    V: float
    Q: float
    k: float
    k_unit: str
    C_A_in: float
    C_A_0: float
    tau_initial: float
    t_final: float
    n_points: int
    solver_method: str
    rtol: float
    atol: float
    has_step_change: bool
    step_time: Optional[float]
    step_C_in_new: Optional[float]
    step_Q_new: Optional[float]
    noise_sigma: float
    random_seed: int
    code_version: str
    is_edge_case: bool
    edge_case_type: Optional[str] = None
    provenance: str = "SYNTHETIC_MECHANISTIC_SOLVER"


@dataclass
class FaultDiagnosisSample:
    """Record for fault diagnosis and anomaly detection task."""

    sample_id: str
    trajectory_id: str
    time_min: float
    C_A_measured: float
    C_A_true: float
    Q: float
    V: float
    C_A_in: float
    k: float
    order: int
    fault_type: str  # "normal", "feed_loss_step", "concentration_shock", "sensor_drift", "sensor_stuck"
    fault_onset_time: Optional[float]
    severity: float
    is_fault: bool
    provenance: str = "SYNTHETIC_MECHANISTIC_SOLVER"


@dataclass
class DynamicTrajectoryData:
    """Full time-series data for a dynamic trajectory."""

    metadata: DynamicTrajectoryMetadata
    t: list[float]
    C_A_clean: list[float]
    C_A_noisy: list[float]
    conversion: Optional[list[Optional[float]]]
    reaction_rate: list[float]


def sample_parameters_lhs(
    n_samples: int,
    order: int = 1,
    bounds: Optional[ParameterBounds] = None,
    seed: int = 42,
) -> list[dict[str, float]]:
    """Sample continuous parameters (V, Q, k, C_A_in, C_A_0) via Latin Hypercube Sampling."""
    if bounds is None:
        bounds = ParameterBounds()

    k_min, k_max = bounds.k_ranges[order]

    # 5 continuous parameters: [V, Q, k, C_A_in, C_A_0]
    sampler = qmc.LatinHypercube(d=5, seed=seed)
    lhs_unit = sampler.random(n=n_samples)

    lower_bounds = [bounds.V_min, bounds.Q_min, k_min, bounds.C_in_min, bounds.C_0_min]
    upper_bounds = [bounds.V_max, bounds.Q_max, k_max, bounds.C_in_max, bounds.C_0_max]

    scaled = qmc.scale(lhs_unit, lower_bounds, upper_bounds)

    samples = []
    for row in scaled:
        samples.append({
            "V": float(row[0]),
            "Q": float(row[1]),
            "k": float(row[2]),
            "C_A_in": float(row[3]),
            "C_A_0": float(row[4]),
            "order": order,
        })
    return samples


def generate_edge_cases(bounds: Optional[ParameterBounds] = None) -> list[dict[str, Any]]:
    """Generate physically critical boundary and edge cases."""
    if bounds is None:
        bounds = ParameterBounds()

    edge_cases = [
        # 1. Canonical Validation Oracle (First Order)
        {
            "V": 10.0,
            "Q": 1.0,
            "k": 0.15,
            "C_A_in": 2.0,
            "C_A_0": 0.0,
            "order": 1,
            "is_edge_case": True,
            "edge_case_type": "canonical_oracle",
        },
        # 2. Zero Inlet Concentration (Conversion Guard Check)
        {
            "V": 10.0,
            "Q": 1.0,
            "k": 0.15,
            "C_A_in": 0.0,
            "C_A_0": 1.0,
            "order": 1,
            "is_edge_case": True,
            "edge_case_type": "zero_inlet_concentration",
        },
        # 3. Zero Initial Concentration (Pure filling/washout)
        {
            "V": 20.0,
            "Q": 2.0,
            "k": 0.10,
            "C_A_in": 3.0,
            "C_A_0": 0.0,
            "order": 1,
            "is_edge_case": True,
            "edge_case_type": "zero_initial_concentration",
        },
        # 4. Fast Kinetics / High Damkohler Number (k*tau >> 1)
        {
            "V": 40.0,
            "Q": 0.5,
            "k": 1.80,  # tau=80 min, Da = 144 -> X > 0.99
            "C_A_in": 4.0,
            "C_A_0": 0.5,
            "order": 1,
            "is_edge_case": True,
            "edge_case_type": "fast_kinetics_near_complete_conversion",
        },
        # 5. Slow Kinetics / Low Damkohler Number (k*tau << 1)
        {
            "V": 2.0,
            "Q": 4.0,
            "k": 0.01,  # tau=0.5 min, Da = 0.005 -> X < 0.01
            "C_A_in": 2.0,
            "C_A_0": 1.0,
            "order": 1,
            "is_edge_case": True,
            "edge_case_type": "slow_kinetics_near_zero_conversion",
        },
        # 6. Zero Order Depletion Boundary
        {
            "V": 10.0,
            "Q": 1.0,
            "k": 0.15,
            "C_A_in": 1.0,  # k*tau = 1.5 > C_in -> Reactant fully depletes
            "C_A_0": 0.5,
            "order": 0,
            "is_edge_case": True,
            "edge_case_type": "zero_order_complete_depletion",
        },
        # 7. Second Order High Concentration
        {
            "V": 15.0,
            "Q": 1.5,
            "k": 0.50,
            "C_A_in": 5.0,
            "C_A_0": 0.0,
            "order": 2,
            "is_edge_case": True,
            "edge_case_type": "second_order_high_concentration",
        },
    ]
    return edge_cases


def generate_steady_state_dataset(
    n_samples_per_order: int = 150,
    seed: int = 101,
) -> list[SteadyStateSample]:
    """Generate a steady-state regression dataset across orders n in {0, 1, 2}."""
    records: list[SteadyStateSample] = []
    bounds = ParameterBounds()

    # 1. Add Edge Cases
    edge_cases = generate_edge_cases(bounds)
    for ec in edge_cases:
        res = solve_steady_state(
            V=ec["V"],
            Q=ec["Q"],
            C_A_in=ec["C_A_in"],
            order=ec["order"],
            k=ec["k"],
        )
        sample = SteadyStateSample(
            sample_id=f"ss-edge-{uuid.uuid4().hex[:8]}",
            order=ec["order"],
            V=ec["V"],
            Q=ec["Q"],
            k=ec["k"],
            C_A_in=ec["C_A_in"],
            tau=res.tau,
            damkohler=ec["k"] * res.tau,
            C_A_ss=res.C_A_ss,
            conversion=res.conversion,
            reaction_rate_ss=res.reaction_rate_ss,
            residual=res.residual,
            is_edge_case=True,
            edge_case_type=ec["edge_case_type"],
        )
        records.append(sample)

    # 2. Add LHS Samples across each order
    for ord_idx in (0, 1, 2):
        lhs_params = sample_parameters_lhs(
            n_samples=n_samples_per_order,
            order=ord_idx,
            bounds=bounds,
            seed=seed + ord_idx * 17,
        )
        for p in lhs_params:
            res = solve_steady_state(
                V=p["V"],
                Q=p["Q"],
                C_A_in=p["C_A_in"],
                order=p["order"],
                k=p["k"],
            )
            sample = SteadyStateSample(
                sample_id=f"ss-lhs-ord{ord_idx}-{uuid.uuid4().hex[:8]}",
                order=ord_idx,
                V=p["V"],
                Q=p["Q"],
                k=p["k"],
                C_A_in=p["C_A_in"],
                tau=res.tau,
                damkohler=p["k"] * res.tau,
                C_A_ss=res.C_A_ss,
                conversion=res.conversion,
                reaction_rate_ss=res.reaction_rate_ss,
                residual=res.residual,
                is_edge_case=False,
            )
            records.append(sample)

    return records


def generate_dynamic_trajectories(
    n_trajectories: int = 120,
    n_points_per_traj: int = 101,
    noise_sigma: float = 0.015,
    step_change_fraction: float = 0.25,
    seed: int = 202,
) -> list[DynamicTrajectoryData]:
    """Generate reproducible dynamic transient trajectories with optional step changes and noise."""
    trajectories: list[DynamicTrajectoryData] = []
    rng = np.random.default_rng(seed)
    bounds = ParameterBounds()

    # 1. Edge cases trajectories
    edge_cases = generate_edge_cases(bounds)
    for idx, ec in enumerate(edge_cases):
        t_id = f"traj-edge-{idx:03d}-{uuid.uuid4().hex[:6]}"
        tau = ec["V"] / ec["Q"]
        t_final = min(100.0, max(20.0, 5.0 * tau))

        res = simulate_dynamic_cstr(
            C_A_0=ec["C_A_0"],
            C_A_in=ec["C_A_in"],
            V=ec["V"],
            Q=ec["Q"],
            order=ec["order"],
            k=ec["k"],
            t_final=t_final,
            n_points=n_points_per_traj,
            method="RK45",
        )

        # Apply measurement noise (independent per trajectory)
        traj_rng = np.random.default_rng(seed + 1000 + idx)
        noise = traj_rng.normal(0.0, noise_sigma, size=len(res.C_A))
        c_noisy = np.maximum(0.0, np.array(res.C_A) + noise).tolist()

        k_unit = RATE_CONSTANT_CANONICAL_UNITS.get(ec["order"], "min^-1")

        meta = DynamicTrajectoryMetadata(
            trajectory_id=t_id,
            order=ec["order"],
            V=ec["V"],
            Q=ec["Q"],
            k=ec["k"],
            k_unit=k_unit,
            C_A_in=ec["C_A_in"],
            C_A_0=ec["C_A_0"],
            tau_initial=tau,
            t_final=t_final,
            n_points=n_points_per_traj,
            solver_method=res.solver_method,
            rtol=res.tolerances["rtol"],
            atol=res.tolerances["atol"],
            has_step_change=False,
            step_time=None,
            step_C_in_new=None,
            step_Q_new=None,
            noise_sigma=noise_sigma,
            random_seed=seed + 1000 + idx,
            code_version=CODE_VERSION,
            is_edge_case=True,
            edge_case_type=ec["edge_case_type"],
        )

        trajectories.append(
            DynamicTrajectoryData(
                metadata=meta,
                t=res.t,
                C_A_clean=res.C_A,
                C_A_noisy=[float(x) for x in c_noisy],
                conversion=res.conversion,
                reaction_rate=res.reaction_rate,
            )
        )

    # 2. Sampled LHS trajectories across orders
    n_per_order = n_trajectories // 3
    for ord_idx in (0, 1, 2):
        lhs_samples = sample_parameters_lhs(
            n_samples=n_per_order,
            order=ord_idx,
            bounds=bounds,
            seed=seed + ord_idx * 31,
        )

        for s_idx, p in enumerate(lhs_samples):
            t_id = f"traj-ord{ord_idx}-{s_idx:03d}-{uuid.uuid4().hex[:6]}"
            tau = p["V"] / p["Q"]
            t_final = min(120.0, max(25.0, 5.0 * tau))

            # Step change decision
            has_step = bool(rng.random() < step_change_fraction)
            step_obj: Optional[StepChange] = None
            step_time: Optional[float] = None
            step_cin_new: Optional[float] = None
            step_q_new: Optional[float] = None

            if has_step:
                step_time = float(rng.uniform(0.25 * t_final, 0.65 * t_final))
                # 50% chance inlet conc jump, 50% chance flow rate jump
                if rng.random() < 0.5:
                    step_cin_new = float(rng.uniform(bounds.C_in_min, bounds.C_in_max))
                    step_obj = StepChange(time=step_time, C_A_in_new=step_cin_new)
                else:
                    step_q_new = float(rng.uniform(bounds.Q_min, bounds.Q_max))
                    step_obj = StepChange(time=step_time, Q_new=step_q_new)

            res = simulate_dynamic_cstr(
                C_A_0=p["C_A_0"],
                C_A_in=p["C_A_in"],
                V=p["V"],
                Q=p["Q"],
                order=ord_idx,
                k=p["k"],
                t_final=t_final,
                n_points=n_points_per_traj,
                method="RK45",
                step_change=step_obj,
            )

            # Trajectory measurement noise
            traj_seed = int(seed + ord_idx * 500 + s_idx)
            traj_rng = np.random.default_rng(traj_seed)
            noise = traj_rng.normal(0.0, noise_sigma, size=len(res.C_A))
            c_noisy = np.maximum(0.0, np.array(res.C_A) + noise).tolist()

            k_unit = RATE_CONSTANT_CANONICAL_UNITS.get(ord_idx, "min^-1")

            meta = DynamicTrajectoryMetadata(
                trajectory_id=t_id,
                order=ord_idx,
                V=p["V"],
                Q=p["Q"],
                k=p["k"],
                k_unit=k_unit,
                C_A_in=p["C_A_in"],
                C_A_0=p["C_A_0"],
                tau_initial=tau,
                t_final=t_final,
                n_points=n_points_per_traj,
                solver_method=res.solver_method,
                rtol=res.tolerances["rtol"],
                atol=res.tolerances["atol"],
                has_step_change=has_step,
                step_time=step_time,
                step_C_in_new=step_cin_new,
                step_Q_new=step_q_new,
                noise_sigma=noise_sigma,
                random_seed=traj_seed,
                code_version=CODE_VERSION,
                is_edge_case=False,
            )

            trajectories.append(
                DynamicTrajectoryData(
                    metadata=meta,
                    t=res.t,
                    C_A_clean=res.C_A,
                    C_A_noisy=[float(x) for x in c_noisy],
                    conversion=res.conversion,
                    reaction_rate=res.reaction_rate,
                )
            )

    return trajectories


def generate_fault_diagnosis_dataset(
    n_trajectories: int = 40,
    n_points_per_traj: int = 51,
    noise_sigma: float = 0.015,
    seed: int = 404,
) -> list[FaultDiagnosisSample]:
    """Generate a fault diagnosis and anomaly detection dataset.

    Includes 5 distinct operating conditions:
    1. 'normal': Nominal operation without disturbances.
    2. 'feed_loss_step': Abrupt reduction in flow rate Q (valve or pump failure).
    3. 'concentration_shock': Sudden shift in feed concentration C_A,in.
    4. 'sensor_drift': Linear sensor drift ramp after onset time.
    5. 'sensor_stuck': Output freeze / stuck sensor measurement after onset time.
    """
    records: list[FaultDiagnosisSample] = []
    rng = np.random.default_rng(seed)

    fault_classes = [
        "normal",
        "feed_loss_step",
        "concentration_shock",
        "sensor_drift",
        "sensor_stuck",
    ]

    trajs_per_fault = max(1, n_trajectories // len(fault_classes))
    traj_counter = 0

    for fault_type in fault_classes:
        for _ in range(trajs_per_fault):
            traj_counter += 1
            traj_id = f"fault-{fault_type[:6]}-{traj_counter:03d}-{uuid.uuid4().hex[:6]}"

            # Base parameters
            V = float(rng.uniform(5.0, 25.0))
            Q_base = float(rng.uniform(0.5, 2.5))
            C_in_base = float(rng.uniform(1.0, 3.0))
            C0 = float(rng.uniform(0.1, 1.0))
            k = float(rng.uniform(0.08, 0.35))
            order = 1
            tau = V / Q_base
            t_final = 5.0 * tau

            step_change: Optional[StepChange] = None
            t_onset: Optional[float] = None
            severity = 0.0

            if fault_type != "normal":
                t_onset = float(rng.uniform(0.30 * t_final, 0.60 * t_final))

            if fault_type == "feed_loss_step":
                severity = float(rng.uniform(0.40, 0.80))  # 40% to 80% loss of flow
                Q_new = max(0.05, Q_base * (1.0 - severity))
                step_change = StepChange(time=t_onset, Q_new=Q_new)
            elif fault_type == "concentration_shock":
                severity = float(rng.uniform(0.50, 1.50))  # Shock multiplier
                C_in_new = float(np.clip(C_in_base * (1.0 + severity), 0.1, 8.0))
                step_change = StepChange(time=t_onset, C_A_in_new=C_in_new)
            elif fault_type in ("sensor_drift", "sensor_stuck"):
                severity = float(rng.uniform(0.20, 0.80))

            sim = simulate_dynamic_cstr(
                C_A_0=C0,
                C_A_in=C_in_base,
                V=V,
                Q=Q_base,
                order=order,
                k=k,
                t_final=t_final,
                n_points=n_points_per_traj,
                method="RK45",
                step_change=step_change,
            )

            # Generate sensor readings with realistic noise and possible sensor faults
            noise = rng.normal(0.0, noise_sigma, size=len(sim.C_A))
            stuck_val: Optional[float] = None

            for idx, t_val in enumerate(sim.t):
                c_true = float(sim.C_A[idx])
                c_meas = max(0.0, c_true + float(noise[idx]))
                is_active_fault = False

                if t_onset is not None and t_val >= t_onset:
                    is_active_fault = True
                    if fault_type == "sensor_drift":
                        dt_fault = t_val - t_onset
                        c_meas = max(0.0, c_meas + severity * (dt_fault / t_final) * c_true)
                    elif fault_type == "sensor_stuck":
                        if stuck_val is None:
                            stuck_val = c_meas
                        c_meas = stuck_val

                # Active flow rate at this time
                current_Q = Q_base
                if step_change and step_change.Q_new is not None and t_val >= step_change.time:
                    current_Q = step_change.Q_new

                current_C_in = C_in_base
                if step_change and step_change.C_A_in_new is not None and t_val >= step_change.time:
                    current_C_in = step_change.C_A_in_new

                sample_id = f"fs-{traj_id[:12]}-{idx:03d}"
                records.append(
                    FaultDiagnosisSample(
                        sample_id=sample_id,
                        trajectory_id=traj_id,
                        time_min=float(t_val),
                        C_A_measured=float(c_meas),
                        C_A_true=float(c_true),
                        Q=float(current_Q),
                        V=float(V),
                        C_A_in=float(current_C_in),
                        k=float(k),
                        order=order,
                        fault_type=fault_type,
                        fault_onset_time=t_onset,
                        severity=float(severity),
                        is_fault=is_active_fault,
                    )
                )

    return records
