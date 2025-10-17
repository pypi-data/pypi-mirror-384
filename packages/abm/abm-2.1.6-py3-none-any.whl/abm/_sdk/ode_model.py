__all__ = ["OdeModel", "OdeModelFromText", "OdeModelTypes", "Schedule"]

from dataclasses import dataclass
from functools import partial
from typing import Literal

from serialite import SerializableMixin, abstract_serializable, serializable

from .._units.ast import Unit
from .job import Job


def allow_unused(serializable: SerializableMixin):
    serializable.__fields_serializer__.from_data = partial(
        serializable.__fields_serializer__.from_data, allow_unused=True
    )


@serializable
@dataclass(frozen=True)
class ExternalParameter:
    value: float
    unit: Unit


@serializable
@dataclass(frozen=True)
class ExternalOutput:
    unit: Unit


@serializable
@dataclass(frozen=True)
class OdeModelTypes:
    parameters: dict[str, ExternalParameter]
    schedules: list[str]
    outputs: dict[str, ExternalOutput]
    time_unit: Unit


# Allow unused fields for backwards compatibility
allow_unused(OdeModelTypes)
allow_unused(ExternalParameter)
allow_unused(ExternalOutput)


@abstract_serializable
class Schedule:
    pass


@abstract_serializable
class OdeModel:
    def store(
        self,
        *,
        deduplicate: bool = True,
        include_types: bool = False,
    ) -> Job[None, OdeModelTypes]:
        from . import client

        job = client.create_jobs(
            [self],
            deduplicate=deduplicate,
            include_types=include_types,
        )
        return job[0]


@serializable
@dataclass(frozen=True)
class OdeModelFromText:
    text: str
    format: Literal["analytic", "kroneckerbio", "mass_action", "reaction", "sbml"]

    def parse(self) -> OdeModel:
        from . import client

        job = client.create_jobs([self])[0]
        client.create_contract(jobs=[job], wait=True)
        return job.output_or_raise()
