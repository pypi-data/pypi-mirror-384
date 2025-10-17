__all__ = ["OdeSimulationBatch"]

from dataclasses import dataclass

import numpy as np
from serialite import serializable

from .data_pipe import DataPipe
from .ode_model_reference import OdeModelReference
from .solver_configuration import SolverConfiguration
from .times import ListTimes, Times


@serializable
@dataclass(frozen=True, kw_only=True)
class OdeSimulationBatch:
    """Batch of simulations of multiple parameter sets.

    Attributes
    ----------
    model : `OdeModelReference`
        Model used to run the simulations.
    data_pipe : `DataPipe`
        Each row of the data_pipe table is the parameter set for an
        individual simulation within the batch.
    output_times : `Times` or `List[Expression]`
        The simulation times at which to return output values.
    output_names : `List[str] | None`, default=`None`
        The names of the simulation outputs to be returned. The possible names
        are any named components of the model. If `None`, then all model
        components are returned.
    configuration : `SolverConfiguration`, default=`SolverConfiguration()`
        The solver options to use. See `SolverConfiguration` for the available
        options and their defaults.
    """

    model: OdeModelReference
    data_pipe: DataPipe
    output_times: Times
    output_names: list[str] = None
    configuration: SolverConfiguration = SolverConfiguration()

    def __post_init__(self):
        if isinstance(self.output_times, list):
            object.__setattr__(self, "output_times", ListTimes(self.output_times))
        elif isinstance(self.output_times, np.ndarray):
            object.__setattr__(self, "output_times", ListTimes(self.output_times.tolist()))
