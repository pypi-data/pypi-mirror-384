__all__ = [
    "DiscreteValueMetadataState",
    "DosingMetadataState",
    "MetadataLinspaceTimesState",
    "MetadataLinspaceTimesState",
    "MetadataListTimesState",
    "MetadataListTimesState",
    "MetadataOutputTimesState",
    "MetadataParameterTransformState",
    "MetadataPlotTransformState",
    "MetadataScanState",
    "MetadataTimesState",
    "MultipleIndicesKeyValueCollectionStateOfQuantityComponentInputMetadataState",
    "MultipleIndicesKeyValueCollectionStateOfQuantityComponentMetricMetadataState",
    "MultipleIndicesKeyValuePairStateOfQuantityComponentInputMetadataState",
    "MultipleIndicesKeyValuePairStateOfQuantityComponentMetricMetadataState",
    "QspDesignerModelMetadata",
    "QuantityComponentInputMetadataState",
    "QuantityComponentMetricMetadataState",
    "QuantityInputMetadataState",
    "QuantityMetricMetadataState",
    "QuantityPlotMetadataState",
]

from dataclasses import dataclass
from uuid import UUID

from serialite import NonnegativeIntegerSerializer, abstract_serializable, field, serializable

from .indexing import MultipleIndicesKeyState
from .simulation_configuration import SimulationConfiguration

# Input metadata


@serializable
@dataclass(frozen=True, kw_only=True)
class MetadataParameterTransformState:
    # c.f. UnitOption in legacy version
    name: str | None
    expression: str
    default_lower_limit: float | None = None
    default_upper_limit: float | None = None


@serializable
@dataclass(frozen=True, kw_only=True)
class DiscreteValueMetadataState:
    # c.f. DropDown in legacy version
    label: str
    value: int | float


@serializable
@dataclass(frozen=True, kw_only=True)
class QuantityComponentInputMetadataState:
    name: str = ""
    symbol: str = ""
    description: str = ""
    default_value: int | float
    discrete_values: list[DiscreteValueMetadataState] = field(default_factory=list)


@serializable
@dataclass(frozen=True, kw_only=True)
class MultipleIndicesKeyValuePairStateOfQuantityComponentInputMetadataState:
    key_state: MultipleIndicesKeyState
    value: QuantityComponentInputMetadataState


@serializable
@dataclass(frozen=True, kw_only=True)
class MultipleIndicesKeyValueCollectionStateOfQuantityComponentInputMetadataState:
    index_ids: list[UUID]
    pairs: list[MultipleIndicesKeyValuePairStateOfQuantityComponentInputMetadataState]


@serializable
@dataclass(frozen=True, kw_only=True)
class QuantityInputMetadataState:
    is_global: bool = False
    unit_transforms: list[MetadataParameterTransformState] = field(default_factory=list)
    components: MultipleIndicesKeyValueCollectionStateOfQuantityComponentInputMetadataState


# Plot metadata
@serializable
@dataclass(frozen=True, kw_only=True)
class MetadataPlotTransformState:
    # c.f. OutputPlotUnit
    name: str | None
    expression: str


@serializable
@dataclass(frozen=True, kw_only=True)
class QuantityPlotMetadataState:
    title: str = ""
    description: str = ""
    lower_limit: float | None = None
    upper_limit: float | None = None
    log_scale: bool = True
    plotted_by_default: bool = False
    unit_transforms: list[MetadataPlotTransformState] = field(default_factory=list)


# Metric metadata
@serializable
@dataclass(frozen=True, kw_only=True)
class QuantityComponentMetricMetadataState:
    qualifier_description: str = ""


@serializable
@dataclass(frozen=True, kw_only=True)
class MultipleIndicesKeyValuePairStateOfQuantityComponentMetricMetadataState:
    key_state: MultipleIndicesKeyState
    value: QuantityComponentMetricMetadataState


@serializable
@dataclass(frozen=True, kw_only=True)
class MultipleIndicesKeyValueCollectionStateOfQuantityComponentMetricMetadataState:
    index_ids: list[UUID]
    pairs: list[MultipleIndicesKeyValuePairStateOfQuantityComponentMetricMetadataState]


@serializable
@dataclass(frozen=True, kw_only=True)
class QuantityMetricMetadataState:
    name: str = ""
    description: str = ""
    varying_quantity: str | None = None  # A model quantity name
    default_threshold: float
    priority: int = 0
    components: MultipleIndicesKeyValueCollectionStateOfQuantityComponentMetricMetadataState


# Dosing plan metadata
@serializable
@dataclass(frozen=True, kw_only=True)
class DosingMetadataState:
    priority: int = 0


# Main model metadata
@serializable
@dataclass(frozen=True, kw_only=True)
class MetadataScanState:
    parameter: str | None = None  # A model parameter name.  Default None means use a leading parameter.
    n: int = field(serializer=NonnegativeIntegerSerializer(), default=11)
    log_scale: bool = True


@abstract_serializable
@dataclass(frozen=True, kw_only=True)
class MetadataTimesState:
    pass


@serializable
@dataclass(frozen=True, kw_only=True)
class MetadataListTimesState(MetadataTimesState):
    times: list[str]


@serializable
@dataclass(frozen=True, kw_only=True)
class MetadataLinspaceTimesState(MetadataTimesState):
    start: str = "0.0"  # Note bare numeric expressions here are assumed to be in model time units
    stop: str
    n: int = field(serializer=NonnegativeIntegerSerializer(), default=51)


@serializable
@dataclass(frozen=True, kw_only=True)
class MetadataOutputTimesState:
    id: str
    name: str = ""  # Human-readable name
    times: MetadataTimesState


@serializable
@dataclass(frozen=True, kw_only=True)
class QspDesignerModelMetadata:
    name: str = ""
    headline: str = ""
    description: str = ""
    documentation: str = ""
    tags: list[str] = field(default_factory=list)
    default_scan_1: MetadataScanState = field(default_factory=MetadataScanState)
    default_scan_2: MetadataScanState = field(default_factory=MetadataScanState)
    output_times: list[MetadataOutputTimesState] = field(default_factory=list)
    default_configuration: SimulationConfiguration = SimulationConfiguration()
