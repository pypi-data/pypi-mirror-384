__all__ = ["BdfSolver", "KluSolver", "LinearSolver", "OdeSolver", "SolverConfiguration", "SpgmrSolver"]

import math
from dataclasses import dataclass
from typing import Literal

from serialite import NonnegativeIntegerSerializer, OptionalSerializer, abstract_serializable, field, serializable


@abstract_serializable
@dataclass(frozen=True, kw_only=True)
class LinearSolver:
    pass


@serializable
@dataclass(frozen=True, kw_only=True)
class KluSolver(LinearSolver):
    pass


@serializable
@dataclass(frozen=True, kw_only=True)
class SpgmrSolver(LinearSolver):
    preconditioner_direction: Literal["none", "left", "right", "both"] = "right"
    gram_schmidt_variant: Literal["modified", "classical"] = "modified"
    krylov_dimension: int = 10
    max_restarts: int = 0


@abstract_serializable
@dataclass(frozen=True, kw_only=True)
class OdeSolver:
    pass


@serializable
@dataclass(frozen=True, kw_only=True)
class BdfSolver(OdeSolver):
    """Configuration for the backward differentiation formula ODE solver.

    Attributes
    ----------
    linear_solver : `LinearSolver`, default=`KluSolver()`
        Linear solver and relevant options used to solve the implicit formula for
        each integration step. Generally this should not be changed from the
        default.
    relative_tolerance : `float`, default=1e-6
        Relative tolerance of the integration.
    absolute_tolerance : `float`, default=1e-9
        Absolute tolerance of the integration.
    max_step : `float`, default=inf
        Maximum time step allowed during integration. Generally, this should not
        be changed from the default (unbounded).
    max_order : `int`, default=5
        Maximum order of the linear multistep formulas used by the ODE solver.
        Setting to a lower value results in smaller but more stable time steps.
        Generally it is recommended to use the largest value that converges.
    max_steps : `int` or `None`, default=`None`
        Maximum number of integration steps to take. If `None`, the integration
        will continue until the end time is reached. If an integer, the
        integration will stop after the specified number of steps.
    """

    linear_solver: LinearSolver = KluSolver()
    relative_tolerance: float = 1e-6
    absolute_tolerance: float = 1e-9
    max_step: float = math.inf
    max_order: int = 5
    max_steps: int | None = field(serializer=OptionalSerializer(NonnegativeIntegerSerializer()), default=None)


@serializable
@dataclass(frozen=True, kw_only=True)
class SolverConfiguration:
    """Configuration for the ODE solver.

    Attributes
    ----------
    ode_solver : `OdeSolver`, default=`BdfSolver()`
        ODE solver and related configuration settings to use for the integration.
        Generally this should not be changed from the default.
    nonnegative : `bool` or `dict[str, bool]`, default=`False`
        Substitute 0 for negative values in the indicated states when evaluating
        the ODE right-hand side. This is useful for avoiding numerical
        difficulties with model expressions like `sqrt` that are not real or not
        defined for negative values. If `False`, no states are substituted if
        negative. If `True`, all states are substituted if negative. If a
        `dict[str, bool]` is provided, any keys with `True` values are
        interpreted as state names to be substituted; any states not appearing
        in the dictionary are not substituted.
    gradient_method : `Literal["forward", "adjoint"]`, default=`"forward"`
        Method to use for calculating an objective gradient with respect to model
        model parameters.  Ignored where not relevant (e.g. in simulation)
    """

    ode_solver: OdeSolver = BdfSolver()
    nonnegative: bool | dict[str, bool] = False
    gradient_method: Literal["forward", "adjoint"] = "forward"
