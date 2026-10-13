"""Baseline machine learning models and naive/mechanistic comparators for CSTR trajectories.

Adheres strictly to GLOBAL-INSTRUCTIONS.md, phase-09, and phase-08A:
- Explicit feature definitions without future-data leakage.
- Grouped/blocked trajectory splits (disjoint trajectory IDs).
- Preprocessing fitted on training split only.
- Compares naive baselines (persistence, mean) and mechanistic analytical baseline
  against scikit-learn models (Ridge, Random Forest, HistGradientBoosting, MLP).
"""

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any, Optional
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.neural_network import MLPRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from backend.app.core.analytical import first_order_dynamic_analytical_trajectory
from backend.app.ml.evaluation import RegressionMetrics, compute_regression_metrics

# Standard feature set for CSTR dynamic trajectory surrogate
FEATURE_COLUMNS = ["time_min", "V_L", "Q_L_min", "k", "C_A_in_mol_L", "C_A_0_mol_L", "order"]
TARGET_COLUMN = "C_A_clean_mol_L"


@dataclass
class BaselineComparisonResult:
    """Consolidated metrics across baseline models on train, val, and locked test splits."""

    train_metrics: dict[str, RegressionMetrics]
    val_metrics: dict[str, RegressionMetrics]
    test_metrics: dict[str, RegressionMetrics]
    features: list[str]
    target: str
    n_train_trajectories: int
    n_val_trajectories: int
    n_test_trajectories: int
    nominal_k: float = 0.10


class PersistenceBaseline:
    """Predicts static initial concentration C_A_0 (no dynamic change)."""

    def fit(self, X: np.ndarray, y: np.ndarray) -> "PersistenceBaseline":
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        # Initial concentration C_A_0 is at index -1
        return np.asarray(X[:, -1], dtype=np.float64)


class MeanBaseline:
    """Predicts the scalar mean of the training target."""

    def __init__(self) -> None:
        self.mean_value_: float = 0.0

    def fit(self, X: np.ndarray, y: np.ndarray) -> "MeanBaseline":
        self.mean_value_ = float(np.mean(y))
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        return np.full(shape=(len(X),), fill_value=self.mean_value_, dtype=np.float64)


class MechanisticBaseline:
    """Analytical first-order CSTR ODE solution using either input rate constant or nominal prior."""

    def __init__(self, nominal_k: float = 0.10, use_input_k: bool = True) -> None:
        self.nominal_k = nominal_k
        self.use_input_k = use_input_k

    def fit(self, X: np.ndarray, y: np.ndarray) -> "MechanisticBaseline":
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        # X: [time, V, Q, k, C_in, C_0] (or [time, V, Q, C_in, C_0] if k omitted)
        preds = []
        for row in X:
            t = float(row[0])
            V = float(row[1])
            Q = float(row[2])
            if len(row) >= 6 and self.use_input_k:
                k_val = float(row[3])
                C_in = float(row[4])
                C_0 = float(row[5])
            else:
                k_val = self.nominal_k
                C_in = float(row[3])
                C_0 = float(row[4])

            tau = V / Q
            denom = 1.0 + k_val * tau
            C_ss = C_in / denom if denom > 0 else 0.0
            lambda_val = (1.0 + k_val * tau) / tau
            c_val = C_ss + (C_0 - C_ss) * np.exp(-lambda_val * t)
            preds.append(max(0.0, float(c_val)))
        return np.asarray(preds, dtype=np.float64)


def build_sklearn_pipelines(seed: int = 42) -> dict[str, Any]:
    """Create reproducible scikit-learn models with standard scalers."""
    return {
        "Ridge": Pipeline([
            ("scaler", StandardScaler()),
            ("regressor", Ridge(alpha=1.0, random_state=seed)),
        ]),
        "RandomForest": Pipeline([
            ("scaler", StandardScaler()),
            ("regressor", RandomForestRegressor(
                n_estimators=60,
                max_depth=12,
                min_samples_split=4,
                random_state=seed,
                n_jobs=-1,
            )),
        ]),
        "HistGradientBoosting": Pipeline([
            ("scaler", StandardScaler()),
            ("regressor", HistGradientBoostingRegressor(
                max_iter=100,
                max_depth=8,
                random_state=seed,
            )),
        ]),
        "MLPRegressor": Pipeline([
            ("scaler", StandardScaler()),
            ("regressor", MLPRegressor(
                hidden_layer_sizes=(64, 32),
                activation="relu",
                max_iter=250,
                random_state=seed,
                early_stopping=False,
            )),
        ]),
    }


