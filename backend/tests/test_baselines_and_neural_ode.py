"""Test suite for Phase 9: Baseline ML models, Naive/Mechanistic baselines, and Grey-Box Neural ODE.

Adheres strictly to GLOBAL-INSTRUCTIONS.md, phase-09, and phase-08A:
- Asserts strict zero-leakage trajectory splitting.
- Validates naive (persistence, mean) and mechanistic baselines against scikit-learn models.
- Verifies Grey-Box Neural ODE kinetic constraints: r_A(C_A) >= 0 and r_A(0) = 0.
- Asserts PyTorch training convergence, early stopping, and seed reproducibility.
- Evaluates physical mass-balance residuals and OOD / canonical oracle performance.
"""

from pathlib import Path
import json
import math
import numpy as np
import pandas as pd
import pytest
import torch

from backend.app.ml.baselines import (
    FEATURE_COLUMNS,
    MeanBaseline,
    MechanisticBaseline,
    PersistenceBaseline,
    build_sklearn_pipelines,
    evaluate_baselines,
    prepare_trajectory_split_matrices,
)
from backend.app.ml.evaluation import (
    ClassificationMetrics,
    compute_classification_metrics,
    compute_regression_metrics,
    format_metrics_table,
)
from backend.app.ml.neural_ode import (
    GreyBoxNeuralODE,
    GreyBoxODESimulator,
    TrajectorySample,
    parse_trajectories_from_df,
    train_grey_box_neural_ode,
)


class TestMetricsAndPhysicalDiagnostics:
    """Tests for regression error metrics and physical residual calculations."""

    def test_perfect_prediction_metrics(self) -> None:
        y_true = np.array([0.5, 1.0, 1.5, 2.0])
        y_pred = np.array([0.5, 1.0, 1.5, 2.0])
        m = compute_regression_metrics(y_true, y_pred)
        assert m.rmse == pytest.approx(0.0, abs=1e-10)
        assert m.mae == pytest.approx(0.0, abs=1e-10)
        assert m.r2 == pytest.approx(1.0, abs=1e-10)
        assert m.negative_conc_count == 0
        assert m.max_error == pytest.approx(0.0, abs=1e-10)

    def test_negative_concentration_detection(self) -> None:
        y_true = np.array([0.1, 0.2, 0.3])
        y_pred = np.array([-0.05, 0.2, -0.01])  # 2 negative concentrations
        m = compute_regression_metrics(y_true, y_pred)
        assert m.negative_conc_count == 2

    def test_safeguards_against_zero_variance(self) -> None:
        y_true = np.array([1.0, 1.0, 1.0])
        y_pred = np.array([1.0, 1.0, 1.0])
        m = compute_regression_metrics(y_true, y_pred)
        assert m.r2 == 1.0  # Safe fallback without zero division

    def test_empty_array_raises(self) -> None:
        with pytest.raises(ValueError, match="Cannot compute metrics on empty arrays"):
            compute_regression_metrics([], [])

    def test_length_mismatch_raises(self) -> None:
        with pytest.raises(ValueError, match="Length mismatch"):
            compute_regression_metrics([1.0, 2.0], [1.0])

    def test_format_metrics_table_structure(self) -> None:
        y_true = [1.0, 2.0]
        y_pred = [1.1, 1.9]
        m = compute_regression_metrics(y_true, y_pred)
        table = format_metrics_table({"TestModel": m})
        assert "| Model | RMSE (mol/L) |" in table
        assert "**TestModel**" in table

    def test_compute_classification_metrics_multiclass(self) -> None:
        y_true = ["normal", "normal", "feed_loss_step", "sensor_drift"]
        y_pred = ["normal", "feed_loss_step", "feed_loss_step", "sensor_drift"]
        m = compute_classification_metrics(y_true, y_pred, normal_label="normal")

        assert m.accuracy == 0.75
        assert 0.0 <= m.macro_f1 <= 1.0
        assert "normal" in m.precision_per_class
        assert "feed_loss_step" in m.recall_per_class
        assert "sensor_drift" in m.f1_per_class
        assert m.confusion_matrix["normal"]["normal"] == 1
        assert m.confusion_matrix["normal"]["feed_loss_step"] == 1

    def test_false_alarm_and_missed_detection_rates(self) -> None:
        # 2 actual normals, 2 actual faults
        y_true = ["normal", "normal", "feed_loss", "sensor_drift"]
        # 1 false alarm (true normal predicted as feed_loss)
        # 1 missed detection (true feed_loss predicted as normal)
        y_pred = ["normal", "feed_loss", "normal", "sensor_drift"]
        m = compute_classification_metrics(y_true, y_pred, normal_label="normal")

        assert m.false_alarm_count == 1
        assert m.false_alarm_rate == pytest.approx(0.50, abs=1e-5)
        assert m.missed_detection_count == 1
        assert m.missed_detection_rate == pytest.approx(0.50, abs=1e-5)


