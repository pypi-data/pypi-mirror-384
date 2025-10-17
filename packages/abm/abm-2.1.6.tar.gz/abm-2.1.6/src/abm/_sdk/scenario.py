__all__ = [
    "LaplacePrior",
    "LogLaplacePrior",
    "LogNormalPrior",
    "LogUniformPrior",
    "NormalPrior",
    "Prior",
    "Scenario",
    "ScenarioParameter",
    "UniformPrior",
]

from dataclasses import dataclass
from typing import ClassVar

from serialite import abstract_serializable, serializable

from .expression import Expression, Unit
from .likelihood import LikelihoodFunction


@abstract_serializable
class Prior:
    __slots__ = ()
    is_logscaled: ClassVar[bool]


@serializable
@dataclass(frozen=True, kw_only=True, slots=True)
class UniformPrior(Prior):
    is_logscaled = False
    lower: Expression = "-inf"
    upper: Expression = "inf"


@serializable
@dataclass(frozen=True, kw_only=True, slots=True)
class LogUniformPrior(Prior):
    is_logscaled = True
    lower: Expression = "0.0"
    upper: Expression = "inf"


@serializable
@dataclass(frozen=True, kw_only=True, slots=True)
class NormalPrior(Prior):
    is_logscaled = False
    mean: Expression
    standard_deviation: Expression
    lower: Expression = "-inf"
    upper: Expression = "inf"


@serializable
@dataclass(frozen=True, kw_only=True, slots=True)
class LogNormalPrior(Prior):
    is_logscaled = True
    geometric_mean: Expression
    logspace_standard_deviation: Expression
    lower: Expression = "0.0"
    upper: Expression = "inf"


@serializable
@dataclass(frozen=True, kw_only=True, slots=True)
class LaplacePrior(Prior):
    is_logscaled = False
    mean: Expression
    mean_absolute_deviation: Expression
    lower: Expression = "-inf"
    upper: Expression = "inf"


@serializable
@dataclass(frozen=True, kw_only=True, slots=True)
class LogLaplacePrior(Prior):
    is_logscaled = True
    geometric_mean: Expression
    logspace_mean_absolute_deviation: Expression
    lower: Expression = "0.0"
    upper: Expression = "inf"


@serializable
@dataclass(frozen=True, kw_only=True, slots=True)
class ScenarioParameter:
    value: Expression
    unit: Unit | None = None
    prior: Prior = LogUniformPrior()


@serializable
@dataclass(frozen=True, slots=True)
class Scenario:
    global_parameters: dict[str, ScenarioParameter]
    likelihood_functions: list[LikelihoodFunction]
