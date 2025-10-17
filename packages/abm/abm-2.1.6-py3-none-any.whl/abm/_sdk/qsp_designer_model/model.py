from dataclasses import dataclass
from typing import Literal
from uuid import UUID

from serialite import AbstractSerializableMixin, abstract_serializable, field, serializable

from ..ode_model import OdeModel
from .get_all_subclasses import get_all_subclasses
from .indexing import IndexRelativeValueState, MultipleIndicesKeyState
from .metadata import (
    DosingMetadataState,
    QspDesignerModelMetadata,
    QuantityInputMetadataState,
    QuantityMetricMetadataState,
    QuantityPlotMetadataState,
)


#######################################################
# Dosing
#######################################################
@abstract_serializable
@dataclass(frozen=True, kw_only=True)
class DosingScheduleState:
    dose_amount: str
    dose_duration: str | None
    is_rate: bool


@serializable
@dataclass(frozen=True, kw_only=True)
class SingleDoseScheduleState(DosingScheduleState):
    start_time: str


@serializable
@dataclass(frozen=True, kw_only=True)
class RegularDosesScheduleState(DosingScheduleState):
    start_time: str
    number_doses: str
    interval: str


@serializable
@dataclass(frozen=True, kw_only=True)
class CustomDoseScheduleState(DosingScheduleState):
    dose_times: str


@abstract_serializable
@dataclass(frozen=True, kw_only=True)
class DoseStateBase:
    pass


@serializable
@dataclass(frozen=True, kw_only=True)
class BolusDoseState(DoseStateBase):
    amount: str
    unit: str | None


@serializable
@dataclass(frozen=True, kw_only=True)
class GeneralBolusDoseState(DoseStateBase):
    amount: str


@serializable
@dataclass(frozen=True, kw_only=True)
class GeneralInfusionState(DoseStateBase):
    infusion_rate: str
    duration: str


#######################################################
# Units
#######################################################
@serializable
@dataclass(frozen=True, kw_only=True)
class BaseUnitState:
    symbol: str


@serializable
@dataclass(frozen=True, kw_only=True)
class PrefixState:
    symbol: str
    definition: float


@serializable
@dataclass(frozen=True, kw_only=True)
class NamedDerivedUnitState:
    symbol: str
    definition: str


@serializable
@dataclass(frozen=True, kw_only=True)
class SimulationBaseUnitsState:
    base_unit_id: UUID
    simulation_base_unit: str


@serializable
@dataclass(frozen=True, kw_only=True)
class MultipleIndicesKeyValuePairStateFloat:
    key_state: MultipleIndicesKeyState
    value: float


@serializable
@dataclass(frozen=True, kw_only=True)
class MultipleIndicesKeyValueCollectionStateFloat:
    index_ids: list[UUID]
    pairs: list[MultipleIndicesKeyValuePairStateFloat]


@serializable
@dataclass(frozen=True, kw_only=True)
class MultipleIndicesKeyValuePairStateUuid:
    key_state: MultipleIndicesKeyState
    value: UUID


@serializable
@dataclass(frozen=True, kw_only=True)
class MultipleIndicesKeyValueCollectionStateUuid:
    index_ids: list[UUID]
    pairs: list[MultipleIndicesKeyValuePairStateUuid]


@serializable
@dataclass(frozen=True, kw_only=True)
class IndexCreatorIndexValuePairState:
    index_creator_id: UUID
    index_value: int


@serializable
@dataclass(frozen=True, kw_only=True)
class MultipleIndicesKeyIndexCreatorsState:
    pairs: list[IndexCreatorIndexValuePairState]
    runtime_pairs: list[IndexRelativeValueState]


#######################################################
# Edge end types
#######################################################
@abstract_serializable
@dataclass(frozen=True, kw_only=True)
class EdgeEndState:
    node_id: UUID


@serializable
@dataclass(frozen=True, kw_only=True)
class NonSpecificEdgeEndState(EdgeEndState):
    each_updated_by_all: bool  # TODO: what does this mean?


@serializable
@dataclass(frozen=True, kw_only=True)
class LegacySpecificEdgeEndState(EdgeEndState):
    key: MultipleIndicesKeyIndexCreatorsState


@serializable
@dataclass(frozen=True, kw_only=True)
class SpecificEdgeEndState(EdgeEndState):
    component: str  # Currently assumed to be an expanded quantity name


#######################################################
# Node traits
#######################################################
@dataclass(frozen=True, kw_only=True)
class Deactivatable:
    is_deactivated: bool


@dataclass(frozen=True, kw_only=True)
class Exposable:
    is_exposed: bool


