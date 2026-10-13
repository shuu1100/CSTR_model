"""Kinetic models and rate expressions for CSTR simulation.

Supported isothermal irreversible reaction models: A -> Products
- Zero-order (n=0): r_A = -k (for C_A > 0; 0 otherwise)
  Unit of k: mol/(L*min)
- First-order (n=1): r_A = -k * C_A
  Unit of k: min^-1 (1/min)
- Second-order (n=2): r_A = -k * C_A^2
  Unit of k: L/(mol*min)
"""

from dataclasses import dataclass
from enum import IntEnum
import math
from typing import Final, Literal


class ReactionOrder(IntEnum):
    """Supported reaction orders."""
    ZERO = 0
    FIRST = 1
    SECOND = 2


# Canonical units for rate constants by reaction order
RATE_CONSTANT_CANONICAL_UNITS: Final[dict[int, str]] = {
    0: "mol/(L*min)",
    1: "min^-1",
    2: "L/(mol*min)",
}


@dataclass(frozen=True)
class KineticModel:
    """Specification of an irreversible isothermal kinetic model for species A."""

    order: int  # 0, 1, or 2
    k: float  # Rate constant in canonical units
    epsilon_depletion: float = 1e-3  # Numerical smoothing threshold for zero-order depletion

    def __post_init__(self) -> None:
        if not isinstance(self.order, int):
            raise TypeError(f"Reaction order must be an integer (0, 1, 2), got {type(self.order).__name__}.")
        if self.order not in (0, 1, 2):
            raise ValueError(f"Unsupported reaction order {self.order}. Supported orders are 0, 1, 2.")
        if not isinstance(self.k, (int, float)):
            raise TypeError(f"Rate constant k must be numeric, got {type(self.k).__name__}.")
        if not math.isfinite(self.k):
            raise ValueError(f"Rate constant k must be finite, got {self.k}.")
        if self.k < 0.0:
            raise ValueError(f"Rate constant k must be non-negative (>= 0), got {self.k}.")

    @property
    def k_unit(self) -> str:
        """Return the canonical unit for this reaction order's rate constant."""
        return RATE_CONSTANT_CANONICAL_UNITS[self.order]

    def reaction_rate(self, C_A: float) -> float:
        """Calculate volumetric rate of reaction r_A [mol/(L*min)] for concentration C_A.

        By chemical convention, consumption of reactant A is negative: r_A <= 0.
        """
        # Strictly enforce non-negative concentration physics
        c_eff = max(0.0, float(C_A))

        if self.order == 0:
            # Physical depletion boundary: smooth linear regularization near zero
            # to prevent solver chattering (discontinuous switching)
            if c_eff <= 0.0:
                return 0.0
            if c_eff < self.epsilon_depletion:
                return -self.k * (c_eff / self.epsilon_depletion)
            return -self.k

        if self.order == 1:
            return -self.k * c_eff

        if self.order == 2:
            return -self.k * (c_eff ** 2)

        raise ValueError(f"Unsupported reaction order: {self.order}")


def calculate_reaction_rate(order: int, k: float, C_A: float) -> float:
    """Convenience function to evaluate reaction rate for given order and k."""
    model = KineticModel(order=order, k=k)
    return model.reaction_rate(C_A)
