# CSTR Lab — Dynamic ODE Solver & Kinetics Documentation

## 1. Mathematical Formulation

The dynamic model solves the unsteady-state material balance for an ideal, constant-volume, isothermal CSTR:

$$\frac{dC_A}{dt} = \frac{Q}{V}\left(C_{A,\text{in}} - C_A\right) + r_A(C_A)$$

where:
- $V$: Reactor volume [L]
- $Q$: Volumetric flow rate [L/min]
- $\tau = V / Q$: Mean space time [min]
- $C_{A,\text{in}}$: Inlet feed concentration [mol/L]
- $C_A(t)$: Reactant concentration inside the vessel and effluent stream [mol/L]
- $r_A(C_A)$: Volumetric reaction rate [$\text{mol}/(\text{L}\cdot\text{min})$]

---

## 2. Kinetic Models & Physical Depletion Boundaries

### 2.1 Zero-Order Reaction ($n=0$)

$$r_A = \begin{cases} -k & \text{if } C_A > 0 \\ 0 & \text{if } C_A \le 0 \end{cases}$$

- **Canonical Rate Constant Unit:** $\text{mol}/(\text{L}\cdot\text{min})$
- **Physical Depletion Boundary:** In zero-order reactions, reaction rate is independent of concentration as long as reactant exists. To prevent unphysical negative concentrations, the depletion boundary smoothly/strictly shuts off reaction when $C_A \le 0$.
- **Analytical Steady State:**
  $$C_{A,\text{ss}} = \max\left(0, C_{A,\text{in}} - k\tau\right)$$

### 2.2 First-Order Reaction ($n=1$)

$$r_A = -k C_A$$

- **Canonical Rate Constant Unit:** $\text{min}^{-1}$
- **Analytical Steady State:**
  $$C_{A,\text{ss}} = \frac{C_{A,\text{in}}}{1 + k\tau}$$
- **Exact Analytical Dynamic Solution:**
  $$C_A(t) = C_{A,\text{ss}} + \left(C_A(0) - C_{A,\text{ss}}\right) \exp\left(-\left(\frac{1}{\tau} + k\right)t\right)$$

### 2.3 Second-Order Reaction ($n=2$)

$$r_A = -k C_A^2$$

- **Canonical Rate Constant Unit:** $\text{L}/(\text{mol}\cdot\text{min})$
- **Analytical Steady State:**
  Setting $\frac{dC_A}{dt} = 0 \implies k\tau C_{A,\text{ss}}^2 + C_{A,\text{ss}} - C_{A,\text{in}} = 0$.
  The unique physically admissible positive root is:
  $$C_{A,\text{ss}} = \begin{cases} \frac{-1 + \sqrt{1 + 4 k \tau C_{A,\text{in}}}}{2 k \tau} & \text{if } k > 0 \\ C_{A,\text{in}} & \text{if } k = 0 \end{cases}$$

---

## 3. Solver Implementation & Numerical Architecture

### 3.1 ODE Integrator (`scipy.integrate.solve_ivp`)
- **Default Method:** `RK45` (Runge-Kutta of order 5(4) with adaptive step sizing).
- **Stiff Alternatives:** `Radau` and `BDF` for high Damköhler numbers or rapid transients.
- **Tolerances:** Default `rtol = 1e-6`, `atol = 1e-9` ensuring high precision without unnecessary overhead.
- **Non-Negativity Enforcement:** Solvers can produce microscopic negative oscillations near machine precision; trajectories are safeguarded against unphysical values ($C_A \ge 0$).

### 3.2 Piecewise Step-Change Integration
When an operational disturbance occurs (e.g. step in $C_{A,\text{in}}$ or $Q$ at $t = t_{\text{step}}$):
1. **Segment 1 ($0 \le t \le t_{\text{step}}$):** Integrates under initial conditions until $t_{\text{step}}$.
2. **State Transfer:** The terminal state $C_A(t_{\text{step}})$ serves as initial condition for Segment 2.
3. **Segment 2 ($t_{\text{step}} \le t \le t_{\text{final}}$):** Integrates under the new operating parameters ($C_{A,\text{in,new}}, Q_{\text{new}}$).
4. **Trajectory Stitching:** Time grids and state trajectories are concatenated seamlessly without duplicating the transition point.
