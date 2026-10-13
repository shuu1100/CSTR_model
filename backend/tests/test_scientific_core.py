"""Tests for Phase 1 scientific core: units, first-order steady state, and analytic tests."""

import math
import pytest

from backend.app.core.isothermal_first_order import (
    SteadyStateFirstOrderResult,
    reaction_rate_first_order,
    residence_time,
    solve_isothermal_first_order_steady_state,
    steady_state_concentration,
    steady_state_conversion,
    steady_state_material_balance_residual,
)
from backend.app.core.units import (
    convert_concentration,
    convert_first_order_rate_constant,
    convert_flow_rate,
    convert_time,
    convert_volume,
)


class TestCanonicalValidationOracle:
    """Canonical test case from project baseline specifications:

    V = 10 L, Q = 1 L/min, k = 0.15 min^-1, C_A_in > 0
    Expected:
    - tau = 10 min
    - C_A,ss / C_A,in = 0.40
    - X_A = 0.60
    """

    def test_canonical_oracle_global_instructions_specification(self):
        """Verify the exact oracle from GLOBAL-INSTRUCTIONS.md:
        V=10 L, Q=1 L/min, k=0.15 min^-1, CAin=1 mol/L => tau=10 min, CA_ss=0.4 mol/L, X=0.6.
        """
        V = 10.0
        Q = 1.0
        k = 0.15
        C_A_in = 1.0

        res = solve_isothermal_first_order_steady_state(V, Q, C_A_in, k)
        assert isinstance(res, SteadyStateFirstOrderResult)
        assert math.isclose(res.tau, 10.0, rel_tol=1e-12)
        assert math.isclose(res.C_A_ss, 0.40, rel_tol=1e-12)
        assert res.conversion is not None
        assert math.isclose(res.conversion, 0.60, rel_tol=1e-12)
        assert math.isclose(res.reaction_rate_ss, -0.15 * 0.40, rel_tol=1e-12)
        assert abs(res.residual) < 1e-14
        assert res.diagnostics["material_balance_closed"] is True
        assert math.isclose(res.diagnostics["damkohler_number"], 1.5, rel_tol=1e-12)

    def test_canonical_case_with_arbitrary_positive_inlet(self):
        V = 10.0  # L
        Q = 1.0  # L/min
        k = 0.15  # min^-1
        C_A_in = 2.0  # mol/L

        res = solve_isothermal_first_order_steady_state(V, Q, C_A_in, k)

        assert isinstance(res, SteadyStateFirstOrderResult)
        assert math.isclose(res.tau, 10.0, rel_tol=1e-12)
        assert math.isclose(res.C_A_ss, 0.80, rel_tol=1e-12)
        assert math.isclose(res.C_A_ss / C_A_in, 0.40, rel_tol=1e-12)
        assert res.conversion is not None
        assert math.isclose(res.conversion, 0.60, rel_tol=1e-12)
        assert math.isclose(res.reaction_rate_ss, -0.15 * 0.80, rel_tol=1e-12)

        # Residual check: dC_A/dt = (Q/V)*(C_in - C_ss) + r_A = 0
        assert abs(res.residual) < 1e-14
        assert res.diagnostics["material_balance_closed"] is True
        assert math.isclose(res.diagnostics["damkohler_number"], 1.5, rel_tol=1e-12)

    @pytest.mark.parametrize("Da", [0.01, 0.1, 0.5, 1.0, 1.5, 5.0, 10.0, 100.0])
    def test_damkohler_conversion_scaling(self, Da):
        V = 10.0
        Q = 1.0  # tau = 10 min
        k = Da / 10.0
        C_A_in = 2.5

        res = solve_isothermal_first_order_steady_state(V, Q, C_A_in, k)
        expected_X = Da / (1.0 + Da)
        expected_Css = C_A_in / (1.0 + Da)
        assert math.isclose(res.conversion, expected_X, rel_tol=1e-12)
        assert math.isclose(res.C_A_ss, expected_Css, rel_tol=1e-12)
        assert abs(res.residual) < 1e-14

    def test_canonical_oracle_independent_functions(self):
        V = 10.0
        Q = 1.0
        k = 0.15
        C_A_in = 1.5

        tau = residence_time(V, Q)
        assert tau == 10.0

        c_ss = steady_state_concentration(V, Q, C_A_in, k)
        assert math.isclose(c_ss / C_A_in, 0.40, rel_tol=1e-12)

        conv = steady_state_conversion(C_A_in, c_ss)
        assert conv is not None
        assert math.isclose(conv, 0.60, rel_tol=1e-12)

        res = steady_state_material_balance_residual(V, Q, C_A_in, c_ss, k)
        assert abs(res) < 1e-14


