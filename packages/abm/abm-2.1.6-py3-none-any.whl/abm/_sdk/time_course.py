__all__ = ["TimeCourse"]

from dataclasses import dataclass

from serialite import serializable

from .expression import Unit


@serializable
@dataclass(frozen=True, slots=True, kw_only=True)
class Output:
    unit: Unit


@serializable
@dataclass(frozen=True, slots=True, kw_only=True)
class Constant(Output):
    value: float


@serializable
@dataclass(frozen=True, slots=True, kw_only=True)
class Variable(Output):
    values: list[float]


@serializable
@dataclass(frozen=True, slots=True)
class TimeCourse:
    times: Variable
    outputs: dict[str, Constant | Variable]
