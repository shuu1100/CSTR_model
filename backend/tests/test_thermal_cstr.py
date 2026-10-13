"""Test suite for Phase 13: Arrhenius Kinetics and Coupled Non-Isothermal CSTR.

Adheres strictly to GLOBAL-INSTRUCTIONS.md, phase-13, and phase-08A:
- Asserts Arrhenius k(T) calculation, monotonic temperature scaling, and Kelvin safeguards.
- Verifies coupled reactor + cooling jacket energy balances.
- Asserts exact recovery of isothermal behavior when isothermal=True.
- Verifies thermal runaway detection for highly exothermic reactions.
- Tests /api/v1/simulations/thermal REST endpoint with input validation.
"""

import pytest
from fastapi.testclient import TestClient

from backend.app.core.thermal import (
    ThermalCSTRConfig,
    arrhenius_rate_constant,
    simulate_thermal_cstr,
)
from backend.app.main import app

client = TestClient(app)


class TestArrheniusKinetics:
    """Tests for temperature-dependent Arrhenius rate constants."""

    def test_arrhenius_monotonicity_with_temperature(self) -> None:
        A = 1.0e7
        Ea = 50000.0  # J/mol
        k_300 = arrhenius_rate_constant(300.0, A, Ea)
        k_320 = arrhenius_rate_constant(320.0, A, Ea)
        k_350 = arrhenius_rate_constant(350.0, A, Ea)

        assert 0.0 < k_300 < k_320 < k_350

    def test_temperature_must_be_positive_kelvin(self) -> None:
        with pytest.raises(ValueError, match="Absolute temperature must be strictly positive"):
            arrhenius_rate_constant(0.0, 1e7, 50000.0)

        with pytest.raises(ValueError, match="Absolute temperature must be strictly positive"):
            arrhenius_rate_constant(-10.0, 1e7, 50000.0)

    def test_negative_parameters_raise(self) -> None:
        with pytest.raises(ValueError, match="Pre-exponential factor"):
            arrhenius_rate_constant(300.0, -10.0, 50000.0)

        with pytest.raises(ValueError, match="Activation energy"):
            arrhenius_rate_constant(300.0, 1e7, -500.0)


class TestCoupledThermalSimulation:
    """Tests for coupled non-isothermal CSTR ODE integration."""

    def test_baseline_thermal_simulation(self) -> None:
        config = ThermalCSTRConfig(
            V=10.0,
            Q=1.0,
            C_A_in=2.0,
            T_in=300.0,
            delta_H_rxn=-50.0,  # Exothermic
            UA=20.0,
            T_j_in=290.0,
        )

        res = simulate_thermal_cstr(
            config=config,
            C_A_0=0.0,
            T_0=300.0,
            T_j_0=290.0,
            t_final=30.0,
        )

        assert len(res.t) > 0
        assert all(c >= 0.0 for c in res.C_A)
        assert all(t > 0.0 for t in res.T_reactor)
        assert all(tj > 0.0 for tj in res.T_jacket)
        # Steady state reached
        assert res.steady_state_C_A < 2.0
        assert res.steady_state_T > 290.0
        assert res.provenance == "NON_ISOTHERMAL_MECHANISTIC_SOLVER"

    def test_isothermal_mode_recovers_constant_temperature(self) -> None:
        config = ThermalCSTRConfig(
            V=10.0,
            Q=1.0,
            C_A_in=2.0,
            T_in=310.0,
            isothermal=True,  # Isothermal lock
        )

        res = simulate_thermal_cstr(config=config, C_A_0=0.0, t_final=20.0)

        # Temperature must remain identically T_in throughout
        for T in res.T_reactor:
            assert T == pytest.approx(310.0, abs=1e-6)

        assert res.thermal_runaway_detected is False

    def test_thermal_runaway_detection(self) -> None:
        # Extreme exothermic reaction with zero cooling
        config = ThermalCSTRConfig(
            V=10.0,
            Q=1.0,
            C_A_in=4.0,
            T_in=320.0,
            delta_H_rxn=-200.0,  # Highly exothermic
            UA=0.0,              # Zero cooling
            A=5.0e8,
            Ea=40000.0,
        )

        res = simulate_thermal_cstr(config=config, C_A_0=1.0, t_final=15.0)

        assert res.thermal_runaway_detected is True
        assert len(res.warnings) > 0
        assert "Thermal runaway" in res.warnings[0]


