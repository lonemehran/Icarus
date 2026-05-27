"""
Flask application — web front-end and JSON API for the root-finding
comparison platform.

Routes
------
GET  /            → serves the index page (templates/index.html)
GET  /api/demos   → returns the list of predefined demo functions
POST /api/solve   → accepts a JSON body, runs the full comparison pipeline,
                     and returns structured results
"""

from __future__ import annotations

import math
import traceback
from typing import Any, Dict, List

from flask import Flask, render_template, request, jsonify

from engine.parser import parse_function, detect_function_properties
from engine.comparator import compare_methods
from engine.reasoning import (
    generate_reasoning,
    detect_patterns,
    generate_method_explanation,
)
from engine.methods import get_all_methods

# ===================================================================== #
#                         DEMO FUNCTIONS                                 #
# ===================================================================== #

DEMO_FUNCTIONS: List[Dict[str, Any]] = [
    {
        "name": "Cubic Polynomial",
        "function": "x**3 - 2*x - 5",
        "a": 1,
        "b": 4,
        "x0": 2.5,
        "description": "Standard smooth polynomial",
    },
    {
        "name": "Absolute Value",
        "function": "abs(x) - 2",
        "a": -5,
        "b": 5,
        "x0": 1.0,
        "description": "Non-differentiable at x=0",
    },
    {
        "name": "Reciprocal",
        "function": "1/x - 1",
        "a": 0.1,
        "b": 3,
        "x0": 0.5,
        "description": "Discontinuous at x=0",
    },
    {
        "name": "Tangent",
        "function": "tan(x) - 1",
        "a": 0,
        "b": 1.4,
        "x0": 0.5,
        "description": "Periodic with asymptotes",
    },
    {
        "name": "Quadratic",
        "function": "x**2 - 4",
        "a": 0,
        "b": 5,
        "x0": 3.0,
        "description": "Simple parabola, root at x=2",
    },
    {
        "name": "Exponential",
        "function": "exp(x) - 3",
        "a": 0,
        "b": 3,
        "x0": 1.5,
        "description": "Smooth transcendental",
    },
    {
        "name": "Sign Function",
        "function": "sign(x) + x - 0.5",
        "a": -2,
        "b": 2,
        "x0": 0.1,
        "description": "Discontinuous step function component",
    },
    {
        "name": "Steep Derivative",
        "function": "x**10 - 1",
        "a": 0,
        "b": 2,
        "x0": 0.5,
        "description": "Very steep near root, flat elsewhere",
    },
]

# ===================================================================== #
#                          FLASK APP                                     #
# ===================================================================== #

app = Flask(__name__)


def _sanitise_for_json(obj: Any) -> Any:
    """Recursively replace non-JSON-serialisable floats (inf, nan)
    with JSON-safe strings so ``jsonify`` does not choke."""
    if isinstance(obj, float):
        if math.isinf(obj):
            return "Infinity" if obj > 0 else "-Infinity"
        if math.isnan(obj):
            return "NaN"
        return obj
    if isinstance(obj, dict):
        return {k: _sanitise_for_json(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_sanitise_for_json(v) for v in obj]
    return obj


# --------------------------------------------------------------------- #
#  GET /                                                                 #
# --------------------------------------------------------------------- #

@app.route("/")
def index():
    """Serve the main single-page application."""
    return render_template("index.html", demos=DEMO_FUNCTIONS)


# --------------------------------------------------------------------- #
#  GET /api/demos                                                        #
# --------------------------------------------------------------------- #

@app.route("/api/demos", methods=["GET"])
def api_demos():
    """Return the list of predefined demo functions."""
    return jsonify({"demos": DEMO_FUNCTIONS})


# --------------------------------------------------------------------- #
#  POST /api/solve                                                       #
# --------------------------------------------------------------------- #

@app.route("/api/solve", methods=["POST"])
def api_solve():
    """Run the full comparison pipeline.

    Expected JSON body
    ------------------
    {
        "function":   "x**3 - 2*x - 5",   // required
        "a":          1.0,                  // required – interval start
        "b":          4.0,                  // required – interval end
        "x0":         2.5,                  // optional – initial guess (default: midpoint)
        "tolerance":  1e-10,               // optional
        "max_iter":   100,                 // optional
        "methods":    ["bisection", ...]   // optional – null → all
    }

    Response JSON
    -------------
    {
        "results":             { ... per-method result dicts ... },
        "rankings":            { ... },
        "function_properties": { ... },
        "reasoning":           [ ... ],
        "patterns":            [ ... ],
        "method_explanations": { method_name: "..." }
    }
    """
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"error": "Request body must be valid JSON"}), 400

    # ---- Extract & validate parameters -----------------------------------
    expr_str = data.get("function")
    if not expr_str or not isinstance(expr_str, str):
        return jsonify({"error": "'function' is required and must be a string"}), 400

    try:
        a = float(data.get("a", 0))
        b = float(data.get("b", 1))
    except (TypeError, ValueError):
        return jsonify({"error": "'a' and 'b' must be numbers"}), 400

    x0 = float(data.get("x0", (a + b) / 2.0))
    tolerance = float(data.get("tolerance", 1e-10))
    max_iter = int(data.get("max_iter", 100))
    selected_methods = data.get("methods")  # None means all

    # ---- Step 1: parse function ------------------------------------------
    try:
        f, df, sym_expr = parse_function(expr_str)
    except ValueError as exc:
        return jsonify({"error": f"Function parse error: {exc}"}), 400

    # ---- Step 2: detect function properties ------------------------------
    try:
        func_props = detect_function_properties(sym_expr, a, b)
    except Exception:
        # Non-fatal: fall back to empty properties
        func_props = {
            "is_polynomial": False,
            "is_continuous": True,
            "is_differentiable": True,
            "has_singularities": False,
            "function_class": "general",
            "singularity_points": [],
            "has_asymptotes": False,
        }

    # ---- Step 3: run comparison ------------------------------------------
    try:
        comparison = compare_methods(
            f=f, df=df, a=a, b=b, x0=x0,
            tolerance=tolerance, max_iter=max_iter,
            selected_methods=selected_methods,
        )
    except Exception as exc:
        return jsonify({"error": f"Comparison failed: {exc}",
                        "traceback": traceback.format_exc()}), 500

    # ---- Step 4: generate reasoning --------------------------------------
    results = comparison.get("results", {})
    try:
        reasoning = generate_reasoning(results, func_props, comparison)
    except Exception:
        reasoning = ["Reasoning generation encountered an error."]

    # ---- Step 5: detect patterns -----------------------------------------
    try:
        patterns = detect_patterns(results, func_props)
    except Exception:
        patterns = ["Pattern detection encountered an error."]

    # ---- Step 6: per-method explanations ----------------------------------
    method_explanations: Dict[str, str] = {}
    for name, res in results.items():
        try:
            method_explanations[name] = generate_method_explanation(name, res)
        except Exception:
            method_explanations[name] = f"{name}: explanation unavailable."

    # ---- Assemble response -----------------------------------------------
    response = _sanitise_for_json({
        "results": results,
        "rankings": comparison.get("rankings", {}),
        "function_properties": func_props,
        "reasoning": reasoning,
        "patterns": patterns,
        "method_explanations": method_explanations,
    })

    return jsonify(response)


# ===================================================================== #
#                          ENTRY POINT                                   #
# ===================================================================== #

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
