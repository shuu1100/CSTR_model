"""Tests for conventional kinetic parameter estimation using SciPy optimization."""

import numpy as np
import pytest
from starlette.testclient import TestClient

from backend.app.core.analytical import first_order_dynamic_analytical_trajectory
from backend.app.core.dynamic_solver import solve_dynamic_cstr
from backend.app.core.parameter_estimation import (
    evaluate_kinetic_model_on_test_split,
    fit_dynamic_kinetics,
    fit_steady_state_kinetics,
    validate_data_compatibility_for_kinetics,
)
from backend.app.core.steady_state import solve_steady_state
from backend.app.main import app


@pytest.fixture
def client():
    return TestClient(app)


# ---------------------------------------------------------------------------
# Unit tests: Synthetic Parameter Recovery
# ---------------------------------------------------------------------------


def test_first_order_clean_synthetic_recovery():
    """Verify exact recovery of known oracle rate constant k=0.15 from clean dynamic trajectory."""
    V = 10.0
    Q = 1.0
    k_true = 0.15
    C_in = 1.0
    C0 = 0.1
    t_eval = np.linspace(0.0, 40.0, 41)  # dt = 1 min

    # Generate ground truth analytical trajectory
    y_true = first_order_dynamic_analytical_trajectory(
        t_points=t_eval, V=V, Q=Q, C_A_in=C_in, k=k_true, C_A_0=C0
    )

    result = fit_dynamic_kinetics(
        time=t_eval,
        C_A_obs=y_true,
        V=V,
        Q=Q,
        C_A_in=C_in,
        order=1,
        C_A_0=C0,
        k_init=0.45,  # Deliberately perturbed initial guess
    )

    assert result.optimizer_success is True
    assert result.fitted_k == pytest.approx(k_true, abs=1e-4)
    assert result.r_squared == pytest.approx(1.0, abs=1e-4)
    assert result.rmse < 1e-4
    assert result.provenance_label.startswith("FITTED ESTIMATE")
    assert result.confidence_interval_k is not None
    assert result.confidence_interval_k.std_error < 1e-3


def test_first_order_noisy_synthetic_recovery():
    """Verify recovery of rate constant under realistic sensor measurement noise."""
    np.random.seed(42)
    V = 10.0
    Q = 1.0
    k_true = 0.15
    C_in = 1.0
    C0 = 0.2
    t_eval = np.linspace(0.0, 50.0, 51)

    y_clean = first_order_dynamic_analytical_trajectory(
        t_points=t_eval, V=V, Q=Q, C_A_in=C_in, k=k_true, C_A_0=C0
    )
    noise = np.random.normal(0.0, 0.01, size=len(t_eval))
    y_noisy = np.maximum(0.0, y_clean + noise)

    result = fit_dynamic_kinetics(
        time=t_eval,
        C_A_obs=y_noisy,
        V=V,
        Q=Q,
        C_A_in=C_in,
        order=1,
        C_A_0=C0,
        k_init=0.05,
    )

    assert result.optimizer_success is True
    # Should recover within 0.005 of 0.15
    assert result.fitted_k == pytest.approx(k_true, abs=0.005)
    assert result.r_squared > 0.90
    assert result.confidence_interval_k is not None
    assert result.confidence_interval_k.std_error < 0.005
    assert result.confidence_interval_k.ci_lower < result.fitted_k < result.confidence_interval_k.ci_upper


def test_second_order_synthetic_recovery():
    """Verify recovery for second-order kinetics n=2."""
    V = 10.0
    Q = 1.0
    k_true = 0.25  # L/(mol*min)
    C_in = 2.0
    C0 = 0.5
    t_eval = np.linspace(0.0, 30.0, 31)

    sim = solve_dynamic_cstr(
        C_A_0=C0,
        C_A_in=C_in,
        V=V,
        Q=Q,
        order=2,
        k=k_true,
        t_final=30.0,
        t_eval=t_eval,
    )

    result = fit_dynamic_kinetics(
        time=sim.t,
        C_A_obs=sim.C_A,
        V=V,
        Q=Q,
        C_A_in=C_in,
        order=2,
        k_init=0.1,
    )

    assert result.optimizer_success is True
    assert result.fitted_k == pytest.approx(k_true, abs=1e-3)
    assert result.r_squared > 0.999


def test_zero_order_synthetic_recovery():
    """Verify recovery for zero-order kinetics n=0."""
    V = 10.0
    Q = 1.0
    k_true = 0.04  # mol/(L*min)
    C_in = 1.0
    C0 = 0.8
    t_eval = np.linspace(0.0, 20.0, 21)

    sim = solve_dynamic_cstr(
        C_A_0=C0,
        C_A_in=C_in,
        V=V,
        Q=Q,
        order=0,
        k=k_true,
        t_final=20.0,
        t_eval=t_eval,
    )

    result = fit_dynamic_kinetics(
        time=sim.t,
        C_A_obs=sim.C_A,
        V=V,
        Q=Q,
        C_A_in=C_in,
        order=0,
        k_init=0.1,
    )

    assert result.optimizer_success is True
    assert result.fitted_k == pytest.approx(k_true, abs=1e-3)


