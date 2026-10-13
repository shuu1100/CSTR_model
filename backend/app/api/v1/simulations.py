"""Endpoints for steady-state and dynamic CSTR simulations."""

from fastapi import APIRouter, HTTPException, status

from backend.app.core.dynamic_solver import StepChange, simulate_dynamic_cstr
from backend.app.core.steady_state import solve_steady_state
from backend.app.core.sweeps import (
    SweepVariable,
    compute_1d_parameter_sweep,
    compute_2d_parameter_sweep,
    compute_lhs_parameter_sweep,
)
from backend.app.core.thermal import ThermalCSTRConfig, simulate_thermal_cstr
from backend.app.schemas.simulation import (
    DynamicSimulationRequest,
    DynamicSimulationResponse,
    SolverDetails,
    SteadyStateOutputs,
    SteadyStateRequest,
    SteadyStateResponse,
    ThermalSimulationRequest,
    ThermalSimulationResponse,
)
from backend.app.schemas.sweep import (
    LHSSweepPointSchema,
    LHSSweepRequest,
    LHSSweepResponse,
    LocalSensitivitySchema,
    ParameterSweepRequest,
    ParameterSweepResponse,
    Sweep1DResponse,
    Sweep2DResponse,
    SweepPointSchema,
)

router = APIRouter(prefix="/simulations", tags=["Simulations"])


