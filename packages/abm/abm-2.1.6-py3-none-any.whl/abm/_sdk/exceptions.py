__all__ = ["JobRuntimeError"]

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True, kw_only=True)
class JobRuntimeError(Exception):
    _type: str
    payload: Any
    message: str
    traceback: list[str]

    def __str__(self) -> str:
        return f"{self._type}: {self.message}"
