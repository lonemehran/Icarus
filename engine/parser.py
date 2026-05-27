"""
Function parser — converts user-supplied math strings into callable
functions and their symbolic derivatives using SymPy.

Public API
----------
parse_function(expr_str) -> (f, df, sym_expr)
detect_function_properties(sym_expr, a, b) -> dict
"""

from __future__ import annotations

import re
from typing import Callable, Dict, List, Tuple, Any

import numpy as np
import sympy
from sympy import (
    Symbol, sympify, diff, lambdify,
    Abs, Piecewise, sign, floor, ceiling,
    sin, cos, tan, asin, acos, atan, sinh, cosh, tanh,
    exp, log, sqrt, pi, E, oo,
    Rational, Float, Integer,
    solveset, S, Interval,
)
from sympy.core.function import AppliedUndef

# The single independent variable used everywhere.
x = Symbol("x", real=True)

# --------------------------------------------------------------------- #
#  Custom transformation map so users can type natural math notation.    #
# --------------------------------------------------------------------- #
_USER_REPLACEMENTS: List[Tuple[str, str]] = [
    # Caret exponentiation (common user expectation)
    ("^", "**"),
]

# Mapping from common user tokens → SymPy-compatible tokens.
_FUNC_ALIASES: Dict[str, str] = {
    "abs":   "Abs",
    "sign":  "sign",
    "floor": "floor",
    "ceil":  "ceiling",
    "ln":    "log",
    "arcsin": "asin",
    "arccos": "acos",
    "arctan": "atan",
}


def _preprocess(expr_str: str) -> str:
    """Normalise a user-supplied expression string.

    Steps
    -----
    1. Strip leading / trailing whitespace.
    2. Apply caret-to-power replacement.
    3. Translate common function aliases (``abs`` → ``Abs``, etc.).
    4. Replace implicit multiplication patterns like ``2x`` → ``2*x``
       where a digit is directly followed by a letter.

    Returns the cleaned expression string ready for ``sympify``.
    """
    s = expr_str.strip()

    # 1. Simple textual replacements
    for old, new in _USER_REPLACEMENTS:
        s = s.replace(old, new)

    # 2. Function aliases — replace only whole-word occurrences to avoid
    #    mangling substrings like "absolute" or "designer".
    for alias, canonical in _FUNC_ALIASES.items():
        # Use word-boundary regex so 'abs(' → 'Abs(' but 'tabs' is untouched.
        s = re.sub(rf"\b{alias}\b", canonical, s)

    # 3. Implicit multiplication: "2x" → "2*x", "3sin" → "3*sin"
    s = re.sub(r"(\d)([a-zA-Z])", r"\1*\2", s)

    return s


# --------------------------------------------------------------------- #
#                            PUBLIC: parse_function                      #
# --------------------------------------------------------------------- #

def parse_function(
    expr_str: str,
) -> Tuple[Callable[[float], float], Callable[[float], float], sympy.Expr]:
    """Parse a mathematical expression string into callables.

    Parameters
    ----------
    expr_str : str
        Human-readable math string, e.g. ``'x**3 - 2*x - 5'`` or
        ``'abs(x) - 2'``.

    Returns
    -------
    f : callable(float) -> float
        Numerically evaluates the expression.
    df : callable(float) -> float
        Numerically evaluates the symbolic derivative w.r.t. *x*.
    sym_expr : sympy.Expr
        The parsed SymPy expression for downstream analysis.

    Raises
    ------
    ValueError
        If the string cannot be parsed into a valid SymPy expression.
    """
    cleaned = _preprocess(expr_str)

    # Build a local namespace with common math objects so sympify can
    # resolve them.
    local_ns: Dict[str, Any] = {
        "x": x,
        "pi": pi,
        "e": E,
        "E": E,
        "Abs": Abs,
        "sign": sign,
        "floor": floor,
        "ceiling": ceiling,
        "sin": sin,
        "cos": cos,
        "tan": tan,
        "asin": asin,
        "acos": acos,
        "atan": atan,
        "sinh": sinh,
        "cosh": cosh,
        "tanh": tanh,
        "exp": exp,
        "log": log,
        "sqrt": sqrt,
        "Piecewise": Piecewise,
    }

    try:
        sym_expr = sympify(cleaned, locals=local_ns)
    except (sympy.SympifyError, SyntaxError, TypeError) as exc:
        raise ValueError(f"Cannot parse expression '{expr_str}': {exc}") from exc

    # --- symbolic derivative ------------------------------------------------
    sym_deriv = diff(sym_expr, x)

    # --- convert to fast numpy-backed callables ----------------------------
    # We wrap in a try/except so that evaluation errors at specific x values
    # propagate as inf rather than crashing.
    _modules = ["numpy", {"Abs": np.abs, "sign": np.sign,
                           "floor": np.floor, "ceiling": np.ceil}]

    _f_raw = lambdify(x, sym_expr, modules=_modules)
    _df_raw = lambdify(x, sym_deriv, modules=_modules)

    def f(val: float) -> float:  # noqa: D401
        """Evaluate the parsed function at *val*."""
        try:
            result = float(_f_raw(val))
        except Exception:
            result = float("inf")
        return result

    def df(val: float) -> float:  # noqa: D401
        """Evaluate the derivative at *val*."""
        try:
            result = float(_df_raw(val))
        except Exception:
            result = float("inf")
        return result

    return f, df, sym_expr


