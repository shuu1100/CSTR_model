# CSTR Lab — Backend API Specification (v1)

## Base URL
Default local development base URL:
`http://127.0.0.1:8000/api/v1`

---

## Endpoints

### 1. `GET /api/v1/health`
Operational health check.

**Sample Response (200 OK):**
```json
{
  "status": "ok",
  "app_name": "CSTR Lab API",
  "version": "0.1.0",
  "timestamp": "2026-10-12T04:00:00.000000+00:00"
}
```

---

### 2. `GET /api/v1/models`
Returns catalog of available reactor models, supported reaction orders, canonical units, assumptions, and solvers.

**Sample Response (200 OK):**
```json
{
  "models": [
    {
      "model_id": "isothermal_cstr_elementary",
      "name": "Ideal Isothermal CSTR",
      "description": "Continuous Stirred-Tank Reactor operating isothermally with constant volume, perfect mixing, and elementary kinetics (orders 0, 1, 2).",
      "supported_orders": [0, 1, 2],
      "canonical_units": {
        "V": "L",
        "Q": "L/min",
        "C_A": "mol/L",
        "t": "min",
        "tau": "min",
        "k_order_0": "mol/(L*min)",
        "k_order_1": "min^-1",
        "k_order_2": "L/(mol*min)",
        "r_A": "mol/(L*min)"
      },
      "assumptions": [
        "Perfect mixing (spatially uniform concentration in vessel)",
        "Constant liquid volume and constant fluid density",
        "Equal inlet and outlet volumetric flow rates (Q_in = Q_out)",
        "Isothermal operation (constant temperature)",
        "Irreversible reaction A -> Products",
        "Physical depletion boundary enforced for zero-order kinetics"
      ],
      "solvers": [
        "Analytical (first order)",
        "SciPy solve_ivp (RK45, Radau, BDF, LSODA, RK23, DOP853)"
      ]
    }
  ]
}
```

---

### 3. `POST /api/v1/simulations/steady-state`
Computes the steady-state operating point and material-balance residual diagnostics for orders $n=0, 1, 2$.

**Sample Request (First-Order Canonical Oracle):**
```json
{
  "V": 10.0,
  "Q": 1.0,
  "C_A_in": 2.0,
  "order": 1,
  "k": 0.15
}
```

**Sample Response (200 OK):**
```json
{
  "model_id": "isothermal_cstr_order_1",
  "normalized_inputs": {
    "V": 10.0,
    "Q": 1.0,
    "C_A_in": 2.0,
    "order": 1,
    "k": 0.15
  },
  "outputs": {
    "tau": 10.0,
    "C_A_ss": 0.8,
    "conversion": 0.6,
    "reaction_rate_ss": -0.12,
    "residual": 0.0
  },
  "units": {
    "V": "L",
    "Q": "L/min",
    "C_A_in": "mol/L",
    "k": "min^-1",
    "tau": "min",
    "C_A_ss": "mol/L",
    "conversion": "fraction [0, 1]",
    "reaction_rate_ss": "mol/(L*min)",
    "residual": "mol/(L*min)"
  },
  "assumptions": [
    "Perfect mixing (spatially uniform concentration in vessel)",
    "Constant liquid volume and constant fluid density",
    "Equal inlet and outlet volumetric flow rates (Q_in = Q_out)",
    "Isothermal operation",
    "Irreversible reaction with kinetic order n=1"
  ],
  "diagnostics": {
    "material_balance_closed": true,
    "residual_absolute": 0.0,
    "residual_tolerance": 1e-09
  },
  "warnings": []
}
```

---

### 4. `POST /api/v1/simulations/dynamic`
Computes the transient concentration trajectory using `scipy.integrate.solve_ivp`, supporting piecewise step changes.

**Sample Request:**
```json
{
  "C_A_0": 0.5,
  "C_A_in": 2.0,
  "V": 10.0,
  "Q": 1.0,
  "order": 1,
  "k": 0.15,
  "t_final": 50.0,
  "n_points": 51,
  "solver_method": "RK45",
  "step_change": {
    "time": 25.0,
    "C_A_in_new": 4.0
  }
}
```

**Sample Response (200 OK):**
```json
{
  "model_id": "dynamic_cstr_order_1",
  "normalized_inputs": {
    "C_A_0": 0.5,
    "C_A_in": 2.0,
    "V": 10.0,
    "Q": 1.0,
    "order": 1,
    "k": 0.15,
    "t_final": 50.0,
    "n_points": 51,
    "solver_method": "RK45",
    "rtol": 1e-06,
    "atol": 1e-09,
    "step_change": {
      "time": 25.0,
      "C_A_in_new": 4.0,
      "Q_new": null
    }
  },
  "t": [0.0, 1.0, "..."],
  "C_A": [0.5, 0.56, "..."],
  "conversion": [0.75, 0.72, "..."],
  "reaction_rate": [-0.075, "..."],
  "tau_initial": 10.0,
  "C_A_ss_initial": 0.8,
  "solver_details": {
    "method": "RK45",
    "success": true,
    "status": 0,
    "message": "The solver successfully reached the end of the integration interval.",
    "tolerances": {
      "rtol": 1e-06,
      "atol": 1e-09
    }
  },
  "analytical_comparison": null,
  "step_change_applied": {
    "time": 25.0,
    "C_A_in_initial": 2.0,
    "C_A_in_new": 4.0,
    "Q_initial": 1.0,
    "Q_new": 1.0,
    "C_A_at_step": 0.799
  },
  "units": {
    "t": "min",
    "C_A": "mol/L",
    "conversion": "fraction [0, 1]",
    "reaction_rate": "mol/(L*min)",
    "V": "L",
    "Q": "L/min",
    "k": "min^-1"
  },
  "assumptions": [
    "Unsteady-state species mole balance: dC_A/dt = (Q/V)*(C_in - C_A) + r_A",
    "Perfect mixing throughout the reactor volume",
    "Constant reactor volume and constant fluid density",
    "Isothermal operation",
    "Reaction order n=1"
  ],
  "warnings": []
}
```

---

## Local Development Server

Run FastAPI locally via Uvicorn:
```bash
python -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```
Interactive Swagger UI documentation is available at:
`http://127.0.0.1:8000/docs`
