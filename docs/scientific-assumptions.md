# CSTR Lab — Scientific Assumptions & Governing Equations

## 1. Scope & Physical Assumptions

This document defines the scientific principles, mathematical formulations, kinetic rate models, and unit systems underpinning the CSTR Lab simulation and ML engine.

### Core Assumptions (Isothermal Mechanistic Core, Phases 0–12)
1. **Ideal Continuous Stirred-Tank Reactor (CSTR):** Fluid contents are perfectly mixed at all times (macromixing and micromixing are ideal). Spatial concentration gradients within the active volume are zero.
2. **Equivalence of Tank and Effluent State:** Perfect mixing implies that effluent leaving the vessel has the identical concentration and temperature as the internal bulk fluid:
   $$C_{A,\text{out}}(t) = C_A(t)$$
3. **Constant Density and Active Volume:** The liquid reacting phase is incompressible with constant density $\rho$. Active reactor liquid volume $V$ is held strictly constant by liquid-level control, such that inlet volumetric flow rate equals outlet volumetric flow rate:
   $$Q_{\text{in}}(t) = Q_{\text{out}}(t) = Q(t)$$
4. **Isothermal Operation:** Heat generated or absorbed by reaction is instantaneously balanced by jacket/bath heat exchange ($T(t) = T = \text{const}$). Temperature dynamics are deferred to Phase 13 (Arrhenius & Non-Isothermal CSTR).
5. **Elementary Irreversible Reaction:** Reaction stoichiometry $A \rightarrow \text{Products}$, where reactant consumption rate is $r_A \le 0$.

---

## 2. Kinetic Rate Laws & Canonical Units

To eliminate unit ambiguity across Python, TypeScript, and database serialization, all internal computation is executed in **canonical units**.

| Physical Quantity | Symbol | Canonical Unit | Supported Alternate Units |
|---|---|---|---|
| Reactor Volume | $V$ | $\text{L}$ (Liters) | $\text{m}^3$, $\text{mL}$ |
| Volumetric Flow Rate | $Q$ | $\text{L/min}$ | $\text{L/s}$, $\text{L/h}$, $\text{m}^3/\text{h}$, $\text{m}^3/\text{s}$ |
| Residence Time | $\tau = V/Q$ | $\text{min}$ (Minutes) | $\text{s}$, $\text{h}$ |
| Concentration | $C_A, C_{A,\text{in}}, C_{A,\text{ss}}$ | $\text{mol/L}$ | $\text{kmol/m}^3$, $\text{mol/m}^3$, $\text{mmol/L}$ |
| Zero-Order Rate Constant | $k_0$ | $\text{mol/(L}\cdot\text{min)}$ | $\text{mol/(L}\cdot\text{s)}$, $\text{mol/(m}^3\cdot\text{s)}$ |
| First-Order Rate Constant | $k_1$ | $\text{min}^{-1}$ | $\text{s}^{-1}$, $\text{h}^{-1}$ |
| Second-Order Rate Constant | $k_2$ | $\text{L/(mol}\cdot\text{min)}$ | $\text{m}^3/\text{(mol}\cdot\text{s)}$, $\text{L/(mol}\cdot\text{s)}$ |
| Reaction Rate | $r_A$ | $\text{mol/(L}\cdot\text{min)}$ | — |
| Fractional Conversion | $X_A$ | dimensionless fraction $[0, 1]$ | $\%$ |

### Kinetic Rate Expressions ($r_A$)
- **Zero-Order ($n=0$):**
  $$r_A(C_A) = -k_0 \quad \text{for } C_A > 0$$
  *Depletion Boundary & Regularization:* Because chemical reactions cannot proceed in the absence of reactant, $r_A = 0$ when $C_A \le 0$. To prevent sliding-mode chattering in adaptive ODE solvers (e.g. RK45) when $k_0 \tau > C_{A,\text{in}}$, a continuous linear regularization is applied within $[0, \epsilon_{\text{depletion}}]$ with $\epsilon_{\text{depletion}} = 10^{-3}\text{ mol/L}$:
  $$r_A(C_A) = -k_0 \cdot \min\left(1.0, \frac{\max(0, C_A)}{\epsilon_{\text{depletion}}}\right)$$
- **First-Order ($n=1$):**
  $$r_A(C_A) = -k_1 C_A$$
- **Second-Order ($n=2$):**
  $$r_A(C_A) = -k_2 C_A^2$$

---

## 3. Dynamic Mole Balance Differential Equation

