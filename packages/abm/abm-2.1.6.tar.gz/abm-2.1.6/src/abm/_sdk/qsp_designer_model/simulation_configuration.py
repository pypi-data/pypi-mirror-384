__all__ = ["SimulationConfiguration"]

from dataclasses import dataclass
from typing import Literal

from serialite import serializable


@serializable
@dataclass(frozen=True, kw_only=True)
class SimulationConfiguration:
    """For Assess metadata"""

    linear_solver: Literal["KLU", "SPGMR"] = "KLU"
    abstol: float = 1e-11  # These are the QSP Designer defaults
    reltol: float = 1e-8
