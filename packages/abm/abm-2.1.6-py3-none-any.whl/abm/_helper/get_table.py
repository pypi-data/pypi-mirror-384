from pathlib import Path

import pandas as pd
import tabeline as tl

from abm._sdk.data_frame import DataFrame

from .helper import DataFrameLike, PathLike, replace_empty_string_with_none


def get_table(table: DataFrameLike | PathLike) -> tl.DataFrame:
    match table:
        case str() | Path():
            table = Path(table)
            if not Path(table).is_file():
                raise FileNotFoundError(f" {table} is not a file")
            # This is mainly because polars is weird with reading csv files with certain values for example:
            # if there is a file with this content it will fail:
            # col1,
            # 1,
            # ,
            # [3,4],
            data = {name: array.values for name, array in DataFrame.from_file(table).columns.items()}
            if len(data) == 0:
                return tl.DataFrame.from_dict({})
            return tl.DataFrame.from_dict(cast_to_most_complex_type(replace_empty_string_with_none(data)))
        case tl.DataFrame():
            data = table.to_dict()
            return tl.DataFrame.from_dict(cast_to_most_complex_type(data))
        case pd.DataFrame():
            # This needs to be done because if the pandas DataFrame comes from a dict with mixed types,
            # tl.DataFrame.from_pandas fails https://github.com/wesm/feather/issues/349
            pd_data = table.to_dict(orient="list")
            return tl.DataFrame.from_dict(cast_to_most_complex_type(pd_data))
        case DataFrame():
            data = {name: array.values for name, array in table.columns.items()}
            return tl.DataFrame.from_dict(cast_to_most_complex_type(replace_empty_string_with_none(data)))
        case _:
            raise NotImplementedError(
                "Expected a path to a CSV file or a DataFrame from ABM or Tabeline or Pandas, but"
                f" got {type(table).__name__}"
            )


def find_most_complex_type(lst: list) -> type:
    complex_types = [type(None), bool, int, float]
    most_complex_type = complex_types[0]
    for element in lst:
        element_type = type(element)
        if isinstance(element, list | str):
            return str
        elif isinstance(element, (float, int)):
            if complex_types.index(element_type) > complex_types.index(most_complex_type):
                most_complex_type = element_type
        elif element is None:
            # Nones are handled later with a better error message
            continue
        else:
            raise ValueError(f"Unsupported type {element_type}")
    return most_complex_type


def cast_to_most_complex_type(data: dict[str, list]) -> dict[str, list]:
    for column, values in data.items():
        if len(values) > 0:
            most_complex_type = find_most_complex_type(values)
            data[column] = [most_complex_type(value) if value is not None else None for value in values]
        else:
            data[column] = []
    return data
