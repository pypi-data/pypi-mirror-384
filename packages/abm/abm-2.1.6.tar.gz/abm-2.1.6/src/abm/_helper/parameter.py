__all__ = ["Parameter", "ScanParameter"]

from dataclasses import dataclass

from abm._sdk.expression import Unit


@dataclass(frozen=True)
class Parameter:
    value: float
    unit: Unit | None = None


@dataclass(frozen=True, kw_only=True)
class ScanParameter(Parameter):
    fold: float
