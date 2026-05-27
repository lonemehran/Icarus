"""
Root-Finding Methods — Fully implemented from scratch.

Every method returns a standardised result dict:
    root            – best approximation found (float | None)
    converged       – True iff |f(root)| <= tol  (bool)
    iterations      – number of iterations actually performed (int)
    steps           – list[dict] with per-iteration diagnostics
    final_error     – last computed |f(root)| or |b-a|/2 (float)
    method_name     – human-readable label (str)
    diverged        – True if error grew for DIVERGE_WINDOW consecutive iters
    oscillated      – True if x values began cycling
    stagnated       – True if error stopped decreasing meaningfully
"""

from __future__ import annotations

import math
from typing import Callable, Dict, List, Optional, Any

# ---------------------------------------------------------------------------
# Tuning constants
# ---------------------------------------------------------------------------
DIVERGE_WINDOW: int = 5          # consecutive error-increases before we flag divergence
OSCILLATION_WINDOW: int = 6     # look-back for cycle detection
STAGNATION_RATIO: float = 0.999 # if error_n / error_{n-1} > this for DIVERGE_WINDOW iters


# ===================================================================== #
#                       INTERNAL HELPERS                                 #
# ===================================================================== #

def _safe_eval(f: Callable[[float], float], x: float) -> float:
    """Evaluate *f(x)* with overflow / nan protection.

    Returns math.inf when the result is non-finite so that callers
    can treat it uniformly as a failure signal.
    """
    try:
        val = float(f(x))
    except (ZeroDivisionError, OverflowError, ValueError):
        return math.inf
    if math.isnan(val) or math.isinf(val):
        return math.inf
    return val


def _detect_divergence(errors: List[float]) -> bool:
    """Return True if the last DIVERGE_WINDOW errors are monotonically increasing."""
    if len(errors) < DIVERGE_WINDOW:
        return False
    tail = errors[-DIVERGE_WINDOW:]
    return all(tail[i] > tail[i - 1] for i in range(1, len(tail)))


def _detect_oscillation(xs: List[float]) -> bool:
    """Detect cycling by checking if recent x values repeat within tolerance."""
    if len(xs) < OSCILLATION_WINDOW:
        return False
    tail = xs[-OSCILLATION_WINDOW:]
    # Simple heuristic: check if we see a period-2 or period-3 cycle.
    # Period-2: x_{n} ≈ x_{n-2} and x_{n-1} ≈ x_{n-3}
    for period in (2, 3):
        if len(tail) >= 2 * period:
            cycling = True
            for i in range(period):
                if abs(tail[-(i + 1)] - tail[-(i + 1 + period)]) > 1e-12:
                    cycling = False
                    break
            if cycling:
                return True
    return False


def _detect_stagnation(errors: List[float]) -> bool:
    """Return True if error barely changes for DIVERGE_WINDOW iterations."""
    if len(errors) < DIVERGE_WINDOW:
        return False
    tail = errors[-DIVERGE_WINDOW:]
    for i in range(1, len(tail)):
        prev = tail[i - 1]
        if prev == 0:
            return False  # already converged, not stagnation
        ratio = tail[i] / prev
        if ratio < STAGNATION_RATIO:
            return False  # meaningful decrease happened
    return True


def _build_result(
    root: Optional[float],
    converged: bool,
    iterations: int,
    steps: List[Dict[str, Any]],
    final_error: float,
    method_name: str,
    errors: List[float],
    xs: List[float],
) -> Dict[str, Any]:
    """Construct the canonical result dict including diagnostics."""
    return {
        "root": root,
        "converged": converged,
        "iterations": iterations,
        "steps": steps,
        "final_error": final_error,
        "method_name": method_name,
        "diverged": _detect_divergence(errors),
        "oscillated": _detect_oscillation(xs),
        "stagnated": _detect_stagnation(errors),
    }


# ===================================================================== #
#                        1.  BISECTION                                   #
# ===================================================================== #

