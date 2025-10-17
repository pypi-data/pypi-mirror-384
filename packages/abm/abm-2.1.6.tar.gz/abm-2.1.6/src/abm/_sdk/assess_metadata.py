__all__ = [
    "AssessMetadata",
    "DiscreteValue",
    "Metric",
    "MetricKey",
    "MetricTarget",
    "OutputPlot",
    "OutputTimes",
    "Parameter",
    "ParameterTransform",
    "PlotTransform",
    "Qualifier",
    "QualifierValue",
    "Scan",
    "Schedule",
]

from dataclasses import dataclass, field
from enum import StrEnum, auto
from typing import Literal

from serialite import serializable

from .expression import Expression
from .ode_model import Schedule as OdeModelSchedule
from .times import Times


class ScaleType(StrEnum):
    linear = auto()
    log = auto()


@serializable
@dataclass(frozen=True, slots=True, kw_only=True)
class Scan:
    parameter: str  # A model parameter name
    n: int = 11
    scale: ScaleType = ScaleType.log


@serializable
@dataclass(frozen=True, slots=True, kw_only=True)
class ParameterTransform:
    id: str | None  # Should also be human-readable
    expression: Expression
    default_lower_limit: float | None = None
    default_upper_limit: float | None = None


@serializable
@dataclass(frozen=True, slots=True, kw_only=True)
class Schedule:
    id: str
    schedule: OdeModelSchedule


@serializable
@dataclass(frozen=True, slots=True)
class DiscreteValue:
    name: str  # Human-readable name; formerly `label`
    value: int | float


@serializable
@dataclass(frozen=True, slots=True, kw_only=True)
class Parameter:
    id: str  # A model parameter name
    name: str = ""  # Human-readable name
    symbol: str = ""
    description: str = ""
    default_value: int | float
    is_global: bool = False
    transforms: list[ParameterTransform] = field(default_factory=list)
    discrete_values: list[DiscreteValue] = field(default_factory=list)


@serializable
@dataclass(frozen=True, slots=True)
class QualifierValue:
    id: str
    name: str = ""


@serializable
@dataclass(frozen=True, slots=True, kw_only=True)
class Qualifier:
    name: str = ""
    description: str = ""
    values: list[QualifierValue]


@serializable
@dataclass(frozen=True, slots=True, kw_only=True)
class MetricTarget:
    reduced: str
    varying: str | None = None
    description: str = ""


@serializable
@dataclass(frozen=True, slots=True)
class MetricKey:
    # Keys are tuples of option ids; represents an element of the Cartesian product the containing metric's qualifiers.
    values: list[str]

    def __hash__(self) -> int:
        return hash(tuple(self.values))


@serializable
@dataclass(frozen=True, slots=True, kw_only=True)
class PlotTransform:
    id: str | None  # Should also be human-readable
    expression: Expression


@serializable
@dataclass(frozen=True, slots=True, kw_only=True)
class Metric:  # c.f. `Criterion` in legacy version
    id: str
    name: str = ""  # Human-readable name
    description: str = ""
    default_threshold: float
    unit: str
    qualifiers: list[Qualifier] = field(default_factory=list)
    mapping: dict[MetricKey, MetricTarget] = field(default_factory=dict)
    plot_lower_limit: float | None = None
    plot_upper_limit: float | None = None
    plot_scale: ScaleType = ScaleType.log
    plot_transforms: list[PlotTransform] = field(default_factory=list)


@serializable
@dataclass(frozen=True, slots=True, kw_only=True)
class OutputTimes:
    id: str
    name: str = ""  # Human-readable name
    times: Times


@serializable
@dataclass(frozen=True, slots=True, kw_only=True)
class OutputPlot:
    id: str
    title: str = ""
    description: str = ""
    scale: ScaleType = ScaleType.log
    transforms: list[PlotTransform] = field(default_factory=list)
    is_selected: bool = False


@serializable
@dataclass(frozen=True, slots=True, kw_only=True)
class SimulationConfiguration:
    # Essentially a subset of compute.SolverConfiguration options
    linear_solver: Literal["KLU", "SPGMR"] = "KLU"
    abstol: float = 1e-9
    reltol: float = 1e-6
    maxord: Literal[1, 2, 3, 4, 5] = 5


@serializable
@dataclass(frozen=True, slots=True, kw_only=True)
class AssessMetadata:
    model_id: str
    name: str = ""
    pack: str = ""
    headline: str = ""
    description: str = ""
    documentation: str = ""
    thumbnail: str | None = None  # ID to some asset on /images/
    diagram: str | None = None  # As above
    pharmacology_diagram: str | None = None  # As above
    tags: list[str] = field(default_factory=list)
    parameters: list[Parameter] = field(default_factory=list)
    schedules: list[Schedule] = field(default_factory=list)
    metrics: list[Metric] = field(default_factory=list)
    default_scan_1: Scan
    default_scan_2: Scan
    output_times: list[OutputTimes] = field(default_factory=list)
    output_plots: list[OutputPlot] = field(default_factory=list)
    plot_time_transform: PlotTransform
    default_configuration: SimulationConfiguration = SimulationConfiguration()