def prepare_trajectory_split_matrices(
    df: pd.DataFrame,
    manifest: dict[str, Any],
    features: Optional[list[str]] = None,
    target: str = TARGET_COLUMN,
) -> tuple[
    tuple[np.ndarray, np.ndarray, pd.DataFrame],
    tuple[np.ndarray, np.ndarray, pd.DataFrame],
    tuple[np.ndarray, np.ndarray, pd.DataFrame],
]:
    """Extract train, validation, and test matrices strictly partitioned by trajectory IDs."""
    if features is None:
        features = FEATURE_COLUMNS

    tasks = manifest.get("tasks", {})
    task_splits = tasks.get("transient_dynamic_forecasting") or tasks.get("transient_trajectories") or {}
    partitions = task_splits.get("partitions", {})

    train_ids = set(partitions.get("train_ids", []) or task_splits.get("train", {}).get("trajectory_ids", []))
    val_ids = set(partitions.get("val_ids", []) or task_splits.get("val", {}).get("trajectory_ids", []))
    test_ids = set(partitions.get("test_ids", []) or task_splits.get("test", {}).get("trajectory_ids", []))

    if not train_ids or not val_ids or not test_ids:
        raise ValueError("Manifest missing transient trajectory train/val/test IDs.")

    # Assert zero overlap
    assert train_ids.isdisjoint(val_ids), "Data leakage: train and val share trajectory IDs!"
    assert train_ids.isdisjoint(test_ids), "Data leakage: train and test share trajectory IDs!"
    assert val_ids.isdisjoint(test_ids), "Data leakage: val and test share trajectory IDs!"

    df_train = df[df["trajectory_id"].isin(train_ids)].copy()
    df_val = df[df["trajectory_id"].isin(val_ids)].copy()
    df_test = df[df["trajectory_id"].isin(test_ids)].copy()

    X_train = df_train[features].to_numpy(dtype=np.float64)
    y_train = df_train[target].to_numpy(dtype=np.float64)

    X_val = df_val[features].to_numpy(dtype=np.float64)
    y_val = df_val[target].to_numpy(dtype=np.float64)

    X_test = df_test[features].to_numpy(dtype=np.float64)
    y_test = df_test[target].to_numpy(dtype=np.float64)

    return (X_train, y_train, df_train), (X_val, y_val, df_val), (X_test, y_test, df_test)


def evaluate_baselines(
    df_trajectories: pd.DataFrame,
    manifest: dict[str, Any],
    seed: int = 42,
    nominal_k: float = 0.10,
) -> BaselineComparisonResult:
    """Train all baselines and evaluate performance on disjoint validation and locked test splits."""
    (X_tr, y_tr, df_tr), (X_val, y_val, df_val), (X_te, y_te, df_te) = prepare_trajectory_split_matrices(
        df_trajectories, manifest
    )

    models: dict[str, Any] = {
        "Persistence": PersistenceBaseline(),
        "Mean": MeanBaseline(),
        "Mechanistic_Nominal": MechanisticBaseline(nominal_k=nominal_k),
    }
    models.update(build_sklearn_pipelines(seed=seed))

    train_results: dict[str, RegressionMetrics] = {}
    val_results: dict[str, RegressionMetrics] = {}
    test_results: dict[str, RegressionMetrics] = {}

    for name, model in models.items():
        # Fit on training split ONLY
        model.fit(X_tr, y_tr)

        # Predictions
        pred_tr = model.predict(X_tr)
        pred_val = model.predict(X_val)
        pred_te = model.predict(X_te)

        train_results[name] = compute_regression_metrics(y_tr, pred_tr)
        val_results[name] = compute_regression_metrics(y_val, pred_val)
        test_results[name] = compute_regression_metrics(y_te, pred_te)

    return BaselineComparisonResult(
        train_metrics=train_results,
        val_metrics=val_results,
        test_metrics=test_results,
        features=FEATURE_COLUMNS,
        target=TARGET_COLUMN,
        n_train_trajectories=len(set(df_tr["trajectory_id"])),
        n_val_trajectories=len(set(df_val["trajectory_id"])),
        n_test_trajectories=len(set(df_te["trajectory_id"])),
        nominal_k=nominal_k,
    )


def train_sklearn_surrogate(
    X_train: np.ndarray,
    y_train: np.ndarray,
    model_type: str = "HistGradientBoosting",
    seed: int = 42,
) -> Pipeline:
    """Train and return a single scikit-learn surrogate pipeline."""
    pipelines = build_sklearn_pipelines(seed=seed)
    if model_type not in pipelines:
        raise ValueError(f"Unknown model_type '{model_type}'. Choose from {list(pipelines.keys())}")
    pipeline = pipelines[model_type]
    pipeline.fit(X_train, y_train)
    return pipeline
