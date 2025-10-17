"""These are needed to support the v1 ReactionModel data structure in the Assess client."""

__all__ = ["LegacyReactionModel", "LegacyRouteSchedule", "LegacySolverConfiguration"]

import math
from abc import abstractmethod
from dataclasses import dataclass
from typing import Literal

from serialite import abstract_serializable, field, serializable

from . import reaction_model as rm
from .expression import Expression, StaticExpression, Unit
from .ode_model import OdeModel, Schedule
from .solver_configuration import BdfSolver, KluSolver, SolverConfiguration, SpgmrSolver


def ascribe_unit(expression: Expression, unit: Unit | None) -> Expression:
    # For parameters, asssignments, etc., v1 allowed literals to be assigned to any unit.  Here we explicitly ascribe
    # the unit (if provided) to the expression to support this.
    if unit is None:
        return expression

    # Could use ._helper.maybe_add_parentheses for the unit, but still would potentially need wrap the expression.
    # Just wrap everything in parentheses.
    return f"({expression}):({unit})"


def range_to_count_expression(*, start: Expression, stop: Expression, interval: Expression) -> Expression:
    if stop == "inf":
        return "inf"

    # Like ascribe_unit above, this is raw string substitution; use lots of parentheses.
    return f"floor((({stop}) - ({start})) / ({interval})) + 1"


@serializable
@dataclass(frozen=True)
class LegacyParameter:
    value: StaticExpression
    unit: Unit | None = None

    def to_v2_parameter(self) -> rm.Parameter:
        return rm.Parameter(value=ascribe_unit(self.value, self.unit), unit=self.unit)


@serializable
@dataclass(frozen=True)
class LegacyAssignment:
    definition: Expression
    unit: Unit | None = None

    def to_v2_assignment(self) -> rm.Assignment:
        return rm.Assignment(definition=ascribe_unit(self.definition, self.unit), unit=self.unit)


@serializable
@dataclass(frozen=True)
class LegacyCompartment:
    dimension: Literal[0, 1, 2, 3]
    size: Expression
    unit: Unit | None = None

    def to_v2_compartment(self) -> rm.Compartment:
        return rm.Compartment(dimension=self.dimension, size=ascribe_unit(self.size, self.unit), unit=self.unit)


@serializable
@dataclass(frozen=True)
class LegacyState:
    initial_value: Expression
    compartment: str | None = None
    unit: Unit | None = None

    def to_v2_state(self) -> rm.State:
        return rm.State(
            initial_value=ascribe_unit(self.initial_value, self.unit),
            compartment=self.compartment,
            unit=self.unit,
        )


@abstract_serializable
class LegacyRouteSchedule:
    @abstractmethod
    def to_v2_schedule(self) -> Schedule:
        pass


@serializable
@dataclass(frozen=True)
class EmptyRouteSchedule(LegacyRouteSchedule):
    def to_v2_schedule(self) -> Schedule:
        return rm.EmptySchedule()


@serializable
@dataclass(frozen=True, kw_only=True)
class RepeatedRouteSchedule(LegacyRouteSchedule):
    start: Expression = 0.0
    stop: Expression = "inf"
    interval: Expression
    amount: Expression
    duration: Expression = 0.0

    def to_v2_schedule(self) -> Schedule:
        return rm.RepeatSchedule(
            start=self.start,
            interval=self.interval,
            n=range_to_count_expression(start=self.start, stop=self.stop, interval=self.interval),
            amount=self.amount,
            duration=None if self.duration == 0.0 else self.duration,
        )


@serializable
@dataclass(frozen=True, kw_only=True)
class IteratedRouteSchedule(LegacyRouteSchedule):
    start: Expression = 0.0
    interval: Expression
    n: Expression = "inf"
    amount: Expression
    duration: Expression = 0.0

    def to_v2_schedule(self) -> Schedule:
        return rm.RepeatSchedule(
            start=self.start,
            interval=self.interval,
            n=self.n,
            amount=self.amount,
            duration=None if self.duration == 0.0 else self.duration,
        )


@serializable
@dataclass(frozen=True)
class ListRouteSchedule(LegacyRouteSchedule):
    times: list[Expression]
    amounts: list[Expression]
    durations: list[Expression] | None = None

    def to_v2_schedule(self) -> Schedule:
        return rm.ListSchedule(
            times=self.times,
            amounts=self.amounts,
            durations=self.durations,
        )


@abstract_serializable
class LegacyJumpSchedule:
    @abstractmethod
    def to_v2_schedule(self) -> Schedule:
        pass


