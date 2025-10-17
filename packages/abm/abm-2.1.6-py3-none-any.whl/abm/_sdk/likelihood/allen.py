__all__ = [
    "AllenLikelihoodFunction",
    "AllenResidual",
    "AllenResiduals",
    "AllenTerm",
    "LinearAllenTerm",
    "LogarithmicAllenTerm",
]

from dataclasses import dataclass

from serialite import abstract_serializable, serializable

from ..expression import Expression, Unit
from ..ode_model_reference import OdeModelReference
from ..solver_configuration import SolverConfiguration
from .base import LikelihoodFunction, LikelihoodFunctionResiduals


@abstract_serializable
@dataclass(frozen=True, kw_only=True, slots=True)
class AllenTerm:
    time: Expression
    target: str
    center: Expression


@serializable
@dataclass(frozen=True, kw_only=True, slots=True)
class LinearAllenTerm(AllenTerm):
    radius: Expression


@serializable
@dataclass(frozen=True, kw_only=True, slots=True)
class LogarithmicAllenTerm(AllenTerm):
    logspace_radius: Expression


@serializable
@dataclass(frozen=True, kw_only=True, slots=True)
class AllenLikelihoodFunction(LikelihoodFunction):
    mapping: dict[str, Expression]
    model: OdeModelReference
    terms: list[AllenTerm]
    configuration: SolverConfiguration = SolverConfiguration()


@serializable
@dataclass(frozen=True, kw_only=True, slots=True)
class AllenResidual:
    time: float
    time_unit: Unit
    target: str
    measurement: float
    unit: Unit
    prediction: float
    residual: float
    normalized_residual: float


@serializable
@dataclass(frozen=True, kw_only=True, slots=True)
class AllenResiduals(LikelihoodFunctionResiduals):
    residuals: list[AllenResidual]
