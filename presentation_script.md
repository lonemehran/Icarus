# Icarus — Presentation Script & Demo Guide

A structured guide for presenting the Icarus platform. Total estimated time: **20 minutes** (adjustable).

---

## 1. Opening (2 minutes)

### Slide / Talking Points

> **"Every engineer learns Newton-Raphson in their first numerical methods course. It's fast, elegant, and it works — until it doesn't."**

- Root-finding is one of the most fundamental problems in computational mathematics.
  - Solving $f(x) = 0$ underlies optimization, control systems, signal processing, financial modeling, structural analysis, and more.
  - Newton-Raphson is the textbook default — quadratic convergence sounds unbeatable.

- **The thesis of this presentation:**
  - Newton-Raphson carries hidden assumptions (differentiability, good initial guess, simple root) that frequently break in practice.
  - There is no universally best root-finding method — the right choice depends on what you know about $f$.
  - Icarus makes this trade-off visible by running six methods side-by-side on the same problem.

### Transition

> *"Let me show you what I mean. Let's start with a function where Newton wins easily — and then break it."*

---

## 2. Background (3 minutes)

### Method Overview (brief — don't over-explain here; the demos will teach)

Present the six methods in two groups:

**Bracket methods** (maintain an interval $[a, b]$ containing the root):
| Method | Key idea | Speed |
|--------|----------|-------|
| Bisection | Halve the interval every step | Slow but guaranteed |
| Regula Falsi | Interpolate, keep the bracket | Can stagnate |
| Illinois | Fix Regula Falsi's stagnation | Superlinear |
| Brent's | Hybrid: bisection + interpolation + IQI | Best of both worlds |

**Open methods** (no bracket; iterate from a starting guess):
| Method | Key idea | Speed |
|--------|----------|-------|
| Newton-Raphson | Tangent line intercept | Quadratic (fastest) |
| Secant | Secant line intercept (no derivative) | Superlinear |

### Key Distinction

> *"Bracket methods trade speed for safety. Open methods trade safety for speed. Brent's method is the only one that genuinely gets both."*

### Transition

> *"Let's see this in action. I'll run five demo scenarios, each designed to expose a different method's weakness."*

---

## 3. Demo Flow (10 minutes)

### Pre-Demo Checklist

Before starting:
- [ ] Application running at `http://localhost:5000`
- [ ] Browser window visible (preferably on a large screen or projector)
- [ ] Terminal visible showing server logs (optional but useful for credibility)
- [ ] Demo functions panel visible in the sidebar

---

### Demo 1: Simple Polynomial — $x^3 - 2x - 5$ (2 min)

**Setup:**
- Function: `x**3 - 2*x - 5`
- Bracket: $[1, 3]$
- Initial guess: $x_0 = 2.5$
- Tolerance: $10^{-10}$

**What to do:**
1. Click the "Classic Polynomial" demo or type the function manually.
2. Run the comparison.
3. Point at the results table.

**What to say:**

> *"This is the happy path. The function is smooth, differentiable everywhere, with a single real root near 2.09. Look at the iteration counts:"*

| Method | Expected iterations |
|--------|-------------------|
| Bisection | ~34 |
| Secant | ~8 |
| Regula Falsi | ~12 |
| Illinois | ~9 |
| Brent's | ~8 |
| Newton-Raphson | ~5 |

> *"Newton-Raphson converges in about 5 iterations — that's quadratic convergence in action. Each iteration roughly doubles the number of correct digits. The Secant method is close behind with about 8 iterations, and it didn't need a derivative."*

> *"Bisection took 34 iterations — that's the price of guaranteed convergence. One bit of accuracy per step, no matter what."*

> *"So if this were the only type of problem we'd ever face, we'd just use Newton and go home. But real problems aren't always this nice."*

**Transition:**
> *"What happens when the function isn't differentiable?"*

---

### Demo 2: Non-Differentiable Function — $|x| - 2$ (2 min)

**Setup:**
- Function: `abs(x) - 2`
- Bracket: $[-5, 5]$ (or $[0, 5]$ for the positive root)
- Initial guess: $x_0 = 1$
- Tolerance: $10^{-10}$

**What to do:**
1. Load the demo or enter `abs(x) - 2`.
2. Run comparison.
3. Highlight Newton-Raphson's result.