@serializable
@dataclass(frozen=True, kw_only=True)
class RepeatedJumpSchedule(LegacyJumpSchedule):
    start: Expression = 0.0
    stop: Expression = "inf"
    interval: Expression

    def to_v2_schedule(self) -> Schedule:
        return rm.RepeatSchedule(
            start=self.start,
            interval=self.interval,
            n=range_to_count_expression(start=self.start, stop=self.stop, interval=self.interval),
        )


@serializable
@dataclass(frozen=True, kw_only=True)
class IteratedJumpSchedule(LegacyJumpSchedule):
    start: Expression = 0.0
    interval: Expression
    n: Expression = "inf"

    def to_v2_schedule(self) -> Schedule:
        return rm.RepeatSchedule(
            start=self.start,
            interval=self.interval,
            n=self.n,
        )


@serializable
@dataclass(frozen=True)
class ListJumpSchedule(LegacyJumpSchedule):
    times: list[Expression]

    def to_v2_schedule(self) -> Schedule:
        return rm.ListSchedule(times=self.times)


@serializable
@dataclass(frozen=True)
class LegacyRoute:
    effects: dict[str, Expression]
    schedule: LegacyRouteSchedule
    amount_unit: Unit | None = None

    def to_v2_route(self) -> rm.Route:
        effects = {target: rm.DoseEffect(value) for target, value in self.effects.items()}
        return rm.Route(
            effects=effects,
            schedule=self.schedule.to_v2_schedule(),
            amount_unit=self.amount_unit,
        )


@serializable
@dataclass(frozen=True)
class LegacyJump:
    effects: dict[str, Expression]
    schedule: LegacyJumpSchedule

    def to_v2_route(self) -> rm.Route:
        effects = {target: rm.JumpEffect(value) for target, value in self.effects.items()}
        return rm.Route(
            effects=effects,
            schedule=self.schedule.to_v2_schedule(),
        )


@serializable
@dataclass(frozen=True)
class LegacyReactionModel(OdeModel):
    parameters: dict[str, LegacyParameter] = field(default_factory=dict)
    assignments: dict[str, LegacyAssignment] = field(default_factory=dict)
    compartments: dict[str, LegacyCompartment] = field(default_factory=dict)
    states: dict[str, LegacyState] = field(default_factory=dict)
    reactions: list[rm.Reaction] = field(default_factory=list)
    routes: dict[str, LegacyRoute] = field(default_factory=dict)
    jumps: dict[str, LegacyJump] = field(default_factory=dict)
    events: list[rm.Event] = field(default_factory=list)
    initialization: rm.Initialization = rm.InitialValue()
    time_unit: Unit = "1"

    def to_v2_model(self) -> rm.ReactionModel:
        converted_parameters = {name: parameter.to_v2_parameter() for name, parameter in self.parameters.items()}
        converted_assignments = {name: assignment.to_v2_assignment() for name, assignment in self.assignments.items()}
        converted_compartments = {
            name: compartment.to_v2_compartment() for name, compartment in self.compartments.items()
        }
        converted_states = {name: state.to_v2_state() for name, state in self.states.items()}
        converted_routes = {name: route.to_v2_route() for name, route in self.routes.items()}
        converted_jumps = {name: jump.to_v2_route() for name, jump in self.jumps.items()}

        return rm.ReactionModel(
            parameters=converted_parameters,
            assignments=converted_assignments,
            compartments=converted_compartments,
            states=converted_states,
            reactions=self.reactions,
            routes=converted_routes | converted_jumps,
            events=self.events,
            initialization=self.initialization,
            time_unit=self.time_unit,
        )


@serializable
@dataclass(frozen=True)
class LegacySolverConfiguration:
    ode_solver: Literal["BDF"] = "BDF"
    linear_solver: Literal["KLU", "SPGMR"] = "KLU"
    reltol: float = 1e-6
    abstol: float = 1e-9
    maxstep: float = math.inf
    maxord: int = 5
    nonnegative: bool | dict[str, bool] = False
    gradient_method: Literal["forward", "adjoint"] = "forward"

    def to_v2_solver_configuration(self) -> SolverConfiguration:
        match self.linear_solver:
            case "KLU":
                linear_solver = KluSolver()
            case "SPGMR":
                linear_solver = SpgmrSolver()
            case _:
                raise NotImplementedError()

        return SolverConfiguration(
            ode_solver=BdfSolver(
                linear_solver=linear_solver,
                relative_tolerance=self.reltol,
                absolute_tolerance=self.abstol,
                max_step=self.maxstep,
                max_order=self.maxord,
            ),
            nonnegative=self.nonnegative,
            gradient_method=self.gradient_method,
        )
