"""API endpoints for engineering analysis and parameter estimation."""

import numpy as np
from fastapi import APIRouter, HTTPException, status

from backend.app.core.parameter_estimation import (
    fit_dynamic_kinetics,
    fit_steady_state_kinetics,
)
from backend.app.core.units import (
    convert_concentration,
    convert_flow_rate,
    convert_time,
    convert_volume,
)
from backend.app.schemas.estimation import (
    FitKineticsRequest,
    FitKineticsResponse,
    ParameterConfidenceIntervalSchema,
)

router = APIRouter(prefix="/analysis", tags=["Analysis"])


@router.post(
    "/fit-kinetics",
    response_model=FitKineticsResponse,
    status_code=status.HTTP_200_OK,
    summary="Fit kinetic rate parameters using nonlinear least squares",
)
def fit_kinetics(request: FitKineticsRequest) -> FitKineticsResponse:
    """Perform kinetic parameter estimation against experimental or simulation time-series data."""
    # Unit conversions to canonical: min, mol/L, L, L/min
    try:
        t_canon = [convert_time(t, request.time_unit) for t in request.time_series]
        c_obs_canon = [convert_concentration(c, request.conc_unit) for c in request.observed_C_A]
        v_canon = convert_volume(request.V, request.vol_unit)
        q_canon = convert_flow_rate(request.Q, request.flow_unit)
        c_in_canon = convert_concentration(request.C_A_in, request.conc_unit)
        c_0_canon = (
            convert_concentration(request.C_A_0, request.conc_unit)
            if request.C_A_0 is not None
            else None
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"Unit conversion failed: {str(exc)}",
        ) from exc

    try:
        if request.model_type == "dynamic":
            res = fit_dynamic_kinetics(
                time=t_canon,
                C_A_obs=c_obs_canon,
                V=v_canon,
                Q=q_canon,
                C_A_in=c_in_canon,
                order=request.order,
                C_A_0=c_0_canon,
                fit_initial_conc=request.fit_initial_conc,
                k_init=request.k_init,
                k_min=request.k_min,
                k_max=request.k_max,
                confidence_level=request.confidence_level,
                dataset_split=request.dataset_split,
                has_temperature_only=request.has_temperature_only,
            )
        else:
            res = fit_steady_state_kinetics(
                tau_or_flow=t_canon,
                C_A_obs=c_obs_canon,
                C_A_in=c_in_canon,
                V=v_canon,
                is_flow_rate=request.is_flow_rate_input,
                order=request.order,
                k_init=request.k_init,
                k_min=request.k_min,
                k_max=request.k_max,
                confidence_level=request.confidence_level,
                dataset_split=request.dataset_split,
                has_temperature_only=request.has_temperature_only,
            )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc

    ci_schema = None
    if res.confidence_interval_k is not None:
        ci_schema = ParameterConfidenceIntervalSchema(
            param_name=res.confidence_interval_k.param_name,
            estimate=res.confidence_interval_k.estimate,
            std_error=res.confidence_interval_k.std_error,
            confidence_level=res.confidence_interval_k.confidence_level,
            ci_lower=res.confidence_interval_k.ci_lower,
            ci_upper=res.confidence_interval_k.ci_upper,
            degrees_of_freedom=res.confidence_interval_k.degrees_of_freedom,
            t_critical=res.confidence_interval_k.t_critical,
        )

    return FitKineticsResponse(
        model_type=res.model_type,
        reaction_order=res.reaction_order,
        fitted_k=res.fitted_k,
        k_unit=res.k_unit,
        initial_k_guess=res.initial_k_guess,
        k_bounds=res.k_bounds,
        fitted_C_A_0=res.fitted_C_A_0,
        confidence_interval_k=ci_schema,
        uncertainty_note=res.uncertainty_note,
        condition_number=res.condition_number,
        parameter_correlation=res.parameter_correlation,
        n_points=res.n_points,
        degrees_of_freedom=res.degrees_of_freedom,
        ssr=res.ssr,
        rmse=res.rmse,
        mae=res.mae,
        r_squared=res.r_squared,
        optimizer_success=res.optimizer_success,
        optimizer_status=res.optimizer_status,
        optimizer_message=res.optimizer_message,
        n_fev=res.n_fev,
        time_series=res.time_series,
        observed_C_A=res.observed_C_A,
        predicted_C_A=res.predicted_C_A,
        residuals=res.residuals,
        warnings=res.warnings,
        provenance_label=res.provenance_label,
    )
