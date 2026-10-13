"""Tests for Phase 8: Mechanistic synthetic data generation, LHS sampling, edge cases, and zero-leakage splits."""

import json
import math
import numpy as np
import pytest

from backend.app.core.splitting import (
    SplitPartition,
    build_split_manifest,
    fit_scaler_train_only,
    split_trajectories_by_id,
)
from backend.app.core.synthetic_data import (
    FaultDiagnosisSample,
    ParameterBounds,
    generate_dynamic_trajectories,
    generate_edge_cases,
    generate_fault_diagnosis_dataset,
    generate_steady_state_dataset,
    sample_parameters_lhs,
)


class TestLHSSamplingAndBounds:
    """Verify Quasi-Monte Carlo Latin Hypercube Sampling covers bounded physical space."""

    def test_lhs_samples_within_bounds(self):
        bounds = ParameterBounds()
        samples = sample_parameters_lhs(n_samples=50, order=1, bounds=bounds, seed=42)

        assert len(samples) == 50
        for s in samples:
            assert bounds.V_min <= s["V"] <= bounds.V_max
            assert bounds.Q_min <= s["Q"] <= bounds.Q_max
            assert bounds.C_in_min <= s["C_A_in"] <= bounds.C_in_max
            assert bounds.C_0_min <= s["C_A_0"] <= bounds.C_0_max
            k_min, k_max = bounds.k_ranges[1]
            assert k_min <= s["k"] <= k_max

    def test_lhs_deterministic_reproducibility(self):
        s1 = sample_parameters_lhs(n_samples=20, order=1, seed=123)
        s2 = sample_parameters_lhs(n_samples=20, order=1, seed=123)
        assert s1 == s2


class TestEdgeCasesInclusion:
    """Acceptance Gate: Canonical validation oracle and critical edge cases are included."""

    def test_canonical_oracle_present(self):
        edge_cases = generate_edge_cases()
        types = [ec.get("edge_case_type") for ec in edge_cases]

        assert "canonical_oracle" in types
        assert "zero_inlet_concentration" in types
        assert "zero_initial_concentration" in types
        assert "fast_kinetics_near_complete_conversion" in types
        assert "slow_kinetics_near_zero_conversion" in types
        assert "zero_order_complete_depletion" in types

        # Check canonical oracle values specifically
        oracle = next(ec for ec in edge_cases if ec["edge_case_type"] == "canonical_oracle")
        assert oracle["V"] == 10.0
        assert oracle["Q"] == 1.0
        assert oracle["k"] == 0.15
        assert oracle["C_A_in"] == 2.0


class TestSteadyStateDatasetGeneration:
    """Verify steady-state dataset generation and physical validity."""

    def test_generate_steady_state_dataset(self):
        samples = generate_steady_state_dataset(n_samples_per_order=10, seed=42)
        # 7 edge cases + 3 * 10 = 37 records
        assert len(samples) == 37

        for s in samples:
            assert s.V > 0
            assert s.Q > 0
            assert s.C_A_in >= 0
            assert s.k >= 0
            assert s.tau == pytest.approx(s.V / s.Q, rel=1e-9)
            if not (s.order == 0 and s.C_A_ss == 0.0):
                assert abs(s.residual) < 1e-6
            assert s.provenance == "SYNTHETIC_MECHANISTIC_SOLVER"


class TestDynamicTrajectoriesGeneration:
    """Verify transient trajectories simulation and noise handling."""

    def test_generate_dynamic_trajectories(self):
        trajectories = generate_dynamic_trajectories(
            n_trajectories=6,
            n_points_per_traj=21,
            noise_sigma=0.01,
            seed=42,
        )
        assert len(trajectories) >= 6

        for tr in trajectories:
            m = tr.metadata
            assert m.n_points == 21
            assert len(tr.t) == 21
            assert len(tr.C_A_clean) == 21
            assert len(tr.C_A_noisy) == 21

            # Strictly non-negative concentrations
            assert all(c >= 0.0 for c in tr.C_A_clean)
            assert all(c >= 0.0 for c in tr.C_A_noisy)
            assert tr.t[0] == 0.0
            assert tr.t[-1] == pytest.approx(m.t_final)


class TestSplittingAndLeakagePrevention:
    """Acceptance Gate: Disjoint 70/15/15 partitions and train-only transform fitting."""

    def test_split_trajectories_disjointness(self):
        traj_ids = [f"traj_{i:04d}" for i in range(100)]
        partition = split_trajectories_by_id(traj_ids, seed=42)

        # Proportions
        assert len(partition.train_ids) == 70
        assert len(partition.val_ids) == 15
        assert len(partition.test_ids) == 15

        # Disjoint assertion
        s_train = set(partition.train_ids)
        s_val = set(partition.val_ids)
        s_test = set(partition.test_ids)

        assert s_train.isdisjoint(s_val)
        assert s_train.isdisjoint(s_test)
        assert s_val.isdisjoint(s_test)
        assert len(s_train) + len(s_val) + len(s_test) == 100

    def test_partition_assert_disjoint_raises_on_overlap(self):
        # Manually construct an overlapping partition to ensure assertion fires
        overlapping = SplitPartition(
            train_ids=("id1", "id2", "id3"),
            val_ids=("id3", "id4"),
            test_ids=("id5",),
            seed=42,
            n_total=6,
        )
        with pytest.raises(AssertionError, match="Leakage detected"):
            overlapping.assert_disjoint()

    def test_fit_scaler_train_only(self):
        """Verify scaler mean and variance are learned strictly from train partition."""
        np.random.seed(42)
        # Train data centered at 10.0
        train_data = np.random.normal(loc=10.0, scale=2.0, size=(100, 2))
        # Val data centered at 50.0 (distribution shift / different operating region)
        val_data = np.random.normal(loc=50.0, scale=2.0, size=(20, 2))
        # Test data centered at 100.0
        test_data = np.random.normal(loc=100.0, scale=2.0, size=(20, 2))

        scaler, tr_scaled, val_scaled, test_scaled = fit_scaler_train_only(
            train_features=train_data,
            val_features=val_data,
            test_features=test_data,
        )

        # Scaler mean must match train_data mean (~10.0), NOT val or test
        assert scaler.mean_[0] == pytest.approx(10.0, abs=0.5)
        assert tr_scaled.mean(axis=0) == pytest.approx(np.zeros(2), abs=1e-7)

        # Val scaled mean should be ~ (50 - 10) / 2 = 20, proving no val contamination into scaler
        assert val_scaled.mean(axis=0)[0] > 15.0

    def test_build_split_manifest(self):
        traj_ids = [f"t_{i}" for i in range(20)]
        part = split_trajectories_by_id(traj_ids, seed=99)
        manifest = build_split_manifest(
            task_name="test_task",
            partition=part,
            dataset_sha256="dummy_hash",
        )

        assert manifest["task_name"] == "test_task"
        assert manifest["leakage_assertion"]["disjoint_train_val"] is True
        assert manifest["counts"]["total_trajectories"] == 20
        assert manifest["counts"]["train"] + manifest["counts"]["val"] + manifest["counts"]["test"] == 20


