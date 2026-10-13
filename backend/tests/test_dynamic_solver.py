"""Tests for Phase 2: Dynamic solver, reaction-order models, analytical comparisons, and step changes."""

import math
import numpy as np
import pytest

from backend.app.core.analytical import (
    first_order_dynamic_analytical_point,
    first_order_dynamic_analytical_trajectory,
    first_order_steady_state_analytical,
)
from backend.app.core.dynamic_solver import (
    DynamicSimulationResult,
    StepChange,
    simulate_dynamic_cstr,
)
from backend.app.core.kinetics import (
    RATE_CONSTANT_CANONICAL_UNITS,
    KineticModel,
    ReactionOrder,
    calculate_reaction_rate,
)
from backend.app.core.steady_state import (
    calculate_steady_state_second_order,
    calculate_steady_state_zero_order,
    solve_steady_state,
)


class TestKineticsAndSteadyState:
    """Validate kinetic models and analytical/numerical steady-state solvers for n=0, 1, 2."""

    def test_rate_constant_units_documented(self):
        assert RATE_CONSTANT_CANONICAL_UNITS[0] == "mol/(L*min)"
        assert RATE_CONSTANT_CANONICAL_UNITS[1] == "min^-1"
        assert RATE_CONSTANT_CANONICAL_UNITS[2] == "L/(mol*min)"

    def test_zero_order_kinetics_depletion_boundary(self):
        model = KineticModel(order=0, k=0.5)
        # Positive concentration gives -k
        assert model.reaction_rate(1.0) == -0.5
        assert model.reaction_rate(0.01) == -0.5
        # At zero or negative, reaction shuts off to prevent unphysical depletion
        assert model.reaction_rate(0.0) == 0.0
        assert model.reaction_rate(-0.5) == 0.0

    def test_zero_order_steady_state(self):
        # V=10 L, Q=1 L/min => tau=10 min
        # Case A: C_in=8, k=0.5 => k*tau=5.0 < 8 => C_ss = 8 - 5 = 3 mol/L
        resA = solve_steady_state(V=10.0, Q=1.0, C_A_in=8.0, order=0, k=0.5)
        assert math.isclose(resA.C_A_ss, 3.0, rel_tol=1e-12)
        assert math.isclose(resA.conversion, 5.0 / 8.0, rel_tol=1e-12)
        assert resA.diagnostics["material_balance_closed"] is True

        # Case B: C_in=2, k=0.5 => k*tau=5.0 > 2 => complete consumption, C_ss = 0
        resB = solve_steady_state(V=10.0, Q=1.0, C_A_in=2.0, order=0, k=0.5)
        assert resB.C_A_ss == 0.0
        assert math.isclose(resB.conversion, 1.0, rel_tol=1e-12)

    def test_first_order_steady_state_matches_phase1(self):
        # Canonical validation oracle: V=10, Q=1, k=0.15, C_in=2.0 => C_ss=0.8, X=0.6
        res = solve_steady_state(V=10.0, Q=1.0, C_A_in=2.0, order=1, k=0.15)
        assert math.isclose(res.tau, 10.0, rel_tol=1e-12)
        assert math.isclose(res.C_A_ss, 0.80, rel_tol=1e-12)
        assert math.isclose(res.conversion, 0.60, rel_tol=1e-12)
        assert abs(res.residual) < 1e-14
        assert res.diagnostics["material_balance_closed"] is True

    def test_second_order_steady_state(self):
        # V=10 L, Q=1 L/min => tau=10 min, C_in=2 mol/L, k=0.1 L/(mol*min)
        # k*tau*C_ss^2 + C_ss - C_in = 0 => 1.0 * C_ss^2 + C_ss - 2.0 = 0
        # Roots: C_ss = (-1 + sqrt(1 + 8)) / 2 = (-1 + 3) / 2 = 1.0 mol/L
        res = solve_steady_state(V=10.0, Q=1.0, C_A_in=2.0, order=2, k=0.1)
        assert math.isclose(res.C_A_ss, 1.0, rel_tol=1e-12)
        assert math.isclose(res.conversion, 0.50, rel_tol=1e-12)
        assert abs(res.residual) < 1e-14
        assert res.diagnostics["material_balance_closed"] is True


class TestAnalyticalTrajectory:
    """Verify first-order analytical dynamic formula."""

    def test_analytical_start_and_long_time_limit(self):
        V, Q, k, C_in = 10.0, 1.0, 0.15, 2.0
        C_0 = 0.5
        c_ss = 0.80

        # At t = 0, C_A must equal C_0
        c_t0 = first_order_dynamic_analytical_point(0.0, C_0, V, Q, C_in, k)
        assert math.isclose(c_t0, C_0, rel_tol=1e-12)

        # At t -> infinity, C_A must approach C_ss
        c_t_inf = first_order_dynamic_analytical_point(100.0, C_0, V, Q, C_in, k)
        assert math.isclose(c_t_inf, c_ss, rel_tol=1e-8)


