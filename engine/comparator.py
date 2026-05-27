"""
Comparator — runs multiple root-finding methods on the same function,
measures performance, and produces ranked comparison tables.

Public API
----------
compare_methods(f, df, a, b, x0, tolerance, max_iter, selected_methods) -> dict
"""

from __future__ import annotations

import time
from typing import Callable, Dict, List, Optional, Tuple, Any

from engine.methods import get_all_methods


# --------------------------------------------------------------------- #
# Space-complexity estimates (constant for each algorithm).              #
# --------------------------------------------------------------------- #
_SPACE_COMPLEXITY: Dict[str, str] = {
    "bisection":      "O(1) — only the bracket endpoints",
    "secant":         "O(1) — two prior iterates",
    "regula_falsi":   "O(1) — bracket endpoints + interpolation point",
    "illinois":       "O(1) — bracket endpoints + side flag",
    "brent":          "O(1) — bracket + 2 auxiliary points + flags",
    "newton_raphson":  "O(1) — single iterate + derivative evaluation",
}


def _compute_error_reduction_rates(steps: List[Dict[str, Any]]) -> List[float]:
    """Return the ratio ``error[i] / error[i-1]`` for consecutive steps.

    A ratio < 1 indicates error is shrinking; > 1 means it is growing.
    When the previous error is (near) zero the ratio is recorded as 0.0
    to avoid division-by-zero artefacts.
    """
    rates: List[float] = []
    for i in range(1, len(steps)):
        prev = steps[i - 1].get("error", 1.0)
        curr = steps[i].get("error", 1.0)
        if prev < 1e-30:
            rates.append(0.0)
        else:
            rates.append(curr / prev)
    return rates


def _run_single_method(
    method_name: str,
    f: Callable[[float], float],
    df: Callable[[float], float],
    a: float,
    b: float,
    x0: float,
    tol: float,
    max_iter: int,
) -> Dict[str, Any]:
    """Execute one root-finding method and wrap its result with timing."""
    methods = get_all_methods()
    method_fn = methods[method_name]

    # ----- dispatch with the correct signature ---------------------------
    start = time.perf_counter()
    try:
        if method_name == "newton_raphson":
            result = method_fn(f, df, x0, tol=tol, max_iter=max_iter)
        elif method_name == "secant":
            # Use a and x0 as the two initial guesses for secant.
            result = method_fn(f, a, x0, tol=tol, max_iter=max_iter)
        else:
            # Bracket methods: bisection, regula_falsi, illinois, brent
            result = method_fn(f, a, b, tol=tol, max_iter=max_iter)
    except Exception as exc:
        # Catch-all so one broken method doesn't crash the whole comparison.
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        return {
            "root": None,
            "converged": False,
            "iterations": 0,
            "execution_time_ms": elapsed_ms,
            "final_error": float("inf"),
            "space_complexity": _SPACE_COMPLEXITY.get(method_name, "O(1)"),
            "steps": [],
            "diverged": False,
            "oscillated": False,
            "stagnated": False,
            "error_reduction_rates": [],
            "error_message": str(exc),
        }
    elapsed_ms = (time.perf_counter() - start) * 1000.0

    error_rates = _compute_error_reduction_rates(result.get("steps", []))

    return {
        "root": result.get("root"),
        "converged": result.get("converged", False),
        "iterations": result.get("iterations", 0),
        "execution_time_ms": round(elapsed_ms, 4),
        "final_error": result.get("final_error", float("inf")),
        "space_complexity": _SPACE_COMPLEXITY.get(method_name, "O(1)"),
        "steps": result.get("steps", []),
        "diverged": result.get("diverged", False),
        "oscillated": result.get("oscillated", False),
        "stagnated": result.get("stagnated", False),
        "error_reduction_rates": error_rates,
    }


# --------------------------------------------------------------------- #
#                         Ranking helpers                                #
# --------------------------------------------------------------------- #

