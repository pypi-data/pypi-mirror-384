__all__ = [
    "AssessParameterScan1D",
    "AssessParameterScan1DResult",
    "AssessParameterScan2D",
    "AssessParameterScan2DResult",
    "TargetCriterion",
]

from dataclasses import dataclass, field
from typing import Any, Literal

from serialite import serializable

from .expression import Expression
from .ode_model import Schedule
from .solver_configuration import SolverConfiguration
from .times import Times

ColorScaleTuple = list[list[str | float]]


@serializable
@dataclass(frozen=True, slots=True)
class Axis:
    automargin: bool | None = None
    range: list[float] | None = None
    rangemode: str | None = None
    tickmode: str | None = None
    tickvals: list[float] | None = None
    ticktext: list[float] | None = None
    title: str | None = None
    type: str | None = None
    zeroline: bool | None = None


@serializable
@dataclass(frozen=True, slots=True)
class Line:
    color: str | None = None
    dash: str | None = None


@serializable
@dataclass(frozen=True, slots=True)
class Font:
    family: str | None = None
    color: str | None = None
    size: float | None = None


@serializable
@dataclass(frozen=True, slots=True)
class Contours:
    coloring: str | None = None
    showlabels: bool | None = None
    labelfont: Font | None = None
    start: float | None = None
    end: float | None = None
    size: float | None = None


@serializable
@dataclass(frozen=True, slots=True)
class Trace:
    x: list[list[float]] | list[float] | None = None
    y: list[list[float]] | list[float] | None = None
    z: list[list[float]] | None = None
    name: str | float | None = None
    hoverinfo: str | None = None
    line: Line | None = None
    mode: str | None = None
    text: list[float] | None = None  # TODO: explain float
    type: str | None = None
    contours: Contours | None = None

    xgap: float | None = None
    ygap: float | None = None
    zauto: bool | None = None
    zmin: float | None = None
    zmax: float | None = None
    colorscale: str | ColorScaleTuple | None = None


@serializable
@dataclass(frozen=True, slots=True)
class Text:
    text: str | None = None
    font: Font | None = None


@serializable
@dataclass(frozen=True, slots=True)
class Legend:
    title: Text | None = None
    font: Font | None = None
    orientation: Literal["v", "h", None] = None
    y: float | None = None


@serializable
@dataclass(frozen=True, slots=True)
class Layout:
    legend: Legend | None = None
    showlegend: bool | None = None
    title: str | None = None
    xaxis: Axis | None = None
    yaxis: Axis | None = None


@serializable
@dataclass(frozen=True, slots=True)
class PlotlyPlot:
    data: list[Trace]
    layout: Layout


@serializable
@dataclass(frozen=True, slots=True)
class ViewWindow:
    x_lower_limit: float | None
    x_upper_limit: float | None
    y_lower_limit: float | None
    y_upper_limit: float | None


@serializable
@dataclass(frozen=True)
class AssessPlot:
    plot: Any
    type: Literal["index", "dependent", "detached"]


@serializable
@dataclass(frozen=True, slots=True)
class TargetCriterion:
    value: Expression
    time_value: Expression
    target: float


@serializable
@dataclass(frozen=True, kw_only=True)
class TransformedParameter:
    value: float
    transform: Expression


@serializable
@dataclass(frozen=True)
class PlotOptions:
    criterion_value_max: float | None = None
    criterion_value_min: float | None = None
    criterion_value_name: str | None = None

    show_legend: bool = True
    legend_title: str | None = None
    legend_orientation: str | None = None

    output: str | None = None

    title: str | None = None

    x_scale: str | None = None
    x_title: str | None = None
    x_transform: str | None = "1"
    x_unit: str | None = None

    y_scale: str | None = None
    y_title: str | None = None
    y_transform: str | None = "1"
    y_unit: str | None = None


@serializable
@dataclass(frozen=True)
class Plot:
    type: Literal[
        "scan1d_response",
        "scan2d_heatmap",
        "scan2d_contour",
        "scan2d_feasible_contour",
        "criterion_plot",
        "output_plot",
    ]
    options: PlotOptions


@serializable
@dataclass(frozen=True, kw_only=True)
class AssessSimulation:
    model_id: str
    transformed_parameters: dict[str, TransformedParameter]
    route_schedules: dict[str, Schedule]
    output: Times
    target_criterion: TargetCriterion
    plots: list[Plot] | None = field(default_factory=list)
    configuration: SolverConfiguration = SolverConfiguration()


@serializable
@dataclass(frozen=True, slots=True)
class AssessSimulationResult:
    criterion_value: float
    criterion_time_value: list[float]
    plots: list[AssessPlot] | None


@serializable
@dataclass(frozen=True, kw_only=True)
class AssessParameterScan1D:
    model_id: str
    transformed_parameters: dict[str, TransformedParameter]
    route_schedules: dict[str, Schedule]
    scan_parameter_1: str
    lower_limit: float
    upper_limit: float
    n: int
    scale: Literal["linear", "log"]
    output: Times
    target_criterion: TargetCriterion
    plots: list[Plot] | None = field(default_factory=list)
    optima_method: Literal["brentq", "cubic_spline"] = "brentq"
    configuration: SolverConfiguration = SolverConfiguration()


@serializable
@dataclass(frozen=True)
class AssessParameterScan1DResult:
    scan_values: list[float]
    criterion_values: list[float]
    criterion_time_values: list[list[float]]
    optima: list[float]
    optimal_indices: list[int]
    plots: list[AssessPlot] | None


@serializable
@dataclass(frozen=True, kw_only=True)
class AssessParameterScan2D:
    model_id: str
    transformed_parameters: dict[str, TransformedParameter]
    route_schedules: dict[str, Schedule]
    scan_parameter_1: str
    scan_parameter_2: str
    lower_limit_1: float
    lower_limit_2: float
    upper_limit_1: float
    upper_limit_2: float
    n_1: int
    n_2: int
    scale_1: str
    scale_2: str
    output: Times
    target_criterion: TargetCriterion
    plots: list[Plot] | None = None
    configuration: SolverConfiguration = SolverConfiguration()


@serializable
@dataclass(frozen=True)
class AssessParameterScan2DResult:
    scan_values_1: list[float]
    scan_values_2: list[float]
    criterion_values: list[float]
    criterion_time_values: list[list[float]]
    plots: list[AssessPlot] | None
    optima_exists: bool
