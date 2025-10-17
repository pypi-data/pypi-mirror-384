__all__ = [
    "AssessOutputTime",
    "Criterion",
    "DropDown",
    "LegacyAssessMetadata",
    "LegacyMetadataParameter",
    "Modifier",
    "ModifierOption",
    "OutputPlotOption",
    "OutputPlotUnit",
    "Reducer",
    "UnitOption",
]

from dataclasses import dataclass, field
from typing import Literal

from serialite import serializable

from .expression import Expression
from .legacy import LegacyRouteSchedule
from .ode_model import Schedule


@serializable
@dataclass(frozen=True)
class DropDown:
    label: str
    value: str


@serializable
@dataclass(frozen=True)
class UnitOption:
    unit: str | None
    transform: str
    default_lower_limit: float | None
    default_upper_limit: float | None


@serializable
@dataclass(frozen=True)
class LegacyMetadataParameter:
    id: str
    name: str
    description: str
    symbol: str
    default_value: str
    is_global: bool
    default_unit: str | None
    units: list[UnitOption]
    dropdown_items: list[DropDown]


@serializable
@dataclass(frozen=True)
class ModifierOption:
    name: str
    value: str


@serializable
@dataclass(frozen=True)
class Modifier:
    id: str
    name: str
    options: list[ModifierOption]
    description: str | None = None


@serializable
@dataclass(frozen=True)
class Reducer:
    id: str
    name: str
    expression_template: str
    description: str | None = None


@serializable
@dataclass(frozen=True)
class Criterion:
    id: str
    time_value_template: str  # JavaScript template literal that, upon substitution is an Expression
    modifiers: list[Modifier]
    reducers: list[Reducer]
    name: str
    default_threshold: float
    value_unit: str
    value_min: float
    value_max: float
    value_scale: str
    description: str


@serializable
@dataclass(frozen=True)
class AssessOutputTime:
    name: str
    expression: Expression


@serializable
@dataclass(frozen=True)
class OutputPlotUnit:
    transform: Expression  # Numeric expression --> model_output * eval(transform, model.parameters) = plot_output


@serializable
@dataclass(frozen=True)
class OutputPlotOption:
    title: str
    unit: str
    units: dict[str, OutputPlotUnit]
    scale: str
    description: str = ""


@serializable
@dataclass(frozen=True)
class LegacyAssessMetadata:
    id: str
    pack: str
    model_id: str
    report_id: str
    name: str
    headline: str
    description: str
    thumbnail: str
    diagram: str
    pharmacology_diagram: str | None
    documentation: str
    parameters: list[LegacyMetadataParameter]
    routes: dict[str, Schedule] | dict[str, LegacyRouteSchedule]
    criteria: list[Criterion]
    default_criterion: str
    default_scan_parameter_1: str
    default_scan_parameter_2: str
    default_n_1: int
    default_n_2: int
    default_scale_1: Literal["linear", "log"]
    default_scale_2: Literal["linear", "log"]
    default_route: str
    default_linear_solver: Literal["KLU", "SPGMR"]
    default_optima_method: Literal["brentq", "cubic_spline"]
    default_abstol: float
    default_reltol: float
    default_maxord: Literal[1, 2, 3, 4, 5]
    output_interval: Expression
    output_starts: dict[str, AssessOutputTime]
    output_stops: dict[str, AssessOutputTime]
    output_n: int  # This n is the number of timepoints in the replicated LinspaceTimes
    default_output_start: str
    default_output_stop: str
    output_plot_options: dict[str, OutputPlotOption]
    selected_output_plots: list[str]
    plot_time_unit: str
    plot_time_transform: float  # seconds -> plot_time_unit conversion
    tags: list[str] = field(default_factory=list)
