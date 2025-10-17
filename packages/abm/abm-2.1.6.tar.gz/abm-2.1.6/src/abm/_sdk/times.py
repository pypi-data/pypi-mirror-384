__all__ = ["LinspaceTimes", "ListTimes", "ReplicateTimes", "Times"]

from dataclasses import dataclass, field

from serialite import abstract_serializable, serializable

from .expression import Expression


@abstract_serializable
class Times:
    pass


@serializable
@dataclass(frozen=True)
class ListTimes(Times):
    times: list[Expression]


@serializable
@dataclass(frozen=True, kw_only=True)
class LinspaceTimes(Times):
    start: Expression = 0.0
    stop: Expression
    n: int = 51


@serializable
@dataclass(frozen=True)
class ReplicateTimes(Times):
    times: Times
    start: Expression = field(default=0.0, kw_only=True)
    stop: Expression = field(kw_only=True)
    interval: Expression | None = field(default=None, kw_only=True)
