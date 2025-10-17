from __future__ import annotations

__all__ = ["DataFrame"]

import csv
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import overload

import pandas as pd
import tabeline as tl
from serialite import DeserializationFailure, DeserializationResult, DeserializationSuccess, serializable

from .array import Array
from .data_type import Boolean, DataType, Float64, Integer64, Nothing, String


@serializable
@dataclass(frozen=True, slots=True)
class DataFrame:
    columns: dict[str, Array]
    height: int
    width: int
    group_levels: list[list[str]] = field(default_factory=list)

    @overload
    def __init__(self, **columns: bool | int | float | str | list[bool] | list[int] | list[float] | list[str] | Array):
        pass

    @overload
    def __init__(self, columns: dict[str, Array], /, *, height: int | None = None, group_levels: list[list[str]] = []):
        pass

    def __init__(self, *args, **kwargs):
        match args:
            case []:
                # Determine height
                height = 0
                for column in kwargs.values():
                    if isinstance(column, (bool, int, float, str)):
                        height = 1
                    else:
                        height = len(column)
                        break

                # Determine width
                width: int = len(kwargs)

                # Convert columns
                columns = {}
                for name, column in kwargs.items():
                    match column:
                        case bool():
                            data_type = Boolean()
                            values = [column] * height
                        case int():
                            data_type = Integer64()
                            values = [column] * height
                        case float():
                            data_type = Float64()
                            values = [column] * height
                        case str():
                            data_type = String()
                            values = [column] * height
                        case []:
                            data_type = Nothing()
                            values = []
                        case [first, *_]:
                            values = column
                            match first:
                                case bool():
                                    data_type = Boolean()
                                case int():
                                    data_type = Integer64()
                                case float():
                                    data_type = Float64()
                                case str():
                                    data_type = String()

                    if len(values) != height:
                        raise ValueError(
                            f"Column {name} has length {len(values)} which is different from the first column with "
                            f"length {height}"
                        )

                    columns[name] = Array[data_type](*values)

                group_levels = []
            case [columns]:
                height = kwargs.pop("height", None)
                if height is None:
                    height = len(next(iter(columns.values())))

                width = len(columns)

                group_levels = kwargs.pop("group_levels", [])

                if len(kwargs) > 0:  # Some unused kwargs remain
                    raise TypeError(f"DataFrame() got unexpected keywords arguments: {', '.join(kwargs.keys())}")
            case _:
                raise TypeError(f"DataFrame() expected 0 positional arguments, got {len(args)}")

        object.__setattr__(self, "columns", columns)
        object.__setattr__(self, "height", height)
        object.__setattr__(self, "width", width)
        object.__setattr__(self, "group_levels", group_levels)

    @property
    def column_names(self) -> list[str]:
        return list(self.columns.keys())

    @property
    def data_types(self) -> dict[str, DataType]:
        return {name: column.data_type for name, column in self.columns.items()}

    def __getitem__(self, key):
        indexes, names = key

        if not isinstance(names, str):
            raise TypeError("Only a single column is supported")

        return self.columns[names][indexes]

    @classmethod
    def from_data(cls, data) -> DeserializationResult[DataFrame]:
        result = cls.__fields_serializer__.from_data(data)
        match result:
            case DeserializationFailure():
                return result
            case DeserializationSuccess(fields):
                columns = fields["columns"]
                height = fields["height"]
                width = fields["width"]
                group_levels = fields["group_levels"]

                # Collect errors
                errors = defaultdict(dict)

                # Check that number of rows in each column is actually consistent with height
                for column_name, column in columns.items():
                    if height != len(column):
                        errors["columns"][column_name] = (
                            f"Number of elements ({len(column)}) does not match height ({height})"
                        )

                # Check that number of columns is actually consistent with width
                if width != len(columns):
                    errors["width"] = f"Number of elements in columns ({len(columns)}) does not match width ({width})"

                # Check that the group names are actually column names and not duplicated
                group_names = set()
                for level in group_levels:
                    for name in level:
                        if name not in columns:
                            errors["group_levels"][name] = "Group name not present in columns"
                        if name in group_names:
                            errors["group_levels"][name] = "Group name is duplicated"
                        group_names.add(name)

                if len(errors) != 0:
                    return DeserializationFailure(errors)

                return DeserializationSuccess(DataFrame(columns, height=height, group_levels=group_levels))

    @staticmethod
    def from_file(filename: Path):
        if isinstance(filename, str):
            filename = Path(filename)

        with filename.open(newline="", encoding="utf-8-sig") as csv_file:
            csv_reader = csv.DictReader(csv_file, skipinitialspace=True)
            field_names = csv_reader.fieldnames
            data = {name: [] for name in field_names}

            height = 0
            for row in csv_reader:
                height += 1
                for name, value in row.items():
                    try:
                        data[name].append(int(value))
                    except ValueError:
                        try:
                            data[name].append(float(value))
                        except ValueError:
                            data[name].append(value)

        # Convert all values to a common type
        columns = {}
        for key, values in data.items():
            columns[key] = Array(*values)

        return DataFrame(columns, height=height)

    def to_data_pipe(self):
        from .data_pipe import DataFrameLiteralElement

        return DataFrameLiteralElement(self)

    @staticmethod
    def from_pandas(df: pd.DataFrame):
        if df.ndim != 2:
            raise TypeError(f"Can only convert pandas DataFrame with 2 dimensions, not {df.ndim}")

        return DataFrame(
            {name: Array.from_numpy(series) for name, series in df.to_dict("series").items()},
            height=df.shape[0],
        )

    def to_pandas(self):
        return pd.DataFrame.from_dict({name: array.to_numpy() for name, array in self.columns.items()})

    @staticmethod
    def from_tabeline(df: tl.DataFrame) -> DataFrame:
        group_levels = [list(grouper) for grouper in df.group_levels]
        columns = {name: Array.from_numpy(df[:, name].to_numpy()) for name in df.column_names}
        return DataFrame(columns, height=df.height, group_levels=group_levels)

    def to_tabeline(self) -> tl.DataFrame:
        if self.width == 0:
            return tl.DataFrame.columnless(self.height)
        else:
            columns = {name: array.to_numpy() for name, array in self.columns.items()}
            df = tl.DataFrame.from_dict(columns)
            for group_level in self.group_levels:
                df = df.group_by(*group_level)
            return df

    def __eq__(self, other):
        if isinstance(other, DataFrame):
            return (
                self.height == other.height
                and self.width == other.width
                # Column names must be in the same order
                and all(name1 == name2 for name1, name2 in zip(self.data.keys(), other.data.keys(), strict=True))
                and self.columns == other.columns
                and self.group_levels == other.group_levels
            )
        else:
            return NotImplemented

    def __str__(self):
        return str(self.to_pandas())

    def _repr_html_(self):
        return self.to_pandas()._repr_html_()