@dataclass(frozen=True, kw_only=True)
class Subgraphable:
    subgraph_definition_id: UUID


#######################################################
# Abstract graph entity type
#######################################################
@dataclass(frozen=True, kw_only=True)
class GraphEntityState(AbstractSerializableMixin):
    id: UUID


#######################################################
# Abstract node types
#######################################################
@dataclass(frozen=True, kw_only=True)
class LocalNodeState(GraphEntityState):
    name: str


@dataclass(frozen=True, kw_only=True)
class LocalQuantityState(LocalNodeState, Subgraphable, Exposable):
    values: MultipleIndicesKeyValueCollectionStateFloat
    unit: str | None
    attached_index_node_ids: list[UUID]
    is_output: bool
    # None for these means the quantity has no metadata of that category
    input_metadata: QuantityInputMetadataState | None = None
    metric_metadata: QuantityMetricMetadataState | None = None
    plot_metadata: QuantityPlotMetadataState | None = None


#######################################################
# Node types
#######################################################
@serializable
@dataclass(frozen=True, kw_only=True)
class LocalAssignmentState(LocalNodeState, Subgraphable, Deactivatable):
    is_initial_only: bool
    expression: str | None  # Can be None if is_deactivated is True
    condition: str | None = None
    alternative_expression: str | None = None


@serializable
@dataclass(frozen=True, kw_only=True)
class DosingEffectState:
    type: Literal["Dose", "Jump"]
    target: str
    expression: str


@serializable
@dataclass(frozen=True, kw_only=True)
class LocalDosingPlanState(LocalNodeState, Subgraphable, Exposable, Deactivatable):
    dosing_schedule_state: DosingScheduleState
    effects: list[DosingEffectState]
    metadata: DosingMetadataState | None = None


@serializable
@dataclass(frozen=True, kw_only=True)
class EventEffectState:
    target: str | None
    expression: str


@serializable
@dataclass(frozen=True, kw_only=True)
class LocalEventState(LocalNodeState, Subgraphable, Exposable, Deactivatable):
    condition: str
    effects: list[EventEffectState]


@serializable
@dataclass(frozen=True, kw_only=True)
class LocalIndexNodeState(LocalNodeState, Subgraphable):
    index_values: list[str]
    index_id: UUID
    priority: int
    # These are for quantity metric metadata.  Default None means defer to the main quantity names
    descriptive_name: str | None = None
    descriptive_values: list[str] | None = None
    description: str = ""


@serializable
@dataclass(frozen=True, kw_only=True)
class LocalRuntimeIndexNodeState(LocalNodeState, Subgraphable):
    range_expression: str
    index_id: UUID
    priority: int


@serializable
@dataclass(frozen=True, kw_only=True)
class LocalReactionState(LocalNodeState, Subgraphable, Exposable, Deactivatable):
    rate: str | None  # Can be None if is_deactivated is True
    reverse_rate: str | None
    index_mapping: str | None


#######################################################
# Quantity node types
#######################################################
@serializable
@dataclass(frozen=True, kw_only=True)
class LocalCompartmentState(LocalQuantityState):
    pass


@serializable
@dataclass(frozen=True, kw_only=True)
class LocalParameterState(LocalQuantityState):
    pass


@serializable
@dataclass(frozen=True, kw_only=True)
class LocalSpeciesState(LocalQuantityState):
    owner_id: UUID
    is_concentration: bool = False


#######################################################
# Abstract edge types
#######################################################
@dataclass(frozen=True, kw_only=True)
class EdgeState(GraphEntityState):
    pass


#######################################################
# Edge types
#######################################################
@serializable
@dataclass(frozen=True, kw_only=True)
class LocalAssignmentEdgeState(EdgeState):
    direction: Literal["FromAssignment", "ToAssignment", "ToAssignmentInhibitor"]
    quantity_end: EdgeEndState
    assignment_end: EdgeEndState


@serializable
@dataclass(frozen=True, kw_only=True)
class DosingPlanEdgeState(EdgeState):
    quantity_end: EdgeEndState
    dosing_plan_end: EdgeEndState


@serializable
@dataclass(frozen=True, kw_only=True)
class LocalEventEdgeState(EdgeState):
    edge_type: Literal["Growth", "Product", "Modifier", "Inhibitor"]
    quantity_end: EdgeEndState
    event_end: EdgeEndState


@serializable
@dataclass(frozen=True, kw_only=True)
class ReactionParameterEdgeState(EdgeState):
    reaction_end: EdgeEndState
    parameter_end: EdgeEndState


