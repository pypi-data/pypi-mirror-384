__all__ = ["OdeSimulation"]

from dataclasses import dataclass
from pathlib import Path

import numpy as np
from serialite import serializable

from .expression import Expression
from .ode_model_reference import OdeModelReference
from .solver_configuration import SolverConfiguration
from .times import ListTimes, Times
from .to_matlab_ode_simulation import to_matlab
from .to_simbiology_ode_simulation import to_simbiology


@serializable
@dataclass(frozen=True, kw_only=True)
class OdeSimulation:
    """Specifies a simulation.

    Attributes
    ----------
    model : `OdeModelReference`
        The `OdeModelReference` to be simulated. The `OdeModelReference` specifies the
        model and any parameter or route schedule changes to the model.
    output_times : `Times` or `list[Expression]`
        The simulation times to be returned.
    output_names : `list[str] | None`, default=`None`
        The names of the simulation outputs to be returned. The possible names
        are any named components of the model. If `None`, then all model
        components are returned.
    configuration : `SolverConfiguration`, default=`SolverConfiguration()`
        The solver configuration (tolerances, etc.) to use.
        Create an instance of the `SolverConfiguration` class to specify the
        configuration.

    See Also
    --------
    `OdeSimulationBatch`: A batch of simulations varying one or more model parameters.
    """

    model: OdeModelReference
    output_times: Times | list[Expression]
    output_names: list[str] | None = None
    configuration: SolverConfiguration = SolverConfiguration()

    def __post_init__(self):
        if isinstance(self.output_times, list):
            object.__setattr__(self, "output_times", ListTimes(self.output_times))
        elif isinstance(self.output_times, np.ndarray):
            object.__setattr__(self, "output_times", ListTimes(self.output_times.tolist()))

    def to_matlab(self, path: Path | str):
        """Export the simulation to a MATLAB script.

        Parameters
        ----------
        path : `Path | str`
            The name of the file to which the MATLAB script is written.
        """

        to_matlab(path, **self.__dict__)

    def to_simbiology(self, path: Path | str):
        """Export the simulation to a SimBiology project.

        Parameters
        ----------
        path : ` Path | str`
            The name of the file to which the SimBiology project is written.
        """

        to_simbiology(path, **self.__dict__)
