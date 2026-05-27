"""
Reasoning engine — generates natural-language insights, pattern
analyses, and per-method explanations from root-finding comparison
results.

Public API
----------
generate_reasoning(results, function_properties, comparison) -> list[str]
detect_patterns(results, function_properties) -> list[str]
generate_method_explanation(method_name, result) -> str
"""

from __future__ import annotations

from typing import Any, Dict, List


# ===================================================================== #
#  Internal helpers                                                      #
# ===================================================================== #

def _converged_methods(results: Dict[str, Dict]) -> List[str]:
    """Return names of methods that converged."""
    return [n for n, r in results.items() if r.get("converged")]


def _failed_methods(results: Dict[str, Dict]) -> List[str]:
    """Return names of methods that did *not* converge."""
    return [n for n, r in results.items() if not r.get("converged")]


def _bracket_methods() -> set:
    """Names of methods that require (and maintain) a bracket."""
    return {"bisection", "regula_falsi", "illinois", "brent"}


def _avg_error_rate(result: Dict) -> float:
    """Mean of the error-reduction-rate list, or 1.0 if empty."""
    rates = result.get("error_reduction_rates", [])
    if not rates:
        return 1.0
    return sum(rates) / len(rates)


# ===================================================================== #
#                  PUBLIC: generate_reasoning                            #
# ===================================================================== #