@serializable
@dataclass(frozen=True, kw_only=True)
class ReactionSpeciesEdgeState(EdgeState):
    stoichiometry: str
    edge_type: Literal["Substrate", "Product", "Modifier", "Growth", "Inhibitor"]
    reaction_end: EdgeEndState
    species_end: EdgeEndState


#######################################################
# Meta edge types
#######################################################
@serializable
@dataclass(frozen=True, kw_only=True)
class MetaEdgeState(GraphEntityState):
    from_id: UUID
    to_id: UUID


@serializable
@dataclass(frozen=True, kw_only=True)
class WeakCloningMetaEdgeState(MetaEdgeState):
    pass


@serializable
@dataclass(frozen=True, kw_only=True)
class LocalNonEventBasedAssignerState(LocalNodeState):
    is_initial_only: bool


@serializable
@dataclass(frozen=True, kw_only=True)
class MultiDimensionalConstraintState(LocalNonEventBasedAssignerState, Deactivatable, Exposable, Subgraphable):
    initial_guess: float | None
    expression_list: list[str]


@serializable
@dataclass(frozen=True, kw_only=True)
class LocalConstraintEdgeState(EdgeState):
    edge_type: Literal["Modifier", "Inhibitor", "Growth"]
    quantity_end: EdgeEndState
    constraint_end: EdgeEndState


@serializable
@dataclass(frozen=True, kw_only=True)
class LocalNodeSubgraphProxyState(LocalNodeState, Subgraphable):
    subgraph_instance_id: UUID
    referenced_node_name: str | None


@serializable
@dataclass(frozen=True, kw_only=True)
class LocalReactionSubgraphProxyState(LocalNodeSubgraphProxyState, Exposable, Deactivatable):
    pass


@serializable
@dataclass(frozen=True, kw_only=True)
class LocalStaticIndexNodeSubgraphProxyState(LocalNodeSubgraphProxyState):
    pass


#######################################################
# Inline functions
#######################################################
@serializable
@dataclass(frozen=True, kw_only=True)
class LocalInlineFunctionState(LocalNodeState, Subgraphable):
    name: str
    arguments: list[str]
    expression: str


#######################################################
# Subgraphs
#######################################################
@serializable
@dataclass(frozen=True, kw_only=True)
class LocalSubgraphDefinitionState(GraphEntityState, Exposable):
    name: str


@serializable
@dataclass(frozen=True, kw_only=True)
class LocalSubgraphInstanceState(GraphEntityState, Subgraphable):  # Technically Subgraphable, but not supported here
    name: str
    definition_node_name: str
    categories_are_prefixed: bool


@serializable
@dataclass(frozen=True, kw_only=True)
class LocalQuantitySubgraphProxyState(LocalNodeSubgraphProxyState):  # Technically Subgraphable, but not supported here
    pass


@serializable
@dataclass(frozen=True, kw_only=True)
class LocalCompartmentSubgraphProxyState(LocalQuantitySubgraphProxyState):
    pass


@serializable
@dataclass(frozen=True, kw_only=True)
class LocalParameterSubgraphProxyState(LocalQuantitySubgraphProxyState):
    pass


@serializable
@dataclass(frozen=True, kw_only=True)
class LocalSpeciesSubgraphProxyState(LocalQuantitySubgraphProxyState):
    pass


#######################################################
# Imports
#######################################################
@serializable
@dataclass(frozen=True, kw_only=True)
class WorkspaceImportState(GraphEntityState):
    name: str
    job_id: str
    import_type: Literal["Private", "Global"]


@dataclass(frozen=True, kw_only=True)
class LocalQuantityImportState(LocalNodeState):
    workspace_import_name: str
    imported_node_name: str


@serializable
@dataclass(frozen=True, kw_only=True)
class LocalCompartmentImportState(LocalQuantityImportState):
    pass


@serializable
@dataclass(frozen=True, kw_only=True)
class LocalParameterImportState(LocalQuantityImportState):
    pass


@serializable
@dataclass(frozen=True, kw_only=True)
class LocalSpeciesImportState(LocalQuantityImportState):
    pass


@serializable
@dataclass(frozen=True, kw_only=True)
class QspDesignerModel(OdeModel):
    base_unit_states: list[BaseUnitState]
    prefix_states: list[PrefixState]
    named_derived_unit_states: list[NamedDerivedUnitState]
    simulation_base_units: list[SimulationBaseUnitsState]
    graph_entity_states: list[GraphEntityState]
    time_unit: str | None  # unit fields may be any string (or None) if ignore_units is True
    metadata: QspDesignerModelMetadata = field(default_factory=QspDesignerModelMetadata)
    ignore_units: bool = False


GraphEntityState.__subclass_serializers__ = get_all_subclasses(GraphEntityState)
