"""Tests for Phase 5 parameter sweeps and sensitivity analysis."""

import math
import pytest
from fastapi.testclient import TestClient

from backend.app.core.sweeps import (
    SweepVariable,
    compute_1d_parameter_sweep,
    compute_2d_parameter_sweep,
    compute_lhs_parameter_sweep,
)
from backend.app.main import app

client = TestClient(app)


class TestCore1DSweeps:
    """Verify 1D parameter sweep scientific logic and known monotonicity trends."""

    def test_sweep_rate_constant_monotonicity(self):
        """Increasing k must monotonically increase conversion and decrease C_A,ss."""
        res = compute_1d_parameter_sweep(
            variable=SweepVariable.RATE_CONSTANT,
            min_val=0.01,
            max_val=1.0,
            n_points=25,
            baseline_V=10.0,
            baseline_Q=1.0,
            baseline_C_in=2.0,
            baseline_k=0.15,
            order=1,
        )

        assert len(res.points) == 25
        assert all(p.status == "ok" for p in res.points)

        # Monotonicity checks
        conversions = [p.conversion for p in res.points]
        concs = [p.C_A_ss for p in res.points]

        assert all(c is not None for c in conversions)
        for i in range(len(conversions) - 1):
            assert conversions[i + 1] > conversions[i]
            assert concs[i + 1] < concs[i]

        # Local sensitivity at baseline (k=0.15, tau=10 => X = 1.5/2.5 = 0.60)
        # Analytical dX/dk = tau / (1 + k*tau)^2 = 10 / 2.5^2 = 10 / 6.25 = 1.6
        assert res.local_sensitivity is not None
        assert math.isclose(res.local_sensitivity["derivative_dX_dp"], 1.6, rel_tol=1e-3)
        assert res.local_sensitivity["normalized_elasticity"] > 0.0

    def test_sweep_volume_monotonicity(self):
        """Increasing V increases residence time tau and conversion."""
        res = compute_1d_parameter_sweep(
            variable=SweepVariable.VOLUME,
            min_val=1.0,
            max_val=50.0,
            n_points=20,
            baseline_V=10.0,
            baseline_Q=1.0,
            baseline_C_in=2.0,
            baseline_k=0.15,
            order=1,
        )

        conversions = [p.conversion for p in res.points]
        for i in range(len(conversions) - 1):
            assert conversions[i + 1] > conversions[i]

    def test_sweep_flow_rate_monotonicity(self):
        """Increasing Q decreases residence time and decreases conversion."""
        res = compute_1d_parameter_sweep(
            variable=SweepVariable.FLOW_RATE,
            min_val=0.2,
            max_val=10.0,
            n_points=20,
            baseline_V=10.0,
            baseline_Q=1.0,
            baseline_C_in=2.0,
            baseline_k=0.15,
            order=1,
        )

        conversions = [p.conversion for p in res.points]
        for i in range(len(conversions) - 1):
            assert conversions[i + 1] < conversions[i]

    def test_first_order_conversion_invariance_to_inlet_conc(self):
        """For first-order kinetics, conversion X_A is independent of C_A,in."""
        res = compute_1d_parameter_sweep(
            variable=SweepVariable.INLET_CONCENTRATION,
            min_val=0.5,
            max_val=10.0,
            n_points=15,
            baseline_V=10.0,
            baseline_Q=1.0,
            baseline_C_in=2.0,
            baseline_k=0.15,
            order=1,
        )

        conversions = [p.conversion for p in res.points]
        # All points should give X_A = 0.60
        for conv in conversions:
            assert conv is not None
            assert math.isclose(conv, 0.60, rel_tol=1e-6)


