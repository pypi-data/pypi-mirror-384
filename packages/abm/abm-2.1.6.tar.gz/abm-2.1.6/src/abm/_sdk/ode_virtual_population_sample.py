__all__ = [
    "ExpectedPopulation",
    "FixedBeta",
    "OdeVirtualPopulationSample",
    "OdeVirtualPopulationSampleMethod",
]

from dataclasses import dataclass

from serialite import abstract_serializable, serializable

from .data_pipe import DataPipe
from .scenario import Scenario


@abstract_serializable
class OdeVirtualPopulationSampleMethod:
    pass


@serializable
@dataclass(frozen=True)
class FixedBeta(OdeVirtualPopulationSampleMethod):
    beta: float
    k: int = 5


@serializable
@dataclass(frozen=True)
class ExpectedPopulation(OdeVirtualPopulationSampleMethod):
    expected_n: int
    k: int = 5


@serializable
@dataclass(frozen=True)
class OdeVirtualPopulationSample:
    seed: int
    data_pipe: DataPipe
    method: OdeVirtualPopulationSampleMethod
    scenario: Scenario
    active_parameters: set[str] | None = None
