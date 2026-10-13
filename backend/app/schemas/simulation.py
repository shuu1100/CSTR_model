"""Pydantic request and response schemas for CSTR Lab API."""

from datetime import datetime, timezone
from typing import Any, Literal, Optional
from pydantic import BaseModel, Field, field_validator, model_validator

from backend.app.core.kinetics import RATE_CONSTANT_CANONICAL_UNITS
from backend.app.core.units import (
    ConcentrationUnit,
    FlowRateUnit,
    TimeUnit,
    VolumeUnit,
    convert_concentration,
    convert_flow_rate,
    convert_time,
    convert_volume,
)


class HealthResponse(BaseModel):
    """Health check response schema."""

    status: Literal["ok", "degraded", "error"] = "ok"
    app_name: str
    version: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ModelCatalogItem(BaseModel):
    """Specification of an available reactor model."""

    model_id: str
    name: str
    description: str
    supported_orders: list[int]
    canonical_units: dict[str, str]
    assumptions: list[str]
    solvers: list[str]


class ModelCatalogResponse(BaseModel):
    """Catalog of all supported models in CSTR Lab."""

    models: list[ModelCatalogItem]


class StepChangeSchema(BaseModel):
    """Step change specification for transient simulation."""

    time: float = Field(..., gt=0.0, description="Simulation time in minutes when step change takes effect")
    C_A_in_new: Optional[float] = Field(None, ge=0.0, description="New inlet reactant concentration [mol/L]")
    Q_new: Optional[float] = Field(None, gt=0.0, description="New volumetric flow rate [L/min]")

    @model_validator(mode="after")
    def check_at_least_one_change(self) -> "StepChangeSchema":
        if self.C_A_in_new is None and self.Q_new is None:
            raise ValueError("At least one parameter (C_A_in_new or Q_new) must be provided in step_change.")
        return self

    model_config = {
        "json_schema_extra": {
            "example": {
                "time": 25.0,
                "C_A_in_new": 2.0,
                "Q_new": None,
            }
        }
    }


class SteadyStateRequest(BaseModel):
    """Request payload for steady-state simulation."""

    V: float = Field(..., gt=0.0, description="Reactor volume [L]")
    Q: float = Field(..., gt=0.0, description="Volumetric flow rate [L/min]")
    C_A_in: float = Field(..., ge=0.0, description="Inlet reactant concentration [mol/L]")
    order: Literal[0, 1, 2] = Field(1, description="Reaction order (0: zero-order, 1: first-order, 2: second-order)")
    k: float = Field(..., ge=0.0, description="Reaction rate constant in canonical units")

    # Optional input unit specifiers for automatic normalization
    volume_unit: VolumeUnit = Field("L", description="Unit of V (default: L)")
    flow_rate_unit: FlowRateUnit = Field("L/min", description="Unit of Q (default: L/min)")
    concentration_unit: ConcentrationUnit = Field("mol/L", description="Unit of C_A_in (default: mol/L)")

    model_config = {
        "json_schema_extra": {
            "example": {
                "V": 10.0,
                "Q": 1.0,
                "C_A_in": 1.0,
                "order": 1,
                "k": 0.15,
                "volume_unit": "L",
                "flow_rate_unit": "L/min",
                "concentration_unit": "mol/L",
            }
        }
    }

    def get_canonical_inputs(self) -> dict[str, float]:
        """Convert input values to canonical internal units."""
        v_can = convert_volume(self.V, self.volume_unit)
        q_can = convert_flow_rate(self.Q, self.flow_rate_unit)
        c_in_can = convert_concentration(self.C_A_in, self.concentration_unit)
        return {
            "V": v_can,
            "Q": q_can,
            "C_A_in": c_in_can,
            "order": self.order,
            "k": self.k,
        }


class SteadyStateOutputs(BaseModel):
    """Calculated steady-state physical variables."""

    tau: float = Field(..., description="Mean space time [min]")
    C_A_ss: float = Field(..., description="Steady-state outlet concentration [mol/L]")
    conversion: Optional[float] = Field(None, description="Reactant fractional conversion [0, 1]")
    reaction_rate_ss: float = Field(..., description="Steady-state reaction rate [mol/(L*min)]")
    residual: float = Field(..., description="Material balance residual closure error [mol/(L*min)]")


class SteadyStateResponse(BaseModel):
    """Response payload for steady-state simulation."""

    model_id: str
    normalized_inputs: dict[str, Any]
    outputs: SteadyStateOutputs
    units: dict[str, str]
    assumptions: list[str]
    diagnostics: dict[str, Any]
    warnings: list[str] = Field(default_factory=list)


