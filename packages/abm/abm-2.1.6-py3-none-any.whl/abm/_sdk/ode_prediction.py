from __future__ import annotations

__all__ = ["OdePrediction"]

from dataclasses import dataclass

from serialite import serializable

from .likelihood import LikelihoodFunctionPredictions
from .scenario import Scenario


@serializable
@dataclass(frozen=True, kw_only=True)
class OdePrediction:
    scenario: Scenario


@serializable
@dataclass(frozen=True, kw_only=True, slots=True)
class ScenarioPredictions:
    likelihood_function_predictions: list[LikelihoodFunctionPredictions]