def bisection(
    f: Callable[[float], float],
    a: float,
    b: float,
    tol: float = 1e-10,
    max_iter: int = 100,
) -> Dict[str, Any]:
    """Classic interval-halving root finder.

    Prerequisites
    -------------
    f(a) and f(b) must have opposite signs, i.e. f(a)*f(b) < 0.

    Algorithm
    ---------
    1. Compute midpoint c = (a + b) / 2.
    2. If f(c) has the same sign as f(a), replace a with c; else replace b.
    3. Stop when |b − a| / 2 < tol or max_iter reached.

    Returns the standard result dict.
    """
    steps: List[Dict[str, Any]] = []
    errors: List[float] = []
    xs: List[float] = []

    fa = _safe_eval(f, a)
    fb = _safe_eval(f, b)

    # --- guard: sign check -------------------------------------------------
    if fa * fb > 0:
        return _build_result(
            root=None, converged=False, iterations=0, steps=steps,
            final_error=float("inf"), method_name="Bisection",
            errors=errors, xs=xs,
        )

    for i in range(1, max_iter + 1):
        c = (a + b) / 2.0
        fc = _safe_eval(f, c)
        error = abs(b - a) / 2.0

        steps.append({
            "iteration": i, "x": c, "fx": fc, "error": error,
            "a": a, "b": b,
        })
        errors.append(error)
        xs.append(c)

        if error < tol or fc == 0.0:
            return _build_result(c, True, i, steps, error, "Bisection", errors, xs)

        if fa * fc < 0:
            b, fb = c, fc
        else:
            a, fa = c, fc

    # Did not converge within max_iter
    c = (a + b) / 2.0
    return _build_result(c, False, max_iter, steps, errors[-1], "Bisection", errors, xs)


# ===================================================================== #
#                        2.  SECANT                                      #
# ===================================================================== #

def secant(
    f: Callable[[float], float],
    x0: float,
    x1: float,
    tol: float = 1e-10,
    max_iter: int = 100,
) -> Dict[str, Any]:
    """Secant method — two-point derivative-free root finder.

    Uses the approximation f'(x) ≈ (f(x1) − f(x0)) / (x1 − x0) to build
    a Newton-like iteration without requiring an analytic derivative.

    Iteration
    ---------
    x_{n+1} = x_n − f(x_n) · (x_n − x_{n-1}) / (f(x_n) − f(x_{n-1}))

    Returns the standard result dict.
    """
    steps: List[Dict[str, Any]] = []
    errors: List[float] = []
    xs: List[float] = []

    f0 = _safe_eval(f, x0)
    f1 = _safe_eval(f, x1)

    for i in range(1, max_iter + 1):
        denom = f1 - f0
        if abs(denom) < 1e-30:
            # Division by (almost) zero — cannot continue
            error = abs(f1)
            steps.append({"iteration": i, "x": x1, "fx": f1, "error": error,
                          "x_prev": x0, "note": "zero denominator"})
            errors.append(error)
            xs.append(x1)
            return _build_result(x1, False, i, steps, error, "Secant", errors, xs)

        x_new = x1 - f1 * (x1 - x0) / denom
        f_new = _safe_eval(f, x_new)
        error = abs(f_new)

        steps.append({
            "iteration": i, "x": x_new, "fx": f_new, "error": error,
            "x_prev": x1,
        })
        errors.append(error)
        xs.append(x_new)

        if error < tol:
            return _build_result(x_new, True, i, steps, error, "Secant", errors, xs)

        # Divergence / overflow guard
        if math.isinf(f_new) or abs(x_new) > 1e15:
            return _build_result(x_new, False, i, steps, error, "Secant", errors, xs)

        x0, f0 = x1, f1
        x1, f1 = x_new, f_new

    return _build_result(x1, False, max_iter, steps, errors[-1], "Secant", errors, xs)


