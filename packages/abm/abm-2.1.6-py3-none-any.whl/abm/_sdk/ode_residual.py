from __future__ import annotations

__all__ = ["OdeResidual"]

from dataclasses import dataclass

from serialite import serializable

from .likelihood import LikelihoodFunctionResiduals
from .scenario import Scenario


@serializable
@dataclass(frozen=True, kw_only=True)
class OdeResidual:
    scenario: Scenario


@serializable
@dataclass(frozen=True)
class ScenarioResiduals:
    log_likelihood: float
    likelihood_function_residuals: list[LikelihoodFunctionResiduals]
