__all__ = [
    "IndexIndexValuePairState",
    "IndexRelativeValueState",
    "MultipleIndicesKeyState",
]

from dataclasses import dataclass
from uuid import UUID

from serialite import serializable


@serializable
@dataclass(frozen=True, kw_only=True)
class IndexIndexValuePairState:
    index_id: UUID
    index_value: int


@serializable
@dataclass(frozen=True, kw_only=True)
class IndexRelativeValueState:
    id: UUID
    offset: int | None = None
    offset_wraps: bool | None = None
    index_value: str | None = None
    index_value_variable: str | None = None


@serializable
@dataclass(frozen=True, kw_only=True)
class MultipleIndicesKeyState:
    pairs: list[IndexIndexValuePairState]
    runtime_pairs: list[IndexRelativeValueState]