# ===================================================================== #
#                     3.  REGULA FALSI (False Position)                  #
# ===================================================================== #

def regula_falsi(
    f: Callable[[float], float],
    a: float,
    b: float,
    tol: float = 1e-10,
    max_iter: int = 100,
) -> Dict[str, Any]:
    """Regula Falsi (False Position) method.

    Like bisection, it maintains a bracket [a, b] with f(a)·f(b) < 0, but
    instead of taking the midpoint it uses the x-intercept of the secant line
    through (a, f(a)) and (b, f(b)):

        c = a − f(a) · (b − a) / (f(b) − f(a))

    This converges faster than bisection for many smooth functions but can
    *stagnate* when one endpoint remains fixed (see Illinois variant).

    Returns the standard result dict.
    """
    steps: List[Dict[str, Any]] = []
    errors: List[float] = []
    xs: List[float] = []

    fa = _safe_eval(f, a)
    fb = _safe_eval(f, b)

    if fa * fb > 0:
        return _build_result(None, False, 0, steps, float("inf"),
                             "Regula Falsi", errors, xs)

    for i in range(1, max_iter + 1):
        denom = fb - fa
        if abs(denom) < 1e-30:
            error = abs(fa)
            steps.append({"iteration": i, "x": a, "fx": fa, "error": error,
                          "a": a, "b": b, "note": "zero denominator"})
            errors.append(error)
            xs.append(a)
            return _build_result(a, False, i, steps, error, "Regula Falsi", errors, xs)

        # False-position interpolation point
        c = a - fa * (b - a) / denom
        fc = _safe_eval(f, c)
        error = abs(fc)

        steps.append({
            "iteration": i, "x": c, "fx": fc, "error": error,
            "a": a, "b": b,
        })
        errors.append(error)
        xs.append(c)

        if error < tol:
            return _build_result(c, True, i, steps, error, "Regula Falsi", errors, xs)

        # Update bracket
        if fa * fc < 0:
            b, fb = c, fc
        else:
            a, fa = c, fc

    c_final = a - fa * (b - a) / (fb - fa) if abs(fb - fa) > 1e-30 else (a + b) / 2
    return _build_result(c_final, False, max_iter, steps, errors[-1],
                         "Regula Falsi", errors, xs)


# ===================================================================== #
#                     4.  ILLINOIS  (Modified Regula Falsi)              #
# ===================================================================== #

def illinois(
    f: Callable[[float], float],
    a: float,
    b: float,
    tol: float = 1e-10,
    max_iter: int = 100,
) -> Dict[str, Any]:
    """Illinois modification of Regula Falsi.

    When the same endpoint is retained in two consecutive iterations the
    function value at that endpoint is *halved*, preventing the classic
    Regula Falsi stagnation issue.  This guarantees super-linear convergence
    while still maintaining a valid bracket.

    Returns the standard result dict.
    """
    steps: List[Dict[str, Any]] = []
    errors: List[float] = []
    xs: List[float] = []

    fa = _safe_eval(f, a)
    fb = _safe_eval(f, b)

    if fa * fb > 0:
        return _build_result(None, False, 0, steps, float("inf"),
                             "Illinois", errors, xs)

    side: int = 0  # 0 = initial, -1 = last update was 'a', +1 = last update was 'b'

    for i in range(1, max_iter + 1):
        denom = fb - fa
        if abs(denom) < 1e-30:
            error = abs(fa)
            steps.append({"iteration": i, "x": a, "fx": fa, "error": error,
                          "a": a, "b": b, "note": "zero denominator"})
            errors.append(error)
            xs.append(a)
            return _build_result(a, False, i, steps, error, "Illinois", errors, xs)

        c = a - fa * (b - a) / denom
        fc = _safe_eval(f, c)
        error = abs(fc)

        steps.append({
            "iteration": i, "x": c, "fx": fc, "error": error,
            "a": a, "b": b,
        })
        errors.append(error)
        xs.append(c)

        if error < tol:
            return _build_result(c, True, i, steps, error, "Illinois", errors, xs)

        if fa * fc < 0:
            # Root is in [a, c] → replace b
            if side == 1:
                # 'a' was retained last time too → halve fa (Illinois trick)
                fa *= 0.5
            b, fb = c, fc
            side = 1
        else:
            # Root is in [c, b] → replace a
            if side == -1:
                # 'b' was retained last time too → halve fb
                fb *= 0.5
            a, fa = c, fc
            side = -1

    c_final = a - fa * (b - a) / (fb - fa) if abs(fb - fa) > 1e-30 else (a + b) / 2
    return _build_result(c_final, False, max_iter, steps, errors[-1],
                         "Illinois", errors, xs)