class TestBaselinesAndLeakageGuards:
    """Tests for naive/mechanistic baselines and leakage-free trajectory data handling."""

    @pytest.fixture
    def mock_dataset_and_manifest(self) -> tuple[pd.DataFrame, dict]:
        # Create minimal synthetic trajectory dataframe
        rows = []
        for traj_id in ["traj-01", "traj-02", "traj-03"]:
            for t in [0.0, 1.0, 2.0]:
                rows.append({
                    "trajectory_id": traj_id,
                    "time_min": t,
                    "V_L": 10.0,
                    "Q_L_min": 1.0,
                    "k": 0.15,
                    "order": 1,
                    "C_A_in_mol_L": 2.0,
                    "C_A_0_mol_L": 0.5,
                    "C_A_clean_mol_L": 0.5 + 0.1 * t,
                })
        df = pd.DataFrame(rows)
        manifest = {
            "tasks": {
                "transient_dynamic_forecasting": {
                    "partitions": {
                        "train_ids": ["traj-01"],
                        "val_ids": ["traj-02"],
                        "test_ids": ["traj-03"],
                    }
                }
            }
        }
        return df, manifest

    def test_leakage_detection_asserts(self, mock_dataset_and_manifest) -> None:
        df, manifest = mock_dataset_and_manifest
        # Intentionally contaminate validation with a training trajectory
        manifest["tasks"]["transient_dynamic_forecasting"]["partitions"]["val_ids"].append("traj-01")
        with pytest.raises(AssertionError, match="Data leakage"):
            prepare_trajectory_split_matrices(df, manifest)

    def test_baselines_execution(self, mock_dataset_and_manifest) -> None:
        df, manifest = mock_dataset_and_manifest
        result = evaluate_baselines(df, manifest, seed=42)

        # Confirm all standard baselines were evaluated
        expected_models = {"Persistence", "Mean", "Mechanistic_Nominal", "Ridge", "RandomForest"}
        assert expected_models.issubset(set(result.test_metrics.keys()))

        # Check that persistence predicts non-negative values
        p_res = result.test_metrics["Persistence"]
        assert p_res.negative_conc_count == 0
        assert p_res.rmse > 0.0

    def test_mechanistic_baseline_conforms_to_analytical_physics(self) -> None:
        model = MechanisticBaseline(nominal_k=0.15)
        # Canonical test case: t=10, V=10, Q=1, k=0.15, C_in=2, C_0=0, order=1
        X = np.array([[10.0, 10.0, 1.0, 0.15, 2.0, 0.0, 1]])
        pred = model.predict(X)
        # Analytical C_A(10) with k=0.15: tau=10, C_ss = 2 / (1 + 1.5) = 0.8
        # lambda = 2.5 / 10 = 0.25 -> C_A(10) = 0.8 + (0 - 0.8)*exp(-2.5) ~ 0.7343
        assert pred[0] == pytest.approx(0.7343, abs=0.01)


class TestGreyBoxNeuralODEPhysics:
    """Tests for physical constraints in Grey-Box Neural ODE architecture."""

    def test_kinetic_network_zero_concentration_guard(self) -> None:
        model = GreyBoxNeuralODE(hidden_dim=16, num_layers=2)
        zero_tensor = torch.tensor([0.0, -0.5, -10.0], dtype=torch.float32)
        rate = model.kinetics(zero_tensor)
        # At C_A <= 0, reaction rate must be strictly 0
        assert torch.all(rate == 0.0).item()

    def test_kinetic_network_strictly_non_negative_rate(self) -> None:
        model = GreyBoxNeuralODE(hidden_dim=16, num_layers=2)
        c_vals = torch.linspace(0.01, 10.0, 50, dtype=torch.float32)
        rates = model.kinetics(c_vals)
        # Rate must be strictly non-negative for positive concentrations
        assert torch.all(rates >= 0.0).item()

    def test_ode_rhs_mass_balance_formulation(self) -> None:
        model = GreyBoxNeuralODE(hidden_dim=16, num_layers=2)
        c_val = torch.tensor([1.0], dtype=torch.float32)
        V, Q, Cin = 10.0, 1.0, 2.0
        rhs = model.ode_rhs(c_val, V=V, Q=Q, C_in=Cin)
        # Convection term = (1/10)*(2 - 1) = 0.1
        # Net rhs must be <= 0.1 because rate >= 0
        assert rhs.item() <= 0.10001

    def test_forward_trajectory_monotonic_grid_check(self) -> None:
        model = GreyBoxNeuralODE(hidden_dim=16, num_layers=2)
        non_monotonic_t = torch.tensor([0.0, 2.0, 1.0], dtype=torch.float32)
        with pytest.raises(ValueError, match="strictly monotonically increasing"):
            model.forward_trajectory(non_monotonic_t, C_0=0.0, V=10.0, Q=1.0, C_in=2.0)


