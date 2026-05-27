# Icarus — Numerical Root-Finding Analysis Platform

**An interactive platform for comparing, analyzing, and visualizing numerical root-finding algorithms across diverse function classes.**

`Python 3.10+` · `Flask` · `MIT License`

---

## Overview

Icarus is a computational mathematics platform that lets you run six classical root-finding algorithms side-by-side on any user-supplied function and instantly compare their convergence behavior, iteration counts, and failure modes.

### Why This Project Exists

Newton-Raphson is the default choice for root-finding in most textbooks and production codebases—but it carries strong assumptions: the function must be differentiable, the derivative must be nonzero at the root, and the initial guess must lie within the basin of attraction. When any of these assumptions break, Newton-Raphson can diverge, oscillate, or silently return a wrong answer.

Icarus makes these limitations visible. By running multiple algorithms on the same problem and presenting their convergence traces together, the platform turns an abstract theoretical comparison into an empirical, interactive experience.

### Key Features

- **Six methods in one interface** — Bisection, Secant, Regula Falsi, Illinois, Brent's, and Newton-Raphson.
- **Real-time convergence comparison** — watch iteration-by-iteration progress for every method simultaneously.
- **Built-in reasoning engine** — automatic function classification (continuous, differentiable, bracketed) with per-method suitability analysis.
- **Demo library** — curated set of challenging test functions that expose each method's strengths and weaknesses.
- **Safe evaluation** — user-supplied expressions are parsed through a restricted evaluator; no arbitrary code execution.
- **JSON API** — programmatic access for batch experiments and integration with notebooks.
- **Detailed diagnostics** — per-method error traces, convergence order estimates, and failure-mode annotations.

---

## Screenshots

> See the application running at `http://localhost:5000`

---

## Installation

### Prerequisites

- Python 3.10 or later
- `pip` (bundled with modern Python installations)

### Steps

```bash
# Clone or navigate to the project directory
cd Icrus_the_algo

# Install dependencies
pip install -r requirements.txt

# Launch the application
python app.py
```

The server starts on **http://localhost:5000** by default.

---

## Usage

### Inputting Functions

Type any single-variable expression using `x` as the variable. Icarus supports standard Python math syntax:

| Syntax           | Meaning                          | Example          |
|------------------|----------------------------------|------------------|
| `x**n`           | Power                            | `x**3 - 2*x - 5`|
| `abs(x)`         | Absolute value                   | `abs(x) - 2`     |
| `sin(x)`, `cos(x)`, `tan(x)` | Trigonometric functions | `tan(x) - 1` |
| `exp(x)`         | Exponential                      | `exp(x) - 3`     |
| `log(x)`         | Natural logarithm                | `log(x) - 1`     |
| `sqrt(x)`        | Square root                      | `sqrt(x) - 2`    |
| `1/x`            | Rational expressions             | `1/x - 1`        |

Parentheses, addition, subtraction, multiplication, and division work as expected.

### Running a Comparison

