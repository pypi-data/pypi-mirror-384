__all__ = [
    "ClassifierSurrogate",
    "OdeProposalPopulationSample",
    "OdeProposalPopulationSampleMethod",
    "TruncatedSSE",
]

from dataclasses import dataclass

from serialite import abstract_serializable, serializable

from .data_pipe import DataPipe
from .ode_optimization_configuration import OdeOptimizationConfiguration
from .scenario import Scenario


@abstract_serializable
class OdeProposalPopulationSampleMethod:
    pass


@serializable
@dataclass(frozen=True)
class TruncatedSSE(OdeProposalPopulationSampleMethod):
    sample_n: int = 1000
    optimization_configuration: OdeOptimizationConfiguration = OdeOptimizationConfiguration(min_objective=0.0)


@serializable
@dataclass(frozen=True)
class ClassifierSurrogate(OdeProposalPopulationSampleMethod):
    sample_n: int = 3000
    max_iters: int = 10
    init_batch_size: int = 2500
    max_batch_size: int = 1000
    anchors: DataPipe | None = None


@serializable
@dataclass(frozen=True)
class OdeProposalPopulationSample:
    seed: int
    method: OdeProposalPopulationSampleMethod
    scenario: Scenario
    active_parameters: set[str] | None = None
