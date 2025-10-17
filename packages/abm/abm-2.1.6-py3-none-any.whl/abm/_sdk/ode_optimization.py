__all__ = ["OdeOptimization"]


from dataclasses import dataclass

from serialite import serializable

from .ode_optimization_configuration import OdeOptimizationConfiguration
from .scenario import Scenario


@serializable
@dataclass(frozen=True, kw_only=True)
class OdeOptimization:
    """Object for fitting model parameters to an output.

    Attributes
    ----------
    scenario : `Scenario`
        The scenario contains the data that will be fit, as well as the mapping
        parameters, which are used to define how the global parameters will
        influence the model parameters as well as how the parameters change for
        each dataset.
    active_parameters : `set[str]` | `None`
        Subset of the scenario global parameters that will be fit.  If `None`
        (default), all parameters are fit.
    configuration : `OdeOptimizationConfiguration`
        Configuration controls the optimizer settings. See the
        `OdeOptimizationConfiguration` object for optimizer options.

    See Also
    --------
    Scenario :
        A `Scenario` used to configure parameter optimization involving a
        single simulation.
    """

    scenario: Scenario
    active_parameters: set[str] | None = None
    configuration: OdeOptimizationConfiguration = OdeOptimizationConfiguration()
