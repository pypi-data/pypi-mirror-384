from dataclasses import dataclass
from typing import Literal

from serialite import field, serializable

from abm._sdk.legacy import LegacyRouteSchedule, LegacySolverConfiguration
from abm._sdk.ode_model import Schedule
from abm._sdk.solver_configuration import SolverConfiguration


@serializable
@dataclass(frozen=True)
class UnitData:
    name: str
    transform: str


@serializable
@dataclass(frozen=True)
class ModelParameterData:
    name: str
    units: dict[str, UnitData]  # Cannot be empty
    default_unit_id: str
    default_value: float
    symbol: str | None = None  # LaTeX math string
    description: str | None = None


@serializable
@dataclass(frozen=True)
class ModelRouteData:
    name: str
    description: str | None = None


@serializable
@dataclass(frozen=True)
class ModifierOption:
    name: str


@serializable
@dataclass(frozen=True)
class AssessModifierData:
    name: str
    options: dict[str, ModifierOption]  # nonempty
    description: str | None = None


@serializable
@dataclass(frozen=True)
class AssessReducerData:
    name: str
    expression_template: str
    description: str | None = None


@serializable
@dataclass(frozen=True)
class AssessCriterionData:
    name: str
    time_value_template: str
    modifiers: dict[str, AssessModifierData] | None
    reducers: dict[str, AssessReducerData]  # nonempty
    default_threshold: float
    unit: str
    min: float
    max: float
    scale: Literal["log", "linear"]
    description: str | None = None


@serializable
@dataclass(frozen=True)
class AssessOutputTime:
    name: str
    expression: str


@serializable
@dataclass(frozen=True)
class OutputPlotUnit:
    name: str
    transform: str  # Numeric expression --> model_output * eval(transform, model.parameters) = plot_output


@serializable
@dataclass(frozen=True)
class OutputPlotOption:
    name: str
    units: dict[str, OutputPlotUnit]  # nonempty
    default_unit_id: str
    scale: Literal["log", "linear"]
    default_is_visible: bool = False
    description: str = ""


@serializable
@dataclass(frozen=True)
class AssessUnitData:
    default_lower: float
    default_upper: float


@serializable
@dataclass(frozen=True)
class EnumeratedParameterValue:
    value: str  # Must be in model units
    label: str


@serializable
@dataclass(frozen=True)
class AssessParameterData:
    default_is_global: bool
    units: dict[str, AssessUnitData] = field(default_factory=dict)
    enum: list[EnumeratedParameterValue] | None = None  # If nonempty, takes precedence over units


@serializable
@dataclass(frozen=True)
class AssessTreatment:
    name: str
    route_id: str
    schedule: Schedule | LegacyRouteSchedule
    description: str | None = None


@serializable
@dataclass(frozen=True)
class AssessData:
    parameters: dict[str, AssessParameterData]
    default_scan_parameter_1: str
    default_scan_parameter_2: str
    default_n_1: int
    default_n_2: int
    default_scale_1: str
    default_scale_2: str

    treatments: dict[str, AssessTreatment]
    default_treatment: str

    criteria: dict[str, AssessCriterionData]
    default_criterion: str

    default_optima_method: str

    output_starts: dict[str, AssessOutputTime]  # nonempty
    default_output_start: str
    output_stops: dict[str, AssessOutputTime]  # nonempty
    default_output_stop: str
    default_output_n: int  # This n is the number of timepoints in the replicated LinspaceTimes
    output_interval: str

    output_plot_options: dict[str, OutputPlotOption]
    plot_time_transform: float
    plot_time_unit: str

    default_solver_configuration: SolverConfiguration | LegacySolverConfiguration

    pack: str

    report_url: str | None = None


@serializable
@dataclass(frozen=True)
class ApplicationModel:
    url: str
    name: str
    parameters: dict[str, ModelParameterData] = field(default_factory=dict)
    routes: dict[str, ModelRouteData] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    brief: str | None = None
    headline: str | None = None
    thumbnail_url: str | None = None
    drug_diagram_url: str | None = None
    pharmacology_diagram_url: str | None = None
    documentation: str | None = None
    assess: AssessData | None = None
