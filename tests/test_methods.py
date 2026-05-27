"""
Unit tests for the root-finding comparison platform.

Run with:
    pytest tests/test_methods.py -v

Covers:
- Every root-finding method on x² − 4  (root at x = 2)
- Bisection on |x| − 2  (root at x = 2)
- Newton failure on |x| − 2  (non-differentiable at 0)
- Result structure validation for all methods
- Function parser on various expression strings
- Function property detection
"""

from __future__ import annotations

import math
import pytest

# ------------------------------------------------------------------ #
#                       FIXTURES                                      #
# ------------------------------------------------------------------ #

from engine.methods import (
    bisection,
    secant,
    regula_falsi,
    illinois,
    brent,
    newton_raphson,
    get_all_methods,
)
from engine.parser import parse_function, detect_function_properties
from engine.comparator import compare_methods


# Simple test functions
def f_quadratic(x: float) -> float:
    """x² − 4, roots at ±2."""
    return x ** 2 - 4


def df_quadratic(x: float) -> float:
    """Derivative of x² − 4."""
    return 2 * x


def f_abs(x: float) -> float:
    """|x| − 2, roots at ±2.  Non-differentiable at x = 0."""
    return abs(x) - 2


def df_abs(x: float) -> float:
    """'Derivative' of |x| − 2.  Undefined at 0; we return sign(x)."""
    if x > 0:
        return 1.0
    elif x < 0:
        return -1.0
    else:
        return 0.0  # technically undefined


REQUIRED_KEYS = {
    "root", "converged", "iterations", "steps",
    "final_error", "method_name", "diverged", "oscillated", "stagnated",
}


# ================================================================== #
#                  TEST: Each method on x² − 4                        #
# ================================================================== #

class TestQuadratic:
    """All six methods should converge to x = 2 on [0, 5]."""

    TOL = 1e-10

    def test_bisection(self) -> None:
        result = bisection(f_quadratic, 0, 5, tol=self.TOL)
        assert result["converged"] is True
        assert abs(result["root"] - 2.0) < 1e-8
        assert result["iterations"] > 0

    def test_secant(self) -> None:
        result = secant(f_quadratic, 0, 5, tol=self.TOL)
        assert result["converged"] is True
        assert abs(result["root"] - 2.0) < 1e-8

    def test_regula_falsi(self) -> None:
        result = regula_falsi(f_quadratic, 0, 5, tol=self.TOL)
        assert result["converged"] is True
        assert abs(result["root"] - 2.0) < 1e-8

    def test_illinois(self) -> None:
        result = illinois(f_quadratic, 0, 5, tol=self.TOL)
        assert result["converged"] is True
        assert abs(result["root"] - 2.0) < 1e-8

    def test_brent(self) -> None:
        result = brent(f_quadratic, 0, 5, tol=self.TOL)
        assert result["converged"] is True
        assert abs(result["root"] - 2.0) < 1e-8

    def test_newton_raphson(self) -> None:
        result = newton_raphson(f_quadratic, df_quadratic, 3.0, tol=self.TOL)
        assert result["converged"] is True
        assert abs(result["root"] - 2.0) < 1e-8


# ================================================================== #
#         TEST: Bisection on |x| − 2  (root at x = 2)                #
# ================================================================== #

class TestAbsoluteBisection:
    """Bisection should handle the non-differentiable |x| − 2 just fine."""

    def test_converges_to_positive_root(self) -> None:
        result = bisection(f_abs, 0, 5, tol=1e-10)
        assert result["converged"] is True
        assert abs(result["root"] - 2.0) < 1e-8

    def test_converges_to_negative_root(self) -> None:
        result = bisection(f_abs, -5, 0, tol=1e-10)
        assert result["converged"] is True
        assert abs(result["root"] - (-2.0)) < 1e-8


# ================================================================== #
#     TEST: Newton failure on |x| − 2  (non-differentiable)          #
# ================================================================== #

class TestNewtonFailure:
    """Newton-Raphson should struggle with |x| − 2 when starting near 0."""

    def test_newton_near_zero_derivative(self) -> None:
        # Starting at x=0 the derivative is 0 → should not converge.
        result = newton_raphson(f_abs, df_abs, 0.0, tol=1e-10, max_iter=100)
        # At x=0, df_abs returns 0 → zero derivative → early exit without convergence
        assert result["converged"] is False

    def test_newton_away_from_kink_works(self) -> None:
        # Starting far from the kink, Newton can still converge for |x|−2.
        result = newton_raphson(f_abs, df_abs, 3.0, tol=1e-10, max_iter=100)
        # From x=3 in the region x>0, |x|=x so f=x-2, f'=1 → converges
        assert result["converged"] is True
        assert abs(result["root"] - 2.0) < 1e-8


# ================================================================== #
#               TEST: Result structure for all methods                #
# ================================================================== #

