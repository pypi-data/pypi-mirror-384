from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import tabeline as tl

from .._sdk.data_frame import DataFrame
from .._sdk.expression import StaticExpression, Unit
from .._sdk.times import LinspaceTimes
from .._units.ast import Atom, Dimensionless, Dynamic, Parenthesis
from .._units.parser import un

SingleUnitType = Parenthesis | Dimensionless | Atom | Dynamic

DataFrameLike = pd.DataFrame | tl.DataFrame | DataFrame
PathLike = str | Path


# A function to replace asterisk with None in a DataFrame
def replace_asterisk_with_none(df: tl.DataFrame) -> tl.DataFrame:
    for column in df.column_names:
        if "*" in df[:, column]:
            kw = {column: f"if_else({column} != '*', {column})"}
            df = df.mutate(**kw)
    return df


# A function to replace asterisk with None in a DataFrame
def replace_none_with_asterisk(df: tl.DataFrame, label_columns=set[str]) -> tl.DataFrame:
    df_columns = set(df.column_names)
    for column in label_columns:
        if column in df_columns and None in df[:, column]:
            kw = {column: f"if_else({column} == None, '*', {column})"}
            df = df.mutate(**kw)
    return df


def replace_empty_string_with_none(data: dict[str, list]) -> dict[str, list]:
    for column, values in data.items():
        for i, value in enumerate(values):
            if value == "":
                data[column][i] = None
    return data


def find_duplicate_keys(results: list[dict]) -> list[str]:
    seen_keys = set()
    duplicated_keys = []
    for d in results:
        key = next(iter(d))
        if key in seen_keys:
            duplicated_keys.append(key)
            continue
        seen_keys.add(key)
    return duplicated_keys


def broadcast(x, n, x_name):
    if len(x) == 1:
        x = x * n
    elif len(x) != n:
        raise ValueError(f"Expected length of 1 or {n} of {x_name}, got {len(x)}")
    return x


@dataclass(frozen=True)
class UnittedLinSpace:
    start: float | int
    stop: float | int
    n: int
    unit: Unit | None = None

    def __post_init__(self):
        if not isinstance(self.start, float | int):
            raise ValueError("start must be of type float")
        if not isinstance(self.stop, float | int):
            raise ValueError("stop must be of type float")
        if not isinstance(self.n, int):
            raise ValueError("n must be of type int")

    def to_list(self) -> list[StaticExpression]:
        if self.unit is None:
            return np.linspace(self.start, self.stop, self.n).tolist()
        else:
            return [f"{v}:{self.unit}" for v in np.linspace(self.start, self.stop, self.n)]

    def to_linspace_times(self) -> LinspaceTimes:
        if self.unit is None:
            return LinspaceTimes(start=self.start, stop=self.stop, n=self.n)
        else:
            return LinspaceTimes(start=f"{self.start}:{self.unit}", stop=f"{self.stop}:{self.unit}", n=self.n)


@dataclass(frozen=True)
class UnittedLogSpace:
    start: float | int
    stop: float | int
    n: int
    unit: Unit | None = None

    def __post_init__(self):
        if not isinstance(self.start, float | int):
            raise ValueError("start must be of type float")
        if not isinstance(self.stop, float | int):
            raise ValueError("stop must be of type float")
        if not isinstance(self.n, int):
            raise ValueError("n must be of type int")

    def to_list(self) -> list[StaticExpression]:
        start = np.log10(self.start)
        stop = np.log10(self.stop)
        if self.unit is None:
            return np.logspace(start, stop, self.n).tolist()
        else:
            return [f"{x}:{self.unit}" for x in np.logspace(start, stop, self.n)]


def linspace(start: float, stop: float, count: int, unit: Unit | None = None) -> UnittedLinSpace:
    """Create a list of evenly spaced numbers.

    Parameters
    ----------
    start : float
        The starting value of the sequence.
    stop : float
        The end value of the sequence.
    count : int
        Number of samples to generate.
    unit : str | None = None
        The unit of the numbers. If None, the numbers are dimensionless.

    output:
    -------
    UnittedLinSpace
    """

    # if unit is None it is dimensionless
    return UnittedLinSpace(start, stop, count, unit)


def logspace(start: float, stop: float, count: int, unit: Unit | None = None) -> UnittedLogSpace:
    """Create a list of numbers spaced evenly on a log scale.

    parameters
     ----------
    start : float
        The starting value of the sequence.
    stop : float
        The end value of the sequence.
    count : int
        Number of samples to generate.
    unit : str | None = None
        The unit of the numbers. If None, the numbers are dimensionless.

    output:
    -------
    UnittedLogSpace
    """

    return UnittedLogSpace(start, stop, count, unit)


def maybe_add_parentheses(unit: str | None) -> str | None:
    if unit is None:
        return unit
    parsed_unit = un(unit)
    if isinstance(parsed_unit, SingleUnitType):
        return unit
    else:
        return f"({unit})"


@np.errstate(divide="ignore")  # Squelch any log(0.0) warnings
def scale_parameter(is_log: bool, value: float) -> float:
    """Transformation θ(U) from a raw value U to the coordinate system of the parameter"""
    if is_log:
        return np.log(value).item()
    else:
        return value


@np.errstate(over="ignore")  # Squelch any exp(big) warnings
def unscale_parameter(is_log: bool, value: float) -> float:
    """Inverse transformation U(θ) of scale_parameter"""
    if is_log:
        return np.exp(value).item()
    else:
        return value
