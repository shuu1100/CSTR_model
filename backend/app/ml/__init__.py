"""CSTR Machine Learning & Grey-Box Neural ODE package.

Adheres strictly to GLOBAL-INSTRUCTIONS.md, phase-09, and phase-08A protocols:
- Grouped/blocked splits by trajectory (zero leakage).
- Naive and mechanistic baselines compared against scikit-learn models.
- PyTorch Grey-box Neural ODE enforcing macroscopic mass-balance physics.
- Comprehensive metric tracking (RMSE, MAE, R2, physical residuals, steady-state error).
"""

from backend.app.ml.baselines import (
    BaselineComparisonResult,
    evaluate_baselines,
    train_sklearn_surrogate,
)
from backend.app.ml.evaluation import (
    RegressionMetrics,
    compute_regression_metrics,
    format_metrics_table,
)
from backend.app.ml.neural_ode import (
    GreyBoxNeuralODE,
    GreyBoxODESimulator,
    train_grey_box_neural_ode,
)
from backend.app.ml.pinn import (
    CSTRPINN,
    PINNLossComponents,
    PINNTrainingResult,
    train_cstr_pinn,
)

__all__ = [
    "BaselineComparisonResult",
    "CSTRPINN",
    "GreyBoxNeuralODE",
    "GreyBoxODESimulator",
    "PINNLossComponents",
    "PINNTrainingResult",
    "RegressionMetrics",
    "compute_regression_metrics",
    "evaluate_baselines",
    "format_metrics_table",
    "train_cstr_pinn",
    "train_grey_box_neural_ode",
    "train_sklearn_surrogate",
]

