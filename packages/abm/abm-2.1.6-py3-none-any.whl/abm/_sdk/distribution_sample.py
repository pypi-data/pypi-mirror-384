__all__ = [
    "Distribution",
    "DistributionSample",
    "GridDistribution",
    "LatinUniformDistribution",
    "ListDistribution",
    "LogGridDistribution",
    "LogNormalDistribution",
    "LogUniformDistribution",
    "MultivariateLogNormalDistribution",
    "MultivariateNormalDistribution",
    "NormalDistribution",
    "ProductDistribution",
    "UniformDistribution",
    "ZipDistribution",
]

from dataclasses import dataclass
from typing import Literal

from serialite import abstract_serializable, serializable

from .expression import Expression


@abstract_serializable
class Distribution:
    __slots__ = ()


@serializable
@dataclass(frozen=True, slots=True)
class ListDistribution(Distribution):
    name: str
    values: list[Expression]
    mode: Literal["cycle", "random"] = "cycle"


@serializable
@dataclass(frozen=True, slots=True)
class GridDistribution(Distribution):
    name: str
    lower: Expression
    upper: Expression
    n: int
    mode: Literal["cycle", "random"] = "cycle"


@serializable
@dataclass(frozen=True, slots=True)
class LogGridDistribution(Distribution):
    name: str
    lower: Expression
    upper: Expression
    n: int
    mode: Literal["cycle", "random"] = "cycle"


@serializable
@dataclass(frozen=True, slots=True)
class UniformDistribution(Distribution):
    name: str
    lower: Expression
    upper: Expression


@serializable
@dataclass(frozen=True, slots=True)
class LogUniformDistribution(Distribution):
    name: str
    lower: Expression
    upper: Expression


@serializable
@dataclass(frozen=True, slots=True)
class LatinUniformDistribution(Distribution):
    name: str
    lower: Expression
    upper: Expression
    n: int


@serializable
@dataclass(frozen=True, slots=True)
class NormalDistribution(Distribution):
    name: str
    mean: Expression
    standard_deviation: Expression
    lower: Expression = "-inf"
    upper: Expression = "inf"


@serializable
@dataclass(frozen=True, slots=True)
class LogNormalDistribution(Distribution):
    name: str
    geometric_mean: Expression
    logspace_standard_deviation: Expression
    lower: Expression = "0.0"
    upper: Expression = "inf"


@serializable
@dataclass(frozen=True, slots=True)
class MultivariateNormalDistribution(Distribution):
    names: list[str]
    mean: list[Expression]
    variance: list[list[Expression]]


@serializable
@dataclass(frozen=True, slots=True)
class MultivariateLogNormalDistribution(Distribution):
    names: list[str]
    geometric_mean: list[Expression]
    logspace_variance: list[list[Expression]]


@serializable
@dataclass(frozen=True, slots=True)
class ZipDistribution(Distribution):
    """Zip multiple distributions into a single table.

    The nth element of this distribution is the combination of the nth elements from all member distributions.
    """

    distributions: list[Distribution]
    n: int | None = None


@serializable
@dataclass(frozen=True, slots=True)
class ProductDistribution(Distribution):
    """Take the Cartesian product of multiple distributions.

    All possible combinations of elements from each distribution is generated.
    """

    distributions: list[Distribution]


@serializable
@dataclass(frozen=True, kw_only=True)
class DistributionSample:
    """Task definition for sampling from a distribution."""

    distribution: Distribution
    seed: int
    n: int
    rng: Literal["mt", "pcg64"] = "pcg64"
    filter: Expression | None = None
