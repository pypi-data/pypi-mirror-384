__all__ = ["OdeResidualBatch"]

from dataclasses import dataclass

from serialite import serializable

from .data_pipe import DataPipe
from .scenario import Scenario


@serializable
@dataclass(frozen=True)
class OdeResidualBatch:
    """Batch of residuals from a tidy table of global parameters.

    Attributes
    ----------
    data_pipe : `DataPipe`
        A tidy table with columns for `id`, `parameter_name`, `parameter_value`, and `parameter_unit`.
        For each unique `id`, a residual will be computed based on the parameters
    scenario : `Scenario`
        The scenario contains the likelihood functions for which the residuals will be computed.
    """

    data_pipe: DataPipe
    scenario: Scenario
