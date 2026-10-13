"""Model catalog and metadata endpoint."""

from fastapi import APIRouter
from backend.app.schemas.simulation import ModelCatalogItem, ModelCatalogResponse

router = APIRouter(tags=["Models"])


@router.get("/models", response_model=ModelCatalogResponse)
def get_models() -> ModelCatalogResponse:
    """Return catalog of available CSTR models, supported orders, units, and assumptions."""
    isothermal_cstr = ModelCatalogItem(
        model_id="isothermal_cstr_elementary",
        name="Ideal Isothermal CSTR",
        description="Continuous Stirred-Tank Reactor operating isothermally with constant volume, perfect mixing, and elementary kinetics (orders 0, 1, 2).",
        supported_orders=[0, 1, 2],
        canonical_units={
            "V": "L",
            "Q": "L/min",
            "C_A": "mol/L",
            "t": "min",
            "tau": "min",
            "k_order_0": "mol/(L*min)",
            "k_order_1": "min^-1",
            "k_order_2": "L/(mol*min)",
            "r_A": "mol/(L*min)",
        },
        assumptions=[
            "Perfect mixing (spatially uniform concentration in vessel)",
            "Constant liquid volume and constant fluid density",
            "Equal inlet and outlet volumetric flow rates (Q_in = Q_out)",
            "Isothermal operation (constant temperature)",
            "Irreversible reaction A -> Products",
            "Physical depletion boundary enforced for zero-order kinetics",
        ],
        solvers=["Analytical (first order)", "SciPy solve_ivp (RK45, Radau, BDF, LSODA, RK23, DOP853)"],
    )

    return ModelCatalogResponse(models=[isothermal_cstr])