def generate_reasoning(
    results: Dict[str, Dict[str, Any]],
    function_properties: Dict[str, Any],
    comparison: Dict[str, Any],
) -> List[str]:
    """Produce a list of technically precise, natural-language insight
    statements that explain *why* the methods performed the way they did
    on this particular function.

    Parameters
    ----------
    results : dict
        Per-method result dicts (from ``comparator.compare_methods``
        → ``results``).
    function_properties : dict
        Output of ``parser.detect_function_properties``.
    comparison : dict
        The full comparison dict including ``rankings``.

    Returns
    -------
    list[str]
        At least 3–5 substantive statements; each 1–3 sentences.
    """
    insights: List[str] = []
    converged = _converged_methods(results)
    failed = _failed_methods(results)
    f_class = function_properties.get("function_class", "general")
    is_diff = function_properties.get("is_differentiable", True)
    is_cont = function_properties.get("is_continuous", True)
    has_sing = function_properties.get("has_singularities", False)
    rankings = comparison.get("rankings", {})

    # ------------------------------------------------------------------
    # 1. Newton diverged on non-differentiable function
    # ------------------------------------------------------------------
    if "newton_raphson" in failed and not is_diff:
        insights.append(
            "Newton-Raphson failed to converge because the function is not "
            "differentiable everywhere in the search interval.  Newton's "
            "method relies on dividing by f'(x), which is undefined or "
            "discontinuous at non-smooth points such as those introduced by "
            "abs(), sign(), or piecewise definitions."
        )

    # ------------------------------------------------------------------
    # 2. Bracket methods succeeded where Newton failed
    # ------------------------------------------------------------------
    bracket_converged = [m for m in converged if m in _bracket_methods()]
    if bracket_converged and "newton_raphson" in failed:
        insights.append(
            f"Bracket methods ({', '.join(bracket_converged)}) succeeded "
            f"where Newton-Raphson failed.  Bracket methods only require "
            f"that the function changes sign across the interval [a, b] — "
            f"they do not need a derivative, making them robust for "
            f"non-smooth or oscillatory functions."
        )

    # ------------------------------------------------------------------
    # 3. Brent was fastest overall
    # ------------------------------------------------------------------
    overall = rankings.get("overall", [])
    if overall and overall[0][0] == "brent":
        insights.append(
            "Brent's method achieved the best overall ranking.  Its hybrid "
            "strategy dynamically switches between inverse quadratic "
            "interpolation, secant steps, and safe bisection fall-backs, "
            "combining super-linear convergence speed with the guaranteed "
            "bracket contraction of bisection."
        )

    # ------------------------------------------------------------------
    # 4. Illinois beat Regula Falsi
    # ------------------------------------------------------------------
    rf = results.get("regula_falsi")
    il = results.get("illinois")
    if rf and il:
        rf_iters = rf.get("iterations", float("inf"))
        il_iters = il.get("iterations", float("inf"))
        if il.get("converged") and il_iters < rf_iters:
            insights.append(
                "The Illinois modification converged in fewer iterations "
                f"({il_iters}) than standard Regula Falsi ({rf_iters}).  "
                "Classic False Position can stagnate when one bracket "
                "endpoint remains fixed across many iterations; Illinois "
                "prevents this by halving the function value at the retained "
                "endpoint, forcing the interpolation point toward the root."
            )
        if rf.get("stagnated") and not il.get("stagnated"):
            insights.append(
                "Regula Falsi exhibited stagnation (the error stopped "
                "decreasing meaningfully), while the Illinois variant did "
                "not.  This confirms the theoretical advantage of the "
                "Illinois modification on functions where one side of the "
                "bracket dominates."
            )

    # ------------------------------------------------------------------
    # 5. Convergence-rate comparison
    # ------------------------------------------------------------------
    rate_info: List[tuple] = []
    for name, r in results.items():
        if r.get("converged"):
            rate_info.append((name, _avg_error_rate(r)))
    if len(rate_info) >= 2:
        rate_info.sort(key=lambda t: t[1])
        fastest_name, fastest_rate = rate_info[0]
        slowest_name, slowest_rate = rate_info[-1]
        insights.append(
            f"Among converged methods, {fastest_name} had the fastest "
            f"average error-reduction rate ({fastest_rate:.4f}), while "
            f"{slowest_name} was the slowest ({slowest_rate:.4f}).  A ratio "
            f"below 1.0 means each iteration shrinks the error; lower is "
            f"better."
        )

    # ------------------------------------------------------------------
    # 6. Function class favours certain methods
    # ------------------------------------------------------------------
    if f_class == "polynomial" and converged:
        insights.append(
            "For a polynomial function, all well-initialised methods are "
            "expected to converge.  Newton-Raphson typically converges "
            "quadratically on smooth polynomials, while bisection provides "
            "guaranteed (but linear) convergence."
        )
    elif f_class == "trigonometric" and has_sing:
        insights.append(
            "Trigonometric functions with asymptotes (e.g. tan(x)) can trap "
            "open methods that step past a singularity.  Bracket methods "
            "confined to a sign-change interval avoid this risk."
        )
    elif f_class in ("piecewise", "absolute_value"):
        insights.append(
            f"The function is classified as '{f_class}', which implies "
            f"points of non-differentiability or discontinuity.  Derivative-"
            f"based methods (Newton-Raphson) may produce unreliable results "
            f"near these points; bracket methods are inherently safer."
        )
    elif f_class == "transcendental":
        insights.append(
            "Transcendental functions (involving exp, log) are smooth and "
            "well-suited for Newton-Raphson, which can exploit the "
            "analytically computable derivative for rapid quadratic "
            "convergence."
        )

    # ------------------------------------------------------------------
    # 7. Divergence / oscillation observations
    # ------------------------------------------------------------------
    diverged_names = [n for n, r in results.items() if r.get("diverged")]
    oscillated_names = [n for n, r in results.items() if r.get("oscillated")]
    if diverged_names:
        insights.append(
            f"The following method(s) diverged (error increased for 5+ "
            f"consecutive iterations): {', '.join(diverged_names)}.  "
            f"Divergence typically occurs when the iteration overshoots the "
            f"root and enters a region where the function grows rapidly."
        )
    if oscillated_names:
        insights.append(
            f"Oscillation was detected in: {', '.join(oscillated_names)}.  "
            f"The iterate values began cycling between two or more points "
            f"without converging, often a sign of a poorly conditioned "
            f"iteration near an inflection point or a flat region."
        )

    # ------------------------------------------------------------------
    # 8. Guarantee at least 3 insights
    # ------------------------------------------------------------------
    if len(insights) < 3:
        if converged:
            best = min(converged, key=lambda n: results[n].get("iterations", float("inf")))
            insights.append(
                f"{results[best]['method_name'] if 'method_name' in results[best] else best} "
                f"converged in the fewest iterations ({results[best]['iterations']})."
            )
        if failed:
            insights.append(
                f"{len(failed)} method(s) failed to converge within the "
                f"given tolerance and iteration budget: {', '.join(failed)}."
            )
        insights.append(
            "Bisection, while typically slower in iteration count, "
            "guarantees convergence for any continuous function with a "
            "sign change — making it a reliable baseline for comparison."
        )

    return insights


