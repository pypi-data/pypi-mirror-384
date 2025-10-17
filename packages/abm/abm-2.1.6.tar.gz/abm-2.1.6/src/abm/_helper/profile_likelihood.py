__all__ = ["ThresholdMethod", "check_empty_profiles", "threaded_profile_likelihood"]

import math
from dataclasses import dataclass
from enum import StrEnum, auto
from typing import Callable, Literal

import numpy as np
from prettytable import PrettyTable
from returns.result import Result, Success

from .._sdk.client_interface import ThreadPoolExecutor
from .._sdk.data_frame import DataFrame
from .._sdk.data_pipe import DataPipe
from .._sdk.data_pipe_builder import concatenate_rows
from .._sdk.expression import Unit


class ThresholdMethod(StrEnum):
    step_over = auto()
    linear_interpolation = auto()


class ProfileTermination(StrEnum):
    threshold = auto()
    bound = auto()
    max_iterations = auto()
    reversal = auto()
    error = auto()


# Type hints purely for better syntax highlighting (avoiding confusion with the str.lower, etc. methods)
class ProfileDirection(StrEnum):
    lower: str = auto()
    upper: str = auto()


@dataclass(frozen=True, slots=True)
class OneSidedProfile:
    T: list[float]
    G: list[float]
    termination: ProfileTermination
    threshold: tuple[float, float] | None  # (T, G) pair if termination="threshold", None otherwise

    @property
    def is_empty(self) -> bool:
        assert len(self.T) == len(self.G)
        return len(self.T) == 0

    def to_data_pipe(self) -> DataPipe:
        if self.threshold is None:
            T_threshold, G_threshold = math.nan, math.nan
        else:
            T_threshold, G_threshold = self.threshold

        return DataFrame(
            scaled_parameter_value=self.T,
            objective_value=self.G,
            termination=self.termination,
            scaled_parameter_threshold=T_threshold,
            objective_threshold=G_threshold,
        ).to_data_pipe()


@dataclass(frozen=True, slots=True, kw_only=True)
class TwoSidedProfile:
    lower: OneSidedProfile
    upper: OneSidedProfile

    def to_data_pipe(self, *, name: str, unit: Unit, is_logscaled: bool) -> DataPipe:
        lower = self.lower.to_data_pipe().mutate(direction=f"'{ProfileDirection.lower}'")
        upper = self.upper.to_data_pipe().mutate(direction=f"'{ProfileDirection.upper}'")
        scaled = concatenate_rows(lower, upper).mutate(parameter_name=f"'{name}'", parameter_unit=f"'{unit}'")

        # It is a little weird that some of the scaling operations are done client-side, while this un-scaling is done
        # server-side, but we choose to do this as one contiguous data pipe.
        if is_logscaled:
            with_unscaled = scaled.mutate(
                parameter_value="exp(scaled_parameter_value)", parameter_threshold="exp(scaled_parameter_threshold)"
            )
        else:
            with_unscaled = scaled.mutate(
                parameter_value="scaled_parameter_value", parameter_threshold="scaled_parameter_threshold"
            )

        # Drop the scaled columns and reorganize
        reorganized = with_unscaled.select(
            "parameter_name",
            "parameter_value",
            "parameter_unit",
            "objective_value",
            "direction",
            "termination",
            "parameter_threshold",
            "objective_threshold",
        )
        return reorganized


def _single_profile(
    fun_grad: Callable[[float], Result[tuple[float, float], None]],
    initial: float,
    direction: Literal[-1, 1],
    *,
    target_threshold: float,
    precision: float,
    max_iterations: int,
    min_step: float,
    max_step: float,
    bound: float | None,
    reversal_reltol: float,
    reversal_abstol: float,
    threshold_method: ThresholdMethod,
) -> OneSidedProfile:
    if bound is None:
        bound = direction * math.inf

    # Analytically, we want theta_step ~= precision * target_threshold / gradient
    # We bound the computed gradient to ensure min_step <= dir * theta_step <= max_step
    # Define reflected_G_dT := dir * G_dT; we want this bounded away from zero and above.
    # Note that if reflected_G_dT is sufficiently negative, this indicates a reversal and terminates the algorithm.
    target_G_step = precision * target_threshold
    min_reflected_G_dT = target_G_step / max_step
    max_reflected_G_dT = target_G_step / min_step

    T_out = np.zeros(max_iterations)
    G_out = np.zeros(max_iterations)

    n = 0
    T = initial
    G0: float | None = None  # Set on first step
    threshold = None
    termination: ProfileTermination | None = None
    while True:
        if n >= max_iterations:
            termination = ProfileTermination.max_iterations
            break

        # Check whether we've crossed a parameter bound
        if not np.isfinite(T) or direction * (T - bound) > 0.0:
            termination = ProfileTermination.bound
            break

        # Calculate current profile likelihood value and its gradient
        match fun_grad(T):
            case Success((G, G_dT)):
                pass
            case _:
                termination = ProfileTermination.error
                break

        # First step only
        if n == 0:
            G0 = G

        # Check whether we've crossed the threshold
        if G - G0 >= target_threshold:
            termination = ProfileTermination.threshold
            if threshold_method == ThresholdMethod.linear_interpolation and n >= 1:
                T_prev = T_out[n - 1]
                G_prev = G_out[n - 1]
                if not G - G0 > G_prev - G0:
                    # Shouldn't be here; we would have crossed the threshold last step
                    raise ValueError("Cannot interpolate because the objective did not increase last step.")
                T_interp = float(np.interp(target_threshold, [G_prev - G0, G - G0], [T_prev, T]))
                threshold = (T_interp, G0 + target_threshold)
            else:  # threshold_method == "step_over" or at first step
                threshold = (T, G)
            break

        # Check for reversal
        reflected_G_dT = direction * G_dT
        if reflected_G_dT < -(reversal_reltol * np.abs(G) + reversal_abstol):
            termination = ProfileTermination.reversal
            break

        # Save current T and G before taking step
        T_out[n] = T
        G_out[n] = G

        # reflected_G_dT is sufficiently nonnegative; clamp it, and reflect back
        clamped_G_dT = direction * np.clip(reflected_G_dT, min_reflected_G_dT, max_reflected_G_dT)

        # Take step, keeping T a Python float for cleanliness
        step = float(target_G_step / clamped_G_dT)
        T += step
        n += 1

    assert termination is not None
    return OneSidedProfile(T_out[:n].tolist(), G_out[:n].tolist(), termination, threshold)


