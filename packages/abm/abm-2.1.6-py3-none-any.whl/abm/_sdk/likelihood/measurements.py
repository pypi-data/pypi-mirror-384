__all__ = [
    "Measurement",
    "MeasurementPrediction",
    "MeasurementResidual",
    "MeasurementsLikelihoodFunction",
    "MeasurementsPredictions",
    "MeasurementsResiduals",
]

from dataclasses import dataclass

from serialite import serializable

from ..expression import Expression, Unit
from ..ode_model_reference import OdeModelReference
from ..solver_configuration import SolverConfiguration
from .base import LikelihoodFunction, LikelihoodFunctionPredictions, LikelihoodFunctionResiduals


@serializable
@dataclass(frozen=True, kw_only=True, slots=True)
class Measurement:
    time: Expression
    target: str
    measurement: Expression | None = None
    constant_error: Expression = "0.0"
    proportional_error: Expression = 0.0
    exponential_error: Expression = 0.0
    lower_limit_of_quantification: Expression = "-inf"
    upper_limit_of_quantification: Expression = "inf"


@serializable
@dataclass(frozen=True, kw_only=True, slots=True)
class MeasurementsLikelihoodFunction(LikelihoodFunction):
    mapping: dict[str, Expression]
    model: OdeModelReference
    measurements: list[Measurement]
    configuration: SolverConfiguration = SolverConfiguration()


@serializable
@dataclass(frozen=True, kw_only=True, slots=True)
class MeasurementPrediction:
    time: float
    time_unit: Unit
    target: str
    unit: Unit
    prediction: float


@serializable
@dataclass(frozen=True, kw_only=True, slots=True)
class MeasurementsPredictions(LikelihoodFunctionPredictions):
    predictions: list[MeasurementPrediction]


@serializable
@dataclass(frozen=True, kw_only=True, slots=True)
class MeasurementResidual:
    time: float
    time_unit: Unit
    target: str
    measurement: float
    unit: Unit
    prediction: float
    residual: float
    normalized_residual: float | None = None
    log_likelihood: float


@serializable
@dataclass(frozen=True)
class MeasurementsResiduals(LikelihoodFunctionResiduals):
    residuals: list[MeasurementResidual]
