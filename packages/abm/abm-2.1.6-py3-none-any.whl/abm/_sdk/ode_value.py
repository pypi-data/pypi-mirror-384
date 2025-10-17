__all__ = ["OdeValue"]

from dataclasses import dataclass

from serialite import serializable

from .scenario import Scenario


@serializable
@dataclass(frozen=True, kw_only=True)
class OdeValue:
    """Compute scenario objective. Result is a dictionary with G and its components,
    likelihood and prior."""

    scenario: Scenario


@serializable
@dataclass(frozen=True, kw_only=True)
class OdeValueResult:
    """Result of the OdeValue computation."""

    g: float
    likelihood_g: float
    prior_g: float