class TestCore2DSweeps:
    """Verify 2D surface parameter sweep grids."""

    def test_2d_sweep_grid(self):
        res = compute_2d_parameter_sweep(
            var_x=SweepVariable.RATE_CONSTANT,
            x_min=0.05,
            x_max=0.5,
            n_x=10,
            var_y=SweepVariable.VOLUME,
            y_min=5.0,
            y_max=25.0,
            n_y=8,
            baseline_V=10.0,
            baseline_Q=1.0,
            baseline_C_in=2.0,
            baseline_k=0.15,
            order=1,
        )

        assert len(res.x_values) == 10
        assert len(res.y_values) == 8
        assert len(res.conversion_grid) == 8  # rows = y
        assert len(res.conversion_grid[0]) == 10  # cols = x

        # Corner check: lowest k and lowest V gives lowest conversion
        conv_min = res.conversion_grid[0][0]
        # Corner check: highest k and highest V gives highest conversion
        conv_max = res.conversion_grid[-1][-1]
        assert conv_min is not None and conv_max is not None
        assert conv_max > conv_min


class TestSweepValidationAndBounds:
    """Verify boundary checks and exceptions."""

    def test_invalid_range(self):
        with pytest.raises(ValueError, match="min_val .* must be strictly less than max_val"):
            compute_1d_parameter_sweep(SweepVariable.RATE_CONSTANT, 1.0, 0.5, 20, 10, 1, 2, 0.15)

    def test_non_positive_volume_bound(self):
        with pytest.raises(ValueError, match="must be strictly positive"):
            compute_1d_parameter_sweep(SweepVariable.VOLUME, 0.0, 10.0, 20, 10, 1, 2, 0.15)

    def test_oversized_points(self):
        with pytest.raises(ValueError, match="exceeds maximum limit"):
            compute_1d_parameter_sweep(SweepVariable.RATE_CONSTANT, 0.1, 1.0, 2000, 10, 1, 2, 0.15)

    def test_2d_same_variable_rejected(self):
        with pytest.raises(ValueError, match="must be different"):
            compute_2d_parameter_sweep(
                SweepVariable.VOLUME, 1, 10, 5,
                SweepVariable.VOLUME, 5, 20, 5,
                10, 1, 2, 0.15
            )


class TestSweepApiEndpoint:
    """Verify POST /api/v1/simulations/parameter-sweep."""

    def test_1d_sweep_api_call(self):
        payload = {
            "is_2d": False,
            "variable": "k",
            "min_val": 0.01,
            "max_val": 0.5,
            "n_points": 20,
            "baseline_V": 10.0,
            "baseline_Q": 1.0,
            "baseline_C_in": 2.0,
            "baseline_k": 0.15,
            "order": 1,
        }
        response = client.post("/api/v1/simulations/parameter-sweep", json=payload)
        assert response.status_code == 200
        data = response.json()

        assert data["sweep_type"] == "1D"
        assert data["variable"] == "k"
        assert len(data["points"]) == 20
        assert "trend_summary" in data
        assert data["local_sensitivity"] is not None

    def test_2d_sweep_api_call(self):
        payload = {
            "is_2d": True,
            "variable": "k",
            "min_val": 0.05,
            "max_val": 0.3,
            "n_points": 10,
            "variable_y": "V",
            "min_val_y": 5.0,
            "max_val_y": 20.0,
            "n_points_y": 8,
            "baseline_V": 10.0,
            "baseline_Q": 1.0,
            "baseline_C_in": 2.0,
            "baseline_k": 0.15,
            "order": 1,
        }
        response = client.post("/api/v1/simulations/parameter-sweep", json=payload)
        assert response.status_code == 200
        data = response.json()

        assert data["sweep_type"] == "2D"
        assert len(data["x_values"]) == 10
        assert len(data["y_values"]) == 8
        assert len(data["conversion_grid"]) == 8

    def test_invalid_sweep_api_rejected(self):
        # min_val > max_val
        payload = {
            "is_2d": False,
            "variable": "k",
            "min_val": 5.0,
            "max_val": 1.0,
            "n_points": 20,
        }
        response = client.post("/api/v1/simulations/parameter-sweep", json=payload)
        assert response.status_code == 422