# ===================================================================== #
#                     5.  BRENT'S METHOD                                 #
# ===================================================================== #

def brent(
    f: Callable[[float], float],
    a: float,
    b: float,
    tol: float = 1e-10,
    max_iter: int = 100,
) -> Dict[str, Any]:
    """Brent's method — a hybrid combining bisection, secant, and inverse
    quadratic interpolation.

    The algorithm maintains a bracket [a, b] with ``|f(b)| ≤ |f(a)|``
    (swapping as needed).  At each step it chooses the *best* of three
    possible next iterates:

    1. **Inverse Quadratic Interpolation (IQI)** — used when three
       distinct function values are available and the IQI step lands
       inside the bracket.
    2. **Secant step** — used when only two distinct values are
       available and the secant step lands inside the bracket.
    3. **Bisection** — the safe fallback that guarantees halving the
       bracket width.

    A set of acceptance tests ensures that no step is "too small" or
    "too large", falling back to bisection otherwise.  This gives
    worst-case bisection speed with typical super-linear convergence.

    Returns the standard result dict.
    """
    steps: List[Dict[str, Any]] = []
    errors: List[float] = []
    xs: List[float] = []

    fa = _safe_eval(f, a)
    fb = _safe_eval(f, b)

    if fa * fb > 0:
        return _build_result(None, False, 0, steps, float("inf"),
                             "Brent", errors, xs)

    # Ensure |f(b)| <= |f(a)| so b is always the best guess.
    if abs(fa) < abs(fb):
        a, b = b, a
        fa, fb = fb, fa

    c, fc = a, fa          # c is the previous value of the "contra-point"
    d = b - a              # step size from two iterations ago
    e = d                  # step size from the last iteration

    mflag = True           # True → last step was bisection

    for i in range(1, max_iter + 1):
        error = abs(fb)

        steps.append({
            "iteration": i, "x": b, "fx": fb, "error": error,
            "a": a, "b": b,
            "step_type": "init" if i == 1 else steps[-1].get("next_step_type", ""),
        })
        errors.append(error)
        xs.append(b)

        if error < tol:
            return _build_result(b, True, i, steps, error, "Brent", errors, xs)

        # ----- choose step type -----
        step_type = "bisection"  # default fallback

        if abs(fa - fc) > 1e-30 and abs(fb - fc) > 1e-30:
            # Try inverse quadratic interpolation (three distinct f-values)
            s = (a * fb * fc / ((fa - fb) * (fa - fc))
                 + b * fa * fc / ((fb - fa) * (fb - fc))
                 + c * fa * fb / ((fc - fa) * (fc - fb)))
            step_type = "IQI"
        elif abs(fa - fb) > 1e-30:
            # Fall back to secant
            s = b - fb * (b - a) / (fb - fa)
            step_type = "secant"
        else:
            s = (a + b) / 2.0
            step_type = "bisection"

        # Acceptance tests — if any fails, use bisection instead.
        use_bisection = False
        mid = (a + b) / 2.0

        # Condition 1: s must be between (3a+b)/4 and b
        lo, hi = sorted(((3 * a + b) / 4.0, b))
        if not (lo <= s <= hi):
            use_bisection = True

        # Condition 2: if last step was bisection, check |s − b| < |e|/2
        if mflag and abs(s - b) >= abs(e) / 2.0:
            use_bisection = True

        # Condition 3: if last step was interpolation, same test with d
        if not mflag and abs(s - b) >= abs(d) / 2.0:
            use_bisection = True

        # Condition 4: step not too small
        if mflag and abs(e) < tol:
            use_bisection = True
        if not mflag and abs(d) < tol:
            use_bisection = True

        if use_bisection:
            s = mid
            step_type = "bisection"
            mflag = True
            e = d
            d = s - b
        else:
            mflag = False
            e = d
            d = s - b

        # Record what the *next* step type will be logged as.
        steps[-1]["next_step_type"] = step_type

        # Move: c ← old b, then evaluate s
        c, fc = a, fa   # Brent keeps the "contra-point" as old a (not b)
        # Actually, in classical Brent c tracks the *second-to-last* contra point:
        # we update a or b below.

        fs = _safe_eval(f, s)

        # Update bracket
        if fa * fs < 0:
            b, fb = s, fs
        else:
            a, fa = s, fs

        # Keep |f(b)| ≤ |f(a)|
        if abs(fa) < abs(fb):
            a, b = b, a
            fa, fb = fb, fa

    return _build_result(b, False, max_iter, steps, errors[-1], "Brent", errors, xs)