class TestThermalAPIEndpoint:
    """Integration tests for POST /api/v1/simulations/thermal."""

    def test_thermal_api_success(self) -> None:
        payload = {
            "V": 10.0,
            "Q": 1.0,
            "C_A_in": 2.0,
            "T_in": 300.0,
            "C_A_0": 0.0,
            "t_final": 25.0,
            "n_points": 26,
        }
        res = client.post("/api/v1/simulations/thermal", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert len(data["t"]) == 26
        assert len(data["T_reactor"]) == 26
        assert len(data["T_jacket"]) == 26
        assert data["provenance"] == "NON_ISOTHERMAL_MECHANISTIC_SOLVER"

    def test_thermal_api_invalid_volume_rejected(self) -> None:
        payload = {
            "V": -10.0,  # Invalid
        }
        res = client.post("/api/v1/simulations/thermal", json=payload)
        assert res.status_code == 422

    def test_thermal_api_prbs_audit(self) -> None:
        res = client.get("/api/v1/simulations/thermal/prbs-audit")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "success"
        assert data["row_count"] >= 3000
        assert data["dt_seconds"] == pytest.approx(0.5, abs=1e-3)
        assert "reactor_temp_k" in data["signal_mappings"]
        assert "validate kinetic concentration" in data["scientific_governance_notice"].lower()

    def test_thermal_api_prbs_calibration(self) -> None:
        res = client.post("/api/v1/simulations/thermal/prbs-calibration")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "success"
        assert "k_jacket_per_s" in data["calibrated_parameters"]
        assert "derivative_rmse_k_per_s" in data["locked_test_metrics"]
        assert data["scientific_data_governance"]["concentration_validated"] is False


class TestPRBSThermalAuditAndCalibration:
    """Tests for experimental PRBS workbook ingestion, signal mappings, and thermal calibration."""

    def test_prbs_workbook_audit_and_signal_mapping(self) -> None:
        from backend.app.core.prbs_thermal import load_and_audit_prbs_dataset

        df, report = load_and_audit_prbs_dataset()
        assert len(df) >= 3000
        assert report.missing_values_count == 0
        assert report.dt_seconds == pytest.approx(0.5, abs=1e-3)
        # Check verified Kelvin temperatures
        assert all(df["reactor_temp_k"] > 273.15)
        assert all(df["jacket_temp_k"] > 273.15)
        assert all(df["feed_inlet_temp_k"] > 273.15)
        # Check identifiability
        assert report.excitation_identifiability["is_sufficiently_excited"] is True

    def test_prbs_blocked_chronology_split(self) -> None:
        from backend.app.core.prbs_thermal import load_and_audit_prbs_dataset, split_prbs_blocked_chronology

        df, _ = load_and_audit_prbs_dataset()
        cal, val, test = split_prbs_blocked_chronology(df, cal_ratio=0.6, val_ratio=0.2, test_ratio=0.2)

        assert len(cal) + len(val) + len(test) == len(df)
        # Strictly chronological without overlap
        assert cal["time_s"].max() < val["time_s"].min()
        assert val["time_s"].max() < test["time_s"].min()

    def test_prbs_thermal_calibration_and_locked_test(self) -> None:
        from backend.app.core.prbs_thermal import calibrate_and_evaluate_prbs_thermal

        results = calibrate_and_evaluate_prbs_thermal()
        assert results["status"] == "success"

        # Valid heat transfer parameters
        params = results["calibrated_parameters"]
        assert params["k_jacket_per_s"] > 0.0

        # Physical residuals evaluated on locked test split
        test_metrics = results["locked_test_metrics"]
        assert test_metrics["derivative_rmse_k_per_s"] < 1.0  # Stable gradient fit
        assert abs(test_metrics["derivative_mean_residual_k_per_s"]) < 0.1  # Zero systematic drift
        assert test_metrics["temperature_1step_rmse_k"] < 0.5  # Accurate 1-step prediction

    def test_prbs_temperature_only_cannot_validate_concentration(self) -> None:
        from backend.app.core.prbs_thermal import assert_cannot_validate_concentration_on_prbs

        with pytest.raises(ValueError, match="Temperature-only data cannot validate concentration"):
            assert_cannot_validate_concentration_on_prbs()

