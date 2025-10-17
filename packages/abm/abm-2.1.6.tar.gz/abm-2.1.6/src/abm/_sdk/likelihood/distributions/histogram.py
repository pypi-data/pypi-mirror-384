__all__ = [
    "HistogramDistribution",
    "HistogramPrediction",
    "HistogramResidual",
]

from dataclasses import dataclass

from serialite import serializable

from ...expression import StaticExpression, Unit
from .base import Distribution, DistributionPrediction, DistributionResidual


@serializable
@dataclass(frozen=True, kw_only=True, slots=True)
class HistogramDistribution(Distribution):
    time: StaticExpression
    target: str
    bin_edges: list[StaticExpression]
    bin_probabilities: list[StaticExpression]
    smoothness: StaticExpression | None = None


@serializable
@dataclass(frozen=True, kw_only=True, slots=True)
class HistogramPrediction(DistributionPrediction):
    time: float
    time_unit: Unit
    target: str
    unit: Unit
    prediction: float


@serializable
@dataclass(frozen=True, kw_only=True, slots=True)
class HistogramResidual(DistributionResidual):
    time: float
    time_unit: Unit
    target: str
    measurement: float
    unit: Unit
    prediction: float
    residual: float
    normalized_residual: float
    log_likelihood: float
