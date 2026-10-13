"""Pydantic schemas for conventional kinetic parameter estimation."""

from typing import Literal, Optional
from pydantic import BaseModel, Field

from backend.app.core.units import ConcentrationUnit, FlowRateUnit, TimeUnit, VolumeUnit


class ParameterConfidenceIntervalSchema(BaseModel):
    """Statistical confidence interval for an estimated parameter."""

    param_name: str
    estimate: float
    std_error: float
    confidence_level: float
    ci_lower: float
    ci_upper: float
    degrees_of_freedom: int
    t_critical: float


class FitKineticsRequest(BaseModel):
    """Request schema for kinetic parameter estimation."""

    model_type: Literal["dynamic", "steady_state"] = Field(
        "dynamic",
        description="Whether fitting dynamic transient ODE data or multi-condition steady-state points.",
    )
    order: int = Field(1, ge=0, le=2, description="Reaction order (0, 1, or 2).")
    time_series: list[float] = Field(
        ...,
        min_length=2,
        description="Time points (dynamic) or residence times / flow rates (steady-state).",
    )
    observed_C_A: list[float] = Field(
        ...,
        min_length=2,
        description="Measured outlet concentration values C_A.",
    )
    V: float = Field(10.0, gt=0.0, description="Reactor volume.")
    Q: float = Field(1.0, gt=0.0, description="Volumetric flow rate.")
    C_A_in: float = Field(1.0, ge=0.0, description="Inlet feed concentration C_A,in.")
    C_A_0: Optional[float] = Field(
        None, ge=0.0, description="Initial concentration C_A(0) (if None, first observed point is used)."
    )
    fit_initial_conc: bool = Field(
        False, description="Whether to co-estimate initial concentration C_A(0) along with k."
    )
    k_init: float = Field(0.1, gt=0.0, description="Initial guess for kinetic rate constant k.")
    k_min: float = Field(1e-6, ge=0.0, description="Lower bound for rate constant k.")
    k_max: float = Field(50.0, gt=0.0, description="Upper bound for rate constant k.")
    confidence_level: float = Field(0.95, gt=0.5, lt=1.0, description="Confidence level for intervals.")

    time_unit: TimeUnit = Field("min", description="Unit of time vector.")
    conc_unit: ConcentrationUnit = Field("mol/L", description="Unit of concentration.")
    flow_unit: FlowRateUnit = Field("L/min", description="Unit of flow rate.")
    vol_unit: VolumeUnit = Field("L", description="Unit of volume.")
    is_flow_rate_input: bool = Field(
        False, description="For steady-state fitting, whether time_series represents flow rate Q instead of tau."
    )
    dataset_split: Optional[str] = Field(
        None,
        description="Optional dataset split designation ('train', 'val', 'test'). Test partition data is rejected to prevent leakage.",
    )
    has_temperature_only: bool = Field(
        False,
        description="Whether input represents temperature-only data without measured concentration.",
    )


class FitKineticsResponse(BaseModel):
    """Response containing fitted parameters, metrics, confidence intervals, and residuals."""

    model_type: str
    reaction_order: int
    fitted_k: float
    k_unit: str
    initial_k_guess: float
    k_bounds: tuple[float, float]
    fitted_C_A_0: Optional[float] = None
    confidence_interval_k: Optional[ParameterConfidenceIntervalSchema] = None
    uncertainty_note: Optional[str] = None
    condition_number: Optional[float] = None
    parameter_correlation: Optional[dict[str, float]] = None

    n_points: int
    degrees_of_freedom: int
    ssr: float
    rmse: float
    mae: float
    r_squared: float

    optimizer_success: bool
    optimizer_status: int
    optimizer_message: str
    n_fev: int

    time_series: list[float]
    observed_C_A: list[float]
    predicted_C_A: list[float]
    residuals: list[float]

    warnings: list[str] = Field(default_factory=list)
    provenance_label: str = (
        "FITTED ESTIMATE: The reported kinetic parameters are mathematical estimates "
        "derived from numerical optimization and model assumptions. They are not direct laboratory measurements."
    )
