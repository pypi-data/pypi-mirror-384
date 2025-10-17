from __future__ import annotations

__all__ = ["OdeParameterPosteriorSample"]

from dataclasses import dataclass

from serialite import serializable

from .ode_posterior_sample_configuration import OdePosteriorSampleConfiguration
from .scenario import Scenario


@serializable
@dataclass(frozen=True, kw_only=True)
class OdeParameterPosteriorSample:
    """Object for sampling from the parameter posterior distribution given data.

    Attributes
    ----------
    scenario : `Scenario`
        The scenario contains the data that will be fit, as well as the mapping
        parameters, which are used to define how the global parameters will
        influence the model parameters as well as how the parameters change for
        each dataset.
    n : `int`
        Number of samples.
    seed : `int`
        Random number seed to use.
    configuration : `OdePosteriorSampleConfiguration`
        Configuration controls the sampler settings. See the
        `OdePosteriorSampleConfiguration` object for sampling options.

    See Also
    --------
    Scenario :
        A `Scenario` used to configure parameter optimization involving a
        single simulation.
    """

    scenario: Scenario
    n: int
    seed: int
    configuration: OdePosteriorSampleConfiguration = OdePosteriorSampleConfiguration()
