__all__ = ["OdePosteriorSampleConfiguration"]

from dataclasses import dataclass
from typing import Literal

from serialite import serializable


@serializable
@dataclass(frozen=True)
class OdePosteriorSampleConfiguration:
    """Configuration settings for parameter posterior sampling.

    Attributes
    ----------
    method: `str`, default="NUTS"
        Algorithm to use for the posterior sampling. The possible methods are
        the following pymc.sample step methods:  NUTS ("No U-Turn Sampler"),
        HamiltonianMC, Metropolis, DEMetropolisZ, and Slice.
    tune: `int`, default=1000
        Number of iterations for method-specific algorithm parameter tuning.
    discard_tuned_samples: `bool`, default=True
        Whether to discard the samples used in the tuning phase. Note that tuned
        samples are a biased sample of the underlying posterior distribution and
        should only be used in situations where statistical correctness is not
        required.
    thin: `int`, default=1
        Out of `n` * `thin` raw samples drawn, every `thin` samples are re-
        tained for the final output table.  Can be used to reduce auto-
        correlation among samples.
    """

    method: Literal["NUTS", "HamiltonianMC", "Metropolis", "DEMetropolisZ", "Slice"] = "NUTS"
    tune: int = 1000
    discard_tuned_samples: bool = True
    thin: int = 1