# --------------------------------------------------------------------- #
#                      PUBLIC: detect_function_properties                #
# --------------------------------------------------------------------- #

def detect_function_properties(
    sym_expr: sympy.Expr,
    a: float,
    b: float,
) -> Dict[str, Any]:
    """Analyse structural properties of *sym_expr* over [a, b].

    The analysis is *heuristic* — it inspects the SymPy expression tree
    to classify the function and flag potential numerical pitfalls, but
    it does **not** perform rigorous mathematical proofs.

    Returns
    -------
    dict with keys:
        is_polynomial, is_continuous, is_differentiable,
        has_singularities, function_class, singularity_points,
        has_asymptotes
    """
    atoms = sym_expr.atoms(sympy.Function)
    free = sym_expr.free_symbols

    # ---- Helper predicates ------------------------------------------------

    def _has_type(*types: type) -> bool:
        """True if the expression tree contains any node of the given types."""
        return any(isinstance(a, tuple(types)) for a in sym_expr.atoms(*types))

    def _contains_abs() -> bool:
        return _has_type(Abs)

    def _contains_piecewise() -> bool:
        return _has_type(Piecewise)

    def _contains_sign() -> bool:
        return _has_type(sympy.sign)

    def _contains_floor_ceil() -> bool:
        return _has_type(sympy.floor, sympy.ceiling)

    def _contains_trig() -> bool:
        return _has_type(sin, cos, tan, asin, acos, atan)

    def _contains_exp_log() -> bool:
        return _has_type(exp, log)

    # ---- is_polynomial ----------------------------------------------------
    is_polynomial: bool = sym_expr.is_polynomial(x)

    # ---- singularity detection --------------------------------------------
    # Look for potential division-by-zero in the expression.
    # We find sub-expressions of the form 1/g(x) or g(x)**(-n) and solve
    # g(x) = 0 within [a, b].
    singularity_points: List[float] = []
    has_singularities = False

    # Walk the expression tree for Pow(base, neg_exp)
    for sub in sympy.preorder_traversal(sym_expr):
        if isinstance(sub, sympy.Pow):
            base, ex = sub.args
            if ex.is_negative:
                try:
                    sols = solveset(base, x, domain=Interval(a, b))
                    for s in sols:
                        val = float(s)
                        if a <= val <= b:
                            singularity_points.append(val)
                            has_singularities = True
                except Exception:
                    # solveset can fail on complex expressions — flag cautiously
                    has_singularities = True

    # tan(x) has singularities at odd multiples of pi/2
    if _contains_trig():
        for sub in sympy.preorder_traversal(sym_expr):
            if isinstance(sub, tan):
                arg = sub.args[0]
                try:
                    # cos(arg) = 0 inside [a, b]
                    sols = solveset(sympy.cos(arg), x, domain=Interval(a, b))
                    for s in sols:
                        val = float(s)
                        if a <= val <= b:
                            singularity_points.append(val)
                            has_singularities = True
                except Exception:
                    has_singularities = True

    # De-duplicate and sort
    singularity_points = sorted(set(round(sp, 12) for sp in singularity_points))

    # ---- continuity / differentiability -----------------------------------
    is_continuous = True
    is_differentiable = True

    if _contains_abs() or _contains_sign():
        is_differentiable = False  # |x| is not differentiable at 0

    if _contains_piecewise() or _contains_sign() or _contains_floor_ceil():
        is_continuous = False      # step / piecewise may be discontinuous
        is_differentiable = False

    if has_singularities:
        is_continuous = False
        is_differentiable = False

    # ---- function class ---------------------------------------------------
    if _contains_piecewise():
        function_class = "piecewise"
    elif _contains_abs():
        function_class = "absolute_value"
    elif is_polynomial:
        function_class = "polynomial"
    elif has_singularities and not _contains_trig() and not _contains_exp_log():
        function_class = "rational"
    elif _contains_trig():
        # Distinguish "oscillatory" (sin/cos dominant) from plain trig
        # Simple heuristic: if the expression *is* a trig function or a sum
        # of trig terms, call it oscillatory; otherwise just trigonometric.
        trig_atoms = {a for a in atoms if isinstance(a, (sin, cos))}
        if len(trig_atoms) >= 2:
            function_class = "oscillatory"
        else:
            function_class = "trigonometric"
    elif _contains_exp_log():
        function_class = "transcendental"
    elif _contains_sign() or _contains_floor_ceil():
        function_class = "piecewise"
    else:
        function_class = "general"

    # ---- asymptotes -------------------------------------------------------
    has_asymptotes = has_singularities  # vertical asymptotes at singularities

    # Also check for horizontal asymptotes (limit at ±∞)
    if not has_asymptotes:
        try:
            lim_pos = sympy.limit(sym_expr, x, oo)
            lim_neg = sympy.limit(sym_expr, x, -oo)
            if lim_pos.is_finite or lim_neg.is_finite:
                has_asymptotes = True
        except Exception:
            pass

    return {
        "is_polynomial": is_polynomial,
        "is_continuous": is_continuous,
        "is_differentiable": is_differentiable,
        "has_singularities": has_singularities,
        "function_class": function_class,
        "singularity_points": singularity_points,
        "has_asymptotes": has_asymptotes,
    }