class TestFaultDiagnosisDataset:
    """Verify Task 4: Fault diagnosis and anomaly detection dataset generation and splitting."""

    def test_generate_fault_diagnosis_dataset(self):
        samples = generate_fault_diagnosis_dataset(n_trajectories=10, n_points_per_traj=21, seed=42)
        assert len(samples) > 0
        
        fault_types = {s.fault_type for s in samples}
        assert "normal" in fault_types
        assert "feed_loss_step" in fault_types
        assert "concentration_shock" in fault_types
        assert "sensor_drift" in fault_types
        assert "sensor_stuck" in fault_types

        # Verify physics integrity
        for s in samples:
            assert s.C_A_measured >= 0.0
            assert s.C_A_true >= 0.0
            assert s.Q > 0.0
            assert s.V > 0.0
            assert s.C_A_in > 0.0
            assert s.provenance == "SYNTHETIC_MECHANISTIC_SOLVER"

    def test_fault_diagnosis_disjoint_split(self):
        samples = generate_fault_diagnosis_dataset(n_trajectories=20, n_points_per_traj=11, seed=42)
        traj_ids = list(dict.fromkeys(s.trajectory_id for s in samples))
        partition = split_trajectories_by_id(traj_ids, seed=42)

        assert partition.n_total == len(traj_ids)
        s_train = set(partition.train_ids)
        s_val = set(partition.val_ids)
        s_test = set(partition.test_ids)

        assert s_train.isdisjoint(s_val)
        assert s_train.isdisjoint(s_test)
        assert s_val.isdisjoint(s_test)


class TestSolverStressAndFailedCases:
    """Verify numerical solver stability under physical stress and edge conditions."""

    def test_zero_inlet_guard_handles_cleanly(self):
        """Zero inlet concentration should result in conversion=None without unhandled ZeroDivisionError."""
        from backend.app.core.steady_state import solve_steady_state
        res = solve_steady_state(V=10.0, Q=1.0, C_A_in=0.0, order=1, k=0.15)
        assert res.C_A_ss == 0.0
        assert res.conversion is None

    def test_zero_order_depletion_boundary_no_negative_conc(self):
        """Zero-order reaction depletion should clamp cleanly to >= 0.0."""
        from backend.app.core.dynamic_solver import simulate_dynamic_cstr
        sim = simulate_dynamic_cstr(
            C_A_0=0.2,
            C_A_in=0.1,
            V=10.0,
            Q=1.0,
            order=0,
            k=0.50,  # Fast zero order depletion
            t_final=20.0,
            n_points=41,
        )
        assert all(c >= 0.0 for c in sim.C_A)
        assert sim.C_A[-1] == pytest.approx(0.0, abs=1e-4)

    def test_stiff_high_damkohler_solves_accurately(self):
        """Extreme Damkohler number (Da=144) should solve stably without numerical divergence."""
        from backend.app.core.dynamic_solver import simulate_dynamic_cstr
        sim = simulate_dynamic_cstr(
            C_A_0=0.5,
            C_A_in=4.0,
            V=40.0,
            Q=0.5,
            order=1,
            k=1.80,  # Da = 1.80 * 80 = 144.0
            t_final=50.0,
            n_points=51,
        )
        assert all(c >= 0.0 for c in sim.C_A)
        assert all(math.isfinite(c) for c in sim.C_A)
        # Steady state should be C_A_ss = 4.0 / (1 + 144) ~ 0.02758 mol/L
        expected_ss = 4.0 / (1.0 + 144.0)
        assert sim.C_A[-1] == pytest.approx(expected_ss, abs=1e-3)

    def test_failed_cases_manifest_integrity(self):
        """Verify that failed_cases.json exists and documents all edge stress scenarios."""
        import os
        import json
        manifest_path = os.path.abspath("data/generated/failed_cases.json")
        assert os.path.isfile(manifest_path)
        with open(manifest_path, "r", encoding="utf-8") as f:
            cases = json.load(f)
        assert len(cases) >= 5
        case_ids = {c["test_case_id"] for c in cases}
        assert "STRESS-01-ZERO-INLET" in case_ids
        assert "STRESS-02-ZERO-ORDER-DEPLETION" in case_ids
        assert "STRESS-03-HIGH-DAMKOHLER-STIFFNESS" in case_ids
        assert all(c["handled_status"] == "HANDLED_SUCCESSFULLY" for c in cases)