def threaded_profile_likelihood(
    fun_grad: Callable[[str, float], Result[tuple[float, float], None]],
    initial: dict[str, float],
    *,
    target_threshold: float = 3.841,  # 95% critical value of χ^2 distribution with df=1
    precision: float = 0.1,  # q in Raue et. al.: target stepwise change in the objective
    max_iterations: int | None = None,  # if None, set to 10 / precision
    min_step: float = 1e-6,
    max_step: float = 0.18,  # ~log(1.2); from the Raue et. al. default max_step = 0.2 * theta
    lower_bound: dict[str, float] = {},
    upper_bound: dict[str, float] = {},
    reversal_reltol: float = 1e-7,  # Detect reversals when G_dT < reltol * |G| + abstol for the positive direction,
    reversal_abstol: float = 1e-8,  # or G_dT > reltol * |G| + abstol for the negative direction
    threshold_method: ThresholdMethod = ThresholdMethod.linear_interpolation,
    max_pool_size: int | None = None,
) -> dict[str, TwoSidedProfile]:
    """Implements a variation on the profile likelihood algorithm of Raue et. al. (2009)."""
    if not target_threshold > 0.0:
        raise ValueError(f"Expected target_threshold > 0, got {target_threshold}")

    if not 0.0 < precision <= 1.0:
        raise ValueError(f"Expected 0 < precision <= 1, got {precision}")

    if not min_step >= 0.0:
        raise ValueError(f"Expected min_step >= 0, got {min_step}")

    if not max_step >= 0.0:
        raise ValueError(f"Expected max_step >= 0, got {max_step}")

    if not min_step <= max_step:
        raise ValueError(f"Expected min_step <= max_step, got min_step={min_step} and max_step={max_step}")

    if not reversal_reltol >= 0.0:
        raise ValueError(f"Expected reversal_reltol >= 0, got {reversal_reltol}")

    if not reversal_abstol >= 0.0:
        raise ValueError(f"Expected reversal_abstol >= 0, got {reversal_abstol}")

    if max_iterations is None:
        max_iterations = int(10.0 / precision)

    def _single_profile_partial(args: tuple[str, float, Literal[1, -1]]) -> OneSidedProfile:
        name, T0_val, dir = args
        return _single_profile(
            lambda T: fun_grad(name, T),
            T0_val,
            dir,
            target_threshold=target_threshold,
            precision=precision,
            max_iterations=max_iterations,
            min_step=min_step,
            max_step=max_step,
            reversal_reltol=reversal_reltol,
            reversal_abstol=reversal_abstol,
            threshold_method=threshold_method,
            bound=upper_bound.get(name, None) if dir > 0 else lower_bound.get(name, None),
        )

    lower_inputs = [(name, T0_val, -1) for name, T0_val in initial.items()]
    upper_inputs = [(name, T0_val, 1) for name, T0_val in initial.items()]
    inputs = [*lower_inputs, *upper_inputs]
    nT = len(initial)

    if max_pool_size is None:
        results = list(map(_single_profile_partial, inputs))
    else:
        with ThreadPoolExecutor(max_workers=min(len(inputs), max_pool_size)) as pool:
            results = list(pool.map(_single_profile_partial, inputs))

    lower_results = results[:nT]
    upper_results = results[nT:]
    combined_results = {
        name: TwoSidedProfile(lower=lower, upper=upper)
        for name, lower, upper in zip(initial.keys(), lower_results, upper_results, strict=True)
    }
    return combined_results


def check_empty_profiles(profiles: dict[str, TwoSidedProfile]) -> None:
    # Profiles which terminate on the first step (for whatever reason) are technically valid, but we can't meaningfully
    # convert them to a table, so we raise an error instead.
    entries: list[tuple[str, ProfileDirection, ProfileTermination]] = []
    for name, profile in profiles.items():
        if profile.lower.is_empty:
            entries.append((name, ProfileDirection.lower, profile.lower.termination))
        if profile.upper.is_empty:
            entries.append((name, ProfileDirection.upper, profile.upper.termination))

    if len(entries) == 0:
        return

    table = PrettyTable(["parameter_name", "direction", "termination"])
    table.add_rows(entries)
    raise ValueError(f"The following profiles terminated at the initial step:\n{table}")