class TestDynamicSolverValidationOracle:
    """Acceptance Gate: Numerical first-order trajectory agrees with analytical solution."""

    def test_first_order_numerical_analytical_agreement(self):
        V = 10.0
        Q = 1.0
        k = 0.15
        C_A_in = 2.0
        C_A_0 = 0.5  # Start away from steady state
        t_final = 50.0  # 5 residence times

        res = simulate_dynamic_cstr(
            C_A_0=C_A_0,
            C_A_in=C_A_in,
            V=V,
            Q=Q,
            order=1,
            k=k,
            t_final=t_final,
            n_points=101,
            method="RK45",
            rtol=1e-7,
            atol=1e-10,
        )

        assert res.success is True
        assert res.analytical_comparison is not None
        # Max absolute error must be tight (< 1e-5 mol/L)
        assert res.analytical_comparison["max_absolute_error"] < 1e-5
        assert res.analytical_comparison["rmse"] < 1e-5
        # Concentrations never negative
        assert all(c >= 0.0 for c in res.C_A)
        # Approaches steady state (0.80) at end
        assert math.isclose(res.C_A[-1], 0.80, abs_tol=1e-3)


class TestDynamicSolverMultipleOrders:
    """Verify dynamic simulations for zero, first, and second order kinetics."""

    @pytest.mark.parametrize("order,k", [(0, 0.1), (1, 0.15), (2, 0.1)])
    def test_dynamic_trajectories_converge_to_steady_state(self, order, k):
        V, Q, C_in, C_0 = 10.0, 1.0, 2.0, 0.0
        t_final = 80.0  # 8 residence times

        res = simulate_dynamic_cstr(
            C_A_0=C_0,
            C_A_in=C_in,
            V=V,
            Q=Q,
            order=order,
            k=k,
            t_final=t_final,
            n_points=161,
            method="RK45",
        )

        assert res.success is True
        # Check non-negativity across trajectory
        assert all(c >= 0.0 for c in res.C_A)

        # Expected steady state
        expected_ss = solve_steady_state(V, Q, C_in, order, k).C_A_ss
        # Trajectory endpoint should match steady state
        assert math.isclose(res.C_A[-1], expected_ss, rel_tol=1e-2)

    def test_zero_inlet_and_initial_concentration(self):
        """Simulation with zero initial and zero inlet concentration stays at zero."""
        res = simulate_dynamic_cstr(
            C_A_0=0.0,
            C_A_in=0.0,
            V=10.0,
            Q=1.0,
            order=1,
            k=0.15,
            t_final=20.0,
        )
        assert res.success is True
        assert all(c == 0.0 for c in res.C_A)


class TestStepChanges:
    """Acceptance Gate: Step changes reflect changed operating inputs piecewise."""

    def test_inlet_concentration_step_change(self):
        V, Q, k = 10.0, 1.0, 0.15
        # Begin at steady state for C_in=2.0 (C_ss=0.80)
        # At t=25 min, step C_in from 2.0 to 4.0 (new C_ss = 4.0 / 2.5 = 1.60)
        step = StepChange(time=25.0, C_A_in_new=4.0)

        res = simulate_dynamic_cstr(
            C_A_0=0.80,
            C_A_in=2.0,
            V=V,
            Q=Q,
            order=1,
            k=k,
            t_final=60.0,
            n_points=121,
            step_change=step,
        )

        assert res.success is True
        assert res.step_change_applied is not None
        assert res.step_change_applied["time"] == 25.0
        assert res.step_change_applied["C_A_in_new"] == 4.0

        # Before step (t=25), concentration is ~0.80
        t_arr = np.array(res.t)
        c_arr = np.array(res.C_A)
        idx_step = np.where(np.isclose(t_arr, 25.0, atol=1e-3))[0][0]
        assert math.isclose(c_arr[idx_step], 0.80, abs_tol=1e-2)

        # By t=60, concentration approaches new steady state 1.60
        assert math.isclose(c_arr[-1], 1.60, abs_tol=1e-2)

    def test_flow_rate_step_change(self):
        V, k, C_in = 10.0, 0.15, 2.0
        # Q increases from 1.0 to 2.0 L/min at t=20 min
        # Initial tau=10 min, C_ss=0.80
        # New tau=5 min, new C_ss = 2.0 / (1 + 0.15*5) = 2.0 / 1.75 = 1.1428 mol/L
        step = StepChange(time=20.0, Q_new=2.0)

        res = simulate_dynamic_cstr(
            C_A_0=0.80,
            C_A_in=C_in,
            V=V,
            Q=1.0,
            order=1,
            k=k,
            t_final=50.0,
            step_change=step,
        )

        assert res.success is True
        expected_new_ss = 2.0 / (1.0 + 0.15 * (10.0 / 2.0))
        assert math.isclose(res.C_A[-1], expected_new_ss, abs_tol=1e-2)