def test_steady_state_parameter_recovery():
    """Verify fitting rate constant from multiple steady-state residence times."""
    V = 10.0
    k_true = 0.15
    C_in = 1.0
    tau_vals = [2.0, 5.0, 10.0, 15.0, 20.0]  # Different residence times
    y_obs = []
    for tau in tau_vals:
        q = V / tau
        ss = solve_steady_state(V=V, Q=q, C_A_in=C_in, order=1, k=k_true)
        y_obs.append(ss.C_A_ss)

    result = fit_steady_state_kinetics(
        tau_or_flow=tau_vals,
        C_A_obs=y_obs,
        C_A_in=C_in,
        V=V,
        is_flow_rate=False,
        order=1,
        k_init=0.5,
    )

    assert result.optimizer_success is True
    assert result.fitted_k == pytest.approx(k_true, abs=1e-4)
    assert result.r_squared == pytest.approx(1.0, abs=1e-4)
    assert result.confidence_interval_k is not None


# ---------------------------------------------------------------------------
# Diagnostics & Identifiability Tests
# ---------------------------------------------------------------------------


def test_insufficient_points_raises():
    with pytest.raises(ValueError, match="at least 3 data points"):
        fit_dynamic_kinetics(
            time=[0.0, 1.0],
            C_A_obs=[0.5, 0.5],
            V=10.0,
            Q=1.0,
            C_A_in=1.0,
        )


def test_poor_excitation_triggers_warning():
    # Constant data series
    t = [0.0, 10.0, 20.0, 30.0]
    y = [0.4, 0.4, 0.4, 0.4]
    result = fit_dynamic_kinetics(
        time=t,
        C_A_obs=y,
        V=10.0,
        Q=1.0,
        C_A_in=1.0,
        k_init=0.15,
    )
    assert any("variance is virtually zero" in w for w in result.warnings)


def test_bound_collision_warning():
    # If observed values are 0 while inlet is high, k pushes toward upper bound
    t = [0.0, 5.0, 10.0, 15.0]
    y = [0.0, 0.0, 0.0, 0.0]
    result = fit_dynamic_kinetics(
        time=t,
        C_A_obs=y,
        V=10.0,
        Q=1.0,
        C_A_in=10.0,
        k_init=1.0,
        k_max=5.0,
    )
    assert any("hit upper bound" in w for w in result.warnings)


# ---------------------------------------------------------------------------
# API Integration Tests
# ---------------------------------------------------------------------------