class TestLatinHypercubeSweeps:
    """Verify multi-parameter sweeps using Latin Hypercube Sampling (SciPy QMC)."""

    def test_lhs_sweep_generation_and_coverage(self):
        bounds = {
            "V": (2.0, 40.0),
            "Q": (0.2, 4.0),
            "k": (0.02, 1.0),
            "C_A_in": (0.5, 4.0),
        }
        res = compute_lhs_parameter_sweep(bounds=bounds, n_samples=30, seed=123, order=1)

        assert res.n_samples == 30
        assert len(res.points) == 30
        assert res.failed_count == 0
        assert res.summary_statistics["successful_evaluations"] == 30

        for p in res.points:
            assert bounds["V"][0] <= p.V <= bounds["V"][1]
            assert bounds["Q"][0] <= p.Q <= bounds["Q"][1]
            assert bounds["k"][0] <= p.k <= bounds["k"][1]
            assert bounds["C_A_in"][0] <= p.C_A_in <= bounds["C_A_in"][1]
            assert p.status == "ok"
            assert p.tau > 0.0
            assert p.C_A_ss >= 0.0
            assert 0.0 <= p.conversion <= 1.0
            assert abs(p.residual) < 1e-12

    def test_lhs_sweep_reproducibility_with_fixed_seed(self):
        bounds = {
            "V": (5.0, 25.0),
            "Q": (0.5, 2.5),
            "k": (0.05, 0.5),
            "C_A_in": (1.0, 3.0),
        }
        res1 = compute_lhs_parameter_sweep(bounds=bounds, n_samples=15, seed=999, order=1)
        res2 = compute_lhs_parameter_sweep(bounds=bounds, n_samples=15, seed=999, order=1)

        for p1, p2 in zip(res1.points, res2.points):
            assert p1.V == p2.V
            assert p1.Q == p2.Q
            assert p1.k == p2.k
            assert p1.C_A_in == p2.C_A_in
            assert p1.C_A_ss == p2.C_A_ss

    def test_lhs_sweep_invalid_bounds_rejected(self):
        # Non-positive volume bound
        bad_bounds_V = {
            "V": (-1.0, 10.0),
            "Q": (1.0, 5.0),
            "k": (0.1, 1.0),
            "C_A_in": (1.0, 2.0),
        }
        with pytest.raises(ValueError, match="strictly positive"):
            compute_lhs_parameter_sweep(bounds=bad_bounds_V, n_samples=10)

        # Upper bound <= Lower bound
        inverted_bounds = {
            "V": (10.0, 5.0),
            "Q": (1.0, 5.0),
            "k": (0.1, 1.0),
            "C_A_in": (1.0, 2.0),
        }
        with pytest.raises(ValueError, match="strictly less than upper bound"):
            compute_lhs_parameter_sweep(bounds=inverted_bounds, n_samples=10)

    def test_lhs_sweep_api_endpoint_success(self):
        payload = {
            "n_samples": 20,
            "seed": 42,
            "order": 1,
            "bounds": {
                "V": [2.0, 20.0],
                "Q": [0.5, 3.0],
                "k": [0.05, 0.5],
                "C_A_in": [1.0, 4.0],
            },
        }
        response = client.post("/api/v1/simulations/parameter-sweep/lhs", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["sweep_type"] == "LHS"
        assert data["n_samples"] == 20
        assert data["seed"] == 42
        assert len(data["points"]) == 20
        assert data["failed_count"] == 0
        assert data["summary_statistics"]["successful_evaluations"] == 20
        assert "mean_conversion" in data["summary_statistics"]

    def test_lhs_sweep_api_endpoint_invalid_bounds(self):
        payload = {
            "n_samples": 20,
            "seed": 42,
            "order": 1,
            "bounds": {
                "V": [-5.0, 20.0],
                "Q": [0.5, 3.0],
                "k": [0.05, 0.5],
                "C_A_in": [1.0, 4.0],
            },
        }
        response = client.post("/api/v1/simulations/parameter-sweep/lhs", json=payload)
        assert response.status_code == 422

