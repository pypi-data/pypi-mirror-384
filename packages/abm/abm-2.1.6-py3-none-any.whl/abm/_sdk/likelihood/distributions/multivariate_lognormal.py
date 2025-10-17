__all__ = [
    "MultivariateLogNormalDistribution",
    "MultivariateLogNormalPrediction",
    "MultivariateLogNormalResidual",
]

from dataclasses import dataclass

from serialite import serializable

from ...expression import StaticExpression, Unit
from .base import Distribution, DistributionPrediction, DistributionResidual


@serializable
@dataclass(frozen=True, kw_only=True, slots=True)
class MultivariateLogNormalDistribution(Distribution):
    times: list[StaticExpression]
    targets: list[str]
    logspace_variance: list[list[StaticExpression]]
    measurements: list[StaticExpression] | None = None


@serializable
@dataclass(frozen=True, kw_only=True, slots=True)
class MultivariateLogNormalPrediction(DistributionPrediction):
    times: list[float]
    time_units: list[Unit]
    targets: list[str]
    units: list[Unit]
    predictions: list[float]


@serializable
@dataclass(frozen=True, kw_only=True, slots=True)
class MultivariateLogNormalResidual(DistributionResidual):
    times: list[float]
    time_units: list[Unit]
    targets: list[str]
    measurements: list[float]
    units: list[Unit]
    predictions: list[float]
    residuals: list[float]
    normalized_residuals: list[float]
    log_likelihood: float
