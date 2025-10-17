__all__ = [
    "Assignment",
    "BindingOffReaction",
    "BindingOnReaction",
    "BoundVariable",
    "Compartment",
    "DoseEffect",
    "Effect",
    "EmaxReaction",
    "EmptySchedule",
    "ForwardAnalyticReaction",
    "ForwardMassActionReaction",
    "HalfLifeReaction",
    "InitialValue",
    "Initialization",
    "JumpEffect",
    "ListSchedule",
    "MichaelisMentenReaction",
    "Parameter",
    "Reaction",
    "ReactionModel",
    "RepeatSchedule",
    "ReversibleAnalyticReaction",
    "ReversibleMassActionReaction",
    "Route",
    "State",
    "SteadyState",
    "SteadyStateReaction",
    "TransportReaction",
]

from dataclasses import dataclass, field
from typing import Literal

from serialite import abstract_serializable, serializable

from .expression import Expression, StaticExpression, Unit
from .ode_model import OdeModel, Schedule


@serializable
@dataclass(frozen=True)
class Parameter:
    value: StaticExpression
    unit: Unit | None = None


@serializable
@dataclass(frozen=True)
class Assignment:
    definition: Expression
    unit: Unit | None = None


@serializable
@dataclass(frozen=True)
class BoundVariable:
    initial_guess: StaticExpression
    unit: Unit | None = None


@serializable
@dataclass(frozen=True)
class Compartment:
    dimension: Literal[0, 1, 2, 3]
    size: Expression
    unit: Unit | None = None


@serializable
@dataclass(frozen=True)
class State:
    initial_value: Expression
    compartment: str | None = None
    unit: Unit | None = None


@abstract_serializable
@dataclass(frozen=True)
class Reaction:
    reactants: list[str]
    products: list[str]


@serializable
@dataclass(frozen=True)
class ForwardMassActionReaction(Reaction):
    parameter: Expression


@serializable
@dataclass(frozen=True)
class ReversibleMassActionReaction(Reaction):
    forward_parameter: Expression
    reverse_parameter: Expression


@serializable
@dataclass(frozen=True)
class ForwardAnalyticReaction(Reaction):
    rate: Expression


@serializable
@dataclass(frozen=True)
class ReversibleAnalyticReaction(Reaction):
    forward_rate: Expression
    reverse_rate: Expression


@serializable
@dataclass(frozen=True)
class TransportReaction(Reaction):
    partition_coefficient: Expression
    distribution_half_life: Expression


@serializable
@dataclass(frozen=True)
class HalfLifeReaction(Reaction):
    half_life: Expression


@serializable
@dataclass(frozen=True)
class BindingOnReaction(Reaction):
    dissociation_parameter: Expression
    association_rate_parameter: Expression


@serializable
@dataclass(frozen=True)
class BindingOffReaction(Reaction):
    dissociation_parameter: Expression
    dissociation_rate_parameter: Expression


@serializable
@dataclass(frozen=True)
class EmaxReaction(Reaction):
    maximum_rate: Expression
    half_maximal_effect_concentration: Expression
    hill_coefficient: Expression
    minimum_rate: Expression = "0.0"


@serializable
@dataclass(frozen=True)
class MichaelisMentenReaction(Reaction):
    michaelis_parameter: Expression
    catalytic_rate_parameter: Expression
    enzyme_amount: Expression


@serializable
@dataclass(frozen=True)
class SteadyStateReaction(Reaction):
    steady_state_concentration: Expression
    half_life: Expression
    volume: Expression | None = None


@serializable
@dataclass(frozen=True)
class EmptySchedule(Schedule):
    """Schedule that cannot apply any doses."""


@serializable
@dataclass(frozen=True, kw_only=True)
class RepeatSchedule(Schedule):
    """Schedule that applies the same dose amount at a regular interval
    a specified number of times.

    Attributes
    ----------
    start : `Expression`
        The time at which the dose will first be applied.
    interval : `Expression`
        The interval of time between doses.
    n : `Expression`
        The number of doses applied.
    amount : `Expression`
        The dose amount.
    duration : `Expression`
        Infusion duration (0 indicates bolus dosing)

    Notes
    -----
    The attributes can be arbitrary expressions of numerics, model parameters,
    and constant rules. If provided as `str`s, they will be parsed into
    `Expression`s.
    """

    start: Expression = "0.0"
    interval: Expression
    n: Expression = "inf"
    amount: Expression | None = None
    duration: Expression | None = None


@serializable
@dataclass(frozen=True, kw_only=True)
class ListSchedule(Schedule):
    """Schedule that applies listed dose amounts at listed times.

    Attributes
    ----------
    times : `list[Expression]`
        The times at which the dose should be applied.
    amounts : `list[Expression]`
        The dose amounts that should be applied.
    durations : `list[Expression]`
        Infusion durations corresponding to each dose.  A duration of 0 indicates
        a bolus dose.

    Notes
    -----
    The `List` elements can contain arbitrary expressions of numerics, model
    parameters, and constant rules. If the elements are provided as `str`s, they
    will be parsed into `Expression`s.
    """

    times: list[Expression]
    amounts: list[Expression] | None = None
    durations: list[Expression] | None = None


@abstract_serializable
class Effect:
    pass


@serializable
@dataclass
class DoseEffect(Effect):
    value: Expression


@serializable
@dataclass
class JumpEffect(Effect):
    value: Expression


@serializable
@dataclass(frozen=True)
class Route:
    effects: dict[str, Effect]
    schedule: Schedule
    amount_unit: Unit | None = None


@serializable
@dataclass(frozen=True)
class Event:
    trigger: Expression
    effects: dict[str, Expression]


@abstract_serializable
class Initialization:
    pass


@serializable
@dataclass(frozen=True)
class InitialValue(Initialization):
    """Simulation starts at the given initial values of the states."""


@serializable
@dataclass(frozen=True)
class SteadyState(Initialization):
    """Simulation starts after states are run to equilibrium.

    Attributes
    ----------
    time_scale : `Expression`
        A static expression evaluating to the typical length of a simulation in
        the time units of the model. Equilibrium is defined as having been
        achieved when the system is expected to change less than the tolerance
        over this time scale.
    max_time : `Expression | None`, default=`None`
        A static expression evaluating to a time in the time units of the model.
        If the simulation has not reached equilibrium by this time, raise an
        exception. This is in the time units of the model. If `None`, a default
        value of `timescale / reltol` is used.
    """

    time_scale: Expression
    max_time: Expression | None = None


@serializable
@dataclass(frozen=True)
class ReactionModel(OdeModel):
    parameters: dict[str, Parameter] = field(default_factory=dict)
    assignments: dict[str, Assignment] = field(default_factory=dict)
    bound_variables: dict[str, BoundVariable] = field(default_factory=dict)
    relationships: list[Expression] = field(default_factory=list)
    compartments: dict[str, Compartment] = field(default_factory=dict)
    states: dict[str, State] = field(default_factory=dict)
    reactions: list[Reaction] = field(default_factory=list)
    routes: dict[str, Route] = field(default_factory=dict)
    events: list[Event] = field(default_factory=list)
    initialization: Initialization = InitialValue()
    time_unit: Unit = "1"
