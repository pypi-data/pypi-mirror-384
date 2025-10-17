__all__ = [
    "ConcatenateColumnsElement",
    "ConcatenateRowsElement",
    "DataFrameElement",
    "DataFrameLiteralElement",
    "DataPipe",
    "DataPipeElement",
    "DeselectElement",
    "DistinctElement",
    "DistributionSampleElement",
    "FilterElement",
    "GatherElement",
    "GroupByElement",
    "InnerJoinElement",
    "MutateElement",
    "OdeOptimizationBatchElement",
    "OdeOptimizationElement",
    "OdeParameterPosteriorSampleElement",
    "OdeParameterPosteriorSampleListDiagnosticElement",
    "OdePredictionElement",
    "OdeProposalPopulationSampleElement",
    "OdeResidualElement",
    "OdeSimulationBatchElement",
    "OdeSimulationElement",
    "OdeVirtualPopulationSampleElement",
    "RenameElement",
    "SelectElement",
    "Slice0Element",
    "Slice1Element",
    "SortElement",
    "SpreadElement",
    "SummarizeElement",
    "TransmuteElement",
    "UngroupElement",
    "UniqueElement",
]

from dataclasses import dataclass
from typing import Literal

import numpy as np
from serialite import abstract_serializable, serializable

from .data_frame import DataFrame
from .data_pipe_builder import DataPipeBuilder
from .expression import Expression, StaticExpression


@abstract_serializable
class DataPipe(DataPipeBuilder):
    def run(
        self,
        *,
        deduplicate: bool = True,
        interval: float = 5.0,
        progress: bool = False,
        timeout: float = 3600,
        wait: bool = True,
    ):
        from .._sdk import client
        from .data_pipe_result import DataPipeResult

        jobs = client.create_jobs([self], deduplicate=deduplicate)
        client.create_contract(jobs, interval=interval, progress=progress, timeout=timeout, wait=wait)
        return DataPipeResult(job=jobs[0])

    def to_data_pipe(self):
        return self


@serializable
@dataclass(frozen=True)
class DataFrameLiteralElement(DataPipe):
    table: DataFrame


@serializable
@dataclass(frozen=True)
class DataFrameElement(DataPipe):
    data_frame_id: str


@serializable
@dataclass(frozen=True)
class OdeSimulationElement(DataPipe):
    simulation_id: str
    on_failure: Literal["error", "empty"] = "error"


@serializable
@dataclass(frozen=True)
class DistributionSampleElement(DataPipe):
    distribution_sample_id: str


@serializable
@dataclass(frozen=True)
class OdeParameterPosteriorSampleElement(DataPipe):
    parameter_posterior_sample_id: str


@serializable
@dataclass(frozen=True)
class OdeParameterPosteriorSampleListDiagnosticElement(DataPipe):
    parameter_posterior_sample_ids: list[str]


@serializable
@dataclass(frozen=True)
class OdeProposalPopulationSampleElement(DataPipe):
    proposal_population_sample_id: str


@serializable
@dataclass(frozen=True)
class OdeVirtualPopulationSampleElement(DataPipe):
    virtual_population_sample_id: str


@serializable
@dataclass(frozen=True)
class OdeSimulationBatchElement(DataPipe):
    simulation_batch_id: str


@serializable
@dataclass(frozen=True)
class OdeOptimizationElement(DataPipe):
    optimization_id: str


@serializable
@dataclass(frozen=True)
class OdePredictionElement(DataPipe):
    prediction_id: str


@serializable
@dataclass(frozen=True)
class OdeResidualElement(DataPipe):
    residual_id: str


@serializable
@dataclass(frozen=True)
class OdeOptimizationBatchElement(DataPipe):
    optimization_batch_id: str


@serializable
@dataclass(frozen=True)
class DataPipeElement(DataPipe):
    data_pipe_id: str


@serializable
@dataclass(frozen=True)
class Slice0Element(DataPipe):
    table: DataPipe
    indexes: list[int]

    def __post_init__(self):
        if isinstance(self.indexes, (range, tuple)):
            # Standardize range to list
            object.__setattr__(self, "indexes", list(self.indexes))
        elif isinstance(self.indexes, np.ndarray):
            # Standardize numpy array to list
            object.__setattr__(self, "indexes", self.indexes.tolist())


@serializable
@dataclass(frozen=True)
class Slice1Element(DataPipe):
    table: DataPipe
    indexes: list[int]

    def __post_init__(self):
        if isinstance(self.indexes, (range, tuple)):
            # Standardize range to list
            object.__setattr__(self, "indexes", list(self.indexes))
        elif isinstance(self.indexes, np.ndarray):
            # Standardize numpy array to list
            object.__setattr__(self, "indexes", self.indexes.tolist())


@serializable
@dataclass(frozen=True)
class FilterElement(DataPipe):
    table: DataPipe
    predicate: Expression


@serializable
@dataclass(frozen=True)
class SortElement(DataPipe):
    table: DataPipe
    columns: list[str]


@serializable
@dataclass(frozen=True)
class InnerJoinElement(DataPipe):
    table: DataPipe
    other: DataPipe
    by: list[tuple[str, str]] | None = None


@serializable
@dataclass(frozen=True)
class DistinctElement(DataPipe):
    table: DataPipe
    columns: list[str]


@serializable
@dataclass(frozen=True)
class UniqueElement(DataPipe):
    table: DataPipe


@serializable
@dataclass(frozen=True)
class SelectElement(DataPipe):
    table: DataPipe
    columns: list[str]


@serializable
@dataclass(frozen=True)
class DeselectElement(DataPipe):
    table: DataPipe
    columns: list[str]


@serializable
@dataclass(frozen=True)
class RenameElement(DataPipe):
    table: DataPipe
    columns: dict[str, str]


@serializable
@dataclass(frozen=True)
class MutateElement(DataPipe):
    table: DataPipe
    mutators: dict[str, Expression]


@serializable
@dataclass(frozen=True)
class TransmuteElement(DataPipe):
    table: DataPipe
    mutators: dict[str, Expression]


@serializable
@dataclass(frozen=True)
class GroupByElement(DataPipe):
    table: DataPipe
    groupers: list[str]


@serializable
@dataclass(frozen=True)
class UngroupElement(DataPipe):
    table: DataPipe


@serializable
@dataclass(frozen=True)
class SummarizeElement(DataPipe):
    table: DataPipe
    summarizers: dict[str, Expression]


@serializable
@dataclass(frozen=True)
class GatherElement(DataPipe):
    table: DataPipe
    key: str
    value: str
    columns: list[str]
    unit: str | None = None


@serializable
@dataclass(frozen=True)
class SpreadElement(DataPipe):
    table: DataPipe
    key: str
    value: str
    fill: StaticExpression | None = None


@serializable
@dataclass(frozen=True)
class ConcatenateRowsElement(DataPipe):
    tables: list[DataPipe]


@serializable
@dataclass(frozen=True)
class ConcatenateColumnsElement(DataPipe):
    tables: list[DataPipe]