# ===================================================================== #
#                  PUBLIC: detect_patterns                               #
# ===================================================================== #

def detect_patterns(
    results: Dict[str, Dict[str, Any]],
    function_properties: Dict[str, Any],
) -> List[str]:
    """Identify cross-method performance patterns.

    Returns
    -------
    list[str]
        Pattern-conclusion statements (2–4 sentences each).
    """
    patterns: List[str] = []
    converged = _converged_methods(results)
    failed = _failed_methods(results)
    f_class = function_properties.get("function_class", "general")
    is_cont = function_properties.get("is_continuous", True)
    is_diff = function_properties.get("is_differentiable", True)

    bracket_names = _bracket_methods()
    bracket_conv = [m for m in converged if m in bracket_names]
    open_conv = [m for m in converged if m not in bracket_names]
    bracket_fail = [m for m in failed if m in bracket_names]
    open_fail = [m for m in failed if m not in bracket_names]

    # Pattern 1: discontinuous function suitability
    if not is_cont:
        patterns.append(
            "Discontinuous functions severely challenge derivative-based and "
            "interpolation methods.  Bisection is the most reliable choice "
            "because it only requires a sign change and never evaluates a "
            "derivative.  Regula Falsi and Illinois can also work if the "
            "discontinuity is outside the initial bracket."
        )

    # Pattern 2: smooth function suitability
    if is_cont and is_diff and f_class in ("polynomial", "transcendental"):
        patterns.append(
            "For smooth, differentiable functions, Newton-Raphson typically "
            "dominates in convergence speed with its quadratic rate, "
            "followed closely by Brent's hybrid approach.  Bisection and "
            "Regula Falsi are slower but serve as robust fail-safes."
        )

    # Pattern 3: bracket vs open
    if bracket_conv and open_fail:
        patterns.append(
            f"Bracket methods ({', '.join(bracket_conv)}) converged while "
            f"open methods ({', '.join(open_fail)}) did not.  This is a "
            f"classic indicator that the function's geometry (e.g. steep "
            f"gradients, non-differentiable points, or near-singularities) "
            f"destabilises iterates that are not constrained to a "
            f"sign-change interval."
        )
    elif open_conv and bracket_fail:
        patterns.append(
            f"Open methods ({', '.join(open_conv)}) converged while bracket "
            f"methods ({', '.join(bracket_fail)}) failed — an unusual "
            f"outcome that suggests the initial bracket [a, b] may not "
            f"satisfy the sign-change requirement, or that f evaluates to "
            f"inf/nan at a bracket endpoint."
        )

    # Pattern 4: Illinois vs Regula Falsi stagnation
    il = results.get("illinois", {})
    rf = results.get("regula_falsi", {})
    if rf.get("stagnated") and not il.get("stagnated"):
        patterns.append(
            "The stagnation pattern in Regula Falsi, absent in Illinois, "
            "confirms a well-known theoretical limitation: when one bracket "
            "endpoint is 'stuck', the false position point barely moves.  "
            "The Illinois half-value trick breaks this deadlock."
        )

    # Pattern 5: general convergence summary
    if len(converged) > 0:
        iter_counts = {n: results[n]["iterations"] for n in converged}
        best = min(iter_counts, key=iter_counts.get)  # type: ignore[arg-type]
        worst = max(iter_counts, key=iter_counts.get)  # type: ignore[arg-type]
        patterns.append(
            f"Across converged methods, {best} needed the fewest iterations "
            f"({iter_counts[best]}) and {worst} needed the most "
            f"({iter_counts[worst]}).  The spread illustrates how algorithm "
            f"choice can dramatically affect computational cost even for the "
            f"same problem."
        )

    # Ensure at least one pattern
    if not patterns:
        patterns.append(
            "No strong cross-method pattern was detected for this function "
            "and parameter combination.  All selected methods behaved "
            "similarly, suggesting the problem is well-conditioned."
        )

    return patterns


# ===================================================================== #
#                PUBLIC: generate_method_explanation                     #
# ===================================================================== #