def test_api_fit_kinetics_dynamic(client):
    t_eval = [0.0, 5.0, 10.0, 15.0, 20.0, 25.0, 30.0]
    y_true = first_order_dynamic_analytical_trajectory(
        t_points=t_eval, V=10.0, Q=1.0, C_A_in=1.0, k=0.15, C_A_0=0.1
    )
    payload = {
        "model_type": "dynamic",
        "order": 1,
        "time_series": t_eval,
        "observed_C_A": list(y_true),
        "V": 10.0,
        "Q": 1.0,
        "C_A_in": 1.0,
        "k_init": 0.2,
        "time_unit": "min",
        "conc_unit": "mol/L",
    }
    response = client.post("/api/v1/analysis/fit-kinetics", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["optimizer_success"] is True
    assert data["fitted_k"] == pytest.approx(0.15, abs=1e-3)
    assert data["r_squared"] > 0.999
    assert data["confidence_interval_k"] is not None
    assert "FITTED ESTIMATE" in data["provenance_label"]


def test_api_fit_kinetics_steady_state(client):
    tau_vals = [2.0, 5.0, 10.0, 20.0]
    y_obs = []
    for tau in tau_vals:
        ss = solve_steady_state(V=10.0, Q=10.0 / tau, C_A_in=1.0, order=1, k=0.15)
        y_obs.append(ss.C_A_ss)

    payload = {
        "model_type": "steady_state",
        "order": 1,
        "time_series": tau_vals,
        "observed_C_A": y_obs,
        "V": 10.0,
        "Q": 1.0,
        "C_A_in": 1.0,
        "k_init": 0.1,
    }
    response = client.post("/api/v1/analysis/fit-kinetics", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["optimizer_success"] is True
    assert data["fitted_k"] == pytest.approx(0.15, abs=1e-3)


# ---------------------------------------------------------------------------
# Compatibility & Leakage Prevention Tests
# ---------------------------------------------------------------------------


def test_temperature_only_data_rejection():
    """Verify that temperature-only data cannot be used for kinetic estimation."""
    with pytest.raises(ValueError, match="temperature-only signals"):
        validate_data_compatibility_for_kinetics(has_concentration=False)

    with pytest.raises(ValueError, match="temperature-only signals"):
        validate_data_compatibility_for_kinetics(has_concentration=True, has_temperature_only=True)

    with pytest.raises(ValueError, match="temperature-only signals"):
        fit_dynamic_kinetics(
            time=[0.0, 5.0, 10.0],
            C_A_obs=[0.5, 0.4, 0.3],
            V=10.0,
            Q=1.0,
            C_A_in=1.0,
            has_temperature_only=True,
        )


def test_test_split_leakage_rejection():
    """Verify that test partition data is strictly barred from parameter fitting."""
    with pytest.raises(ValueError, match="Test partition data must NOT be used"):
        validate_data_compatibility_for_kinetics(dataset_split="test")

    with pytest.raises(ValueError, match="Test partition data must NOT be used"):
        fit_dynamic_kinetics(
            time=[0.0, 5.0, 10.0],
            C_A_obs=[0.5, 0.4, 0.3],
            V=10.0,
            Q=1.0,
            C_A_in=1.0,
            dataset_split="test",
        )


def test_parameter_correlation_and_identifiability():
    """Verify condition number and parameter correlation when co-estimating k and C_A_0."""
    t_eval = np.linspace(0.0, 30.0, 31)
    y_true = first_order_dynamic_analytical_trajectory(
        t_points=t_eval, V=10.0, Q=1.0, C_A_in=1.0, k=0.15, C_A_0=0.2
    )

    result = fit_dynamic_kinetics(
        time=t_eval,
        C_A_obs=y_true,
        V=10.0,
        Q=1.0,
        C_A_in=1.0,
        fit_initial_conc=True,
        k_init=0.25,
    )

    assert result.optimizer_success is True
    assert result.condition_number is not None
    assert result.condition_number > 0
    assert result.parameter_correlation is not None
    assert "k_C_A_0" in result.parameter_correlation
    assert abs(result.parameter_correlation["k_C_A_0"]) <= 1.0


def test_evaluate_kinetic_model_on_test_split():
    """Verify evaluation of a fitted model against an independent held-out test split."""
    # Training split: t in [0, 20]
    t_train = np.linspace(0.0, 20.0, 21)
    y_train = first_order_dynamic_analytical_trajectory(
        t_points=t_train, V=10.0, Q=1.0, C_A_in=1.0, k=0.15, C_A_0=0.1
    )

    fit_res = fit_dynamic_kinetics(
        time=t_train,
        C_A_obs=y_train,
        V=10.0,
        Q=1.0,
        C_A_in=1.0,
        order=1,
        k_init=0.3,
        dataset_split="train",
    )

    assert fit_res.fitted_k == pytest.approx(0.15, abs=1e-3)

    # Held-out test split: independent trajectory with distinct initial concentration C_A(0) = 1.2
    t_test = np.linspace(0.0, 25.0, 26)
    y_test = first_order_dynamic_analytical_trajectory(
        t_points=t_test, V=10.0, Q=1.0, C_A_in=1.0, k=0.15, C_A_0=1.2
    )

    eval_res = evaluate_kinetic_model_on_test_split(
        fit_result=fit_res,
        test_time=t_test,
        test_C_A_obs=y_test,
        V=10.0,
        Q=1.0,
        C_A_in=1.0,
        C_A_0=1.2,
    )

    assert eval_res["test_n_points"] == 26.0
    assert eval_res["test_r_squared"] > 0.999
    assert eval_res["test_rmse"] < 1e-3


def test_api_compatibility_rejection(client):
    """Verify API rejects temperature-only and test split requests with HTTP 422."""
    t_eval = [0.0, 5.0, 10.0]
    y_obs = [0.5, 0.4, 0.3]

    # Temperature only
    resp1 = client.post(
        "/api/v1/analysis/fit-kinetics",
        json={
            "model_type": "dynamic",
            "order": 1,
            "time_series": t_eval,
            "observed_C_A": y_obs,
            "V": 10.0,
            "Q": 1.0,
            "C_A_in": 1.0,
            "has_temperature_only": True,
        },
    )
    assert resp1.status_code == 422
    assert "temperature-only" in resp1.json()["detail"]

    # Test split leakage
    resp2 = client.post(
        "/api/v1/analysis/fit-kinetics",
        json={
            "model_type": "dynamic",
            "order": 1,
            "time_series": t_eval,
            "observed_C_A": y_obs,
            "V": 10.0,
            "Q": 1.0,
            "C_A_in": 1.0,
            "dataset_split": "test",
        },
    )
    assert resp2.status_code == 422
    assert "Test partition" in resp2.json()["detail"]