**What to say:**

> *"This function has a corner at $x = 0$ — the absolute value function is not differentiable there. The roots are $x = 2$ and $x = -2$, which are away from the corner, so you might think Newton is fine."*

> *"And it might be — if the initial guess is on the right side. But watch what happens with certain starting points. The derivative of $|x|$ is $\text{sgn}(x)$, which is discontinuous at zero. If Newton's iterates cross zero, the method can misbehave."*

> *"Meanwhile, look at the bracket methods: Bisection, Illinois, and Brent's all converge without any trouble. They don't care about derivatives — they only need function values."*

**Key point to emphasize:**

> *"This is a mild example — the non-differentiable point isn't at the root. But it illustrates the principle: Newton-Raphson requires differentiability along the entire path of iteration, not just at the root."*

**Transition:**
> *"Now let's try something truly dangerous — a function with a singularity."*

---

### Demo 3: Discontinuous / Singular Function — $1/x - 1$ (2 min)

**Setup:**
- Function: `1/x - 1`
- Bracket: $[0.1, 5]$ (root at $x = 1$, singularity at $x = 0$)
- Initial guess: $x_0 = 0.5$
- Tolerance: $10^{-10}$

**What to do:**
1. Load the demo.
2. Run comparison.
3. Show the convergence traces — especially any method that approaches $x = 0$.

**What to say:**

> *"The function $1/x - 1$ has a vertical asymptote at $x = 0$ and a root at $x = 1$. With a bracket of $[0.1, 5]$, the bracket methods are safe because the root is inside and the singularity is outside."*

> *"But Newton-Raphson with $x_0 = 0.5$... let's see. The derivative is $f'(x) = -1/x^2$. The Newton step from $x_0 = 0.5$ is:"*

$$x_1 = 0.5 - \frac{1/0.5 - 1}{-1/0.25} = 0.5 - \frac{1}{-4} = 0.5 + 0.25 = 0.75$$

> *"That's fine — it moved toward the root. But if we start at $x_0 = 0.1$, the step is much larger and could overshoot. The danger zone is near $x = 0$, where $f$ blows up."*

> *"Brent's method handles this best: its acceptance criteria reject interpolation steps that approach the singularity, falling back to bisection for safety."*

**Key point:**

> *"Singularities create sign changes that look like roots but aren't. A robust method must distinguish between a genuine zero crossing and a pole."*

**Transition:**
> *"Let's see what happens with multiple roots and asymptotes."*

---

### Demo 4: Oscillatory Function — $\tan(x) - 1$ (2 min)

**Setup:**
- Function: `tan(x) - 1`
- Bracket: $[0, 1.4]$ (root at $x = \pi/4 \approx 0.785$; asymptote at $x = \pi/2 \approx 1.571$)
- Initial guess: $x_0 = 1.2$ (dangerously close to the asymptote)
- Tolerance: $10^{-10}$

**What to do:**
1. Load the demo.
2. First run with the safe bracket $[0, 1.4]$ — all methods work.
3. Then change the initial guess for Newton to $x_0 = 1.5$ (very close to the asymptote) and rerun.

**What to say:**

> *"$\tan(x) - 1 = 0$ has roots at $x = \pi/4 + n\pi$ for all integers $n$. The function has vertical asymptotes at $x = \pi/2 + n\pi$. The root at $\pi/4$ is sandwiched between $x = 0$ and the asymptote at $\pi/2$."*

> *"With the bracket $[0, 1.4]$, all bracket methods converge to $\pi/4$ without incident. But watch Newton-Raphson with $x_0 = 1.5$."*

> *"At $x = 1.5$, $\tan(1.5) \approx 14.1$, and $f'(1.5) = \sec^2(1.5) \approx 200$. The Newton step is:"*

$$x_1 = 1.5 - \frac{14.1 - 1}{200} \approx 1.5 - 0.066 = 1.434$$

> *"That's actually okay — it moved away from the asymptote. But the point is: the derivative is enormous near asymptotes, making Newton-Raphson's behavior highly sensitive to the starting point. A slightly different $x_0$ could send the iterate past the asymptote into a completely different branch."*

**Key point:**

> *"Oscillatory functions and functions with multiple branches are treacherous for open methods. The basin of attraction for each root can be fractal-shaped."*