@router.post("/steady-state", response_model=SteadyStateResponse)
def compute_steady_state(request: SteadyStateRequest) -> SteadyStateResponse:
    """Calculate the steady-state state of an isothermal CSTR."""
    try:
        canonical_params = request.get_canonical_inputs()
        result = solve_steady_state(
            V=canonical_params["V"],
            Q=canonical_params["Q"],
            C_A_in=canonical_params["C_A_in"],
            order=canonical_params["order"],
            k=canonical_params["k"],
        )
    except (ValueError, TypeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    outputs = SteadyStateOutputs(
        tau=result.tau,
        C_A_ss=result.C_A_ss,
        conversion=result.conversion,
        reaction_rate_ss=result.reaction_rate_ss,
        residual=result.residual,
    )

    assumptions = [
        "Perfect mixing (spatially uniform concentration in vessel)",
        "Constant liquid volume and constant fluid density",
        "Equal inlet and outlet volumetric flow rates (Q_in = Q_out)",
        "Isothermal operation",
        f"Irreversible reaction with kinetic order n={request.order}",
    ]

    return SteadyStateResponse(
        model_id=result.model_identifier,
        normalized_inputs=canonical_params,
        outputs=outputs,
        units=result.units,
        assumptions=assumptions,
        diagnostics=result.diagnostics,
    )


@router.post("/dynamic", response_model=DynamicSimulationResponse)
def compute_dynamic_simulation(request: DynamicSimulationRequest) -> DynamicSimulationResponse:
    """Simulate transient concentration dynamics in an isothermal CSTR."""
    try:
        canonical_params = request.get_canonical_inputs()

        step_obj = None
        if canonical_params["step_change"] is not None:
            step_obj = StepChange(
                time=canonical_params["step_change"]["time"],
                C_A_in_new=canonical_params["step_change"]["C_A_in_new"],
                Q_new=canonical_params["step_change"]["Q_new"],
            )

        sim_res = simulate_dynamic_cstr(
            C_A_0=canonical_params["C_A_0"],
            C_A_in=canonical_params["C_A_in"],
            V=canonical_params["V"],
            Q=canonical_params["Q"],
            order=canonical_params["order"],
            k=canonical_params["k"],
            t_final=canonical_params["t_final"],
            n_points=canonical_params["n_points"],
            method=canonical_params["solver_method"],
            rtol=canonical_params["rtol"],
            atol=canonical_params["atol"],
            step_change=step_obj,
        )
    except (ValueError, TypeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    solver_details = SolverDetails(
        method=sim_res.solver_method,
        success=sim_res.success,
        status=sim_res.status,
        message=sim_res.message,
        tolerances=sim_res.tolerances,
    )

    assumptions = [
        "Unsteady-state species mole balance: dC_A/dt = (Q/V)*(C_in - C_A) + r_A",
        "Perfect mixing throughout the reactor volume",
        "Constant reactor volume and constant fluid density",
        "Isothermal operation",
        f"Reaction order n={request.order}",
    ]

    return DynamicSimulationResponse(
        model_id=f"dynamic_cstr_order_{request.order}",
        normalized_inputs=canonical_params,
        t=sim_res.t,
        C_A=sim_res.C_A,
        conversion=sim_res.conversion,
        reaction_rate=sim_res.reaction_rate,
        tau_initial=sim_res.tau_initial,
        C_A_ss_initial=sim_res.C_A_ss_initial,
        solver_details=solver_details,
        analytical_comparison=sim_res.analytical_comparison,
        step_change_applied=sim_res.step_change_applied,
        units=sim_res.units,
        assumptions=assumptions,
        warnings=sim_res.warnings,
    )


@router.post("/parameter-sweep", response_model=ParameterSweepResponse)
def compute_parameter_sweep(request: ParameterSweepRequest) -> ParameterSweepResponse:
    """Execute 1D or 2D parameter sweep and local sensitivity analysis."""
    try:
        if request.is_2d:
            # 2D surface parameter sweep
            res_2d = compute_2d_parameter_sweep(
                var_x=SweepVariable(request.variable),
                x_min=request.min_val,
                x_max=request.max_val,
                n_x=request.n_points,
                var_y=SweepVariable(request.variable_y),  # type: ignore[arg-type]
                y_min=request.min_val_y,  # type: ignore[arg-type]
                y_max=request.max_val_y,  # type: ignore[arg-type]
                n_y=request.n_points_y or 20,
                baseline_V=request.baseline_V,
                baseline_Q=request.baseline_Q,
                baseline_C_in=request.baseline_C_in,
                baseline_k=request.baseline_k,
                order=request.order,
            )
            return Sweep2DResponse(
                sweep_type="2D",
                var_x=res_2d.var_x,
                var_x_label=res_2d.var_x_label,
                var_x_unit=res_2d.var_x_unit,
                x_values=res_2d.x_values,
                var_y=res_2d.var_y,
                var_y_label=res_2d.var_y_label,
                var_y_unit=res_2d.var_y_unit,
                y_values=res_2d.y_values,
                fixed_parameters=res_2d.fixed_parameters,
                order=res_2d.order,
                conversion_grid=res_2d.conversion_grid,
                concentration_grid=res_2d.concentration_grid,
                tau_grid=res_2d.tau_grid,
                baseline_point=res_2d.baseline_point,
                trend_summary=res_2d.trend_summary,
                units=res_2d.units,
            )
        else:
            # 1D line parameter sweep
            res_1d = compute_1d_parameter_sweep(
                variable=SweepVariable(request.variable),
                min_val=request.min_val,
                max_val=request.max_val,
                n_points=request.n_points,
                baseline_V=request.baseline_V,
                baseline_Q=request.baseline_Q,
                baseline_C_in=request.baseline_C_in,
                baseline_k=request.baseline_k,
                order=request.order,
            )
            points_schema = [
                SweepPointSchema(
                    param_value=p.param_value,
                    tau=p.tau,
                    C_A_ss=p.C_A_ss,
                    conversion=p.conversion,
                    reaction_rate_ss=p.reaction_rate_ss,
                    residual=p.residual,
                    status=p.status,
                    warning=p.warning,
                )
                for p in res_1d.points
            ]
            sens_schema = (
                LocalSensitivitySchema(
                    derivative_dX_dp=res_1d.local_sensitivity["derivative_dX_dp"],
                    normalized_elasticity=res_1d.local_sensitivity["normalized_elasticity"],
                )
                if res_1d.local_sensitivity
                else None
            )

            return Sweep1DResponse(
                sweep_type="1D",
                variable=res_1d.variable,
                variable_label=res_1d.variable_label,
                variable_unit=res_1d.variable_unit,
                baseline_param_value=res_1d.baseline_param_value,
                fixed_parameters=res_1d.fixed_parameters,
                order=res_1d.order,
                points=points_schema,
                baseline_metrics=res_1d.baseline_metrics,
                local_sensitivity=sens_schema,
                trend_summary=res_1d.trend_summary,
                units=res_1d.units,
            )
    except (ValueError, TypeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


@router.post("/parameter-sweep/lhs", response_model=LHSSweepResponse)
def compute_lhs_sweep(request: LHSSweepRequest) -> LHSSweepResponse:
    """Execute multi-parameter sweep using Latin Hypercube Sampling (SciPy QMC)."""
    try:
        res = compute_lhs_parameter_sweep(
            bounds=request.bounds,
            n_samples=request.n_samples,
            seed=request.seed,
            order=request.order,
        )
        points_schema = [
            LHSSweepPointSchema(
                sample_index=p.sample_index,
                V=p.V,
                Q=p.Q,
                k=p.k,
                C_A_in=p.C_A_in,
                tau=p.tau,
                C_A_ss=p.C_A_ss,
                conversion=p.conversion,
                reaction_rate_ss=p.reaction_rate_ss,
                residual=p.residual,
                status=p.status,
                warning=p.warning,
            )
            for p in res.points
        ]
        bounds_dict = {k: [float(v[0]), float(v[1])] for k, v in res.bounds.items()}
        return LHSSweepResponse(
            sweep_type="LHS",
            n_samples=res.n_samples,
            seed=res.seed,
            order=res.order,
            bounds=bounds_dict,
            points=points_schema,
            summary_statistics=res.summary_statistics,
            failed_count=res.failed_count,
            units=res.units,
        )
    except (ValueError, TypeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


@router.post("/thermal", response_model=ThermalSimulationResponse)
def compute_thermal_simulation(request: ThermalSimulationRequest) -> ThermalSimulationResponse:
    """Simulate coupled non-isothermal CSTR mass and energy dynamics with cooling jacket."""
    try:
        config = ThermalCSTRConfig(
            V=request.V,
            Q=request.Q,
            C_A_in=request.C_A_in,
            T_in=request.T_in,
            A=request.A,
            Ea=request.Ea,
            order=request.order,
            delta_H_rxn=request.delta_H_rxn,
            UA=request.UA,
            V_j=request.V_j,
            Q_j=request.Q_j,
            T_j_in=request.T_j_in,
            isothermal=request.isothermal,
        )

        res = simulate_thermal_cstr(
            config=config,
            C_A_0=request.C_A_0,
            T_0=request.T_0,
            t_final=request.t_final,
            n_points=request.n_points,
        )

        return ThermalSimulationResponse(
            t=res.t,
            C_A=res.C_A,
            T_reactor=res.T_reactor,
            T_jacket=res.T_jacket,
            k_T=res.k_T,
            conversion=res.conversion,
            heat_generated=res.heat_generated,
            heat_removed=res.heat_removed,
            steady_state_C_A=res.steady_state_C_A,
            steady_state_T=res.steady_state_T,
            thermal_runaway_detected=res.thermal_runaway_detected,
            warnings=res.warnings,
            provenance="NON_ISOTHERMAL_MECHANISTIC_SOLVER",
        )
    except (ValueError, TypeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

