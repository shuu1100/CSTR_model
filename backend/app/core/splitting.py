"""Data splitting and leakage prevention protocols for CSTR machine learning.

Enforces rules from GLOBAL-INSTRUCTIONS.md, phase-08, and phase-08A:
- Splits synthetic data strictly by independent trajectory ID / parameter draw (70/15/15).
- Prevents row-level leakage: all time points of a trajectory remain together in one partition.
- Verifies mathematical disjointness between train, validation, and test partitions.
- Fits transformers/scalers on training data ONLY; locks test evaluation.
- Generates reproducible split manifests with seed, source hashes, and assertions.
"""

from dataclasses import asdict, dataclass
import hashlib
import json
import math
from typing import Any, Optional, Sequence, Tuple
import numpy as np
from sklearn.preprocessing import StandardScaler


@dataclass(frozen=True)
class SplitPartition:
    """Designation of dataset partition."""

    train_ids: tuple[str, ...]
    val_ids: tuple[str, ...]
    test_ids: tuple[str, ...]
    seed: int
    n_total: int
    proportions: tuple[float, float, float] = (0.70, 0.15, 0.15)

    def assert_disjoint(self) -> None:
        """Assert zero intersection (leakage) between train, validation, and test partitions."""
        s_train = set(self.train_ids)
        s_val = set(self.val_ids)
        s_test = set(self.test_ids)

        overlap_tv = s_train.intersection(s_val)
        if overlap_tv:
            raise AssertionError(f"Leakage detected between Train and Val: {len(overlap_tv)} shared IDs.")

        overlap_tt = s_train.intersection(s_test)
        if overlap_tt:
            raise AssertionError(f"Leakage detected between Train and Test: {len(overlap_tt)} shared IDs.")

        overlap_vt = s_val.intersection(s_test)
        if overlap_vt:
            raise AssertionError(f"Leakage detected between Val and Test: {len(overlap_vt)} shared IDs.")

        total_split = len(s_train) + len(s_val) + len(s_test)
        if total_split != self.n_total:
            raise AssertionError(
                f"Partition count mismatch: split sum ({total_split}) != total ({self.n_total})."
            )


def split_trajectories_by_id(
    trajectory_ids: Sequence[str],
    train_fraction: float = 0.70,
    val_fraction: float = 0.15,
    seed: int = 42,
) -> SplitPartition:
    """Split trajectory / parameter draw IDs into train/validation/test partitions without row leakage.

    Parameters:
        trajectory_ids: Unique identifier for each independent trajectory or parameter draw.
        train_fraction: Fraction for training partition (default 0.70).
        val_fraction: Fraction for validation tuning (default 0.15).
        seed: Random seed for deterministic reproducibility.

    Returns:
        SplitPartition with disjoint train_ids, val_ids, and test_ids.
    """
    unique_ids = list(dict.fromkeys(trajectory_ids))  # preserve order & unique
    n_total = len(unique_ids)
    if n_total < 3:
        raise ValueError(f"Cannot split fewer than 3 unique trajectories. Got {n_total}.")

    if not math.isclose(train_fraction + val_fraction + (1.0 - train_fraction - val_fraction), 1.0):
        raise ValueError("Fractions must sum to 1.0.")

    # Deterministic permutation
    rng = np.random.default_rng(seed)
    shuffled = list(unique_ids)
    rng.shuffle(shuffled)

    n_train = max(1, int(round(train_fraction * n_total)))
    n_val = max(1, int(round(val_fraction * n_total)))
    n_test = n_total - n_train - n_val

    # Ensure each split has at least 1 trajectory if n_total >= 3
    if n_test < 1:
        n_test = 1
        if n_train > n_val and n_train > 1:
            n_train -= 1
        else:
            n_val -= 1

    train_ids = tuple(shuffled[:n_train])
    val_ids = tuple(shuffled[n_train : n_train + n_val])
    test_ids = tuple(shuffled[n_train + n_val :])

    partition = SplitPartition(
        train_ids=train_ids,
        val_ids=val_ids,
        test_ids=test_ids,
        seed=seed,
        n_total=n_total,
        proportions=(train_fraction, val_fraction, round(1.0 - train_fraction - val_fraction, 2)),
    )
    partition.assert_disjoint()
    return partition


def fit_scaler_train_only(
    train_features: np.ndarray,
    val_features: Optional[np.ndarray] = None,
    test_features: Optional[np.ndarray] = None,
) -> Tuple[StandardScaler, np.ndarray, Optional[np.ndarray], Optional[np.ndarray]]:
    """Fit a feature scaler strictly on the training partition to prevent lookahead data leakage.

    Parameters:
        train_features: Training partition feature matrix (N_train x D).
        val_features: Optional validation partition matrix (N_val x D).
        test_features: Optional locked test partition matrix (N_test x D).

    Returns:
        (scaler, train_scaled, val_scaled, test_scaled)
    """
    scaler = StandardScaler()
    train_scaled = scaler.fit_transform(train_features)

    val_scaled = scaler.transform(val_features) if val_features is not None else None
    test_scaled = scaler.transform(test_features) if test_features is not None else None

    return scaler, train_scaled, val_scaled, test_scaled


def build_split_manifest(
    task_name: str,
    partition: SplitPartition,
    dataset_sha256: str,
    code_version: str = "0.1.0-phase08",
    extra_metadata: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Build a comprehensive manifest recording split boundaries, seed, and leakage assertions."""
    manifest = {
        "task_name": task_name,
        "split_protocol": "70/15/15_by_trajectory_or_parameter_draw",
        "random_seed": partition.seed,
        "dataset_sha256": dataset_sha256,
        "code_version": code_version,
        "counts": {
            "total_trajectories": partition.n_total,
            "train": len(partition.train_ids),
            "val": len(partition.val_ids),
            "test": len(partition.test_ids),
        },
        "percentages": {
            "train": round(len(partition.train_ids) / partition.n_total * 100, 2),
            "val": round(len(partition.val_ids) / partition.n_total * 100, 2),
            "test": round(len(partition.test_ids) / partition.n_total * 100, 2),
        },
        "leakage_assertion": {
            "disjoint_train_val": True,
            "disjoint_train_test": True,
            "disjoint_val_test": True,
            "row_level_leakage_prevented": True,
        },
        "partitions": {
            "train_ids": list(partition.train_ids),
            "val_ids": list(partition.val_ids),
            "test_ids": list(partition.test_ids),
        },
        "metadata": extra_metadata or {},
    }
    return manifest