**Transition:**
> *"One more scenario — what about a function that's technically smooth but numerically challenging?"*

---

### Demo 5: Steep Derivative / Flat Region — $x^{10} - 1$ (2 min)

**Setup:**
- Function: `x**10 - 1`
- Bracket: $[0, 2]$ (root at $x = 1$)
- Initial guess: $x_0 = 0.5$
- Tolerance: $10^{-10}$

**What to do:**
1. Load the demo.
2. Run comparison.
3. Point out the iteration counts — especially Newton-Raphson.

**What to say:**

> *"$x^{10} - 1$ has a root at $x = 1$. It's smooth, differentiable, no singularities — sounds like Newton territory. But look at the convergence."*

> *"The problem is the function's shape: for $x < 1$, $x^{10}$ is extremely flat near zero ($0.5^{10} = 0.000977$, very close to zero), so the function value gives almost no information about where the root is. Newton's derivative $f'(x) = 10x^9$ is also tiny there, creating large, erratic steps."*

> *"From $x_0 = 0.5$:"*

$$x_1 = 0.5 - \frac{0.5^{10} - 1}{10 \cdot 0.5^9} = 0.5 - \frac{-0.999}{0.0195} \approx 0.5 + 51.2 = 51.7$$

> *"Newton just jumped to $x = 51.7$! It will eventually converge (the function grows fast for large $x$, pulling it back), but it may take many iterations of wild oscillation before settling down."*

> *"Meanwhile, Bisection and Brent's stay within the bracket and converge steadily. Bisection takes 34 iterations; Brent's takes about 10."*

**Key point:**

> *"High-degree polynomials with roots near flat regions are deceptively difficult. The derivative is either too small (flat region) or too large (steep region), both of which cause Newton to take inappropriate steps."*

---

## 4. Analysis Discussion (3 minutes)

### Walk Through the Reasoning Engine

After the demos, switch focus to the analysis panel.

**What to say:**

> *"Icarus doesn't just run the methods — it analyzes the function and explains why each method behaved the way it did. Let me walk you through the reasoning engine output."*

**Points to cover:**

1. **Function classification:**
   > *"The engine classifies the function as polynomial, rational, transcendental, piecewise, or composition. This determines which methods are theoretically applicable."*

2. **Property detection:**
   > *"It checks continuity, differentiability, and bracket validity. For $|x| - 2$, it detects the non-differentiable point at $x = 0$. For $1/x - 1$, it detects the singularity."*

3. **Method suitability scores:**
   > *"Each method gets a suitability score based on the function properties. Newton-Raphson scores high on smooth functions but low on non-differentiable ones. Brent's method scores consistently high."*

4. **Convergence diagnostics:**
   > *"The engine estimates the observed convergence order by computing $\log|e_{n+1}| / \log|e_n|$ over the last few iterations. You can verify that Newton achieves order 2 on smooth functions and degrades on difficult ones."*

### Pattern Detection

> *"Across all five demos, a pattern emerges: Brent's method is never the fastest, but it's never the slowest either. It's the method you use when you don't know what you're dealing with — which, in practice, is most of the time."*

---

## 5. Conclusion (2 minutes)

### Summary Table

Present (or point to the comparison table in the app):

| Scenario | Best Method | Why |
|----------|-------------|-----|
| Smooth + derivative available | Newton-Raphson | Quadratic convergence |
| Smooth + no derivative | Secant or Brent's | Speed without derivatives |
| Non-differentiable | Brent's or Illinois | Bracket-based, no derivative needed |
| Singularity present | Brent's | Robust acceptance criteria |
| Unknown function properties | Brent's | Safest default |
| Simplicity / verification needed | Bisection | Trivial to implement and prove correct |

### Closing Statement

> *"The lesson isn't that Newton-Raphson is bad — it's that choosing a root-finding method is an engineering decision, not a mathematical one. You have to weigh convergence speed against robustness, implementation complexity, and what you know about the function."*

> *"Icarus makes that decision process transparent. Instead of guessing, you can run all six methods and see, empirically, which one is best for your problem."*

### Future Work (brief)

> *"Looking ahead, we're exploring machine learning for automatic method selection, multi-root detection, and export to LaTeX reports for academic use."*

---

## 6. Q&A Preparation

