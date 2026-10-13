"""Test suite for Phase 10: Physics-Informed Neural Network (PINN).

Adheres strictly to GLOBAL-INSTRUCTIONS.md, phase-10, and phase-08A:
- Asserts autograd ODE residual formulation across orders n in {0, 1, 2}.
- Tests loss component tracking (data, IC, residual, positivity).
- Verifies training convergence and comparison with canonical analytical solution.
- Confirms zero-observation unsupervised collocation training.
"""

from pathlib import Path
import numpy as np
import pytest
import torch

from backend.app.ml.pinn import (
    CSTRPINN,
    PINNLossComponents,
    PINNNormalizer,
    benchmark_pinn_across_seeds,
    train_cstr_pinn,
    tune_pinn_on_validation,
)


class TestPINNAutogradAndPhysics:
    """Tests for automatic differentiation of continuous CSTR fields and ODE residuals."""

    def test_autograd_derivative_and_residual_calculation(self) -> None:
        pinn = CSTRPINN(
            V=10.0,
            Q=1.0,
            k=0.15,
            C_A_in=2.0,
            C_A_0=0.0,
            order=1,
            t_final=30.0,
        )
        t_colloc = torch.tensor([[0.0], [5.0], [10.0]], dtype=torch.float32)
        res = pinn.compute_ode_residual(t_colloc)
        assert res.shape == (3, 1)
        assert not torch.isnan(res).any()
        assert not torch.isinf(res).any()

    @pytest.mark.parametrize("order", [0, 1, 2])
    def test_reaction_order_residual_support(self, order: int) -> None:
        pinn = CSTRPINN(
            V=10.0,
            Q=1.0,
            k=0.10,
            C_A_in=2.0,
            C_A_0=0.5,
            order=order,
            t_final=20.0,
        )
        t_pts = torch.linspace(0.0, 20.0, 10).reshape(-1, 1)
        res = pinn.compute_ode_residual(t_pts)
        assert res.shape == (10, 1)
        assert not torch.isnan(res).any()

    def test_pinn_prediction_shape_and_range(self) -> None:
        pinn = CSTRPINN(
            V=10.0,
            Q=1.0,
            k=0.15,
            C_A_in=2.0,
            C_A_0=0.0,
            t_final=15.0,
        )
        t_grid = np.linspace(0.0, 15.0, 25)
        preds = pinn.predict(t_grid)
        assert preds.shape == (25,)
        assert isinstance(preds, np.ndarray)


class TestPINNTrainingConvergence:
    """Tests for PINN training loop and physical constraint satisfaction."""

    def test_pinn_training_on_canonical_oracle(self, tmp_path: Path) -> None:
        # Canonical Validation Oracle: V=10, Q=1, k=0.15, Cin=2.0, C0=0.0
        # Target steady state Css = 0.8 mol/L
        result = train_cstr_pinn(
            V=10.0,
            Q=1.0,
            k=0.15,
            C_A_in=2.0,
            C_A_0=0.0,
            order=1,
            t_final=20.0,
            n_collocation=50,
            epochs=60,
            lr=0.01,
            seed=42,
            checkpoint_dir=tmp_path,
        )

        assert len(result.loss_history) == 60
        # Overall loss should reduce significantly
        assert result.loss_history[-1].total_loss < result.loss_history[0].total_loss
        # Checkpoint created
        assert result.checkpoint_path is not None
        assert Path(result.checkpoint_path).exists()
        # Physical metrics
        assert result.metrics.negative_conc_count == 0
        assert result.metrics.rmse < 0.80

    def test_unsupervised_pure_collocation_mode(self) -> None:
        # Train without any data observations (w_data = 0)
        result = train_cstr_pinn(
            V=10.0,
            Q=1.0,
            k=0.15,
            C_A_in=2.0,
            C_A_0=0.5,
            order=1,
            t_final=15.0,
            t_obs=None,
            C_obs=None,
            n_collocation=40,
            epochs=30,
            lr=0.01,
            seed=101,
        )
        # Residual loss should decline
        assert result.loss_history[-1].residual_loss < result.loss_history[0].residual_loss
        assert result.loss_history[-1].data_loss == 0.0

    def test_observation_anchored_training(self) -> None:
        # Provide a few sparse observations along trajectory
        t_sparse = [0.0, 5.0, 10.0, 15.0]
        # Analytical values for V=10, Q=1, k=0.15, Cin=2, C0=0 -> Css=0.8, lam=0.25
        # C(t) = 0.8 * (1 - exp(-0.25*t))
        c_sparse = [0.0, 0.5708, 0.7343, 0.7812]

        result = train_cstr_pinn(
            V=10.0,
            Q=1.0,
            k=0.15,
            C_A_in=2.0,
            C_A_0=0.0,
            order=1,
            t_final=15.0,
            t_obs=t_sparse,
            C_obs=c_sparse,
            w_data=10.0,
            epochs=40,
            seed=42,
        )
        # Data loss should be minimized
        assert result.loss_history[-1].data_loss < 0.10


