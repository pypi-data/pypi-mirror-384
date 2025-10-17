__all__ = ["Distribution", "DistributionPrediction", "DistributionResidual"]

from dataclasses import dataclass

from serialite import abstract_serializable


@abstract_serializable
@dataclass(frozen=True, kw_only=True, slots=True)
class Distribution:
    pass


@abstract_serializable
@dataclass(frozen=True, kw_only=True, slots=True)
class DistributionPrediction:
    pass


@abstract_serializable
@dataclass(frozen=True, kw_only=True, slots=True)
class DistributionResidual:
    pass
