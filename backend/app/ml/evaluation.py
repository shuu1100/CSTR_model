"""Evaluation metrics and physical diagnostics for CSTR machine learning models.

Strictly adheres to GLOBAL-INSTRUCTIONS.md and phase-08A:
- Reports RMSE, MAE, R², max error, MAPE (with near-zero safeguard).
- Evaluates asymptotic steady-state error.
- Assesses physical plausibility: negative concentration count and CSTR mole balance residuals.
"""

from dataclasses import dataclass
import math
from typing import Optional, Sequence
import numpy as np


@dataclass(frozen=True)
class RegressionMetrics:
    """Rigorous evaluation metrics for CSTR models."""

    rmse: float
    mae: float
    r2: float
    max_error: float
    mape_percent: float
    steady_state_error: float
    physical_residual_mean: float
    physical_residual_max: float
    negative_conc_count: int
    n_samples: int

    def to_dict(self) -> dict[str, float | int]:
        return {
            "rmse": self.rmse,
            "mae": self.mae,
            "r2": self.r2,
            "max_error": self.max_error,
            "mape_percent": self.mape_percent,
            "steady_state_error": self.steady_state_error,
            "physical_residual_mean": self.physical_residual_mean,
            "physical_residual_max": self.physical_residual_max,
            "negative_conc_count": self.negative_conc_count,
            "n_samples": self.n_samples,
        }


def compute_regression_metrics(
    y_true: Sequence[float] | np.ndarray,
    y_pred: Sequence[float] | np.ndarray,
    steady_state_true: Optional[float] = None,
    steady_state_pred: Optional[float] = None,
    residuals: Optional[Sequence[float] | np.ndarray] = None,
    eps_mape: float = 1e-4,
) -> RegressionMetrics:
    """Compute standard and physical regression metrics with zero-division safeguards."""
    yt = np.asarray(y_true, dtype=np.float64)
    yp = np.asarray(y_pred, dtype=np.float64)

    if len(yt) != len(yp):
        raise ValueError(f"Length mismatch: len(y_true)={len(yt)} vs len(y_pred)={len(yp)}")
    if len(yt) == 0:
        raise ValueError("Cannot compute metrics on empty arrays.")

    diff = yt - yp
    n = len(yt)

    # Standard error metrics
    mae = float(np.mean(np.abs(diff)))
    rmse = float(np.sqrt(np.mean(diff ** 2)))
    max_err = float(np.max(np.abs(diff)))

    # Safeguarded R²
    ss_tot = float(np.sum((yt - np.mean(yt)) ** 2))
    ss_res = float(np.sum(diff ** 2))
    if ss_tot < 1e-12:
        r2 = 1.0 if ss_res < 1e-12 else 0.0
    else:
        r2 = float(1.0 - (ss_res / ss_tot))

    # Safeguarded MAPE (%)
    safe_yt = np.where(np.abs(yt) < eps_mape, eps_mape, yt)
    mape = float(np.mean(np.abs(diff / safe_yt)) * 100.0)

    # Physical checks
    neg_count = int(np.sum(yp < -1e-6))

    # Steady-state error
    if steady_state_true is not None and steady_state_pred is not None:
        ss_err = float(abs(steady_state_true - steady_state_pred))
    else:
        # Default to final point in series
        ss_err = float(abs(yt[-1] - yp[-1]))

    # Physical mass-balance residuals
    if residuals is not None and len(residuals) > 0:
        res_arr = np.abs(np.asarray(residuals, dtype=np.float64))
        phys_mean = float(np.mean(res_arr))
        phys_max = float(np.max(res_arr))
    else:
        phys_mean = 0.0
        phys_max = 0.0

    return RegressionMetrics(
        rmse=rmse,
        mae=mae,
        r2=r2,
        max_error=max_err,
        mape_percent=mape,
        steady_state_error=ss_err,
        physical_residual_mean=phys_mean,
        physical_residual_max=phys_max,
        negative_conc_count=neg_count,
        n_samples=n,
    )


