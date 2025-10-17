from __future__ import annotations

__all__ = ["Array"]

from dataclasses import dataclass
from typing import Any, overload

import numpy as np
from serialite import serializable

from .data_type import DataType


@serializable
@dataclass(frozen=True, slots=True, kw_only=True)
class Array:
    data_type: DataType
    values: list[Any]

    @overload
    def __init__(self, *, data_type: DataType, values: list[Any]):
        pass

    @overload
    def __init__(self, *values: Any):
        pass

    def __init__(self, *args, **kwargs):
        if len(kwargs) != 0:
            if len(args) != 0 or len(kwargs) != 2:
                raise TypeError(f"Expected 0 keyword arguments, got {len(kwargs)}: {kwargs}")

            # Private constructor
            object.__setattr__(self, "data_type", kwargs["data_type"])
            object.__setattr__(self, "values", kwargs["values"])
        else:
            from .._helper.get_table import find_most_complex_type

            python_type = find_most_complex_type(args)
            data_type = DataType.from_python_type(python_type)

            object.__setattr__(self, "data_type", data_type)
            object.__setattr__(self, "values", [data_type.cast(value) for value in args])

        assert self.data_type is not None

    def __len__(self) -> int:
        return len(self.values)

    def __getitem__(self, key):
        return self.values[key]

    def __class_getitem__(cls, data_type: DataType):
        return ArraySpecialized(data_type)

    @staticmethod
    def from_numpy(array: np.ndarray) -> Array:
        if array.dtype.kind == "O":
            # Use the elements to determine the data type
            return Array(*array.tolist())
        else:
            return Array(data_type=DataType.from_numpy(array.dtype), values=array.tolist())

    def to_numpy(self):
        return np.array(self.values, dtype=self.data_type.to_numpy())


class ArraySpecialized:
    def __init__(self, data_type: DataType):
        self.data_type = data_type

    def __call__(self, *values: Any) -> Any:
        new_values = [self.data_type.cast(value) for value in values]
        return Array(data_type=self.data_type, values=new_values)