class TestScientificBoundaryConditions:
    """Tests for edge cases and boundary conditions."""

    def test_zero_inlet_concentration(self):
        """When C_A_in = 0, C_A_ss must be 0, residual must be 0, conversion is undefined (None)."""
        res = solve_isothermal_first_order_steady_state(V=10.0, Q=1.0, C_A_in=0.0, k=0.15)
        assert res.C_A_ss == 0.0
        assert res.conversion is None
        assert res.reaction_rate_ss == 0.0
        assert abs(res.residual) < 1e-14

    def test_zero_rate_constant(self):
        """When k = 0 (no reaction), C_A_ss must equal C_A_in, and conversion must be 0."""
        res = solve_isothermal_first_order_steady_state(V=10.0, Q=1.0, C_A_in=2.5, k=0.0)
        assert math.isclose(res.C_A_ss, 2.5, rel_tol=1e-12)
        assert res.conversion is not None
        assert math.isclose(res.conversion, 0.0, rel_tol=1e-12)
        assert res.reaction_rate_ss == 0.0
        assert abs(res.residual) < 1e-14

    def test_infinite_rate_limit(self):
        """For extremely large k, conversion approaches 1.0 and C_A_ss approaches 0."""
        res = solve_isothermal_first_order_steady_state(V=10.0, Q=1.0, C_A_in=1.0, k=1e6)
        assert math.isclose(res.C_A_ss, 0.0, abs_tol=1e-6)
        assert res.conversion is not None
        assert math.isclose(res.conversion, 1.0, abs_tol=1e-6)


class TestInputValidationAndErrors:
    """Verify that non-positive, negative, non-finite, or malformed inputs raise explicit errors."""

    @pytest.mark.parametrize("invalid_V", [0.0, -1.0, -100.0, float("nan"), float("inf"), float("-inf")])
    def test_invalid_volume(self, invalid_V):
        with pytest.raises(ValueError, match="Parameter 'V'"):
            residence_time(invalid_V, 1.0)
        with pytest.raises(ValueError, match="Parameter 'V'"):
            steady_state_concentration(invalid_V, 1.0, 1.0, 0.1)

    @pytest.mark.parametrize("invalid_Q", [0.0, -0.5, float("nan"), float("inf")])
    def test_invalid_flow_rate(self, invalid_Q):
        with pytest.raises(ValueError, match="Parameter 'Q'"):
            residence_time(10.0, invalid_Q)
        with pytest.raises(ValueError, match="Parameter 'Q'"):
            steady_state_concentration(10.0, invalid_Q, 1.0, 0.1)

    @pytest.mark.parametrize("invalid_k", [-0.01, -10.0, float("nan"), float("inf")])
    def test_invalid_rate_constant(self, invalid_k):
        with pytest.raises(ValueError, match="Parameter 'k'"):
            reaction_rate_first_order(invalid_k, 1.0)
        with pytest.raises(ValueError, match="Parameter 'k'"):
            steady_state_concentration(10.0, 1.0, 1.0, invalid_k)

    @pytest.mark.parametrize("invalid_C_in", [-0.001, -5.0, float("nan"), float("inf")])
    def test_invalid_inlet_concentration(self, invalid_C_in):
        with pytest.raises(ValueError, match="Parameter 'C_A_in'"):
            steady_state_concentration(10.0, 1.0, invalid_C_in, 0.1)

    def test_type_error_on_non_numerical_input(self):
        with pytest.raises(TypeError):
            residence_time("10", 1.0)  # type: ignore[arg-type]
        with pytest.raises(TypeError):
            residence_time(10.0, None)  # type: ignore[arg-type]


class TestUnitConversions:
    """Verify unit conversion functions to canonical internal units."""

    def test_volume_conversions(self):
        assert math.isclose(convert_volume(1.0, "m3"), 1000.0)
        assert math.isclose(convert_volume(500.0, "mL"), 0.5)
        assert math.isclose(convert_volume(10.0, "L"), 10.0)

    def test_flow_rate_conversions(self):
        assert math.isclose(convert_flow_rate(1.0, "L/s"), 60.0)
        assert math.isclose(convert_flow_rate(60.0, "L/h"), 1.0)
        assert math.isclose(convert_flow_rate(0.06, "m3/h"), 1.0)

    def test_concentration_conversions(self):
        assert math.isclose(convert_concentration(1.0, "kmol/m3"), 1.0)
        assert math.isclose(convert_concentration(1000.0, "mol/m3"), 1.0)
        assert math.isclose(convert_concentration(500.0, "mmol/L"), 0.5)

    def test_rate_constant_conversions(self):
        assert math.isclose(convert_first_order_rate_constant(1.0, "s^-1"), 60.0)
        assert math.isclose(convert_first_order_rate_constant(60.0, "h^-1"), 1.0)
        assert math.isclose(convert_first_order_rate_constant(0.15, "min^-1"), 0.15)

    def test_unsupported_unit_raises_value_error(self):
        with pytest.raises(ValueError, match="Unsupported volume unit"):
            convert_volume(1.0, "gallons")  # type: ignore[arg-type]
        with pytest.raises(ValueError, match="Unsupported flow rate unit"):
            convert_flow_rate(1.0, "gpm")  # type: ignore[arg-type]
        with pytest.raises(ValueError, match="Unsupported concentration unit"):
            convert_concentration(1.0, "ppm")  # type: ignore[arg-type]
        with pytest.raises(ValueError, match="Unsupported time unit"):
            convert_time(1.0, "days")  # type: ignore[arg-type]
        with pytest.raises(ValueError, match="Unsupported rate constant unit"):
            convert_first_order_rate_constant(1.0, "century^-1")  # type: ignore[arg-type]
