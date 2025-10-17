from __future__ import annotations

import math
from typing import TYPE_CHECKING
from uuid import uuid4

import pandas as pd
from IPython.display import HTML, display, update_display

if TYPE_CHECKING:
    from .job import Job


class DisplayJobProgress:
    def __init__(self, job: Job) -> None:
        self._display_id = None
        self._job = job

    def display(self) -> None:
        pass


class DisplayJobProgressOptimization(DisplayJobProgress):
    def display(self) -> None:
        progress: list[dict] = self._job.progress()
        if len(progress) == 0:
            return

        # There is no guarantee of backwards compatibility with the progress format
        # so do the best we can but never raise an exception
        content = []
        for record in progress:
            if "iteration" in record and "objective" in record and "parameters" in record:
                iteration = record["iteration"]
                if not isinstance(iteration, int):
                    iteration = 0

                objective = record["objective"]
                if not isinstance(objective, (int, float)):
                    objective = math.nan

                parameters = record["parameters"]
                if not isinstance(parameters, dict):
                    parameters = {}
                for key, value in parameters.items():
                    if not isinstance(value, (int, float)):
                        parameters[key] = math.nan

                content.append({"iteration": iteration, "objective": objective, **parameters})

        df = pd.DataFrame(content).to_html(index=False)

        if self._display_id is None:
            self._display_id = str(uuid4())
            display(HTML(df), display_id=self._display_id)
        else:
            update_display(HTML(df), display_id=self._display_id)
