"""Pydantic schemas for parameter sweeps and sensitivity analysis."""

from typing import Any, Literal, Optional, Union
from pydantic import BaseModel, Field, model_validator


class SweepPointSchema(BaseModel):
    """Single evaluation point in a 1D parameter sweep."""

    param_value: float
    tau: float
    C_A_ss: float
    conversion: Optional[float]
    reaction_rate_ss: float
    residual: float
    status: Literal["ok", "failed"] = "ok"
    warning: Optional[str] = None


class LocalSensitivitySchema(BaseModel):
    """Local finite-difference sensitivity measures evaluated at baseline."""

    derivative_dX_dp: float = Field(..., description="Local tangent derivative dX_A / dp")
    normalized_elasticity: float = Field(..., description="Normalized sensitivity / elasticity (dX/X) / (dp/p)")


class ParameterSweepRequest(BaseModel):
    """Request payload for 1D or 2D parameter sweep."""

    is_2d: bool = Field(False, description="Whether to execute a 2D surface grid sweep")

    # Primary variable (X axis)
    variable: Literal["V", "Q", "k", "C_A_in"] = Field("k", description="Independent swept parameter")
    min_val: float = Field(0.01, ge=0.0, description="Minimum parameter value")
    max_val: float = Field(1.0, gt=0.0, description="Maximum parameter value")
    n_points: int = Field(50, ge=2, le=500, description="Evaluation points count (2 to 500)")

    # Secondary variable (Y axis for 2D sweeps)
    variable_y: Optional[Literal["V", "Q", "k", "C_A_in"]] = Field(None, description="Second parameter for 2D sweep")
    min_val_y: Optional[float] = Field(None, ge=0.0, description="Minimum Y value for 2D sweep")
    max_val_y: Optional[float] = Field(None, gt=0.0, description="Maximum Y value for 2D sweep")
    n_points_y: Optional[int] = Field(20, ge=2, le=50, description="Y-axis points for 2D sweep (2 to 50)")

    # Baseline & fixed parameters
    baseline_V: float = Field(10.0, gt=0.0, description="Baseline reactor volume [L]")
    baseline_Q: float = Field(1.0, gt=0.0, description="Baseline volumetric flow rate [L/min]")
    baseline_C_in: float = Field(2.0, ge=0.0, description="Baseline inlet reactant conc [mol/L]")
    baseline_k: float = Field(0.15, ge=0.0, description="Baseline rate constant")
    order: Literal[0, 1, 2] = Field(1, description="Reaction kinetic order (0, 1, 2)")

    @model_validator(mode="after")
    def validate_sweep_bounds(self) -> "ParameterSweepRequest":
        if self.min_val >= self.max_val:
            raise ValueError(f"min_val ({self.min_val}) must be strictly less than max_val ({self.max_val}).")

        if self.variable in ("V", "Q") and self.min_val <= 0.0:
            raise ValueError(f"Variable '{self.variable}' must be strictly positive (> 0); min_val cannot be 0.")

        if self.is_2d:
            if not self.variable_y:
                raise ValueError("variable_y must be specified when is_2d is True.")
            if self.variable == self.variable_y:
                raise ValueError("variable and variable_y must be different independent variables.")
            if self.min_val_y is None or self.max_val_y is None:
                raise ValueError("min_val_y and max_val_y must be specified for 2D sweep.")
            if self.min_val_y >= self.max_val_y:
                raise ValueError(f"min_val_y ({self.min_val_y}) must be strictly less than max_val_y ({self.max_val_y}).")
            if self.variable_y in ("V", "Q") and self.min_val_y <= 0.0:
                raise ValueError(f"Variable '{self.variable_y}' must be strictly positive (> 0); min_val_y cannot be 0.")

        return self


class Sweep1DResponse(BaseModel):
    """Response payload for 1D parameter sweep."""

    sweep_type: Literal["1D"] = "1D"
    variable: str
    variable_label: str
    variable_unit: str
    baseline_param_value: float
    fixed_parameters: dict[str, float]
    order: int
    points: list[SweepPointSchema]
    baseline_metrics: dict[str, Any]
    local_sensitivity: Optional[LocalSensitivitySchema]
    trend_summary: str
    units: dict[str, str]


class Sweep2DResponse(BaseModel):
    """Response payload for 2D surface parameter sweep."""

    sweep_type: Literal["2D"] = "2D"
    var_x: str
    var_x_label: str
    var_x_unit: str
    x_values: list[float]

    var_y: str
    var_y_label: str
    var_y_unit: str
    y_values: list[float]

    fixed_parameters: dict[str, float]
    order: int

    conversion_grid: list[list[Optional[float]]]
    concentration_grid: list[list[float]]
    tau_grid: list[list[float]]

    baseline_point: dict[str, float]
    trend_summary: str
    units: dict[str, str]


ParameterSweepResponse = Union[Sweep1DResponse, Sweep2DResponse]


class LHSSweepPointSchema(BaseModel):
    """Calculated metrics for a single Latin Hypercube sample."""

    sample_index: int
    V: float
    Q: float
    k: float
    C_A_in: float
    tau: float
    C_A_ss: float
    conversion: Optional[float]
    reaction_rate_ss: float
    residual: float
    status: Literal["ok", "failed"] = "ok"
    warning: Optional[str] = None


class LHSSweepRequest(BaseModel):
    """Request payload for Latin Hypercube Sampling parameter sweep."""

    n_samples: int = Field(50, ge=2, le=500, description="Number of quasi-Monte Carlo LHS samples")
    seed: int = Field(42, description="Fixed random seed for deterministic reproducibility")
    order: Literal[0, 1, 2] = Field(1, description="Kinetic reaction order")
    bounds: dict[str, tuple[float, float]] = Field(
        default_factory=lambda: {
            "V": (2.0, 30.0),
            "Q": (0.2, 5.0),
            "k": (0.01, 1.0),
            "C_A_in": (0.5, 5.0),
        },
        description="Min and max bounds for V, Q, k, and C_A_in",
    )


class LHSSweepResponse(BaseModel):
    """Response payload for Latin Hypercube Sampling parameter sweep."""

    sweep_type: Literal["LHS"] = "LHS"
    n_samples: int
    seed: int
    order: int
    bounds: dict[str, list[float]]
    points: list[LHSSweepPointSchema]
    summary_statistics: dict[str, Any]
    failed_count: int
    units: dict[str, str]
