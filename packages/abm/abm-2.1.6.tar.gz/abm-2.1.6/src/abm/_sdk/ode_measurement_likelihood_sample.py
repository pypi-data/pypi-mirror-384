__all__ = ["OdeMeasurementLikelihoodSample"]

from dataclasses import dataclass
from typing import Literal

from serialite import serializable

from .scenario import Scenario


@serializable
@dataclass(frozen=True, kw_only=True, slots=True)
class OdeMeasurementLikelihoodSample:
    scenario: Scenario
    rng: Literal["mt"]
    seed: int