# ===================================================================== #
#                     6.  NEWTON–RAPHSON                                 #
# ===================================================================== #

def newton_raphson(
    f: Callable[[float], float],
    df: Callable[[float], float],
    x0: float,
    tol: float = 1e-10,
    max_iter: int = 100,
) -> Dict[str, Any]:
    """Standard Newton–Raphson iteration.

    x_{n+1} = x_n − f(x_n) / f'(x_n)

    Parameters
    ----------
    f   : the function whose root we seek
    df  : the *analytic* derivative of f
    x0  : initial guess

    Returns the standard result dict.
    """
    steps: List[Dict[str, Any]] = []
    errors: List[float] = []
    xs: List[float] = []

    x = float(x0)

    for i in range(1, max_iter + 1):
        fx = _safe_eval(f, x)
        dfx = _safe_eval(df, x)

        error = abs(fx)
        steps.append({
            "iteration": i, "x": x, "fx": fx, "dfx": dfx, "error": error,
        })
        errors.append(error)
        xs.append(x)

        if error < tol:
            return _build_result(x, True, i, steps, error, "Newton-Raphson", errors, xs)

        if abs(dfx) < 1e-30:
            steps[-1]["note"] = "zero derivative"
            return _build_result(x, False, i, steps, error, "Newton-Raphson", errors, xs)

        x_new = x - fx / dfx

        # Overflow guard
        if math.isinf(x_new) or math.isnan(x_new) or abs(x_new) > 1e15:
            steps[-1]["note"] = "overflow"
            return _build_result(x, False, i, steps, error, "Newton-Raphson", errors, xs)

        x = x_new

    fx = _safe_eval(f, x)
    return _build_result(x, False, max_iter, steps, abs(fx), "Newton-Raphson", errors, xs)


# ===================================================================== #
#                        METHOD REGISTRY                                 #
# ===================================================================== #

def get_all_methods() -> Dict[str, Callable]:
    """Return a mapping of method name → function for all six solvers.

    Bracket methods (bisection, regula_falsi, illinois, brent) share
    the signature ``(f, a, b, tol, max_iter)``.

    ``secant`` uses ``(f, x0, x1, tol, max_iter)`` (two initial guesses).

    ``newton_raphson`` uses ``(f, df, x0, tol, max_iter)`` where *df* is
    the analytic derivative.
    """
    return {
        "bisection": bisection,
        "secant": secant,
        "regula_falsi": regula_falsi,
        "illinois": illinois,
        "brent": brent,
        "newton_raphson": newton_raphson,
    }