### Anticipated Questions and Suggested Answers

---

**Q: Why not just use `scipy.optimize.brentq`?**

> *"You absolutely should, in production. SciPy's implementation of Brent's method is battle-tested and efficient. Icarus's purpose is educational: it lets you see what's happening inside these algorithms, compare them side-by-side, and understand when and why each one succeeds or fails. You can't learn that from a single library call that returns a number."*

---

**Q: How does Brent's method decide which strategy to use (bisection, secant, or IQI)?**

> *"Brent's method proposes an interpolation step (secant or IQI) and then runs it through a set of acceptance criteria. The key criterion is that the proposed step must be smaller than half the previous step — this ensures superlinear convergence. If the interpolation step is rejected (too large, outside the bracket, or not converging fast enough), the method falls back to bisection. It's a pessimistic strategy: assume the worst (bisection is needed) unless the evidence says otherwise."*

---

**Q: Can this handle complex roots?**

> *"Not currently. All six methods are designed for real-valued functions on real intervals. Finding complex roots requires different techniques — Müller's method (a complex-valued variant of IQI), the Durand-Kerner algorithm (finds all roots simultaneously), or Newton's method in the complex plane (which produces beautiful fractal basins of attraction). Complex root-finding is on our roadmap."*

---

**Q: What about multi-dimensional problems ($\mathbf{F}(\mathbf{x}) = \mathbf{0}$ where $\mathbf{x} \in \mathbb{R}^n$)?**

> *"Multi-dimensional root-finding is a fundamentally harder problem. The 'bracket' concept doesn't generalize well to higher dimensions. Newton's method generalizes (it becomes the Newton-Raphson method with the Jacobian matrix), but it requires computing and inverting an $n \times n$ Jacobian at every step. Broyden's method is the multi-dimensional analog of the Secant method. This is a rich area, but beyond the scope of a 1D comparison platform."*

---

**Q: How accurate are the convergence order estimates?**

> *"The observed convergence order is estimated from the iteration trace using the formula $p \approx \log|e_{n+1}| / \log|e_n|$. This is asymptotically correct but noisy for the first few iterations. We average over the last 3–5 iterations when convergence is well-established. The estimates should match the theoretical values (2 for Newton, ~1.618 for Secant, 1 for Bisection) to within about 10% on well-behaved problems."*

---

**Q: What if I don't know a bracket?**

> *"Finding a bracket is itself a non-trivial problem. A simple heuristic is to sample $f$ on a coarse grid and look for sign changes. For open methods (Secant, Newton), you don't need a bracket — but you need a good initial guess, which is often equally hard to find. In practice, domain knowledge about the problem usually provides a reasonable starting interval."*

---

**Q: How does this compare to Halley's method or higher-order methods?**

> *"Halley's method uses the second derivative and achieves cubic convergence (order 3). Higher-order Householder methods achieve order $d+1$ using the first $d$ derivatives. The trade-off is that each iteration is more expensive (computing higher derivatives) and the basin of attraction typically shrinks. For most practical problems, Newton-Raphson or Brent's method hits machine precision in so few iterations that the extra complexity of higher-order methods isn't justified."*

---

## Appendix: Timing Guide

| Section | Duration | Cumulative |
|---------|----------|------------|
| Opening | 2 min | 2 min |
| Background | 3 min | 5 min |
| Demo 1: Polynomial | 2 min | 7 min |
| Demo 2: Non-differentiable | 2 min | 9 min |
| Demo 3: Singularity | 2 min | 11 min |
| Demo 4: Oscillatory | 2 min | 13 min |
| Demo 5: Steep/flat | 2 min | 15 min |
| Analysis discussion | 3 min | 18 min |
| Conclusion | 2 min | 20 min |
| Q&A | flexible | — |

### Tips

- **Pace:** Don't rush the demos. Let the audience read the results for a few seconds before explaining.
- **Interaction:** After Demo 2, ask the audience: *"Who expected Newton to struggle here?"* — it grounds the theoretical discussion in intuition.
- **Fallback:** If the app has an issue during the live demo, switch to the pre-computed results in `math_explanation.md` and walk through the theory instead.
- **Audience level:** For a more mathematical audience, spend more time on the convergence proofs. For an engineering audience, focus on the failure modes and practical recommendations.
