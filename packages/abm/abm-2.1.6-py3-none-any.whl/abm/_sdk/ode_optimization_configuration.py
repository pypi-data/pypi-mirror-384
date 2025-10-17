__all__ = ["OdeOptimizationConfiguration"]

import math
from dataclasses import dataclass
from typing import Literal

from serialite import serializable


@serializable
@dataclass(frozen=True)
class OdeOptimizationConfiguration:
    """Optimization option configuration.

    Attributes
    ----------
    method : `'scipy-L-BFGS-B'`,
        `'scipy-TNC'`,
        `'scipy-COBYLA'`,
        `'scipy-SLSQP'`,
        `'scipy-trust-constr'`,
        `'scipy-CG'`,
        `'scipy-BFGS'`,
        `'scipy-Newton-CG'`,
        `'scipy-Nelder-Mead'`,
        `'scipy-Powell'`,
        `'scipy-dual-annealing'`,
        `'fides-BFGS'`,
        `'fides-DFP'`,
        `'fides-Broyden'`,
        `'fides-SR1'`,
        `'fides-BG'`,
        `'fides-BB'`,
        default=`'fides-BFGS'`.
        Algorithm to use for the optimization. The possible methods are the
        supported `scipy.optimize.minimize` methods and `fides` Hessian
        approximation methods.  Note that `'scipy-CG'`, `'scipy-BFGS'`,
        `'scipy-Newton-CG'`, and `'scipy-Powell'` ignore bounds. Also note
        that `'scipy-dual-annealing'` requires a seed be input.
    max_iterations: int, default = 1000
        Maximum number of iterations allowed. Upon reaching the limit, the
        optimization finishes.
    max_objective_evaluations: int, default = 100000
        Maximum number of objective function evaluations allowed. This is not
        a hard limit, and is only used for simulated annealing.
    min_objective: float, default = -inf
        If the objective value is less than or equal to `min_objective` on a
        particular iteration, the optimization finishes.
    objective_tolerance : float, default = 1e-8
        Tolerance on the objective function value used to determine when the
        optimization has converged. When an iteration decreases the objective
        function by less than this value, the optimization finishes.
    """

    method: Literal[
        "scipy-L-BFGS-B",
        "scipy-TNC",
        "scipy-COBYLA",
        "scipy-SLSQP",
        "scipy-trust-constr",
        "scipy-CG",
        "scipy-BFGS",
        "scipy-Newton-CG",
        "scipy-Nelder-Mead",
        "scipy-Powell",
        "scipy-dual-annealing",
        "fides-BFGS",
        "fides-DFP",
        "fides-Broyden",
        "fides-SR1",
        "fides-BG",
        "fides-BB",
    ] = "fides-BFGS"
    max_iterations: int = 1000
    max_objective_evaluations: int = 100000
    min_objective: float = -math.inf
    objective_tolerance: float = 1e-8
    seed: int | None = None
