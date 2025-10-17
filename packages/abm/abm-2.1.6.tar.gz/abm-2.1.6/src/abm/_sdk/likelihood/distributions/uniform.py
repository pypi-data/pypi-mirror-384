__all__ = [
    "UniformDistribution",
    "UniformPrediction",
    "UniformResidual",
]

from dataclasses import dataclass

from serialite import serializable

from ...expression import StaticExpression, Unit
from .base import Distribution, DistributionPrediction, DistributionResidual


@serializable
@dataclass(frozen=True, kw_only=True, slots=True)
class UniformDistribution(Distribution):
    time: StaticExpression
    target: str
    lower: StaticExpression
    upper: StaticExpression
    smoothness: StaticExpression | None = None


@serializable
@dataclass(frozen=True, kw_only=True, slots=True)
class UniformPrediction(DistributionPrediction):
    time: float
    time_unit: Unit
    target: str
    unit: Unit
    prediction: float


@serializable
@dataclass(frozen=True, kw_only=True, slots=True)
class UniformResidual(DistributionResidual):
    time: float
    time_unit: Unit
    target: str
    measurement: float
    unit: Unit
    prediction: float
    residual: float
    normalized_residual: float
    log_likelihood: float
