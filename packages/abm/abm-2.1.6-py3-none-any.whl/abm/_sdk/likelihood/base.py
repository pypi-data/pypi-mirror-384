__all__ = ["LikelihoodFunction", "LikelihoodFunctionPredictions", "LikelihoodFunctionResiduals"]

from dataclasses import dataclass

from serialite import abstract_serializable


@abstract_serializable
class LikelihoodFunction:
    __slots__ = ()


@abstract_serializable
@dataclass(frozen=True, slots=True)
class LikelihoodFunctionPredictions:
    pass


@abstract_serializable
@dataclass(frozen=True, slots=True)
class LikelihoodFunctionResiduals:
    log_likelihood: float
