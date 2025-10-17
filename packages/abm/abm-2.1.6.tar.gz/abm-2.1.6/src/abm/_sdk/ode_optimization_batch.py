__all__ = ["OdeOptimizationBatch"]

from dataclasses import dataclass

from serialite import serializable

from .data_pipe import DataPipe
from .ode_optimization_configuration import OdeOptimizationConfiguration
from .scenario import Scenario


@serializable
@dataclass(frozen=True)
class OdeOptimizationBatch:
    """Batch of optimizations from multiple initial sets of global parameters.

    Attributes
    ----------
    data_pipe : `DataPipe`
        Each row of the data_pipe table is the starting parameter set for an
        individual optimization within the batch.
    scenario : `Scenario`
        The scenario contains the data that will be fit for all the optimizations
        in the batch, as well as the mapping parameters, which are used to define
        how the global parameters will influence the model parameters as well as
        how the parameters change for each dataset (same as required for an
        Optimization)
    active_parameters : `set[str]` | None
        Subset of the scenario global parameters that will be fit.  If `None`
        (default), all parameters are fit.
    configuration : `OdeOptimizationConfiguration`
        Configuration controls the optimizer settings. See the
        `OdeOptimizationConfiguration` object for optimizer options.
    """

    data_pipe: DataPipe
    scenario: Scenario
    active_parameters: set[str] | None = None
    configuration: OdeOptimizationConfiguration = OdeOptimizationConfiguration()
