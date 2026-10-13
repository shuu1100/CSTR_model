"""API tests for CSTR Lab endpoints using FastAPI TestClient."""

import math
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


class TestHealthAndMetadataEndpoints:
    """Verify health check and model catalog endpoints."""

    def test_root_endpoint(self):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "version" in data
        assert data["health_check"] == "/api/v1/health"

    def test_health_check_endpoint(self):
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["app_name"] == "CSTR Lab API"
        assert "timestamp" in data

    def test_model_catalog_endpoint(self):
        response = client.get("/api/v1/models")
        assert response.status_code == 200
        data = response.json()
        assert "models" in data
        assert len(data["models"]) >= 1
        model = data["models"][0]
        assert model["model_id"] == "isothermal_cstr_elementary"
        assert model["supported_orders"] == [0, 1, 2]
        assert "canonical_units" in model

    def test_openapi_spec_json_endpoint(self):
        """OpenAPI 3.x documentation schema is published and valid."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        assert "paths" in schema
        assert "/api/v1/simulations/steady-state" in schema["paths"]
        assert "/api/v1/simulations/dynamic" in schema["paths"]


class TestSteadyStateEndpoint:
    """Verify POST /api/v1/simulations/steady-state."""

    def test_canonical_oracle_global_instructions_via_api(self):
        """Oracle: V=10 L, Q=1 L/min, k=0.15 min^-1, CAin=1.0 mol/L -> tau=10, C_ss=0.4, X=0.60."""
        payload = {
            "V": 10.0,
            "Q": 1.0,
            "C_A_in": 1.0,
            "order": 1,
            "k": 0.15,
        }
        response = client.post("/api/v1/simulations/steady-state", json=payload)
        assert response.status_code == 200
        data = response.json()

        outputs = data["outputs"]
        assert math.isclose(outputs["tau"], 10.0, rel_tol=1e-12)
        assert math.isclose(outputs["C_A_ss"], 0.40, rel_tol=1e-12)
        assert math.isclose(outputs["conversion"], 0.60, rel_tol=1e-12)
        assert abs(outputs["residual"]) < 1e-14
        assert data["diagnostics"]["material_balance_closed"] is True

    def test_canonical_validation_oracle_via_api(self):
        """V=10 L, Q=1 L/min, k=0.15 min^-1, C_A_in=2.0 mol/L -> tau=10, C_ss=0.8, X=0.60."""
        payload = {
            "V": 10.0,
            "Q": 1.0,
            "C_A_in": 2.0,
            "order": 1,
            "k": 0.15,
        }
        response = client.post("/api/v1/simulations/steady-state", json=payload)
        assert response.status_code == 200
        data = response.json()

        outputs = data["outputs"]
        assert math.isclose(outputs["tau"], 10.0, rel_tol=1e-12)
        assert math.isclose(outputs["C_A_ss"], 0.80, rel_tol=1e-12)
        assert math.isclose(outputs["conversion"], 0.60, rel_tol=1e-12)
        assert abs(outputs["residual"]) < 1e-14
        assert data["diagnostics"]["material_balance_closed"] is True

    def test_steady_state_with_unit_conversion(self):
        """Test unit conversion: V=10000 mL (=10 L), Q=60 L/h (=1 L/min)."""
        payload = {
            "V": 10000.0,
            "volume_unit": "mL",
            "Q": 60.0,
            "flow_rate_unit": "L/h",
            "C_A_in": 2.0,
            "order": 1,
            "k": 0.15,
        }
        response = client.post("/api/v1/simulations/steady-state", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert math.isclose(data["outputs"]["tau"], 10.0, rel_tol=1e-6)
        assert math.isclose(data["outputs"]["C_A_ss"], 0.80, rel_tol=1e-6)

    def test_steady_state_zero_and_second_order(self):
        # Zero order: C_in=5, k=0.2, tau=10 => C_ss = 5 - 0.2*10 = 3
        res0 = client.post(
            "/api/v1/simulations/steady-state",
            json={"V": 10.0, "Q": 1.0, "C_A_in": 5.0, "order": 0, "k": 0.2},
        )
        assert res0.status_code == 200
        assert math.isclose(res0.json()["outputs"]["C_A_ss"], 3.0, rel_tol=1e-9)

        # Second order: C_in=2, k=0.1, tau=10 => C_ss = 1.0
        res2 = client.post(
            "/api/v1/simulations/steady-state",
            json={"V": 10.0, "Q": 1.0, "C_A_in": 2.0, "order": 2, "k": 0.1},
        )
        assert res2.status_code == 200
        assert math.isclose(res2.json()["outputs"]["C_A_ss"], 1.0, rel_tol=1e-9)

    def test_steady_state_validation_errors(self):
        """Test non-positive or invalid inputs produce HTTP 422."""
        # Non-positive volume
        res = client.post(
            "/api/v1/simulations/steady-state",
            json={"V": -5.0, "Q": 1.0, "C_A_in": 2.0, "order": 1, "k": 0.15},
        )
        assert res.status_code == 422

        # Invalid reaction order
        res = client.post(
            "/api/v1/simulations/steady-state",
            json={"V": 10.0, "Q": 1.0, "C_A_in": 2.0, "order": 4, "k": 0.15},
        )
        assert res.status_code == 422

        # Negative rate constant
        res = client.post(
            "/api/v1/simulations/steady-state",
            json={"V": 10.0, "Q": 1.0, "C_A_in": 2.0, "order": 1, "k": -0.5},
        )
        assert res.status_code == 422

    def test_steady_state_zero_inlet_guard_via_api(self):
        """Zero inlet concentration returns conversion=null/None without error."""
        res = client.post(
            "/api/v1/simulations/steady-state",
            json={"V": 10.0, "Q": 1.0, "C_A_in": 0.0, "order": 1, "k": 0.15},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["outputs"]["C_A_ss"] == 0.0
        assert data["outputs"]["conversion"] is None


class TestDynamicSimulationEndpoint:
    """Verify POST /api/v1/simulations/dynamic."""

    def test_dynamic_simulation_first_order_oracle(self):
        payload = {
            "C_A_0": 0.5,
            "C_A_in": 2.0,
            "V": 10.0,
            "Q": 1.0,
            "order": 1,
            "k": 0.15,
            "t_final": 50.0,
            "n_points": 51,
            "solver_method": "RK45",
        }
        response = client.post("/api/v1/simulations/dynamic", json=payload)
        assert response.status_code == 200
        data = response.json()

        assert len(data["t"]) == 51
        assert len(data["C_A"]) == 51
        assert data["solver_details"]["success"] is True
        assert data["analytical_comparison"] is not None
        assert data["analytical_comparison"]["max_absolute_error"] < 1e-5

    def test_dynamic_simulation_with_step_change(self):
        payload = {
            "C_A_0": 0.8,
            "C_A_in": 2.0,
            "V": 10.0,
            "Q": 1.0,
            "order": 1,
            "k": 0.15,
            "t_final": 60.0,
            "n_points": 61,
            "step_change": {
                "time": 30.0,
                "C_A_in_new": 4.0,
            },
        }
        response = client.post("/api/v1/simulations/dynamic", json=payload)
        assert response.status_code == 200
        data = response.json()

        assert data["step_change_applied"] is not None
        assert data["step_change_applied"]["time"] == 30.0
        assert data["step_change_applied"]["C_A_in_new"] == 4.0
        # Concentration approaches ~1.60 at the end
        assert math.isclose(data["C_A"][-1], 1.60, abs_tol=1e-2)

    def test_dynamic_simulation_safety_guardrails(self):
        """Excessive t_final or n_points should be rejected with 422."""
        # Horizon over max allowed (10,000 min)
        res = client.post(
            "/api/v1/simulations/dynamic",
            json={
                "C_A_0": 0.5,
                "C_A_in": 2.0,
                "V": 10.0,
                "Q": 1.0,
                "order": 1,
                "k": 0.15,
                "t_final": 50000.0,
                "n_points": 100,
            },
        )
        assert res.status_code == 422

        # Output points over max allowed (10,000)
        res2 = client.post(
            "/api/v1/simulations/dynamic",
            json={
                "C_A_0": 0.5,
                "C_A_in": 2.0,
                "V": 10.0,
                "Q": 1.0,
                "order": 1,
                "k": 0.15,
                "t_final": 50.0,
                "n_points": 50000,
            },
        )
        assert res2.status_code == 422

    def test_dynamic_simulation_stiff_solver_radau(self):
        """Stiff solver Radau via API succeeds and reports solver metadata."""
        payload = {
            "C_A_0": 0.5,
            "C_A_in": 2.0,
            "V": 10.0,
            "Q": 1.0,
            "order": 1,
            "k": 10.0,
            "t_final": 5.0,
            "n_points": 21,
            "solver_method": "Radau",
        }
        res = client.post("/api/v1/simulations/dynamic", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["solver_details"]["method"] == "Radau"
        assert data["solver_details"]["success"] is True

    def test_dynamic_simulation_validation_errors(self):
        """Unphysical inputs and empty step changes return HTTP 422."""
        # Negative initial concentration
        res1 = client.post(
            "/api/v1/simulations/dynamic",
            json={"C_A_0": -1.0, "C_A_in": 2.0, "V": 10.0, "Q": 1.0, "k": 0.15, "t_final": 10.0},
        )
        assert res1.status_code == 422

        # Invalid solver method
        res2 = client.post(
            "/api/v1/simulations/dynamic",
            json={"C_A_0": 0.5, "C_A_in": 2.0, "V": 10.0, "Q": 1.0, "k": 0.15, "t_final": 10.0, "solver_method": "Euler"},
        )
        assert res2.status_code == 422

        # Step change without any change parameter
        res3 = client.post(
            "/api/v1/simulations/dynamic",
            json={
                "C_A_0": 0.5,
                "C_A_in": 2.0,
                "V": 10.0,
                "Q": 1.0,
                "k": 0.15,
                "t_final": 10.0,
                "step_change": {"time": 5.0},
            },
        )
        assert res3.status_code == 422
