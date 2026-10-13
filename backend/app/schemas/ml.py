"""Schemas for Machine Learning API, training jobs, model catalog, and inference.

Strictly adheres to GLOBAL-INSTRUCTIONS.md, phase-11, and phase-08A:
- Schema validation with input bounds checks.
- Explicit units (L, L/min, mol/L, min).
- Clear provenance labeling ('ML_PREDICTED', 'GREY_BOX_NEURAL_ODE').
- Returns warnings for out-of-distribution operating conditions.
"""

from typing import Any, Optional
from pydantic import BaseModel, Field


class MLModelCatalogItem(BaseModel):
    """Metadata describing an available machine learning model or baseline."""

    model_id: str
    model_type: str
    name: str
    description: str
    task: str
    provenance: str = "ML_MODEL"
    status: str = "ready"
    is_trainable: bool = True
    input_features: list[str] = Field(
        default_factory=lambda: ["time_min", "V_L", "Q_L_min", "k", "C_A_in_mol_L", "C_A_0_mol_L", "order"]
    )


class MLTrainingRequest(BaseModel):
    """Hyperparameter and configuration payload for model training/tuning."""

    model_type: str = Field(default="GREY_BOX_NEURAL_ODE", description="Model family to train")
    epochs: int = Field(default=30, ge=5, le=300, description="Number of training epochs")
    learning_rate: float = Field(default=0.01, gt=1e-5, le=0.5, description="Initial learning rate")
    hidden_dim: int = Field(default=32, ge=8, le=128, description="Hidden layer dimension")
    num_layers: int = Field(default=2, ge=1, le=5, description="Number of neural layers")
    random_seed: int = Field(default=42, ge=0, description="Random seed for reproducibility")


class MLTrainingResponse(BaseModel):
    """Detailed training outcome and evaluation metrics."""

    job_id: str
    model_type: str
    status: str
    epochs_completed: int
    best_val_loss: Optional[float] = None
    train_rmse: Optional[float] = None
    val_rmse: Optional[float] = None
    test_rmse: Optional[float] = None
    test_r2: Optional[float] = None
    negative_conc_count: int = 0
    training_duration_seconds: float
    train_loss_history: list[float] = Field(default_factory=list)
    val_loss_history: list[float] = Field(default_factory=list)
    provenance: str = "TRAINED_ML_MODEL"
    warnings: list[str] = Field(default_factory=list)


class MLInferenceRequest(BaseModel):
    """Inference parameters for generating transient trajectory forecasts."""

    model_type: str = Field(default="GREY_BOX_NEURAL_ODE")
    V: float = Field(default=10.0, gt=0.0, le=500.0, description="Volume [L]")
    Q: float = Field(default=1.0, gt=0.0, le=50.0, description="Flow rate [L/min]")
    k: float = Field(default=0.15, ge=0.0, le=100.0, description="Kinetic rate constant")
    C_A_in: float = Field(default=2.0, ge=0.0, le=20.0, description="Inlet concentration [mol/L]")
    C_A_0: float = Field(default=0.0, ge=0.0, le=20.0, description="Initial concentration [mol/L]")
    order: int = Field(default=1, ge=0, le=2, description="Reaction order n in {0, 1, 2}")
    t_final: float = Field(default=20.0, gt=0.1, le=200.0, description="Final time [min]")
    n_points: int = Field(default=41, ge=5, le=500, description="Number of evaluation points")


class MLInferenceResponse(BaseModel):
    """Continuous transient trajectory predicted by selected ML model."""

    model_type: str
    t: list[float]
    C_A: list[float]
    reaction_rate: Optional[list[float]] = None
    mass_balance_residual: Optional[list[float]] = None
    steady_state_C_A: Optional[float] = None
    provenance: str = "ML_PREDICTED"
    warnings: list[str] = Field(default_factory=list)
