from __future__ import annotations

__all__ = ["Boolean", "DataType", "Dynamic", "Float64", "Integer64", "Nothing", "String"]

from dataclasses import dataclass
from typing import NoReturn

import numpy as np
from parsita import Failure, Success
from serialite import DeserializationFailure, DeserializationResult, DeserializationSuccess, Serializable

from .expression import Unit


@dataclass(frozen=True, slots=True)
class DataType(Serializable):
    @staticmethod
    def from_numpy(dtype: np.dtype) -> DataType:
        match dtype.kind:
            case "b":
                return Boolean()
            case "i":
                return Integer64()
            case "f":
                return Float64()
            case "U":
                return String()
            case _:
                raise NotImplementedError(f"Unsupported dtype: {dtype}")

    @staticmethod
    def from_python_type(python_type: type) -> DataType:
        if issubclass(python_type, type(None)):
            return Nothing()
        elif issubclass(python_type, bool):
            return Boolean()
        elif issubclass(python_type, int):
            return Integer64()
        elif issubclass(python_type, float):
            return Float64()
        elif issubclass(python_type, str):
            return String()
        else:
            raise NotImplementedError(f"Unsupported type: {python_type}")

    def to_numpy(self):
        raise NotImplementedError()

    @staticmethod
    def from_data(data) -> DeserializationResult[DataType]:
        from .data_type_parser import parse_data_type

        if not isinstance(data, str):
            return DeserializationFailure("Expected a string, got {data!r}")

        match parse_data_type(data):
            case Failure(error):
                return DeserializationFailure(str(error))
            case Success(data_type):
                return DeserializationSuccess(data_type)

    def to_data(self):
        match self:
            case Boolean():
                return "Boolean"
            case Integer64():
                return "Integer64"
            case Float64(unit):
                return f"Float64[{unit}]"
            case String():
                return "String"
            case Nothing():
                return "Nothing"
            case Dynamic():
                return "dynamic"
            case _:
                raise NotImplementedError(f"Unsupported data type: {self}")


@dataclass(frozen=True, slots=True)
class Boolean(DataType):
    def to_numpy(self):
        return np.dtype(bool)

    def cast(self, value: object) -> bool:
        if not isinstance(value, bool):
            raise TypeError(f"Expected bool, got {type(value)}: {value}")

        return bool(value)


@dataclass(frozen=True, slots=True)
class Integer64(DataType):
    def to_numpy(self):
        return np.dtype(int)

    def cast(self, value: object) -> int:
        return int(value)


@dataclass(frozen=True, slots=True)
class Float64(DataType):
    unit: Unit = "1"

    def to_numpy(self):
        return np.dtype(float)

    def cast(self, value: object) -> float:
        return float(value)


@dataclass(frozen=True, slots=True)
class String(DataType):
    def to_numpy(self):
        return np.dtype(str)

    def cast(self, value: object) -> str:
        return str(value)


@dataclass(frozen=True, slots=True)
class Nothing(DataType):
    def to_numpy(self):
        return np.dtype(float)

    def cast(self, value: object) -> NoReturn:
        raise TypeError(f"Cannot cast value to Nothing: {value}")


@dataclass(frozen=True, slots=True)
class Dynamic(DataType):
    def to_numpy(self):
        return None

    def cast(self, value: object) -> object:
        return value
