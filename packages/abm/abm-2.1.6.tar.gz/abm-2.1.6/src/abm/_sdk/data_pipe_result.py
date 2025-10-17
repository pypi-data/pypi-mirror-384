__all__ = ["DataPipeResult"]

from dataclasses import dataclass

import pandas as pd
import tabeline as tl

from .data_frame import DataFrame
from .data_pipe import DataPipeElement
from .data_pipe_builder import DataPipeBuilder
from .job import Job


@dataclass(frozen=True, kw_only=True)
class DataPipeResult(DataPipeBuilder):
    """Object for the result of datapipe task.

    Attributes
    ----------
    job : `Job[DataFrame, None]`
    """

    job: Job[DataFrame, None]

    def to_data_frame(self) -> DataFrame:
        return self.job.output_or_raise()

    def to_tabeline(self) -> tl.DataFrame:
        return self.job.output_or_raise().to_tabeline()

    def to_pandas(self) -> pd.DataFrame:
        return self.job.output_or_raise().to_pandas()

    def to_data_pipe(self) -> DataPipeElement:
        return DataPipeElement(self.job.id)
