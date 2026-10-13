"""Unit definitions, validation, and conversion for CSTR calculations.

Internal Canonical Units:
- Volume: Liters (L)
- Volumetric Flow Rate: Liters per minute (L/min)
- Concentration: Moles per liter (mol/L)
- Time: Minutes (min)
- First-order rate constant (k): 1/min (min^-1)
- Reaction rate (r_A): mol/(L*min)
"""

from typing import Final, Literal

# Supported units
VolumeUnit = Literal["L", "m3", "mL"]
FlowRateUnit = Literal["L/min", "L/s", "L/h", "m3/h", "m3/s"]
ConcentrationUnit = Literal["mol/L", "kmol/m3", "mol/m3", "mmol/L"]
TimeUnit = Literal["min", "s", "h"]
RateConstantFirstOrderUnit = Literal["min^-1", "1/min", "s^-1", "1/s", "h^-1", "1/h"]

# Conversion factors to canonical units (L, L/min, mol/L, min, min^-1)
VOLUME_TO_CANONICAL: Final[dict[str, float]] = {
    "L": 1.0,
    "mL": 1e-3,
    "m3": 1e3,
}

FLOW_RATE_TO_CANONICAL: Final[dict[str, float]] = {
    "L/min": 1.0,
    "L/s": 60.0,
    "L/h": 1.0 / 60.0,
    "m3/h": 1e3 / 60.0,
    "m3/s": 1e3 * 60.0,
}

CONCENTRATION_TO_CANONICAL: Final[dict[str, float]] = {
    "mol/L": 1.0,
    "kmol/m3": 1.0,  # 1 kmol / m3 = 1000 mol / 1000 L = 1 mol/L
    "mol/m3": 1e-3,
    "mmol/L": 1e-3,
}

TIME_TO_CANONICAL: Final[dict[str, float]] = {
    "min": 1.0,
    "s": 1.0 / 60.0,
    "h": 60.0,
}

RATE_CONSTANT_FIRST_ORDER_TO_CANONICAL: Final[dict[str, float]] = {
    "min^-1": 1.0,
    "1/min": 1.0,
    "s^-1": 60.0,  # k_min = k_s * 60
    "1/s": 60.0,
    "h^-1": 1.0 / 60.0,
    "1/h": 1.0 / 60.0,
}


def convert_volume(value: float, from_unit: VolumeUnit) -> float:
    """Convert volume to canonical unit (L)."""
    if from_unit not in VOLUME_TO_CANONICAL:
        raise ValueError(f"Unsupported volume unit: {from_unit}. Supported: {list(VOLUME_TO_CANONICAL.keys())}")
    return value * VOLUME_TO_CANONICAL[from_unit]


def convert_flow_rate(value: float, from_unit: FlowRateUnit) -> float:
    """Convert volumetric flow rate to canonical unit (L/min)."""
    if from_unit not in FLOW_RATE_TO_CANONICAL:
        raise ValueError(f"Unsupported flow rate unit: {from_unit}. Supported: {list(FLOW_RATE_TO_CANONICAL.keys())}")
    return value * FLOW_RATE_TO_CANONICAL[from_unit]


def convert_concentration(value: float, from_unit: ConcentrationUnit) -> float:
    """Convert concentration to canonical unit (mol/L)."""
    if from_unit not in CONCENTRATION_TO_CANONICAL:
        raise ValueError(f"Unsupported concentration unit: {from_unit}. Supported: {list(CONCENTRATION_TO_CANONICAL.keys())}")
    return value * CONCENTRATION_TO_CANONICAL[from_unit]


def convert_time(value: float, from_unit: TimeUnit) -> float:
    """Convert time to canonical unit (min)."""
    if from_unit not in TIME_TO_CANONICAL:
        raise ValueError(f"Unsupported time unit: {from_unit}. Supported: {list(TIME_TO_CANONICAL.keys())}")
    return value * TIME_TO_CANONICAL[from_unit]


def convert_first_order_rate_constant(value: float, from_unit: RateConstantFirstOrderUnit) -> float:
    """Convert 1st order rate constant to canonical unit (min^-1)."""
    if from_unit not in RATE_CONSTANT_FIRST_ORDER_TO_CANONICAL:
        raise ValueError(f"Unsupported rate constant unit: {from_unit}. Supported: {list(RATE_CONSTANT_FIRST_ORDER_TO_CANONICAL.keys())}")
    return value * RATE_CONSTANT_FIRST_ORDER_TO_CANONICAL[from_unit]