class TestToleranceConvergenceAndStiffness:
    """Verify solver tolerance convergence and performance with stiff methods."""

    def test_tolerance_convergence(self):
        """Tighter tolerances yield monotonically decreasing error against analytical solution."""
        V, Q, k, C_in, C_0 = 10.0, 1.0, 0.15, 2.0, 0.5
        t_final = 30.0
        errors = []
        for rtol, atol in [(1e-3, 1e-6), (1e-6, 1e-9), (1e-9, 1e-12)]:
            res = simulate_dynamic_cstr(
                C_A_0=C_0,
                C_A_in=C_in,
                V=V,
                Q=Q,
                order=1,
                k=k,
                t_final=t_final,
                n_points=51,
                rtol=rtol,
                atol=atol,
            )
            assert res.success is True
            assert res.analytical_comparison is not None
            errors.append(res.analytical_comparison["rmse"])

        assert errors[0] > errors[1] >= errors[2]

    @pytest.mark.parametrize("method", ["Radau", "BDF"])
    def test_stiff_kinetics_solvers(self, method):
        """Stiff solvers (Radau, BDF) solve fast kinetics (Da >> 1) accurately."""
        V, Q, k, C_in, C_0 = 10.0, 1.0, 20.0, 2.0, 0.5
        t_final = 5.0
        res = simulate_dynamic_cstr(
            C_A_0=C_0,
            C_A_in=C_in,
            V=V,
            Q=Q,
            order=1,
            k=k,
            t_final=t_final,
            n_points=41,
            method=method,
            rtol=1e-6,
            atol=1e-9,
        )
        assert res.success is True
        assert res.analytical_comparison is not None
        assert res.analytical_comparison["max_absolute_error"] < 1e-4
        expected_ss = 2.0 / (1.0 + 20.0 * 10.0)
        assert math.isclose(res.C_A[-1], expected_ss, abs_tol=1e-3)

    def test_explicit_t_eval_grid(self):
        """Explicit evaluation grid t_eval is strictly respected in output trajectory."""
        custom_t = np.array([0.0, 1.5, 4.2, 10.0, 18.5, 25.0])
        res = simulate_dynamic_cstr(
            C_A_0=0.5,
            C_A_in=2.0,
            V=10.0,
            Q=1.0,
            order=1,
            k=0.15,
            t_final=25.0,
            t_eval=custom_t,
        )
        assert res.success is True
        assert np.allclose(res.t, custom_t)
        assert len(res.C_A) == len(custom_t)


class TestSolverErrorHandling:
    """Verify invalid and non-finite inputs raise clear exceptions without silent corruption."""

    def test_invalid_parameters(self):
        with pytest.raises(ValueError, match="t_final"):
            simulate_dynamic_cstr(1.0, 1.0, 10.0, 1.0, 1, 0.15, t_final=-5.0)

        with pytest.raises(ValueError, match="n_points"):
            simulate_dynamic_cstr(1.0, 1.0, 10.0, 1.0, 1, 0.15, t_final=10.0, n_points=1)

        with pytest.raises(ValueError, match="Unsupported reaction order"):
            simulate_dynamic_cstr(1.0, 1.0, 10.0, 1.0, order=3, k=0.15, t_final=10.0)

        with pytest.raises(ValueError, match="Step change time"):
            StepChange(time=-2.0, C_A_in_new=1.0)

    @pytest.mark.parametrize("param_name,kwargs", [
        ("C_A_0", {"C_A_0": float("nan")}),
        ("C_A_0", {"C_A_0": float("inf")}),
        ("C_A_in", {"C_A_in": float("nan")}),
        ("C_A_in", {"C_A_in": float("-inf")}),
        ("V", {"V": float("nan")}),
        ("V", {"V": float("inf")}),
        ("Q", {"Q": float("nan")}),
        ("k", {"k": float("nan")}),
        ("t_final", {"t_final": float("nan")}),
        ("t_final", {"t_final": float("inf")}),
    ])
    def test_non_finite_inputs_rejected(self, param_name, kwargs):
        defaults = {
            "C_A_0": 0.5,
            "C_A_in": 2.0,
            "V": 10.0,
            "Q": 1.0,
            "order": 1,
            "k": 0.15,
            "t_final": 20.0,
        }
        defaults.update(kwargs)
        with pytest.raises(ValueError, match=f"(Parameter '{param_name}'|Rate constant k|t_final)"):
            simulate_dynamic_cstr(**defaults)

    def test_invalid_t_eval_non_monotonic_rejected(self):
        non_monotonic = [0.0, 5.0, 3.0, 10.0]
        with pytest.raises(ValueError, match="strictly monotonically increasing"):
            simulate_dynamic_cstr(
                C_A_0=0.5,
                C_A_in=2.0,
                V=10.0,
                Q=1.0,
                order=1,
                k=0.15,
                t_final=10.0,
                t_eval=non_monotonic,
            )
