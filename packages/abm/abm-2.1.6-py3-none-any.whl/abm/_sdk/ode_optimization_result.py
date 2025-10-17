__all__ = ["OdeOptimizationResult"]

from dataclasses import dataclass

from serialite import serializable

from .expression import Unit


@serializable
@dataclass(frozen=True, slots=True, kw_only=True)
class UnittedValue:
    value: float
    unit: Unit


@serializable
@dataclass(frozen=True)
class OdeOptimizationResult:
    final_objective: float
    global_parameters: dict[str, UnittedValue]
