from collections import defaultdict
from pathlib import Path

import pandas as pd

from .._sdk.ode_model import OdeModelTypes
from .get_model import get_remote_model


def initialize_parameter_table(model_path: str, parameter_table: str) -> None:
    path = Path(parameter_table)
    types: OdeModelTypes = get_remote_model(model_path).refresh(include_types=True).types

    table = defaultdict(list)
    for name, parameter in types.parameters.items():
        table["parameter"].append(name)
        table["value"].append(parameter.value)
        table["unit"].append(parameter.unit)

    df = pd.DataFrame.from_dict(table)
    df.to_csv(parameter_table, index=False)

    #  Remove the last new line character
    #  This happens because the last line is written with a newline character.
    path.write_text(path.read_text().rstrip())
