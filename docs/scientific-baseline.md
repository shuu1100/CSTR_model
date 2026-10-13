# CSTR Lab — Scientific Baseline & Core Equations

## 1. Physical Assumptions

The scientific core models an ideal Continuous Stirred-Tank Reactor (CSTR) under the following foundational assumptions:

1. **Perfect Mixing:** The fluid inside the reactor is instantaneously and completely mixed; concentration is spatially uniform throughout the vessel volume $V$.
2. **Equivalence of Tank and Effluent State:** Because the tank is perfectly mixed, the effluent concentration equals the internal tank concentration: $C_{A,\text{out}}(t) = C_A(t)$.
3. **Constant Volume ($V$) and Density ($\rho$):** The liquid reaction medium has constant density, and liquid level is strictly controlled such that inlet volumetric flow rate equals outlet volumetric flow rate: $Q_{\text{in}} = Q_{\text{out}} = Q$.
4. **Isothermal Operation:** Temperature variations and heat of reaction effects are neglected in this baseline phase ($T = \text{const}$).
5. **Elementary Irreversible First-Order Kinetics:** A single reactant $A$ decomposes or reacts via an irreversible first-order mechanism ($A \rightarrow \text{Products}$) with rate equation:
   $$r_A = -k C_A$$

---

## 2. Canonical Units & Dimensional Consistency

To prevent silent unit conversion errors across the stack, the scientific engine uses the following internal canonical unit system:

| Quantity | Symbol | Canonical Unit | Alternate Supported Units |
|---|---|---|---|
| Reactor Volume | $V$ | $\text{L}$ (Liters) | $\text{m}^3$, $\text{mL}$ |
| Volumetric Flow Rate | $Q$ | $\text{L/min}$ | $\text{L/s}$, $\text{L/h}$, $\text{m}^3/\text{h}$, $\text{m}^3/\text{s}$ |
| Space Time / Residence Time | $\tau$ | $\text{min}$ (Minutes) | $\text{s}$, $\text{h}$ |
| Reactant Concentration | $C_A, C_{A,\text{in}}, C_{A,\text{ss}}$ | $\text{mol/L}$ | $\text{kmol/m}^3$, $\text{mol/m}^3$, $\text{mmol/L}$ |
| First-Order Rate Constant | $k$ | $\text{min}^{-1}$ | $\text{s}^{-1}$, $\text{h}^{-1}$ |
| Volumetric Reaction Rate | $r_A$ | $\text{mol}/(\text{L}\cdot\text{min})$ | — |
| Conversion | $X_A$ | dimensionless fraction $[0, 1]$ | $\%$ |

---

## 3. Mathematical Derivations

### 3.1 Unsteady-State Reactant Mole Balance

$$\frac{d N_A}{dt} = F_{A,\text{in}} - F_{A,\text{out}} + r_A V$$

Dividing by constant volume $V$ with $F_A = Q \cdot C_A$:

$$\frac{dC_A}{dt} = \frac{Q}{V}\left(C_{A,\text{in}} - C_A\right) + r_A = \frac{1}{\tau}\left(C_{A,\text{in}} - C_A\right) - k C_A$$

### 3.2 Steady-State Analytical Solution

At steady state, $\frac{dC_A}{dt} = 0$:

$$0 = \frac{Q}{V}(C_{A,\text{in}} - C_{A,\text{ss}}) - k C_{A,\text{ss}}$$

$$C_{A,\text{ss}}\left(\frac{Q}{V} + k\right) = \frac{Q}{V} C_{A,\text{in}}$$

$$C_{A,\text{ss}} = \frac{C_{A,\text{in}}}{1 + k\tau}$$

where the Damköhler number for a first-order reaction is defined as $\text{Da} = k\tau$. Thus:

$$C_{A,\text{ss}} = \frac{C_{A,\text{in}}}{1 + \text{Da}}$$

### 3.3 Fractional Conversion ($X_A$)

When reactant enters ($C_{A,\text{in}} > 0$):

$$X_A = \frac{C_{A,\text{in}} - C_{A,\text{ss}}}{C_{A,\text{in}}} = 1 - \frac{1}{1 + k\tau} = \frac{k\tau}{1 + k\tau} = \frac{\text{Da}}{1 + \text{Da}}$$

When $C_{A,\text{in}} = 0$, conversion is mathematically undefined and returns `None`.

### 3.4 Material-Balance Residual Diagnostic

An independent balance residual diagnostic evaluates the transient rate of change at the computed steady state:

$$\text{Residual} = \frac{Q}{V}(C_{A,\text{in}} - C_{A,\text{ss}}) + r_A(C_{A,\text{ss}})$$

For an exact steady state, $|\text{Residual}| \le 10^{-14}\text{ mol/(L}\cdot\text{min)}$.

---

## 4. Canonical Validation Oracle

The canonical benchmark case from project specifications:

- Reactor Volume: $V = 10.0\text{ L}$
- Volumetric Flow Rate: $Q = 1.0\text{ L/min}$
- First-Order Rate Constant: $k = 0.15\text{ min}^{-1}$
- Inlet Concentration: $C_{A,\text{in}} = 2.0\text{ mol/L}$

**Expected Analytic Values:**
- Residence time: $\tau = \frac{10}{1} = 10.0\text{ min}$
- Damköhler number: $\text{Da} = 0.15 \times 10 = 1.5$
- Concentration ratio: $\frac{C_{A,\text{ss}}}{C_{A,\text{in}}} = \frac{1}{1 + 1.5} = \frac{1}{2.5} = 0.40$ ($40\%$)
- Steady-state concentration: $C_{A,\text{ss}} = 0.40 \times 2.0 = 0.80\text{ mol/L}$
- Conversion: $X_A = \frac{1.5}{2.5} = 0.60$ ($60\%$)
- Reaction rate: $r_A = -0.15 \times 0.80 = -0.12\text{ mol/(L}\cdot\text{min)}$
- Residual: $0.0\text{ mol/(L}\cdot\text{min)}$ (within machine precision $< 10^{-14}$)