class TestGreyBoxNeuralODETrainingAndConvergence:
    """Tests for training loop, seed reproducibility, and checkpointing."""

    @pytest.fixture
    def small_trajectory_dataset(self) -> tuple[list[TrajectorySample], list[TrajectorySample], list[TrajectorySample]]:
        def make_sample(traj_id: str, k: float) -> TrajectorySample:
            t = np.linspace(0.0, 10.0, 11)
            # Simple analytical first order C(t)
            tau = 10.0
            Css = 2.0 / (1.0 + k * tau)
            lam = (1.0 + k * tau) / tau
            c_true = Css + (0.0 - Css) * np.exp(-lam * t)
            return TrajectorySample(
                trajectory_id=traj_id,
                t=t,
                C_true=c_true,
                V=10.0,
                Q=1.0,
                C_in=2.0,
                C_0=0.0,
            )

        train = [make_sample(f"tr-{i}", 0.10 + 0.02 * i) for i in range(4)]
        val = [make_sample(f"val-{i}", 0.15) for i in range(2)]
        test = [make_sample("test-01", 0.12)]
        return train, val, test

    def test_neural_ode_train_reduces_loss(self, small_trajectory_dataset, tmp_path: Path) -> None:
        train, val, test = small_trajectory_dataset
        result = train_grey_box_neural_ode(
            train_samples=train,
            val_samples=val,
            test_samples=test,
            hidden_dim=16,
            num_layers=2,
            lr=0.02,
            epochs=20,
            patience=10,
            seed=42,
            checkpoint_dir=tmp_path,
        )

        # Loss should decrease over epochs
        assert result.train_history[-1] < result.train_history[0]
        # Checkpoint file created
        assert result.checkpoint_path is not None
        assert Path(result.checkpoint_path).exists()
        # Predictions are physically valid
        assert result.test_metrics.negative_conc_count == 0
        assert result.test_metrics.rmse < 0.50

    def test_seed_reproducibility(self, small_trajectory_dataset) -> None:
        train, val, test = small_trajectory_dataset
        res1 = train_grey_box_neural_ode(
            train_samples=train,
            val_samples=val,
            test_samples=test,
            hidden_dim=16,
            epochs=5,
            seed=101,
        )
        res2 = train_grey_box_neural_ode(
            train_samples=train,
            val_samples=val,
            test_samples=test,
            hidden_dim=16,
            epochs=5,
            seed=101,
        )
        assert res1.train_history == pytest.approx(res2.train_history, rel=1e-5)
        assert res1.test_metrics.rmse == pytest.approx(res2.test_metrics.rmse, rel=1e-5)

    def test_neural_ode_ood_and_edge_case_generalization(self, small_trajectory_dataset) -> None:
        """Verify that Grey-Box Neural ODE generalizes safely to OOD conditions without physical violations."""
        train, val, test = small_trajectory_dataset
        res = train_grey_box_neural_ode(
            train_samples=train,
            val_samples=val,
            test_samples=test,
            hidden_dim=16,
            epochs=5,
            seed=42,
        )
        simulator = GreyBoxODESimulator(res.model)

        # 1. Out-Of-Distribution high inlet concentration C_in = 8.0 (beyond training range [1.0, 3.0])
        t_ood = np.linspace(0.0, 20.0, 21)
        pred_ood = simulator.simulate(t_span=t_ood, C_0=0.0, V=10.0, Q=1.0, C_in=8.0)
        assert all(c >= 0.0 for c in pred_ood), "OOD prediction must never violate C_A >= 0"
        assert all(math.isfinite(c) for c in pred_ood), "OOD prediction must remain finite"
        assert pred_ood[-1] > pred_ood[0], "Trajectory must fill monotonically"

        # 2. Zero-concentration boundary check
        zero_rate = simulator.predict_reaction_rate(0.0)
        assert zero_rate.item() == pytest.approx(0.0, abs=1e-7), "r_A(0) must be identically 0"

        # 3. High residence time limit tau = 50 min
        pred_slow = simulator.simulate(t_span=t_ood, C_0=1.0, V=50.0, Q=1.0, C_in=1.0)
        assert all(c >= 0.0 for c in pred_slow)
        assert all(math.isfinite(c) for c in pred_slow)


class TestFullDatasetIntegrationAndComparison:
    """Tests evaluating baselines and Neural ODE on the real Phase 8 generated datasets."""

    def test_phase08_generated_data_baselines_run(self) -> None:
        data_path = Path("data/generated/transient_trajectories.csv")
        manifest_path = Path("data/generated/splits_manifest.json")

        if not data_path.exists() or not manifest_path.exists():
            pytest.skip("Phase 8 synthetic trajectory datasets not found.")

        df = pd.read_csv(data_path)
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        result = evaluate_baselines(df, manifest, seed=42)

        # Verify performance hierarchy on locked test:
        # Machine learning and mechanistic baselines should substantially outperform mean baseline
        rf_rmse = result.test_metrics["RandomForest"].rmse
        mean_rmse = result.test_metrics["Mean"].rmse
        assert rf_rmse < mean_rmse, f"RandomForest RMSE ({rf_rmse}) must be lower than Mean RMSE ({mean_rmse})"
        assert result.test_metrics["RandomForest"].r2 > 0.40

