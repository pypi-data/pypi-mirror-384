__all__ = ["OdeGradient"]


from dataclasses import dataclass

from serialite import serializable

from .scenario import Scenario


@serializable
@dataclass(frozen=True, kw_only=True)
class OdeGradient:
    """Compute scenario objective gradient with respect to active_parameters."""

    scenario: Scenario
    active_parameters: set[str] | None = None
