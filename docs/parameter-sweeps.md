# CSTR Lab — Parameter Sweeps & Sensitivity Analysis

## 1. Scientific Overview

Parameter sweeps allow engineers to systematically explore the parametric design space of a Continuous Stirred-Tank Reactor (CSTR). By sweeping one independent variable across a range while holding other operating parameters at their baseline values, we map out operating curves, conversion asymptotes, and identify sensitive operating regimes.

---

## 2. Independent Variables & Monotonicity Properties

For an ideal isothermal CSTR operating with single reactant $A$ ($A \rightarrow \text{Products}$):

| Variable | Symbol | Canonical Unit | Typical Effect on Conversion ($X_A$) | Physical Reason |
|---|---|---|---|---|
| Rate Constant | $k$ | $\text{min}^{-1}$ (1st order) | Monotonically increases ($\frac{\partial X_A}{\partial k} > 0$) | Faster kinetics consume reactant more rapidly. |
| Reactor Volume | $V$ | $\text{L}$ | Monotonically increases ($\frac{\partial X_A}{\partial V} > 0$) | Larger volume increases mean residence time $\tau = V/Q$. |
| Volumetric Flow Rate | $Q$ | $\text{L/min}$ | Monotonically decreases ($\frac{\partial X_A}{\partial Q} < 0$) | Higher throughput reduces residence time in the tank. |
| Inlet Concentration | $C_{A,\text{in}}$ | $\text{mol/L}$ | Invariant for 1st order ($\frac{\partial X_A}{\partial C_{A,\text{in}}} = 0$) | First-order conversion depends only on Damköhler number $\text{Da} = k\tau$. |

---

## 3. Local Finite-Difference Sensitivity

To quantify local sensitivity at the design baseline point:

### 3.1 Local Tangent Derivative
$$\frac{\partial X_A}{\partial p} \approx \frac{X_A(p + \Delta p) - X_A(p - \Delta p)}{2 \Delta p}$$

### 3.2 Normalized Elasticity
To enable scale-independent comparisons across parameters with different physical units:
$$S_p = \frac{\partial X_A / X_A}{\partial p / p} = \frac{\partial X_A}{\partial p} \cdot \frac{p_{\text{baseline}}}{X_{A,\text{baseline}}}$$

> **Important Distinction:** Local finite-difference sensitivity measures the instantaneous gradient around a nominal operating point. It is strictly distinguished from global variance-based statistical methods (such as Sobol indices or Morris elementary effects).

---

## 4. 2D Surface & Contour Grids

In a 2D sweep:
- Independent variable $X$ is partitioned into $N_x$ points.
- Independent variable $Y$ is partitioned into $N_y$ points.
- For each grid point $(x_i, y_j)$, the steady-state equation is solved deterministically.
- Output matrices $X_A(x, y)$ and $C_{A,\text{ss}}(x, y)$ are visualised as interactive Plotly contour maps and heatmaps with a marker for the nominal baseline operating point.