def _rank_by_iterations(results: Dict[str, Dict]) -> List[Tuple[str, int]]:
    """Sort methods ascending by iteration count.

    Non-converged methods are pushed to the end with a large iteration
    count so they do not appear to outperform converged ones.
    """
    items = []
    for name, r in results.items():
        iters = r["iterations"] if r["converged"] else r["iterations"] + 10_000
        items.append((name, r["iterations"]))
    items.sort(key=lambda t: t[1] if results[t[0]]["converged"] else t[1] + 10_000)
    return items


def _rank_by_time(results: Dict[str, Dict]) -> List[Tuple[str, float]]:
    """Sort methods ascending by wall-clock time (ms)."""
    items = [(n, r["execution_time_ms"]) for n, r in results.items()]
    items.sort(key=lambda t: t[1])
    return items


def _rank_by_accuracy(results: Dict[str, Dict]) -> List[Tuple[str, float]]:
    """Sort methods ascending by final error."""
    items = [(n, r["final_error"]) for n, r in results.items()]
    items.sort(key=lambda t: t[1])
    return items


def _overall_ranking(results: Dict[str, Dict]) -> List[Tuple[str, float]]:
    """Composite score (lower is better).

    The score blends normalised ranks across three criteria —
    iterations, time, and accuracy — with a heavy bonus for convergence.

    Weights
    -------
    convergence : 40 % (binary: 0 if converged, 1 if not)
    iterations  : 20 %
    time        : 20 %
    accuracy    : 20 %
    """
    method_names = list(results.keys())
    n = len(method_names)
    if n == 0:
        return []

    # Build per-criterion rank dicts (0-indexed ranks).
    iter_rank = {name: rank for rank, (name, _) in enumerate(_rank_by_iterations(results))}
    time_rank = {name: rank for rank, (name, _) in enumerate(_rank_by_time(results))}
    acc_rank = {name: rank for rank, (name, _) in enumerate(_rank_by_accuracy(results))}

    scores: List[Tuple[str, float]] = []
    for name in method_names:
        conv_penalty = 0.0 if results[name]["converged"] else 1.0
        norm = max(n - 1, 1)  # avoid division by zero when n=1
        score = (
            0.40 * conv_penalty
            + 0.20 * (iter_rank[name] / norm)
            + 0.20 * (time_rank[name] / norm)
            + 0.20 * (acc_rank[name] / norm)
        )
        scores.append((name, round(score, 4)))

    scores.sort(key=lambda t: t[1])
    return scores


# --------------------------------------------------------------------- #
#                          PUBLIC: compare_methods                       #
# --------------------------------------------------------------------- #

def compare_methods(
    f: Callable[[float], float],
    df: Callable[[float], float],
    a: float,
    b: float,
    x0: float,
    tolerance: float = 1e-10,
    max_iter: int = 100,
    selected_methods: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Run every selected method on *f* and produce a ranked comparison.

    Parameters
    ----------
    f               : target function
    df              : derivative of *f* (needed by Newton only)
    a, b            : bracket interval for bracket methods
    x0              : initial guess for Newton / second guess for Secant
    tolerance       : convergence tolerance
    max_iter        : maximum iterations per method
    selected_methods: subset of method names to run (``None`` → all six)

    Returns
    -------
    dict
        ``results``  – per-method result dicts
        ``rankings`` – four sorted lists (by_iterations, by_time,
                       by_accuracy, overall)
    """
    all_methods = get_all_methods()

    if selected_methods is None:
        selected_methods = list(all_methods.keys())

    # Validate
    selected_methods = [m for m in selected_methods if m in all_methods]

    results: Dict[str, Dict] = {}
    for name in selected_methods:
        results[name] = _run_single_method(name, f, df, a, b, x0, tolerance, max_iter)

    rankings = {
        "by_iterations": _rank_by_iterations(results),
        "by_time": _rank_by_time(results),
        "by_accuracy": _rank_by_accuracy(results),
        "overall": _overall_ranking(results),
    }

    return {
        "results": results,
        "rankings": rankings,
    }
