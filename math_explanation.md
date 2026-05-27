# Mathematical Foundations of Root-Finding Methods

This document provides a rigorous mathematical treatment of the six root-finding algorithms implemented in Icarus. For each method we present the derivation from first principles, the convergence theory, failure modes, and computational cost. A comparative analysis closes the document.

---

## Table of Contents

1. [Preliminaries](#1-preliminaries)
2. [Bisection Method](#2-bisection-method)
3. [Secant Method](#3-secant-method)
4. [Regula Falsi (False Position)](#4-regula-falsi-false-position)
5. [Illinois Algorithm](#5-illinois-algorithm)
6. [Brent's Method](#6-brents-method)
7. [Newton-Raphson Method](#7-newton-raphson-method)
8. [Comparison Summary](#8-comparison-summary)
9. [Why Non-Continuous Functions Matter](#9-why-non-continuous-functions-matter)
10. [Derivative Dependency Analysis](#10-derivative-dependency-analysis)
11. [Bracketing vs Open Methods](#11-bracketing-vs-open-methods)

---

## 1. Preliminaries

We seek a value $x^*$ such that $f(x^*) = 0$, where $f$ is a real-valued function defined on some interval. The methods below differ in what they assume about $f$ (continuity, differentiability, sign change) and in what information they use at each step (function values, derivatives, bracket endpoints).

**Notation conventions:**

- $e_n = x_n - x^*$ denotes the error at iteration $n$.
- $\varepsilon$ denotes the convergence tolerance.
- $[a_n, b_n]$ denotes the bracket at iteration $n$ for bracketing methods.
- A method has **order of convergence** $p$ if $|e_{n+1}| \sim C\,|e_n|^p$ as $n \to \infty$.

---

## 2. Bisection Method

### 2.1 Mathematical Derivation

The Bisection Method is a direct application of the **Intermediate Value Theorem (IVT)**:

> If $f$ is continuous on $[a, b]$ and $f(a)\,f(b) < 0$, then there exists at least one $x^* \in (a, b)$ such that $f(x^*) = 0$.

The method maintains an interval $[a_n, b_n]$ containing a root and systematically halves it.

**Construction.** Given a bracket $[a_0, b_0]$ with $f(a_0)\,f(b_0) < 0$:

1. Compute the midpoint: $c_n = \frac{a_n + b_n}{2}$.
2. Evaluate $f(c_n)$.
3. Update the bracket:
   - If $f(a_n)\,f(c_n) < 0$, set $a_{n+1} = a_n,\; b_{n+1} = c_n$.
   - If $f(c_n)\,f(b_n) < 0$, set $a_{n+1} = c_n,\; b_{n+1} = b_n$.
   - If $f(c_n) = 0$, then $x^* = c_n$; terminate.

### 2.2 Update Equation

$$x_{n+1} = c_n = \frac{a_n + b_n}{2}$$

with the bracket update rule selecting the sub-interval containing the sign change.

### 2.3 Convergence Analysis

**Order of convergence:** Linear (order $p = 1$), with a contraction factor of $\frac{1}{2}$.

**Theorem (Bisection Convergence).** *Let $f$ be continuous on $[a, b]$ with $f(a)\,f(b) < 0$. Then after $n$ iterations of the bisection method, the midpoint $c_n$ satisfies:*

$$|c_n - x^*| \leq \frac{b - a}{2^{n+1}}$$

**Proof.** At each step the bracket width is halved:

$$b_{n} - a_{n} = \frac{b_0 - a_0}{2^n} = \frac{b - a}{2^n}$$

Since $x^*$ lies within $[a_n, b_n]$ and $c_n$ is its midpoint:

$$|c_n - x^*| \leq \frac{b_n - a_n}{2} = \frac{b - a}{2^{n+1}} \qquad \blacksquare$$

**Corollary.** To achieve $|c_n - x^*| < \varepsilon$, we need:

$$n \geq \left\lceil \log_2\!\left(\frac{b - a}{\varepsilon}\right) \right\rceil - 1$$

For $[a, b] = [1, 3]$ and $\varepsilon = 10^{-10}$, this gives $n \geq 34$ iterations.

**Convergence rate.** The error satisfies $|e_{n+1}| = \frac{1}{2}|e_n|$ in the worst case, confirming linear convergence with rate $r = 0.5$. Each iteration gains approximately $\log_{10} 2 \approx 0.301$ decimal digits of accuracy.

### 2.4 Convergence Conditions

- **Required:** $f$ is continuous on $[a, b]$ and $f(a)\,f(b) < 0$.
- **Not required:** differentiability, smoothness, or Lipschitz conditions.
- **When violated:** If $f(a)\,f(b) > 0$, no sign change is detected and the method cannot start. If $f$ is discontinuous with a sign change (e.g., $f(x) = \text{sgn}(x)$), bisection converges to the discontinuity, not a true root.

### 2.5 Limitations

- **Slow convergence:** Only one bit of accuracy per iteration. For double-precision accuracy ($\sim 10^{-16}$), about 53 iterations are needed regardless of the function.
- **Cannot detect even-multiplicity roots:** If the root has even multiplicity, $f$ does not change sign, and bisection cannot find it.
- **Requires an initial bracket:** The user must supply $a$ and $b$ with $f(a)\,f(b) < 0$. Finding such a bracket may itself be non-trivial.
- **Only finds one root:** Even if $[a, b]$ contains multiple roots, bisection converges to exactly one (determined by the sign-change structure).

### 2.6 Computational Complexity

| Metric                        | Cost          |
|-------------------------------|---------------|
| Function evaluations per step | 1             |
| Auxiliary storage             | $O(1)$        |
| Total evaluations to tolerance $\varepsilon$ | $O\!\left(\log\frac{b-a}{\varepsilon}\right)$ |

---

## 3. Secant Method

### 3.1 Mathematical Derivation

The Secant Method arises from **replacing the derivative in Newton-Raphson with a finite-difference approximation.**

Newton-Raphson updates via:

$$x_{n+1} = x_n - \frac{f(x_n)}{f'(x_n)}$$

If $f'(x_n)$ is unavailable, approximate it using the two most recent iterates:

$$f'(x_n) \approx \frac{f(x_n) - f(x_{n-1})}{x_n - x_{n-1}}$$

Substituting:

$$x_{n+1} = x_n - f(x_n) \cdot \frac{x_n - x_{n-1}}{f(x_n) - f(x_{n-1})}$$

**Geometric interpretation:** Draw the secant line through the points $(x_{n-1}, f(x_{n-1}))$ and $(x_n, f(x_n))$; $x_{n+1}$ is the $x$-intercept of this line.

### 3.2 Update Equation

$$x_{n+1} = x_n - f(x_n)\,\frac{x_n - x_{n-1}}{f(x_n) - f(x_{n-1})}$$

Equivalently:

$$x_{n+1} = \frac{x_{n-1}\,f(x_n) - x_n\,f(x_{n-1})}{f(x_n) - f(x_{n-1})}$$

### 3.3 Convergence Analysis

**Order of convergence:** Superlinear, with order $p = \varphi = \frac{1 + \sqrt{5}}{2} \approx 1.618$ (the golden ratio).

**Theorem (Secant Method Convergence Order).** *Let $f \in C^2[a, b]$, $f(x^*) = 0$, $f'(x^*) \neq 0$. If $x_0, x_1$ are sufficiently close to $x^*$, then the secant method converges with order $\varphi$:*

$$|e_{n+1}| \leq C\,|e_n|^{\varphi}$$

*where $C$ depends on $f''(x^*) / (2 f'(x^*))$.*

**Proof sketch.** Define the error $e_n = x_n - x^*$. Taylor-expand $f(x_n)$ and $f(x_{n-1})$ about $x^*$:

$$f(x_n) = f'(x^*)\,e_n + \tfrac{1}{2}f''(x^*)\,e_n^2 + O(e_n^3)$$

Substituting into the secant recurrence and simplifying (dividing out $f'(x^*) \neq 0$):

$$e_{n+1} \approx \frac{f''(x^*)}{2\,f'(x^*)}\,e_n\,e_{n-1}$$

Set $|e_{n+1}| \sim C\,|e_n|^p$. Then $|e_n|^p \sim |e_n|\,|e_{n-1}|$, and since $|e_n| \sim |e_{n-1}|^p$ by induction, we get $|e_n|^p \sim |e_n|\,|e_n|^{1/p}$, whence $p = 1 + 1/p$, giving $p^2 - p - 1 = 0$ and $p = \varphi$. $\blacksquare$

**Comparison with Bisection:** Bisection gains $\sim 0.301$ digits per iteration; the Secant method gains $\sim 0.489$ digits per iteration (since $\log_{10}\varphi \approx 0.489$). However, the secant method uses one function evaluation per step (amortized), making it more efficient per evaluation than Newton-Raphson's quadratic convergence when derivatives are expensive.

### 3.4 Convergence Conditions

- **Required:** $f$ must be $C^2$ near the root, $f'(x^*) \neq 0$ (simple root), and both starting points $x_0, x_1$ must be "sufficiently close" to $x^*$.
- **Not required:** a bracket ($f(x_0)$ and $f(x_1)$ need not have opposite signs), or an explicit derivative.
- **When violated:** If $x_0, x_1$ are far from the root or if $f$ has a flat region, $f(x_n) \approx f(x_{n-1})$ causes the denominator to approach zero, leading to enormous steps and likely divergence.

### 3.5 Limitations

- **No bracket maintenance:** The method can leave the region of interest and diverge.
- **Sensitive to initial points:** Poor choices of $x_0, x_1$ easily cause failure.
- **Failure at multiple roots:** If $f'(x^*) = 0$ (e.g., double root), convergence degrades to order 1.
- **Division by near-zero:** When $f(x_n) \approx f(x_{n-1})$, the step size becomes very large (effective division by zero).

### 3.6 Computational Complexity

| Metric                        | Cost                   |
|-------------------------------|------------------------|
| Function evaluations per step | 1 (reuses previous value) |
| Auxiliary storage             | $O(1)$                 |
| Total evaluations to tolerance $\varepsilon$ | $O\!\left(\log\log\frac{1}{\varepsilon}\right)$ (superlinear) |

The secant method requires roughly $\log_\varphi(\log(1/\varepsilon))$ iterations, making it significantly faster than bisection for smooth functions.

---

## 4. Regula Falsi (False Position)

### 4.1 Mathematical Derivation

Regula Falsi combines the **bracket safety of bisection** with the **interpolation efficiency of the secant method**.

Given $[a_n, b_n]$ with $f(a_n)\,f(b_n) < 0$, instead of choosing the midpoint (bisection) or an unconstrained secant step, we take the $x$-intercept of the line connecting $(a_n, f(a_n))$ and $(b_n, f(b_n))$, then update the bracket.

The secant line through the bracket endpoints is:

$$L(x) = f(a_n) + \frac{f(b_n) - f(a_n)}{b_n - a_n}(x - a_n)$$

Setting $L(c) = 0$ and solving for $c$:

$$c_n = a_n - f(a_n)\,\frac{b_n - a_n}{f(b_n) - f(a_n)} = \frac{a_n\,f(b_n) - b_n\,f(a_n)}{f(b_n) - f(a_n)}$$

Then update:
- If $f(a_n)\,f(c_n) < 0$: set $b_{n+1} = c_n$, $a_{n+1} = a_n$.
- If $f(c_n)\,f(b_n) < 0$: set $a_{n+1} = c_n$, $b_{n+1} = b_n$.

### 4.2 Update Equation

$$c_n = \frac{a_n\,f(b_n) - b_n\,f(a_n)}{f(b_n) - f(a_n)}$$

### 4.3 Convergence Analysis

**Order of convergence:** Linear ($p = 1$), but typically faster than bisection in practice—until stagnation occurs.

**The stagnation problem.** If $f$ is convex (or concave) on $[a, b]$, one bracket endpoint remains fixed for all iterations. For example, if $f$ is convex and the root is near $b$, then $a_n = a_0$ for all $n$, and the method reduces to linear convergence with a poor contraction ratio.

Formally, when one endpoint is stuck:

$$|e_{n+1}| \approx \left(1 - \frac{f'(x^*)}{m}\right)|e_n|$$

where $m$ is the slope of the secant from the fixed endpoint. As the fixed endpoint drifts further from the root, $m$ becomes a worse approximation of $f'(x^*)$, and convergence slows dramatically.

**Theorem (Regula Falsi Convergence).** *Let $f \in C^1[a, b]$ with $f(a)\,f(b) < 0$ and $f'(x) \neq 0$ on $[a, b]$. Then Regula Falsi converges, but the convergence is at best linear.*

### 4.4 Convergence Conditions

- **Required:** $f$ continuous on $[a, b]$, $f(a)\,f(b) < 0$.
- **Guaranteed convergence:** Yes—the bracket never expands and always contains the root.
- **When conditions break:** Same as bisection regarding continuity and sign change.

### 4.5 Limitations

- **Stagnation:** The defining weakness. On convex/concave functions, one endpoint freezes, and convergence becomes painfully slow—potentially slower than bisection despite using interpolation.
- **Cannot improve beyond linear:** Even in the best case, without modifications the order remains $p = 1$.
- **Misleading reputation:** The name "False Position" and its similarity to the Secant method lead to expectations of superlinear convergence, but the bracket constraint prevents it.

### 4.6 Computational Complexity

| Metric                        | Cost          |
|-------------------------------|---------------|
| Function evaluations per step | 1             |
| Auxiliary storage             | $O(1)$        |
| Total evaluations to tolerance $\varepsilon$ | $O(1/\varepsilon)$ worst case (linear convergence with bad constant) |

---

## 5. Illinois Algorithm

### 5.1 Mathematical Derivation

The Illinois Algorithm is a targeted fix for the **stagnation problem** of Regula Falsi. The key insight is elegant:

> When an endpoint has been retained (not updated) for two consecutive iterations, **halve the function value at that endpoint** before computing the next interpolation point.

This artificially reduces the "weight" of the stale endpoint, pulling the interpolation point toward it and forcing the bracket to shrink from both sides.

**Construction.** Run Regula Falsi as usual, but track which endpoint was retained. If the same endpoint was retained in the previous step:

- If $a_n$ was retained: use $\frac{1}{2}f(a_n)$ instead of $f(a_n)$ in the interpolation formula.
- If $b_n$ was retained: use $\frac{1}{2}f(b_n)$ instead of $f(b_n)$.

This is equivalent to modifying the secant line to pass through a "phantom point" closer to the $x$-axis, biasing the interpolation toward the stale side.

### 5.2 Update Equation

Let $\tilde{f}(a_n) = f(a_n)$ normally, or $\tilde{f}(a_n) = \frac{1}{2}f(a_n)$ if $a_n$ was retained from the previous step (and similarly for $b_n$). Then:

$$c_n = \frac{a_n\,\tilde{f}(b_n) - b_n\,\tilde{f}(a_n)}{\tilde{f}(b_n) - \tilde{f}(a_n)}$$

### 5.3 Convergence Analysis

**Order of convergence:** Superlinear, with order $p = \frac{1 + \sqrt{5}}{2} \approx 1.442$ (specifically, the positive root of $p^2 - p - \frac{1}{2} = 0$ for the halving variant).

**Theorem (Illinois Convergence).** *Under the same conditions as Regula Falsi (continuity, bracket with sign change), the Illinois modification guarantees that neither endpoint remains fixed for more than two consecutive iterations, and the method converges superlinearly.*

**Proof sketch.** Suppose endpoint $a$ has been retained twice in succession. The halving step ensures the next interpolation point falls on the opposite side of $x^*$ from $c_n$, forcing $a$ to be updated. This alternation prevents stagnation and, via analysis similar to the Secant method (but with the halving perturbation), yields a convergence order satisfying $p^2 = p + \frac{1}{2}$. $\blacksquare$

**Compared to Regula Falsi:** The Illinois Algorithm typically converges 3–10× faster in iteration count on convex functions, while adding negligible overhead per iteration.

### 5.4 Convergence Conditions

- Identical to Regula Falsi: $f$ continuous, bracket with sign change.
- The halving modification does not require additional assumptions.

### 5.5 Limitations

- **Still bracket-based:** Cannot find roots without an initial sign change.
- **Not as fast as Newton or Brent:** Convergence order $\approx 1.442$ is below the Secant method's $\varphi \approx 1.618$ and Newton's $2$.
- **Multiple variants:** The "halving" strategy is one of several (Pegasus, Anderson–Björck); each has slightly different convergence properties, and the optimal choice is problem-dependent.

### 5.6 Computational Complexity

| Metric                        | Cost          |
|-------------------------------|---------------|
| Function evaluations per step | 1             |
| Auxiliary storage             | $O(1)$        |
| Total evaluations to tolerance $\varepsilon$ | $O\!\left((\log(1/\varepsilon))^{1/p}\right)$ with $p \approx 1.442$ |

---

## 6. Brent's Method

### 6.1 Mathematical Derivation

Brent's Method (1973) is a **hybrid algorithm** that combines the reliability of bisection with the speed of interpolation. It dynamically chooses among three strategies at each step:

1. **Bisection** — guaranteed progress, used as a fallback.
2. **Secant step** — linear interpolation between two points.
3. **Inverse Quadratic Interpolation (IQI)** — fits a quadratic through three points in "inverse" form.

**Inverse Quadratic Interpolation.** Given three distinct points $(x_{n-2}, f_{n-2})$, $(x_{n-1}, f_{n-1})$, $(x_n, f_n)$ with distinct function values, IQI constructs the quadratic $x = Q(y)$ passing through the three points (i.e., $x$ as a function of $y = f(x)$), then evaluates $Q(0)$:

$$x_{n+1} = \frac{f_{n-1} f_n}{(f_{n-2} - f_{n-1})(f_{n-2} - f_n)} x_{n-2} + \frac{f_{n-2} f_n}{(f_{n-1} - f_{n-2})(f_{n-1} - f_n)} x_{n-1} + \frac{f_{n-2} f_{n-1}}{(f_n - f_{n-2})(f_n - f_{n-1})} x_n$$

**Decision logic.** At each iteration, Brent's method proposes a candidate step (secant or IQI) and then checks whether it satisfies several acceptance criteria:

- The candidate must lie within the current bracket $[a_n, b_n]$.
- The step must be smaller than half the previous step (to ensure superlinear progress).
- The step must not be "too small" (to avoid stagnation near machine epsilon).

If any criterion fails, the method defaults to a bisection step.

### 6.2 Update Equation

No single formula; the update is conditional:

$$x_{n+1} = \begin{cases}
\text{IQI step} & \text{if three distinct function values are available and acceptance criteria pass} \\
\text{Secant step} & \text{if only two distinct values or IQI is rejected, and acceptance criteria pass} \\
\frac{a_n + b_n}{2} & \text{(bisection fallback)}
\end{cases}$$

### 6.3 Convergence Analysis

**Order of convergence:** Superlinear in practice; the worst-case guarantee is the same as bisection ($O(\log(1/\varepsilon))$ iterations), but typical convergence is much faster.

**Theorem (Brent's Convergence Guarantee).** *Let $f$ be continuous on $[a, b]$ with $f(a)\,f(b) < 0$. Brent's method converges to a root $x^*$ in at most $O(\log_2((b-a)/\varepsilon))$ iterations (the bisection bound), but in practice achieves superlinear convergence on smooth functions.*

**Practical performance.** On smooth functions, Brent's method typically converges with order close to $\varphi \approx 1.618$ (matching the Secant method) or even approaching quadratic speed when IQI steps dominate. It is generally considered the "gold standard" for bracketed root-finding.

**Why it works.** The acceptance criteria enforce a "contraction" condition: each accepted interpolation step must reduce the bracket by at least a constant factor compared to the previous step. This prevents the pathological stagnation of Regula Falsi while allowing fast interpolation when the function cooperates.

### 6.4 Convergence Conditions

- **Required:** $f$ continuous on $[a, b]$, $f(a)\,f(b) < 0$.
- **Robust behavior:** Brent's method handles the same difficult cases as bisection (non-smooth functions, near-singular derivatives) without sacrificing speed on easy cases.
- **When conditions break:** If $f$ is discontinuous at the root, Brent's method converges to the discontinuity, same as bisection.

### 6.5 Limitations

- **Implementation complexity:** Significantly more complex to implement correctly than bisection or secant. The acceptance criteria involve multiple conditionals and bookkeeping.
- **Not the fastest:** On smooth functions with cheap derivatives, Newton-Raphson converges faster (quadratic vs. superlinear).
- **Black-box switching:** The dynamic strategy selection makes it harder to predict or explain the method's behavior on a given problem.
- **Overhead:** The bookkeeping per iteration is nontrivial, though the cost is dominated by function evaluations for expensive $f$.

### 6.6 Computational Complexity

| Metric                        | Cost          |
|-------------------------------|---------------|
| Function evaluations per step | 1             |
| Auxiliary storage             | $O(1)$        |
| Worst-case total evaluations  | $O\!\left(\log\frac{b-a}{\varepsilon}\right)$ (bisection fallback) |
| Typical total evaluations     | $O\!\left(\log\log\frac{1}{\varepsilon}\right)$ (superlinear regime) |

---

## 7. Newton-Raphson Method

### 7.1 Mathematical Derivation

Newton-Raphson is derived from a **first-order Taylor expansion** of $f$ about the current iterate $x_n$:

$$f(x) \approx f(x_n) + f'(x_n)(x - x_n)$$

Setting this linear approximation to zero and solving for $x$:

$$0 = f(x_n) + f'(x_n)(x_{n+1} - x_n)$$

$$x_{n+1} = x_n - \frac{f(x_n)}{f'(x_n)}$$

**Geometric interpretation:** $x_{n+1}$ is the $x$-intercept of the tangent line to $f$ at $(x_n, f(x_n))$.

**Alternative derivation via fixed-point iteration.** The root-finding problem $f(x) = 0$ is equivalent to the fixed-point problem $x = g(x)$ where $g(x) = x - \frac{f(x)}{f'(x)}$. Newton-Raphson is the fixed-point iteration $x_{n+1} = g(x_n)$, and its quadratic convergence follows from the fact that $g'(x^*) = 0$ when $f'(x^*) \neq 0$:

$$g'(x) = 1 - \frac{[f'(x)]^2 - f(x)\,f''(x)}{[f'(x)]^2} = \frac{f(x)\,f''(x)}{[f'(x)]^2}$$

At $x = x^*$: $g'(x^*) = \frac{f(x^*)\,f''(x^*)}{[f'(x^*)]^2} = 0$ since $f(x^*) = 0$.

### 7.2 Update Equation

$$x_{n+1} = x_n - \frac{f(x_n)}{f'(x_n)}$$

### 7.3 Convergence Analysis

**Order of convergence:** Quadratic ($p = 2$) for simple roots.

**Theorem (Newton's Method Convergence).** *Let $f \in C^2[a, b]$, $f(x^*) = 0$, and $f'(x^*) \neq 0$. Then there exists a neighborhood $B(x^*, \delta)$ such that for any $x_0 \in B(x^*, \delta)$, Newton's method converges quadratically:*

$$|e_{n+1}| \leq \frac{M}{2m}\,|e_n|^2$$

*where $M = \max_{x \in B}|f''(x)|$ and $m = \min_{x \in B}|f'(x)|$.*

**Proof.** By Taylor's theorem:

$$f(x^*) = f(x_n) + f'(x_n)(x^* - x_n) + \frac{1}{2}f''(\xi_n)(x^* - x_n)^2$$

for some $\xi_n$ between $x_n$ and $x^*$. Since $f(x^*) = 0$:

$$0 = f(x_n) + f'(x_n)(-e_n) + \frac{1}{2}f''(\xi_n)\,e_n^2$$

From the Newton update: $e_{n+1} = x_{n+1} - x^* = x_n - \frac{f(x_n)}{f'(x_n)} - x^* = -e_n - \frac{f(x_n)}{f'(x_n)}$.

Rearranging: $f(x_n) = -f'(x_n)(e_n + e_{n+1})$. Substituting into the Taylor expansion:

$$0 = -f'(x_n)(e_n + e_{n+1}) - f'(x_n)\,e_n + \frac{1}{2}f''(\xi_n)\,e_n^2$$

Wait — let us redo this cleanly. From the Newton step:

$$e_{n+1} = e_n - \frac{f(x_n)}{f'(x_n)}$$

From the Taylor expansion: $f(x_n) = -f'(x_n)\,e_n + \frac{1}{2}f''(\xi_n)\,e_n^2$ (using $f(x^*) = 0$ and $x_n = x^* + e_n$). Thus:

$$e_{n+1} = e_n + \frac{f'(x_n)\,e_n - \frac{1}{2}f''(\xi_n)\,e_n^2}{f'(x_n)} = e_n - e_n + \frac{f''(\xi_n)}{2\,f'(x_n)}\,e_n^2 = \frac{f''(\xi_n)}{2\,f'(x_n)}\,e_n^2$$

Therefore:

$$|e_{n+1}| = \frac{|f''(\xi_n)|}{2\,|f'(x_n)|}\,|e_n|^2 \leq \frac{M}{2m}\,|e_n|^2 \qquad \blacksquare$$

**Consequence:** Once $|e_n|$ is small, the number of correct digits roughly doubles at every iteration. Starting from 3 digits of accuracy, after 4 iterations one can expect $3 \to 6 \to 12 \to 24 \to 48$ digits—far beyond double precision.

### 7.4 Convergence Conditions

- **Required:**
  - $f$ is differentiable near $x^*$ (and $f'$ is continuous—i.e., $f \in C^1$ at minimum; $C^2$ for the quadratic convergence proof).
  - $f'(x^*) \neq 0$ (the root is simple).
  - $x_0$ is sufficiently close to $x^*$ (within the basin of attraction).
- **When violated:**
  - **$f'(x^*) = 0$ (multiple root):** Convergence degrades to linear. The modified Newton method $x_{n+1} = x_n - m\,\frac{f(x_n)}{f'(x_n)}$ restores quadratic convergence if the multiplicity $m$ is known.
  - **$f$ not differentiable:** The method cannot be applied (e.g., $f(x) = |x| - 2$).
  - **Poor initial guess:** The method may diverge, oscillate, or converge to a different root.

### 7.5 Limitations

- **Derivative requirement:** Computing $f'(x)$ analytically may be difficult or impossible. Numerical differentiation introduces errors and effectively reduces the method to a secant variant.
- **Basin of attraction:** For many functions, the basin of attraction for a given root can be fractal-shaped and difficult to predict. Starting outside it leads to unpredictable behavior.
- **Failure modes:**
  - *Divergence:* If $f'(x_n) \approx 0$ at some iterate (near a local extremum), the step $f(x_n)/f'(x_n)$ becomes enormous.
  - *Cycling:* The method can enter a periodic orbit (e.g., $f(x) = x^3 - 2x + 2$ starting at $x_0 = 0$ cycles between $0$ and $1$).
  - *Convergence to the wrong root:* With multiple roots, the method may find one far from the initial guess.
- **Non-differentiable functions:** Completely inapplicable to functions like $|x|$, $\lfloor x \rfloor$, or piecewise-defined functions with corners.
- **Expensive derivatives:** For functions arising from PDEs, simulations, or black-box code, derivatives may be unavailable or prohibitively expensive.

### 7.6 Computational Complexity

| Metric                        | Cost          |
|-------------------------------|---------------|
| Function evaluations per step | 1 ($f$) + 1 ($f'$) = **2** |
| Auxiliary storage             | $O(1)$        |
| Total evaluations to tolerance $\varepsilon$ | $O\!\left(\log\log\frac{1}{\varepsilon}\right)$ |

**Efficiency index.** The efficiency index of a method is defined as $p^{1/d}$ where $p$ is the convergence order and $d$ is the number of function evaluations per step. For Newton-Raphson: $2^{1/2} \approx 1.414$. For the Secant method: $\varphi^{1/1} \approx 1.618$. The Secant method is actually more efficient per function evaluation, a fact often overlooked.

---

## 8. Comparison Summary

### 8.1 Method Comparison Table

| Property                | Bisection | Secant | Regula Falsi | Illinois | Brent's | Newton-Raphson |
|-------------------------|-----------|--------|--------------|----------|---------|----------------|
| **Convergence order**   | 1 (linear) | $\varphi \approx 1.618$ | 1 (linear) | $\approx 1.442$ | Superlinear (adaptive) | 2 (quadratic) |
| **Guaranteed convergence** | ✅ Yes | ❌ No | ✅ Yes | ✅ Yes | ✅ Yes | ❌ No |
| **Requires bracket**    | ✅ Yes | ❌ No | ✅ Yes | ✅ Yes | ✅ Yes | ❌ No |
| **Requires derivative** | ❌ No | ❌ No | ❌ No | ❌ No | ❌ No | ✅ Yes |
| **$f$ evals / iteration** | 1 | 1 | 1 | 1 | 1 | 2 ($f$ + $f'$) |
| **Efficiency index**    | $1^{1/1} = 1$ | $\varphi^{1/1} \approx 1.618$ | $1^{1/1} = 1$ | $1.442^{1/1} \approx 1.442$ | $\sim 1.618$ | $2^{1/2} \approx 1.414$ |
| **Handles non-smooth $f$** | ✅ Yes | ⚠️ Risky | ✅ Yes | ✅ Yes | ✅ Yes | ❌ No |
| **Can stagnate**        | ❌ No | ❌ No | ✅ Yes | ❌ No | ❌ No | N/A |
| **Implementation complexity** | Trivial | Simple | Simple | Simple | Complex | Simple |

### 8.2 When to Use Each Method

| Scenario | Recommended Method | Rationale |
|----------|--------------------|-----------|
| Smooth function, derivative available, good initial guess | **Newton-Raphson** | Quadratic convergence makes it fastest |
| Smooth function, no derivative | **Secant** or **Brent's** | Secant for speed, Brent's for safety |
| Non-differentiable function with bracket | **Brent's** or **Illinois** | Bracket methods don't need derivatives |
| Guaranteed convergence is critical | **Bisection** or **Brent's** | Both maintain brackets; Brent's is faster |
| Simple implementation needed | **Bisection** | Trivial to code and verify |
| Production / library code | **Brent's** | Best balance of speed and reliability |
| Educational / pedagogical | **All of them** | Understanding trade-offs is the point |

---

## 9. Why Non-Continuous Functions Matter

### 9.1 The Continuity Assumption

Every convergence theorem in classical numerical analysis begins with some variant of "Let $f$ be continuous on $[a, b]$…". This is not a minor technical convenience—it is the foundation that makes root-finding well-defined. The Intermediate Value Theorem, which guarantees the existence of a root when $f(a)\,f(b) < 0$, **requires** continuity.

### 9.2 What Happens Without Continuity

When $f$ has a jump discontinuity at $x = c$ with $f(c^-) > 0$ and $f(c^+) < 0$, a sign change occurs but there may be **no** $x$ with $f(x) = 0$. All bracket-based methods will converge to $c$, the point of discontinuity, and report it as a root. This is a **silent failure**—the algorithm terminates successfully but returns a mathematically incorrect answer.

**Example.** Consider:

$$f(x) = \begin{cases} 1 & x < 0 \\ -1 & x \geq 0 \end{cases}$$

Bisection on $[-1, 1]$ converges to $x = 0$, but $f(0) = -1 \neq 0$. The "root" is an artifact of the discontinuity.

### 9.3 Singularities and Poles

Functions with vertical asymptotes (e.g., $f(x) = 1/x - 1$) present a different danger. Near the singularity, $f$ changes sign, but the "root" of the sign change is at the pole, not at a zero. Methods may:

- Converge to the pole (bisection, Regula Falsi).
- Evaluate $f$ at the singularity, producing `Inf` or `NaN` (Newton-Raphson, Secant).
- Detect the issue via acceptance criteria (Brent's method, which may reject interpolation steps that approach the singularity).

### 9.4 Practical Implications

Real-world functions—from engineering simulations, financial models, and control systems—are frequently piecewise-defined, discontinuous, or have removable singularities. A robust root-finding platform must:

1. **Detect** potential discontinuities (via sampling or symbolic analysis).
2. **Warn** the user when convergence to a discontinuity is likely.
3. **Verify** that $|f(x^*)| < \varepsilon$ at the returned "root," not just that $|x_n - x_{n-1}| < \varepsilon$.

---

## 10. Derivative Dependency Analysis

### 10.1 Which Methods Need Derivatives?

Of the six methods implemented in Icarus, **only Newton-Raphson** requires the derivative $f'(x)$.

| Method         | Uses $f(x)$ | Uses $f'(x)$ | Uses $f''(x)$ |
|----------------|-------------|---------------|----------------|
| Bisection      | ✅          | ❌            | ❌             |
| Secant         | ✅          | ❌            | ❌             |
| Regula Falsi   | ✅          | ❌            | ❌             |
| Illinois       | ✅          | ❌            | ❌             |
| Brent's        | ✅          | ❌            | ❌             |
| Newton-Raphson | ✅          | ✅            | ❌ (but convergence proof uses it) |

### 10.2 Why Derivatives Are Problematic

1. **Analytical availability.** For simple expressions ($x^3 - 2x - 5$, $\sin(x)$), derivatives are easy to compute symbolically. But for functions defined by algorithms (e.g., "run a simulation and return the output"), no closed-form derivative exists.

2. **Computational cost.** Even when a derivative can be computed, it may be expensive. Automatic differentiation (AD) can help, but adds implementation complexity and memory overhead.

3. **Numerical instability.** Finite-difference approximations $f'(x) \approx \frac{f(x+h) - f(x)}{h}$ suffer from cancellation errors when $h$ is small and truncation errors when $h$ is large. The optimal $h \sim \sqrt{\varepsilon_{\text{machine}}} \approx 10^{-8}$ limits derivative accuracy to about 8 digits.

4. **Non-differentiable functions.** Functions with corners ($|x|$), cusps ($x^{2/3}$), or kinks (piecewise-linear) have undefined or discontinuous derivatives at critical points—often exactly where the root lies.

### 10.3 The Derivative-Free Advantage

Derivative-free methods (Bisection, Secant, Regula Falsi, Illinois, Brent's) treat $f$ as a **black box**: they only require the ability to evaluate $f(x)$ at specified points. This makes them applicable to a strictly larger class of problems, including:

- Black-box simulations.
- Functions with non-smooth points.
- Situations where coding the derivative is error-prone.

The cost is slower convergence (at best superlinear vs. quadratic), but the gain in generality is often worth it.

---

## 11. Bracketing vs Open Methods

### 11.1 Classification

| Category    | Methods                                    | Key Property |
|-------------|-------------------------------------------|--------------|
| **Bracket** | Bisection, Regula Falsi, Illinois, Brent's | Maintain $[a_n, b_n]$ with $f(a_n)\,f(b_n) < 0$ at every step |
| **Open**    | Secant, Newton-Raphson                     | Use one or two current iterates; no bracket guarantee |

### 11.2 Bracketing Methods: Safety at a Cost

Bracketing methods guarantee convergence because they maintain an invariant: the root is always within the current bracket. This makes them:

- **Reliable:** Convergence is guaranteed for continuous $f$ with a sign change.
- **Predictable:** The bracket width gives a rigorous error bound at every iteration.
- **Slower:** The bracket constraint limits how far the iterate can move, preventing the aggressive steps that give open methods their speed.

The fundamental trade-off: **safety vs. speed**.

### 11.3 Open Methods: Speed at a Risk

Open methods (Secant, Newton-Raphson) are unconstrained: the next iterate can be anywhere on the real line. This freedom enables:

- **Fast convergence:** Quadratic (Newton) or superlinear (Secant) when conditions are right.
- **No bracket needed:** Useful when a sign change is unknown or the function is not easily bracketed.

But it also enables:

- **Divergence:** The iterates can fly off to $\pm\infty$.
- **Oscillation:** The iterates can cycle without converging.
- **Wrong root:** Convergence to an unintended root far from the initial guess.

### 11.4 Hybrid Approaches

Brent's method demonstrates that the dichotomy is not absolute. By combining a bracket framework with interpolation acceleration, it achieves:

- Guaranteed convergence (bracket invariant).
- Superlinear speed (interpolation when accepted).
- Graceful degradation (bisection fallback when interpolation fails).

This hybrid philosophy is the reason Brent's method is the default choice in most numerical libraries (e.g., `scipy.optimize.brentq`).

### 11.5 Decision Framework

```
Is a bracket [a, b] with f(a)·f(b) < 0 available?
├── Yes
│   ├── Is f smooth and well-behaved? → Brent's Method
│   ├── Is guaranteed convergence paramount? → Bisection
│   └── Is simplicity preferred? → Illinois
└── No
    ├── Is f differentiable with known f'? → Newton-Raphson
    └── Is f evaluable but derivative unknown? → Secant Method
```

---

## References

1. R. P. Brent, *Algorithms for Minimization Without Derivatives*, Prentice-Hall, 1973.
2. J. F. Traub, *Iterative Methods for the Solution of Equations*, Prentice-Hall, 1964.
3. W. H. Press et al., *Numerical Recipes: The Art of Scientific Computing*, 3rd ed., Cambridge University Press, 2007.
4. A. M. Ostrowski, *Solution of Equations and Systems of Equations*, 2nd ed., Academic Press, 1966.
5. G. E. Alefeld, F. A. Potra, and Y. Shi, "Algorithm 748: Enclosing Zeros of Continuous Functions," *ACM TOMS*, 21(3), 1995.