def generate_method_explanation(
    method_name: str,
    result: Dict[str, Any],
) -> str:
    """Generate a detailed paragraph explaining how a specific method
    performed, including why it converged or diverged.

    Parameters
    ----------
    method_name : str
        Key from ``get_all_methods()`` (e.g. ``"bisection"``).
    result : dict
        The per-method result dict from the comparator.

    Returns
    -------
    str
        Multi-sentence explanation.
    """
    converged = result.get("converged", False)
    iterations = result.get("iterations", 0)
    final_err = result.get("final_error", float("inf"))
    root = result.get("root")
    diverged = result.get("diverged", False)
    oscillated = result.get("oscillated", False)
    stagnated = result.get("stagnated", False)

    # ---- Opening sentence about outcome ----------------------------------
    if converged:
        opening = (
            f"{method_name.replace('_', ' ').title()} converged successfully "
            f"to the root x ≈ {root:.10g} in {iterations} iteration(s) with "
            f"a final error of {final_err:.4e}."
        )
    else:
        opening = (
            f"{method_name.replace('_', ' ').title()} did NOT converge within "
            f"the allotted {iterations} iteration(s).  "
            f"The best approximation was x ≈ {root if root is not None else '(none)'} "
            f"with a residual of {final_err:.4e}."
        )

    # ---- Diagnosis paragraphs --------------------------------------------
    diagnosis_parts: List[str] = []

    if diverged:
        diagnosis_parts.append(
            "The error increased for five or more consecutive iterations, "
            "indicating divergence.  This can happen when the iteration "
            "overshoots into a region where |f(x)| grows without bound, or "
            "when the derivative is near zero, causing Newton-like steps to "
            "become extremely large."
        )

    if oscillated:
        diagnosis_parts.append(
            "The iterates exhibited a cycling pattern (oscillation), "
            "revisiting nearly identical x-values across successive "
            "iterations.  This typically signals a pathological interaction "
            "between the function's shape and the update rule — for "
            "instance, Newton's method oscillating across an inflection "
            "point."
        )

    if stagnated:
        diagnosis_parts.append(
            "The error stopped decreasing meaningfully over multiple "
            "iterations (stagnation).  For Regula Falsi this is a known "
            "deficiency when one bracket endpoint is retained indefinitely.  "
            "For other methods, stagnation may indicate the function is "
            "extremely flat near the root."
        )

    # ---- Method-specific colour ------------------------------------------
    if method_name == "bisection":
        diagnosis_parts.append(
            "Bisection halves the bracket at every step, guaranteeing "
            "linear convergence with a rate of 0.5.  While it cannot "
            "diverge (given a valid sign change), it is the slowest method "
            "in iteration count."
        )
    elif method_name == "secant":
        diagnosis_parts.append(
            "The secant method approximates the derivative via finite "
            "differences, achieving super-linear convergence (order ≈ 1.618) "
            "on smooth functions without requiring an explicit derivative.  "
            "However, it lacks a bracket guarantee and can diverge."
        )
    elif method_name == "regula_falsi":
        diagnosis_parts.append(
            "Regula Falsi maintains a bracket like bisection but uses "
            "linear interpolation for the test point, generally converging "
            "faster.  Its Achilles' heel is stagnation when one endpoint "
            "remains fixed."
        )
    elif method_name == "illinois":
        diagnosis_parts.append(
            "The Illinois variant modifies Regula Falsi by halving the "
            "function value at a retained endpoint, breaking the stagnation "
            "cycle and achieving super-linear convergence while keeping the "
            "bracket guarantee."
        )
    elif method_name == "brent":
        diagnosis_parts.append(
            "Brent's method adaptively selects between inverse quadratic "
            "interpolation, secant, and bisection.  It retains the "
            "worst-case O(log n) guarantee of bisection while typically "
            "matching super-linear convergence of interpolation methods."
        )
    elif method_name == "newton_raphson":
        diagnosis_parts.append(
            "Newton-Raphson uses the analytic derivative to achieve "
            "quadratic convergence near simple roots.  Its primary risks "
            "are division by a near-zero derivative and sensitivity to "
            "the initial guess — a poor starting point can send iterates "
            "far from the root."
        )

    # ---- Error-rate summary ----------------------------------------------
    rates = result.get("error_reduction_rates", [])
    if rates:
        avg_rate = sum(rates) / len(rates)
        diagnosis_parts.append(
            f"The average error-reduction ratio across iterations was "
            f"{avg_rate:.4f} (values < 1.0 indicate convergence; lower is "
            f"faster)."
        )

    return opening + "  " + "  ".join(diagnosis_parts)
