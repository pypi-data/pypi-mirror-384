from pathlib import Path

import pandas as pd
import tabeline as tl

from abm._sdk.data_frame import DataFrame
from abm._sdk.reaction_model import Schedule

from .helper import find_duplicate_keys
from .parse_schedule import parse_schedule

DataFrameLike = pd.DataFrame | tl.DataFrame | DataFrame
PathLike = str | Path


def get_dose_schedules(
    doses: list[dict[str, dict[str, int | float | str]]], labels: dict[str, str | float | int | bool]
) -> dict[str, Schedule]:
    duplicate_routes = find_duplicate_keys(doses)
    if len(duplicate_routes) > 0:
        if len(labels) > 0:
            raise ValueError(
                "Duplicate routes found for label(s)"
                f" {', '.join([f'{key}={value}' for key, value in labels.items()])}:"
                f" {', '.join(duplicate_routes)}"
            )
        else:
            raise ValueError(f"Duplicate routes found: {', '.join(duplicate_routes)}")

    route_schedules_i = {r: parse_schedule(d) for dose in doses for r, d in dose.items()}

    return route_schedules_i
