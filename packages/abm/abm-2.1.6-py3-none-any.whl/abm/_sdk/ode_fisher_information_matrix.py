from __future__ import annotations

__all__ = ["OdeFisherInformationMatrix"]

from dataclasses import dataclass

from serialite import serializable

from .scenario import Scenario


@serializable
@dataclass(frozen=True, kw_only=True)
class OdeFisherInformationMatrix:
    scenario: Scenario
