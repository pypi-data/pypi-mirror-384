from __future__ import annotations

__all__ = ["OdeModelReference"]

from dataclasses import dataclass, field

from serialite import serializable

from .expression import Expression
from .ode_model import Schedule
from .qsp_designer_model import QspDesignerModel  # noqa: F401, make sure QspDesignerModel gets registered


@serializable
@dataclass(frozen=True)
class OdeModelReference:
    """A base model and optional alterations to its parameters and route
    schedules.

    Attributes
    ----------
    model_id : `str`
        The identifying string of the base `Job[OdeModel, None, OdeModelTypes]`.
    parameters : `dict[str, Expression]`, default=`dict()`
        New parameter values to replace those of the base model. The keys are
        the parameter names, and the values are the new parameter values. Any
        unmentioned parameters default to the base model's values. The default
        is to replace no parameter values.
    schedules : `dict[str, Schedule]`, default=`dict()`
        New dose `Schedule`s to replace those of the base model. The keys are
        the names of the `Route`s that will have their `Schedule`s replaced. The
        values are the new `Schedule`s. Any `Route`s not included will default
        to the `Schedule`s defined in the base model. The default is to replace
        no `Schedule`s.
    """

    model_id: str
    parameters: dict[str, Expression] = field(default_factory=dict)
    schedules: dict[str, Schedule] = field(default_factory=dict)