For species $A$, the transient mole balance is:
$$\frac{d(V C_A)}{dt} = Q C_{A,\text{in}} - Q C_A + r_A(C_A) V$$

Dividing by constant volume $V$:
$$\frac{dC_A}{dt} = \frac{Q}{V}(C_{A,\text{in}} - C_A) + r_A(C_A) = \frac{1}{\tau}(C_{A,\text{in}} - C_A) + r_A(C_A)$$

### Numerical Integration
- **Default Solver:** SciPy `solve_ivp` with Runge-Kutta 4(5) (`RK45`), relative tolerance $\text{rtol} = 10^{-6}$, absolute tolerance $\text{atol} = 10^{-9}$.
- **Piecewise Step Changes:** When step disturbances in $C_{A,\text{in}}$ or $Q$ occur at time $t_{\text{step}}$, integration is executed piecewise over $[0, t_{\text{step}}]$ and $[t_{\text{step}}, t_{\text{final}}]$ with continuous state transfer $C_A(t_{\text{step}}^+)=C_A(t_{\text{step}}^-)$, preserving the caller's evaluation grid.

---

## 4. Steady-State Analytical Solutions & Oracles

At steady state, $\frac{dC_A}{dt} = 0$:

### 4.1 Zero-Order ($n=0$)
$$0 = \frac{1}{\tau}(C_{A,\text{in}} - C_{A,\text{ss}}) - k_0 \implies C_{A,\text{ss}} = \max(0.0, C_{A,\text{in}} - k_0 \tau)$$
$$X_A = \min\left(1.0, \frac{k_0 \tau}{C_{A,\text{in}}}\right) \quad (C_{A,\text{in}} > 0)$$

### 4.2 First-Order ($n=1$)
$$0 = \frac{1}{\tau}(C_{A,\text{in}} - C_{A,\text{ss}}) - k_1 C_{A,\text{ss}} \implies C_{A,\text{ss}} = \frac{C_{A,\text{in}}}{1 + k_1 \tau} = \frac{C_{A,\text{in}}}{1 + \text{Da}_1}$$
$$X_A = \frac{k_1 \tau}{1 + k_1 \tau} = \frac{\text{Da}_1}{1 + \text{Da}_1} \quad (C_{A,\text{in}} > 0)$$
where $\text{Da}_1 = k_1 \tau$ is the first-order Damköhler number.

### 4.3 Second-Order ($n=2$)
$$0 = \frac{1}{\tau}(C_{A,\text{in}} - C_{A,\text{ss}}) - k_2 C_{A,\text{ss}}^2 \implies k_2 \tau C_{A,\text{ss}}^2 + C_{A,\text{ss}} - C_{A,\text{in}} = 0$$
Using the physically positive quadratic root:
$$C_{A,\text{ss}} = \frac{-1 + \sqrt{1 + 4 k_2 \tau C_{A,\text{in}}}}{2 k_2 \tau}$$
$$X_A = \frac{C_{A,\text{in}} - C_{A,\text{ss}}}{C_{A,\text{in}}} = \frac{2 k_2 \tau C_{A,\text{in}} + 1 - \sqrt{1 + 4 k_2 \tau C_{A,\text{in}}}}{2 k_2 \tau C_{A,\text{in}}}$$

### 4.4 Canonical Verification Oracle
The gold-standard verification case mandated across all tests and documentation:
- $V = 10.0\text{ L}$
- $Q = 1.0\text{ L/min} \implies \tau = 10.0\text{ min}$
- $k_1 = 0.15\text{ min}^{-1} \implies \text{Da}_1 = 1.50$
- $C_{A,\text{in}} = 1.0\text{ mol/L} \implies C_{A,\text{ss}} = \frac{1.0}{1 + 1.5} = 0.40\text{ mol/L}$, $X_A = 0.60$ ($60\%$)
- If $C_{A,\text{in}} = 2.0\text{ mol/L} \implies C_{A,\text{ss}} = \frac{2.0}{2.5} = 0.80\text{ mol/L}$, $X_A = 0.60$ ($60\%$)
- Dynamic Analytical Trajectory for $n=1$:
  $$C_A(t) = C_{A,\text{ss}} + (C_{A,0} - C_{A,\text{ss}}) e^{-\left(\frac{1}{\tau} + k_1\right) t}$$
  For the oracle with $C_{A,0} = 0.5\text{ mol/L}, C_{A,\text{in}} = 2.0\text{ mol/L}$:
  $$C_A(t) = 0.80 - 0.30 e^{-0.25 t}$$
