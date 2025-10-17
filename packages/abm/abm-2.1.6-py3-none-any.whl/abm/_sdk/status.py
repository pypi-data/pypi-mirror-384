__all__ = ["Status"]

from enum import StrEnum, auto


class Status(StrEnum):
    submitted = auto()
    succeeded = auto()
    failed = auto()