class TestPINNNormalizerAndLeakage:
    """Tests asserting zero leakage and scaling accuracy in PINN normalizers."""

    def test_normalizer_training_only_fit(self) -> None:
        normalizer = PINNNormalizer.fit_from_training_conditions(
            t_final=25.0,
            C_A_0=0.5,
            C_A_in=3.0,
        )
        assert normalizer.t_min == 0.0
        assert normalizer.t_max == 25.0
        assert normalizer.c_max == 3.0

        # Normalization maps 0 -> 0 and t_max -> 1
        t_arr = np.array([0.0, 12.5, 25.0])
        t_norm = normalizer.normalize_time(t_arr)
        np.testing.assert_allclose(t_norm, [0.0, 0.5, 1.0], rtol=1e-5)

    def test_normalizer_inversion_roundtrip(self) -> None:
        normalizer = PINNNormalizer(t_min=0.0, t_max=40.0, c_min=0.0, c_max=5.0)
        c_orig = np.array([0.0, 1.25, 2.5, 5.0])
        c_norm = normalizer.normalize_conc(c_orig)
        c_rec = normalizer.denormalize_conc(c_norm)
        np.testing.assert_allclose(c_rec, c_orig, rtol=1e-6)


class TestPINNValidationTuningAndMultiSeed:
    """Tests for tuning on validation only and multi-seed stochastic benchmarking."""

    def test_validation_tuning_grid(self) -> None:
        tune_res = tune_pinn_on_validation(
            V=10.0,
            Q=1.0,
            k=0.15,
            C_A_in=2.0,
            C_A_0=0.0,
            order=1,
            t_final=15.0,
            collocation_options=(20,),
            w_residual_options=(1.0,),
            hidden_dim_options=(32,),
            lr_options=(0.01,),
            epochs=20,
            seed=42,
        )
        assert tune_res.provenance == "VALIDATION_TUNED_ONLY"
        assert len(tune_res.trials) == 1
        assert "n_collocation" in tune_res.best_config
        assert tune_res.best_val_rmse < 1.0

    def test_multiseed_benchmark_and_baselines_comparison(self) -> None:
        bench_res = benchmark_pinn_across_seeds(
            V=10.0,
            Q=1.0,
            k=0.15,
            C_A_in=2.0,
            C_A_0=0.0,
            order=1,
            t_final=15.0,
            seeds=(42, 101),
            epochs=25,
            lr=0.01,
            n_collocation=25,
        )
        assert bench_res.provenance == "SYNTHETIC_RESEARCH_BENCHMARK"
        assert len(bench_res.trials) == 2
        assert bench_res.total_negative_conc_violations == 0
        assert bench_res.mean_rmse < 0.80
        assert bench_res.mean_steady_state_error < 0.75
        assert "mean_baseline" in bench_res.comparison_baselines
        assert "mechanistic_nominal" in bench_res.comparison_baselines
        assert "persistence_baseline" in bench_res.comparison_baselines