1. Enter your function expression in the input field.
2. Provide the required parameters:
   - **Bracket** $[a, b]$: required for bracket-based methods (Bisection, Regula Falsi, Illinois, Brent's).
   - **Initial guess** $x_0$: required for open methods (Newton-Raphson, Secant). Secant also uses a second point $x_1$.
   - **Tolerance** $\varepsilon$: convergence threshold (default: $10^{-10}$).
   - **Max iterations**: upper bound on iteration count (default: 100).
3. Click **Run Comparison**.
4. Review the results panel: convergence plots, iteration tables, and the reasoning engine's analysis.

### Demo Mode

Click any entry in the **Demo Functions** sidebar to load a pre-configured test case. Each demo includes:

- A function known to challenge at least one method.
- Pre-set brackets and initial guesses.
- Annotations explaining expected behavior.

Demos are ordered by difficulty: start with the polynomial demos before moving to discontinuous or oscillatory cases.

---

## Architecture

### Folder Structure

```
Icrus_the_algo/
├── app.py                  # Flask application entry point
├── requirements.txt        # Python dependencies
├── README.md               # This file
├── math_explanation.md     # Comprehensive mathematical documentation
├── presentation_script.md  # Guided demo/presentation script
│
├── engine/                 # Core computational modules
│   ├── __init__.py
│   ├── methods.py          # Root-finding algorithm implementations
│   ├── analysis.py         # Convergence analysis & diagnostics
│   └── reasoning.py        # Function classification & method recommendation
│
├── static/                 # Front-end assets
│   ├── css/
│   ├── js/
│   └── img/
│
└── templates/              # Jinja2 HTML templates
    └── index.html
```

### Module Descriptions

| Module               | Responsibility |
|----------------------|----------------|
| `app.py`             | HTTP routing, request validation, response formatting. |
| `engine/methods.py`  | Pure implementations of all six root-finding algorithms. Each method returns a full iteration trace. |
| `engine/analysis.py` | Post-hoc convergence analysis: order estimation, error ratios, stagnation detection. |
| `engine/reasoning.py`| Symbolic and numerical function classification. Determines continuity, differentiability, bracket validity, and produces per-method suitability scores. |

### Data Flow

```
User input (function, params)
        │
        ▼
   app.py — validates & parses
        │
        ▼
  engine/reasoning.py — classifies function
        │
        ▼
  engine/methods.py — runs all 6 solvers
        │
        ▼
  engine/analysis.py — computes diagnostics
        │
        ▼
   JSON response → front-end renders results
```

---

## Methods Implemented

| #  | Method           | Convergence Order | Type     | Derivative? |
|----|------------------|-------------------|----------|-------------|
| 1  | Bisection        | Linear ($O(1)$, rate $0.5$) | Bracket  | No  |
| 2  | Secant           | Superlinear ($\approx 1.618$) | Open     | No  |
| 3  | Regula Falsi     | Linear (can stagnate) | Bracket  | No  |
| 4  | Illinois         | Superlinear ($\approx 1.442$) | Bracket  | No  |
| 5  | Brent's Method   | Superlinear (adaptive) | Bracket  | No  |
| 6  | Newton-Raphson   | Quadratic ($2$) | Open     | **Yes** |

**Bisection** — Halves the bracket at every step. Guaranteed convergence for continuous functions with a sign change, but convergence is slow (one binary digit per iteration).

**Secant** — Approximates the derivative with a finite difference. No explicit derivative needed; converges faster than bisection but can diverge without a bracket.

**Regula Falsi (False Position)** — Like bisection, but uses linear interpolation to choose the next point. Maintains a bracket but can stagnate when one endpoint remains fixed for many iterations.

**Illinois Algorithm** — A modified Regula Falsi that halves the function value at the retained endpoint, preventing stagnation and restoring superlinear convergence.

**Brent's Method** — A hybrid strategy that dynamically switches among bisection, secant, and inverse quadratic interpolation. It guarantees convergence (via the bisection fallback) while achieving superlinear speed in practice.

**Newton-Raphson** — Uses the function value and its derivative to compute a tangent-line intercept. Quadratic convergence near simple roots, but requires a computable derivative and a good initial guess.

> For full mathematical derivations, proofs, and convergence analysis, see [`math_explanation.md`](math_explanation.md).

---

## API Reference

### `POST /api/solve`

Run all root-finding methods on a given function.

**Request Body** (JSON):

```json
{
  "function": "x**3 - 2*x - 5",
  "a": 1.0,
  "b": 3.0,
  "x0": 2.5,
  "x1": 2.0,
  "tolerance": 1e-10,
  "max_iterations": 100
}
```

| Field            | Type    | Required | Description |
|------------------|---------|----------|-------------|
| `function`       | string  | Yes      | Mathematical expression in `x`. |
| `a`              | float   | Yes      | Left bracket endpoint. |
| `b`              | float   | Yes      | Right bracket endpoint. |
| `x0`             | float   | No       | Initial guess for open methods (default: midpoint of bracket). |
| `x1`             | float   | No       | Second initial point for Secant method (default: `b`). |
| `tolerance`      | float   | No       | Convergence tolerance (default: `1e-10`). |
| `max_iterations` | int     | No       | Maximum iterations (default: `100`). |

**Response** (JSON):

```json
{
  "results": {
    "bisection": {
      "root": 2.0945514815,
      "iterations": 34,
      "converged": true,
      "error": 5.82e-11,
      "trace": [
        {"iteration": 1, "x": 2.0, "fx": -1.0, "error": 1.0},
        ...
      ]
    },
    "secant": { ... },
    "regula_falsi": { ... },
    "illinois": { ... },
    "brent": { ... },
    "newton_raphson": { ... }
  },
  "analysis": {
    "function_class": "polynomial",
    "is_continuous": true,
    "is_differentiable": true,
    "bracket_valid": true,
    "recommendations": "All methods applicable. Newton-Raphson expected fastest."
  }
}
```

### `GET /api/demos`

Retrieve the list of built-in demo functions.

**Response** (JSON):

```json
{
  "demos": [
    {
      "name": "Classic Polynomial",
      "function": "x**3 - 2*x - 5",
      "a": 1.0,
      "b": 3.0,
      "x0": 2.5,
      "description": "Standard test case — all methods converge."
    },
    ...
  ]
}
```

---

## Future Expansions

- **Machine learning-based method prediction** — Train a classifier on function features (derivative magnitude, curvature, discontinuity density) to recommend the optimal solver before running any iterations.
- **Adaptive hybrid solvers** — Dynamically switch between methods mid-solve based on real-time convergence diagnostics.
- **Automatic discontinuity detection** — Use interval arithmetic and sampling heuristics to locate jumps, poles, and branch cuts before solving.
- **Symbolic convergence analysis** — Leverage SymPy to compute convergence order and asymptotic error constants symbolically for user-supplied functions.
- **Multi-root detection** — Deflation-based strategies and global search to find all roots within a given interval.
- **Complex root finding** — Extend methods to the complex plane using Müller's method and the Durand–Kerner algorithm.
- **Parallel method execution** — Run all six solvers concurrently via Python multiprocessing for faster batch experiments.
- **Export to LaTeX/PDF reports** — Generate publication-ready comparison reports with convergence plots, tables, and annotated analysis.

---

## License

This project is licensed under the **MIT License**.

```
MIT License

Copyright (c) 2026 Icarus Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## Credits

Built as a **computational mathematics analysis platform** for exploring, teaching, and understanding the practical tradeoffs among classical root-finding algorithms.
