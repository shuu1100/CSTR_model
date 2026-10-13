# Phase 13 Technical Report — Arrhenius Kinetics and Non-Isothermal Thermal CSTR

## 1. Executive Summary & Physics Overview

Phase 13 establishes the non-isothermal modeling and Arrhenius kinetic foundation for CSTR Lab, adhering strictly to `GLOBAL-INSTRUCTIONS.md` and `phase-13-arrhenius-thermal-model.md`.

Key deliverables:
1. **Arrhenius Temperature Dependence:**
   $$k(T) = A \exp\left(-\frac{E_a}{R T}\right)$$
   Strict Kelvin tracking with positive temperature validation ($T > 0\text{ K}$) and numerical exponent clamping ($[-100, 50]$).
2. **Coupled Reactor Fluid & Cooling Jacket Dynamics:**
   $$\frac{dC_A}{dt} = \frac{Q}{V}(C_{A,\text{in}} - C_A) - k(T)C_A^n$$
   $$\frac{dT}{dt} = \frac{Q}{V}(T_{\text{in}} - T) + \frac{(-\Delta H_{\text{rxn}})}{\rho C_p} k(T) C_A^n - \frac{U A}{V \rho C_p}(T - T_j)$$
   $$\frac{dT_j}{dt} = \frac{Q_j}{V_j}(T_{j,\text{in}} - T_j) + \frac{U A}{V_j \rho_j C_{pj}}(T - T_j)$$
3. **Selectable Isothermal Mode:** Setting `isothermal=True` holds $T \equiv T_{\text{in}}$ and recovers Phase 1–2 isothermal ODE solutions identically.
4. **Thermal Runaway Detection:** Automated diagnostic flag and warning when reactor temperature exceeds feed temperature by $\Delta T > 50\text{ K}$.
5. **Candidate Data Governance Note:** Candidate workbook `CSTR_24aug_PRBS_dataset.xlsx` measures temperatures and flow signals only; it cannot validate concentration predictions due to the absence of concentration assays.
