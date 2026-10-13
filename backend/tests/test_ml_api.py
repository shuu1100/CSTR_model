"""Test suite for Phase 11: Machine Learning API routes.

Adheres strictly to GLOBAL-INSTRUCTIONS.md, phase-11, and phase-08A:
- Validates model catalog endpoints.
- Verifies benchmark summary retrieval over locked test partition.
- Validates training dispatch and history tracking.
- Verifies inference with provenance and OOD warnings.
- Checks input bounds and schema validation.
"""

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_list_ml_models() -> None:
    response = client.get("/api/v1/ml/models")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    model_types = [m["model_type"] for m in data]
    assert "GREY_BOX_NEURAL_ODE" in model_types
    assert "PINN" in model_types
    assert "MECHANISTIC_NOMINAL" in model_types
    assert "RANDOM_FOREST" in model_types


def test_get_baselines_benchmark() -> None:
    response = client.get("/api/v1/ml/baselines/benchmark")
    assert response.status_code == 200
    data = response.json()
    assert data["task"] == "transient_dynamic_forecasting"
    assert "test_metrics" in data
    assert "RandomForest" in data["test_metrics"]
    assert "Persistence" in data["test_metrics"]
    assert data["provenance"] == "EVALUATED_ON_LOCKED_TEST_SPLIT"


def test_train_pinn_api() -> None:
    payload = {
        "model_type": "PINN",
        "epochs": 10,
        "learning_rate": 0.01,
        "random_seed": 42,
    }
    response = client.post("/api/v1/ml/train", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert data["model_type"] == "PINN"
    assert len(data["train_loss_history"]) == 10
    assert data["provenance"] == "PINN_RESEARCH_SURROGATE"


def test_train_unsupported_model_raises_400() -> None:
    payload = {
        "model_type": "NON_EXISTENT_MODEL",
        "epochs": 10,
    }
    response = client.post("/api/v1/ml/train", json=payload)
    assert response.status_code == 400


def test_predict_grey_box_neural_ode() -> None:
    payload = {
        "model_type": "GREY_BOX_NEURAL_ODE",
        "V": 10.0,
        "Q": 1.0,
        "k": 0.15,
        "C_A_in": 2.0,
        "C_A_0": 0.0,
        "t_final": 20.0,
        "n_points": 21,
    }
    response = client.post("/api/v1/ml/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert len(data["t"]) == 21
    assert len(data["C_A"]) == 21
    assert data["steady_state_C_A"] > 0.0
    assert "GREY_BOX_NEURAL_ODE" in data["provenance"]


def test_predict_pinn() -> None:
    payload = {
        "model_type": "PINN",
        "V": 10.0,
        "Q": 1.0,
        "k": 0.15,
        "C_A_in": 2.0,
        "C_A_0": 0.0,
        "t_final": 10.0,
        "n_points": 11,
    }
    response = client.post("/api/v1/ml/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert len(data["C_A"]) == 11
    assert data["provenance"] == "PINN_RESEARCH_SURROGATE"


def test_predict_mechanistic_baseline() -> None:
    payload = {
        "model_type": "MECHANISTIC_NOMINAL",
        "V": 10.0,
        "Q": 1.0,
        "k": 0.15,
        "C_A_in": 2.0,
        "C_A_0": 0.0,
        "t_final": 20.0,
        "n_points": 21,
    }
    response = client.post("/api/v1/ml/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert len(data["C_A"]) == 21
    assert data["provenance"] == "MECHANISTIC_ANALYTICAL_BASELINE"


def test_predict_damkohler_ood_warning() -> None:
    # High Da: V=100, Q=0.1, k=1.0 -> tau=1000, Da=1000 >> 1
    payload = {
        "model_type": "MECHANISTIC_NOMINAL",
        "V": 100.0,
        "Q": 0.1,
        "k": 1.0,
        "C_A_in": 2.0,
        "C_A_0": 0.0,
    }
    response = client.post("/api/v1/ml/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert any("High Damköhler number" in w for w in data["warnings"])


def test_predict_invalid_bounds_rejected() -> None:
    payload = {
        "model_type": "GREY_BOX_NEURAL_ODE",
        "V": -10.0,  # Negative volume invalid
    }
    response = client.post("/api/v1/ml/predict", json=payload)
    assert response.status_code == 422
