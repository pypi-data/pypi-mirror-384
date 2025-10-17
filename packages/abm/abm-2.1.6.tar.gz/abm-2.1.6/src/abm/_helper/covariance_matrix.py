__all__ = ["AnnotatedFisherRow", "confidence_intervals"]

from dataclasses import dataclass

import numpy as np

from .._sdk.data_frame import DataFrame
from .._sdk.ode_optimization_result import UnittedValue
from .._sdk.scenario import Prior
from .helper import scale_parameter, unscale_parameter


@dataclass(frozen=True, slots=True, kw_only=True)
class AnnotatedFisherRow:
    """A row of the Fisher information matrix along with the corresponding parameter value and prior."""

    parameter_value: float
    parameter_prior: Prior
    values: dict[str, UnittedValue]


def _theta(annotated_matrix: dict[str, AnnotatedFisherRow]) -> np.ndarray:
    return np.asarray([row.parameter_value for row in annotated_matrix.values()])


def _theta_is_logscale(annotated_matrix: dict[str, AnnotatedFisherRow]) -> list[bool]:
    return [row.parameter_prior.is_logscaled for row in annotated_matrix.values()]


def _information_unit(annotated_matrix: dict[str, AnnotatedFisherRow]):
    return np.asarray([[val.unit for val in row.values.values()] for row in annotated_matrix.values()])


def _information_matrix(annotated_matrix: dict[str, AnnotatedFisherRow]) -> list[list[float]]:
    return [[val.value for val in row.values.values()] for row in annotated_matrix.values()]


def covariance_matrix(
    annotated_fisher_information: dict[str, AnnotatedFisherRow],
    uncertainty_ceiling: float = float("inf"),
) -> list[list[float]]:
    """Transform information matrix into covariance intervals.

    Parameters
    ----------
    fisher_information: dict[str, AnnotatedFisherRow]
    uncertainty_ceiling : float, default = inf
        If some parameters are numerically non-identifiable, the information
        on those parameters is very low and the uncertainties very high. In
        this situation, inverting the information matrix is numerically
        unstable, which can result in a bunch of junk for the covariance
        matrix. A value like 1e8 is a good
        number to try if the scenario appears to be non-identifiable.

    Returns
    -------
    List[List[float]]
    """

    eigenvalue_threshold = 1.0 / uncertainty_ceiling**2

    information_matrix_values = np.asarray(_information_matrix(annotated_fisher_information))
    theta = _theta(annotated_fisher_information)
    theta_is_logscale = _theta_is_logscale(annotated_fisher_information)
    theta_array = np.where(theta_is_logscale, theta, 1.0)

    information_matrix = np.einsum("i,ij,j->ij", theta_array, information_matrix_values, theta_array)

    modified_covariance = fisher_information_inverse(information_matrix, eigenvalue_threshold)

    return modified_covariance


def confidence_intervals(
    annotated_fisher_information: dict[str, AnnotatedFisherRow],
    fraction: float,
    uncertainty_ceiling: float = float("inf"),
) -> DataFrame:
    """Transform information matrix into confidence intervals.

    Parameters
    ----------
    annotated_fisher_information: dict[str, AnnotatedFisherRow]
    fraction : float
        The fraction of the distribution to contain within the CI. Use 0.95
        for 95% confidence intervals.
    uncertainty_ceiling : float, default = inf
        If some parameters are numerically non-identifiable, the information
        on those parameters is very low and the uncertainties very high. In
        this situation, inverting the information matrix is numerically
        unstable, which can result in a bunch of junk for the confidence
        intervals. Choosing a ceiling will prevent uncertainties from going
        larger than that, which can prevent large uncertainties from
        polluting the rest of the uncertainties. A value like 1e8 is a good
        number to try if the scenario appears to be non-identifiable.

    Returns
    -------
    DataFrame with columns:
        parameter: str
        value: float
        unit: str
        scale: "linear" | "log"
        lower: float
        upper: float
    """

    from scipy import stats

    if uncertainty_ceiling <= 0.0:
        raise ValueError("Argument 'uncertainty_ceiling' must be positive.")

    modified_covariance = covariance_matrix(annotated_fisher_information, uncertainty_ceiling)

    sigma = np.sqrt(np.diag(modified_covariance))
    lower = []
    upper = []
    theta = _theta(annotated_fisher_information)
    theta_is_logscale = _theta_is_logscale(annotated_fisher_information)

    for t, maybe_scaled_sigma, is_log in zip(theta, sigma, theta_is_logscale, strict=True):
        scaled_mean = scale_parameter(is_log, t)
        scaled_lower, scaled_upper = stats.norm.interval(fraction, scaled_mean, maybe_scaled_sigma)
        lower.append(unscale_parameter(is_log, scaled_lower))
        upper.append(unscale_parameter(is_log, scaled_upper))

    # These units are ugly and also different (in terms of formatting) from what _optimize returns. This
    # should be fixed in the future when Renan's work for diagnostics is in.
    parameter_units = [f"(1/({unit}))^0.5" for unit in np.diag(_information_unit(annotated_fisher_information))]

    return DataFrame(
        parameter=list(annotated_fisher_information.keys()),
        value=theta.tolist(),
        unit=parameter_units,
        scale=["log" if is_log else "linear" for is_log in theta_is_logscale],
        lower=lower,
        upper=upper,
    )


def fisher_information_inverse(F: np.ndarray, eigenvalue_threshold: float = 0.0) -> np.ndarray:
    # for stable inversion of Fisher information matrix; used in confidence_intervals() below

    # locate inf/-inf on diag
    finite_indices = ~np.isinf(np.diag(F))

    # cut out zero/inf indices before inversion
    F_finite = F[np.ix_(finite_indices, finite_indices)]
    L, Q = np.linalg.eigh(F_finite)

    # floor small eigenvalues at threshold
    L[L < eigenvalue_threshold] = eigenvalue_threshold

    # identify indices of exactly zero eigenvalues
    zero_eigs = L == 0.0

    # invert floored eigenvalues, compose modified inverse
    Finv_finite = Q[:, ~zero_eigs] @ np.diag(1.0 / L[~zero_eigs]) @ Q[:, ~zero_eigs].T

    # For exactly zero eigenvalues after flooring, examine entries of corresponding eigenvectors.  Nonzero (> Qthresh)
    # eigenvector entries correspond to columns of F_finite which are nontrivial contributions to this kernel.  Such
    # columns/rows of Finv are set to zero with inf on diagonal.
    Qthresh = F_finite.shape[0] * np.finfo("float").eps
    kernel_cols = np.any(np.abs(Q[:, zero_eigs]) > Qthresh, axis=1)
    Finv_finite[kernel_cols, :] = 0.0
    Finv_finite[:, kernel_cols] = 0.0
    Finv_finite[kernel_cols, kernel_cols] = np.inf

    # Initialize full output, fill in modified inverse
    # (Note inf on diag(A) -> 0 on corresponding row/col of inverse).
    Finv_out = np.zeros(F.shape)
    Finv_out[np.ix_(finite_indices, finite_indices)] = Finv_finite

    return Finv_out
