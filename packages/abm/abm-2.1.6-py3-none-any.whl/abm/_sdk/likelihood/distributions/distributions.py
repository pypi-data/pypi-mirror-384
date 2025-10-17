__all__ = [
    "DistributionsLikelihoodFunction",
    "DistributionsPredictions",
    "DistributionsResiduals",
]

from dataclasses import dataclass

from serialite import serializable

from ...expression import Expression
from ...ode_model_reference import OdeModelReference
from ...solver_configuration import SolverConfiguration
from ..base import LikelihoodFunction, LikelihoodFunctionPredictions, LikelihoodFunctionResiduals
from .base import Distribution, DistributionPrediction, DistributionResidual


@serializable
@dataclass(frozen=True, kw_only=True, slots=True)
class DistributionsLikelihoodFunction(LikelihoodFunction):
    mapping: dict[str, Expression]
    model: OdeModelReference
    distributions: list[Distribution]
    configuration: SolverConfiguration = SolverConfiguration()


@serializable
@dataclass(frozen=True, slots=True)
class DistributionsPredictions(LikelihoodFunctionPredictions):
    predictions: list[DistributionPrediction]


@serializable
@dataclass(frozen=True, slots=True)
class DistributionsResiduals(LikelihoodFunctionResiduals):
    residuals: list[DistributionResidual]