class DynamicSimulationRequest(BaseModel):
    """Request payload for dynamic CSTR simulation."""

    C_A_0: float = Field(..., ge=0.0, description="Initial reactor concentration at t=0 [mol/L]")
    C_A_in: float = Field(..., ge=0.0, description="Inlet reactant concentration [mol/L]")
    V: float = Field(..., gt=0.0, description="Reactor volume [L]")
    Q: float = Field(..., gt=0.0, description="Volumetric flow rate [L/min]")
    order: Literal[0, 1, 2] = Field(1, description="Reaction order (0, 1, 2)")
    k: float = Field(..., ge=0.0, description="Rate constant in canonical units")
    t_final: float = Field(..., gt=0.0, le=10000.0, description="Simulation horizon in minutes (max 10000)")
    n_points: int = Field(101, ge=2, le=10000, description="Number of evaluation points (2 to 10000)")
    solver_method: Literal["RK45", "Radau", "BDF", "LSODA", "RK23", "DOP853"] = Field(
        "RK45", description="ODE solver method"
    )
    rtol: float = Field(1e-6, gt=0.0, le=1e-1, description="Relative error tolerance")
    atol: float = Field(1e-9, gt=0.0, le=1e-1, description="Absolute error tolerance")
    step_change: Optional[StepChangeSchema] = Field(None, description="Optional step change disturbance")

    # Optional unit specifiers
    volume_unit: VolumeUnit = "L"
    flow_rate_unit: FlowRateUnit = "L/min"
    concentration_unit: ConcentrationUnit = "mol/L"
    time_unit: TimeUnit = "min"

    model_config = {
        "json_schema_extra": {
            "example": {
                "C_A_0": 0.5,
                "C_A_in": 1.0,
                "V": 10.0,
                "Q": 1.0,
                "order": 1,
                "k": 0.15,
                "t_final": 50.0,
                "n_points": 51,
                "solver_method": "RK45",
                "rtol": 1e-6,
                "atol": 1e-9,
                "step_change": {
                    "time": 25.0,
                    "C_A_in_new": 2.0,
                },
            }
        }
    }

    def get_canonical_inputs(self) -> dict[str, Any]:
        """Convert input values to canonical units."""
        v_can = convert_volume(self.V, self.volume_unit)
        q_can = convert_flow_rate(self.Q, self.flow_rate_unit)
        c0_can = convert_concentration(self.C_A_0, self.concentration_unit)
        cin_can = convert_concentration(self.C_A_in, self.concentration_unit)
        t_final_can = convert_time(self.t_final, self.time_unit)

        step_dict = None
        if self.step_change is not None:
            step_time_can = convert_time(self.step_change.time, self.time_unit)
            step_cin_can = (
                convert_concentration(self.step_change.C_A_in_new, self.concentration_unit)
                if self.step_change.C_A_in_new is not None
                else None
            )
            step_q_can = (
                convert_flow_rate(self.step_change.Q_new, self.flow_rate_unit)
                if self.step_change.Q_new is not None
                else None
            )
            step_dict = {
                "time": step_time_can,
                "C_A_in_new": step_cin_can,
                "Q_new": step_q_can,
            }

        return {
            "C_A_0": c0_can,
            "C_A_in": cin_can,
            "V": v_can,
            "Q": q_can,
            "order": self.order,
            "k": self.k,
            "t_final": t_final_can,
            "n_points": self.n_points,
            "solver_method": self.solver_method,
            "rtol": self.rtol,
            "atol": self.atol,
            "step_change": step_dict,
        }


class SolverDetails(BaseModel):
    """Metadata regarding numerical ODE integration."""

    method: str
    success: bool
    status: int
    message: str
    tolerances: dict[str, float]


class DynamicSimulationResponse(BaseModel):
    """Response payload for dynamic CSTR simulation."""

    model_id: str
    normalized_inputs: dict[str, Any]
    t: list[float]
    C_A: list[float]
    conversion: Optional[list[float]]
    reaction_rate: list[float]
    tau_initial: float
    C_A_ss_initial: float
    solver_details: SolverDetails
    analytical_comparison: Optional[dict[str, float]] = None
    step_change_applied: Optional[dict[str, Any]] = None
    units: dict[str, str]
    assumptions: list[str]
    warnings: list[str] = Field(default_factory=list)


class ThermalSimulationRequest(BaseModel):
    """Request payload for coupled non-isothermal CSTR with jacket cooling."""

    V: float = Field(default=10.0, gt=0.0, description="Reactor volume [L]")
    Q: float = Field(default=1.0, gt=0.0, description="Feed flow rate [L/min]")
    C_A_in: float = Field(default=2.0, ge=0.0, description="Feed concentration [mol/L]")
    T_in: float = Field(default=300.0, gt=0.0, description="Feed temperature [K]")
    C_A_0: float = Field(default=0.0, ge=0.0, description="Initial concentration [mol/L]")
    T_0: Optional[float] = Field(default=None, gt=0.0, description="Initial temperature [K]")
    A: float = Field(default=1.5e7, ge=0.0, description="Arrhenius pre-exponential factor [min^-1]")
    Ea: float = Field(default=50000.0, ge=0.0, description="Activation energy [J/mol]")
    order: int = Field(default=1, ge=0, le=2, description="Reaction order n in {0, 1, 2}")
    delta_H_rxn: float = Field(default=-60.0, description="Heat of reaction [kJ/mol] (< 0 exothermic)")
    UA: float = Field(default=15.0, ge=0.0, description="Overall heat transfer coefficient * Area [kJ/(min*K)]")
    V_j: float = Field(default=2.5, gt=0.0, description="Jacket volume [L]")
    Q_j: float = Field(default=1.5, gt=0.0, description="Coolant flow rate [L/min]")
    T_j_in: float = Field(default=290.0, gt=0.0, description="Coolant inlet temperature [K]")
    isothermal: bool = Field(default=False, description="Lock reactor temperature to feed temperature")
    t_final: float = Field(default=40.0, gt=0.1, le=1000.0, description="Simulation horizon [min]")
    n_points: int = Field(default=81, ge=5, le=1000, description="Number of evaluation points")


class ThermalSimulationResponse(BaseModel):
    """Response payload for non-isothermal CSTR simulation."""

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
    units: dict[str, str] = Field(
        default_factory=lambda: {
            "time": "min",
            "concentration": "mol/L",
            "temperature": "K",
            "rate_constant": "min^-1",
            "heat_flow": "kJ/min",
        }
    )
    warnings: list[str] = Field(default_factory=list)
    provenance: str = "NON_ISOTHERMAL_MECHANISTIC_SOLVER"

