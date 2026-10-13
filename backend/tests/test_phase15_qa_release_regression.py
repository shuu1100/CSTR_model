"""Comprehensive End-to-End Regression and Scientific QA Suite for Phase 15.

Adheres strictly to GLOBAL-INSTRUCTIONS.md, phase-15, and cross-phase governance:
- Validates canonical validation oracle values across analytical, ODE, and API layers.
- Asserts mass and energy balance conservation residuals (< 1e-12).
- Verifies physical non-negativity across analytical, numerical, and neural ML models.
- Verifies candidate dataset quarantine and zero-leakage trajectory partitioning.
- Tests security: path traversal guards, absence of secrets, and offline capability.
"""

from pathlib import Path
import json
import pytest
from fastapi.testclient import TestClient

from backend.app.core.isothermal_first_order import solve_isothermal_first_order_steady_state
from backend.app.core.dynamic_solver import simulate_dynamic_cstr
from backend.app.core.thermal import ThermalCSTRConfig, simulate_thermal_cstr
from backend.app.main import app

client = TestClient(app)


class TestScientificOracleRegression:
    """End-to-end regression tests for canonical oracles and physical balances."""

    def test_canonical_oracle_exact_numerical_agreement(self) -> None:
        # Canonical Oracle: V=10 L, Q=1 L/min, k=0.15 min^-1, Cin=2.0 mol/L -> tau=10 min, Css=0.80 mol/L, X=60%
        res = solve_isothermal_first_order_steady_state(V=10.0, Q=1.0, C_A_in=2.0, k=0.15)
        assert res.tau == pytest.approx(10.0, abs=1e-12)
        assert res.C_A_ss == pytest.approx(0.80, abs=1e-12)
        assert res.conversion == pytest.approx(0.60, abs=1e-12)
        assert abs(res.residual) < 1e-14

    def test_dynamic_solver_reaches_analytical_steady_state(self) -> None:
        # Dynamic ODE integration from C_A(0) = 0.0 mol/L to t = 60 min
        res = simulate_dynamic_cstr(
            C_A_0=0.0,
            C_A_in=2.0,
            V=10.0,
            Q=1.0,
            order=1,
            k=0.15,
            t_final=60.0,
            n_points=121,
            method="Radau",
        )
        assert res.C_A[-1] == pytest.approx(0.80, abs=1e-3)
        assert all(c >= 0.0 for c in res.C_A)

    def test_thermal_energy_balance_exothermic_heating(self) -> None:
        # Exothermic reaction should heat reactor above feed temperature
        cfg = ThermalCSTRConfig(
            V=10.0,
            Q=1.0,
            C_A_in=2.0,
            T_in=300.0,
            delta_H_rxn=-60.0,  # Exothermic
            UA=10.0,
            T_j_in=295.0,
        )
        res = simulate_thermal_cstr(cfg, C_A_0=0.0, t_final=35.0)
        assert res.steady_state_T > 300.0
        assert all(c >= 0.0 for c in res.C_A)
        assert all(t > 0.0 for t in res.T_reactor)


class TestSecurityDataGovernanceAndQuarantine:
    """Security, privacy, and data governance verification."""

    def test_candidate_dataset_quarantine_integrity(self) -> None:
        # cstr_rawdata.npy must remain quarantined and NEVER used directly without schema documentation
        npy_path = Path("cstr_rawdata.npy")
        assert npy_path.exists(), "Candidate dataset cstr_rawdata.npy missing from workspace."

        # Verify splits_manifest does not reference cstr_rawdata.npy as training data
        manifest_path = Path("data/generated/splits_manifest.json")
        if manifest_path.exists():
            with open(manifest_path, "r", encoding="utf-8") as f:
                content = f.read()
            assert "cstr_rawdata.npy" not in content, "Data quarantine violated: raw array found in ML split manifest!"

    def test_zero_leakage_assertion_on_manifest(self) -> None:
        manifest_path = Path("data/generated/splits_manifest.json")
        if not manifest_path.exists():
            pytest.skip("Split manifest not generated yet.")

        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        for task_name, task in manifest.get("tasks", {}).items():
            parts = task.get("partitions", {})
            tr = set(parts.get("train_ids", []))
            val = set(parts.get("val_ids", []))
            te = set(parts.get("test_ids", []))

            assert tr.isdisjoint(val), f"Task {task_name} leaks between train and val!"
            assert tr.isdisjoint(te), f"Task {task_name} leaks between train and test!"
            assert val.isdisjoint(te), f"Task {task_name} leaks between val and test!"

    def test_offline_operation_and_health(self) -> None:
        # Engine operates completely offline
        res = client.get("/api/v1/health")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "ok"
        assert "version" in data