class TestResultStructure:
    """Every method must return a dict with the required keys and types."""

    @pytest.mark.parametrize("method_name", list(get_all_methods().keys()))
    def test_required_keys_present(self, method_name: str) -> None:
        methods = get_all_methods()
        fn = methods[method_name]

        if method_name == "newton_raphson":
            result = fn(f_quadratic, df_quadratic, 3.0)
        elif method_name == "secant":
            result = fn(f_quadratic, 0.0, 5.0)
        else:
            result = fn(f_quadratic, 0, 5)

        for key in REQUIRED_KEYS:
            assert key in result, f"Missing key '{key}' in {method_name} result"

    @pytest.mark.parametrize("method_name", list(get_all_methods().keys()))
    def test_types(self, method_name: str) -> None:
        methods = get_all_methods()
        fn = methods[method_name]

        if method_name == "newton_raphson":
            result = fn(f_quadratic, df_quadratic, 3.0)
        elif method_name == "secant":
            result = fn(f_quadratic, 0.0, 5.0)
        else:
            result = fn(f_quadratic, 0, 5)

        assert isinstance(result["converged"], bool)
        assert isinstance(result["iterations"], int)
        assert isinstance(result["steps"], list)
        assert isinstance(result["final_error"], float)
        assert isinstance(result["method_name"], str)
        assert isinstance(result["diverged"], bool)
        assert isinstance(result["oscillated"], bool)
        assert isinstance(result["stagnated"], bool)

    @pytest.mark.parametrize("method_name", list(get_all_methods().keys()))
    def test_steps_are_dicts(self, method_name: str) -> None:
        methods = get_all_methods()
        fn = methods[method_name]

        if method_name == "newton_raphson":
            result = fn(f_quadratic, df_quadratic, 3.0)
        elif method_name == "secant":
            result = fn(f_quadratic, 0.0, 5.0)
        else:
            result = fn(f_quadratic, 0, 5)

        for step in result["steps"]:
            assert isinstance(step, dict)
            assert "iteration" in step
            assert "x" in step
            assert "fx" in step
            assert "error" in step


# ================================================================== #
#              TEST: Function parser on various strings               #
# ================================================================== #

class TestParser:
    """parse_function must handle a variety of math expressions."""

    @pytest.mark.parametrize(
        "expr, x_val, expected_approx",
        [
            ("x**2 - 4", 2.0, 0.0),
            ("x**3 - 2*x - 5", 2.0946, 0.0),       # approx root
            ("abs(x) - 2", 2.0, 0.0),
            ("abs(x) - 2", -2.0, 0.0),
            ("sin(x)", 0.0, 0.0),
            ("exp(x) - 1", 0.0, 0.0),
            ("log(x) - 1", math.e, 0.0),
            ("sqrt(x) - 2", 4.0, 0.0),
            ("x^2 - 9", 3.0, 0.0),                   # caret syntax
        ],
    )
    def test_evaluation(self, expr: str, x_val: float, expected_approx: float) -> None:
        f, df, sym = parse_function(expr)
        assert abs(f(x_val) - expected_approx) < 0.01

    def test_derivative_quadratic(self) -> None:
        f, df, sym = parse_function("x**2 - 4")
        # f'(x) = 2x  → f'(3) = 6
        assert abs(df(3.0) - 6.0) < 1e-8

    def test_derivative_sin(self) -> None:
        f, df, sym = parse_function("sin(x)")
        # f'(x) = cos(x) → f'(0) = 1
        assert abs(df(0.0) - 1.0) < 1e-8

    def test_invalid_expression_raises(self) -> None:
        with pytest.raises(ValueError):
            parse_function("???!!!")


# ================================================================== #
#           TEST: Function property detection                        #
# ================================================================== #

class TestFunctionProperties:
    """detect_function_properties should classify common expressions."""

    def test_polynomial(self) -> None:
        _, _, sym = parse_function("x**3 - 2*x - 5")
        props = detect_function_properties(sym, 0, 5)
        assert props["is_polynomial"] is True
        assert props["function_class"] == "polynomial"

    def test_absolute_value(self) -> None:
        _, _, sym = parse_function("abs(x) - 2")
        props = detect_function_properties(sym, -5, 5)
        assert props["function_class"] == "absolute_value"
        assert props["is_differentiable"] is False

    def test_reciprocal_has_singularity(self) -> None:
        _, _, sym = parse_function("1/x - 1")
        props = detect_function_properties(sym, -2, 2)
        assert props["has_singularities"] is True

    def test_trig_classification(self) -> None:
        _, _, sym = parse_function("tan(x) - 1")
        props = detect_function_properties(sym, 0, 1)
        assert props["function_class"] in ("trigonometric", "oscillatory")


# ================================================================== #
#          TEST: Comparator end-to-end                                #
# ================================================================== #

class TestComparator:
    """Smoke test for compare_methods."""

    def test_returns_all_methods(self) -> None:
        f, df, _ = parse_function("x**2 - 4")
        comp = compare_methods(f, df, 0, 5, 3.0, tolerance=1e-10, max_iter=100)
        assert "results" in comp
        assert "rankings" in comp
        assert len(comp["results"]) == 6  # all six methods

    def test_rankings_structure(self) -> None:
        f, df, _ = parse_function("x**2 - 4")
        comp = compare_methods(f, df, 0, 5, 3.0)
        rankings = comp["rankings"]
        for key in ("by_iterations", "by_time", "by_accuracy", "overall"):
            assert key in rankings
            assert isinstance(rankings[key], list)

    def test_selected_methods(self) -> None:
        f, df, _ = parse_function("x**2 - 4")
        comp = compare_methods(f, df, 0, 5, 3.0,
                               selected_methods=["bisection", "brent"])
        assert set(comp["results"].keys()) == {"bisection", "brent"}


# ================================================================== #
#           TEST: Sign-change violation returns gracefully            #
# ================================================================== #

class TestNoSignChange:
    """Bracket methods must return converged=False when f(a)*f(b) > 0."""

    @pytest.mark.parametrize("method_name", ["bisection", "regula_falsi", "illinois", "brent"])
    def test_no_sign_change(self, method_name: str) -> None:
        # f(x)=x²+1 has no real roots → f(a)*f(b) > 0 for any a,b.
        def f_no_root(x: float) -> float:
            return x ** 2 + 1

        methods = get_all_methods()
        result = methods[method_name](f_no_root, -5, 5)
        assert result["converged"] is False
