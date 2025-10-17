__all__ = ["ToSimbiologyOdeSimulation"]

from dataclasses import dataclass
from pathlib import Path

import numpy as np
from serialite import serializable

from .expression import Expression
from .ode_model_reference import OdeModelReference
from .solver_configuration import SolverConfiguration
from .times import ListTimes, Times


@serializable
@dataclass(frozen=True, kw_only=True)
class ToSimbiologyOdeSimulation:
    model: OdeModelReference
    output_times: Times | list[Expression]
    output_names: list[str] | None = None
    configuration: SolverConfiguration = SolverConfiguration()

    def __post_init__(self):
        if isinstance(self.output_times, list):
            object.__setattr__(self, "output_times", ListTimes(self.output_times))
        elif isinstance(self.output_times, np.ndarray):
            object.__setattr__(self, "output_times", ListTimes(self.output_times.tolist()))


def to_simbiology(
    path: Path | str,
    model: OdeModelReference,
    output_times: Times | list[Expression],
    output_names: list[str] | None = None,
    configuration: SolverConfiguration = SolverConfiguration(),
) -> None:
    from . import client

    if isinstance(path, str):
        path = Path(path)

    simulation_to_simbiology = ToSimbiologyOdeSimulation(
        model=model,
        output_times=output_times,
        output_names=output_names,
        configuration=configuration,
    )

    jobs = client.create_jobs([simulation_to_simbiology])
    client.create_contract(jobs)
    simbiology_code = jobs[0].output_or_raise()

    parent_dir = path.parent
    parent_dir.mkdir(parents=True, exist_ok=True)
    path.write_text(simbiology_code, encoding="utf-8")