def format_metrics_table(models_metrics: dict[str, RegressionMetrics]) -> str:
    """Format dictionary of model metrics into a clean Markdown table."""
    lines = [
        "| Model | RMSE (mol/L) | MAE (mol/L) | R² | Max Error | MAPE (%) | SS Error | Phys. Res Mean | C_A < 0 |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for model_name, m in models_metrics.items():
        lines.append(
            f"| **{model_name}** | {m.rmse:.5f} | {m.mae:.5f} | {m.r2:.4f} | "
            f"{m.max_error:.5f} | {m.mape_percent:.2f}% | {m.steady_state_error:.5f} | "
            f"{m.physical_residual_mean:.2e} | {m.negative_conc_count} |"
        )
    return "\n".join(lines)


@dataclass(frozen=True)
class ClassificationMetrics:
    """Evaluation metrics for classification, fault diagnosis, and anomaly detection."""

    accuracy: float
    macro_f1: float
    precision_per_class: dict[str, float]
    recall_per_class: dict[str, float]
    f1_per_class: dict[str, float]
    confusion_matrix: dict[str, dict[str, int]]
    false_alarm_count: int
    false_alarm_rate: float
    missed_detection_count: int
    missed_detection_rate: float
    n_samples: int

    def to_dict(self) -> dict[str, object]:
        return {
            "accuracy": self.accuracy,
            "macro_f1": self.macro_f1,
            "precision_per_class": self.precision_per_class,
            "recall_per_class": self.recall_per_class,
            "f1_per_class": self.f1_per_class,
            "confusion_matrix": self.confusion_matrix,
            "false_alarm_count": self.false_alarm_count,
            "false_alarm_rate": self.false_alarm_rate,
            "missed_detection_count": self.missed_detection_count,
            "missed_detection_rate": self.missed_detection_rate,
            "n_samples": self.n_samples,
        }


def compute_classification_metrics(
    y_true: Sequence[str] | np.ndarray,
    y_pred: Sequence[str] | np.ndarray,
    normal_label: str = "normal",
    labels: Optional[Sequence[str]] = None,
) -> ClassificationMetrics:
    """Compute per-class precision, recall, F1, macro-F1, confusion matrix, and false alarm / miss rates."""
    yt = [str(x) for x in y_true]
    yp = [str(x) for x in y_pred]

    if len(yt) != len(yp):
        raise ValueError(f"Length mismatch: len(y_true)={len(yt)} vs len(y_pred)={len(yp)}")
    if len(yt) == 0:
        raise ValueError("Cannot compute classification metrics on empty arrays.")

    unique_labels = sorted(list(set(yt) | set(yp))) if labels is None else list(labels)
    n = len(yt)

    # Accuracy
    correct = sum(1 for t, p in zip(yt, yp) if t == p)
    accuracy = float(correct / n)

    # Confusion matrix: row = true, col = pred
    cm: dict[str, dict[str, int]] = {lbl: {col: 0 for col in unique_labels} for lbl in unique_labels}
    for t, p in zip(yt, yp):
        if t in cm and p in cm[t]:
            cm[t][p] += 1

    # Per-class metrics
    precision_dict: dict[str, float] = {}
    recall_dict: dict[str, float] = {}
    f1_dict: dict[str, float] = {}

    for lbl in unique_labels:
        tp = cm[lbl][lbl]
        fp = sum(cm[other][lbl] for other in unique_labels if other != lbl)
        fn = sum(cm[lbl][other] for other in unique_labels if other != lbl)

        prec = float(tp / (tp + fp)) if (tp + fp) > 0 else 0.0
        rec = float(tp / (tp + fn)) if (tp + fn) > 0 else 0.0
        f1 = float(2.0 * prec * rec / (prec + rec)) if (prec + rec) > 0 else 0.0

        precision_dict[lbl] = prec
        recall_dict[lbl] = rec
        f1_dict[lbl] = f1

    macro_f1 = float(np.mean(list(f1_dict.values()))) if f1_dict else 0.0

    # False alarm & Missed detection analysis relative to normal_label
    total_normal = sum(1 for t in yt if t == normal_label)
    total_fault = sum(1 for t in yt if t != normal_label)

    # False alarm: True is normal, but predicted is a fault
    false_alarms = sum(1 for t, p in zip(yt, yp) if t == normal_label and p != normal_label)
    false_alarm_rate = float(false_alarms / total_normal) if total_normal > 0 else 0.0

    # Missed detection: True is a fault, but predicted is normal
    missed_detections = sum(1 for t, p in zip(yt, yp) if t != normal_label and p == normal_label)
    missed_detection_rate = float(missed_detections / total_fault) if total_fault > 0 else 0.0

    return ClassificationMetrics(
        accuracy=accuracy,
        macro_f1=macro_f1,
        precision_per_class=precision_dict,
        recall_per_class=recall_dict,
        f1_per_class=f1_dict,
        confusion_matrix=cm,
        false_alarm_count=false_alarms,
        false_alarm_rate=false_alarm_rate,
        missed_detection_count=missed_detections,
        missed_detection_rate=missed_detection_rate,
        n_samples=n,
    )
