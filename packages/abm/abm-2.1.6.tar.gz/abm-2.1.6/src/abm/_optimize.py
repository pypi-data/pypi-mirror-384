from __future__ import annotations

__all__ = ["OptimizationResult", "optimize"]

import math
import re
from dataclasses import dataclass, replace
from typing import Literal

import tabeline as tl
from ordered_set import OrderedSet
from returns.result import Failure, Result, Success
from scipy import stats

from ._helper.covariance_matrix import AnnotatedFisherRow, confidence_intervals
from ._helper.create_map import (
    create_doses_map,
    create_fitting_parameters_map,
    create_measurements_map,
    create_models_map,
)
from ._helper.get_dose_schedules import get_dose_schedules
from ._helper.get_model import get_model_types_i, get_remote_model
from ._helper.helper import (
    DataFrameLike,
    PathLike,
    find_duplicate_keys,
    maybe_add_parentheses,
    replace_none_with_asterisk,
    scale_parameter,
    unscale_parameter,
)
from ._helper.parameter import Parameter
from ._helper.posterior_sample_list_diagnostics import divergences
from ._helper.profile_likelihood import (
    check_empty_profiles,
    threaded_profile_likelihood,
)
from ._helper.validate_columns import (
    necessary_dose_columns,
    necessary_fitting_parameter_columns,
    necessary_model_columns,
    optional_dose_columns,
    optional_fitting_parameter_columns,
    validate_and_process_dose_table,
    validate_and_process_fitting_parameter_tables,
    validate_and_process_measurements_table,
    validate_and_process_model_table,
)
from ._labelset import LabelSet
from ._sdk import client
from ._sdk.contract import Contract
from ._sdk.data_frame import DataFrame
from ._sdk.data_pipe import (
    ConcatenateRowsElement,
    OdeParameterPosteriorSampleElement,
    OdeParameterPosteriorSampleListDiagnosticElement,
    OdeResidualElement,
)
from ._sdk.data_pipe_result import DataPipeResult
from ._sdk.job import Job
from ._sdk.likelihood import Measurement, MeasurementsLikelihoodFunction
from ._sdk.ode_fisher_information_matrix import OdeFisherInformationMatrix
from ._sdk.ode_gradient import OdeGradient
from ._sdk.ode_model_reference import OdeModelReference
from ._sdk.ode_optimization import OdeOptimization
from ._sdk.ode_optimization_configuration import OdeOptimizationConfiguration
from ._sdk.ode_optimization_result import OdeOptimizationResult, UnittedValue
from ._sdk.ode_parameter_posterior_sample import OdeParameterPosteriorSample
from ._sdk.ode_posterior_sample_configuration import OdePosteriorSampleConfiguration
from ._sdk.ode_residual import OdeResidual
from ._sdk.scenario import (
    LaplacePrior,
    LogLaplacePrior,
    LogNormalPrior,
    LogUniformPrior,
    NormalPrior,
    Scenario,
    ScenarioParameter,
    UniformPrior,
)
from ._sdk.solver_configuration import (
    BdfSolver,
    KluSolver,
    SolverConfiguration,
    SpgmrSolver,
)
from ._sdk.status import Status
from ._sdk.times import Times
from ._simulate import SimulationResult, simulate
from ._units.comparison import is_equivalent


def optimize(
    *,
    measurements: DataFrameLike | PathLike,
    models: DataFrameLike | PathLike,
    parameters: DataFrameLike | PathLike,
    doses: DataFrameLike | PathLike | None = None,
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
    ] = "fides-BFGS",
    max_iterations: int = 1000,
    max_objective_evaluations: int = 100000,
    min_objective: float = -math.inf,
    opttol: float = 1e-8,
    gradient_method: Literal["forward", "adjoint"] = "forward",
    linear_solver: Literal["KLU", "SPGMR"] = "KLU",
    reltol: float = 1e-6,
    abstol: float = 1e-9,
    maxstep: float = math.inf,
    maxord: int = 5,
    nonnegative: bool | dict[str, bool] = False,
    max_steps: int | None = None,
    seed: int | None = None,
) -> OptimizationResult:
    """Optimize a table of parameters based on a table of measurements.

    Parameters
    ----------
    measurements: pd.DataFrame | tl.DataFrame | DataFrame | Path | str
        Experimental data table with columns:
            `time`: float, time of measurement
            `time_unit`: str, unit for `time`
            `output`: str, name of a model output
            `measurement`: float, value of measurement
            `measurement_unit`: str, unit for `measurement` and `constant_error`
            `constant_error`: float, constant error for measurement, default = 0.0
            `proportional_error`: float, proportional error for measurement, unitless, default = 0.0
            `exponential_error`: float, exponential error for measurement, unitless, default = 0.0

        At least one of the error columns must be non-zero for each row. If `exponential_error` is
        non-zero, then the the other two error types must be zero.

        This table may also have arbitrary columns in addition to those listed. Each record in
        those label columns is used to match records in columns of the same name in the models,
        parameters, and doses tables. Those that match determine the simulation in which the
        measurement is taken. In the other tables, a "*" may be used in a label column to indicate
        that that row should match any value in the measurement table.
    models: pd.DataFrame | tl.DataFrame | DataFrame | Path | str
        A model or a data frame or a path to a CSV file. If a data frame or CSV, it must have a
        `model` column indicating the path to the model file.
    parameters: pd.DataFrame | tl.DataFrame | DataFrame | Path | str
        Parameter value table with columns:
            `parameter`: str, name of parameter
            `value`: float, value of parameter
            `unit`: str, unit for `value`
            `is_fit`: bool, whether parameter is fit
            `lower_bound`: float, lower bound for parameter
            `upper_bound`: float, upper bound for parameter
            `prior_distribution`: "uniform" | "loguniform" | "normal" | "lognormal" | "laplace" | "loglaplace"
                prior distribution for parameter, default = "loguniform"
            `location`: float, location parameter of prior distribution.  Ignored for "uniform" and "loguniform" and
                mandatory for the other distributions.
            `scale`: float, scale parameter of prior distribution.  Ignored for "uniform" and "loguniform" and
                mandatory for the other distributions.
    doses: pd.DataFrame | tl.DataFrame | DataFrame | Path | str | None
        Dose table with columns:
            `route`: str, name of a model route
            `times`: float or list[float], times of the doses
            `time_unit`: str, unit for `times`
            `amounts`: float or list[float], amount of the doses
            `amount_unit`: str, unit for `amounts`
            `durations`: float or list[float], duration of the doses, default = 0.0
            `duration_unit`: str, unit for `durations`, only mandatory if `durations` is not zero

        Each cell that is a scalar is broadcast the length of the other vectors. The vectors in the
        cells of a given row must all be the same length.

        If None, the model schedules are used.
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
    opttol: float, default = 1e-8
        Tolerance on the objective function value used to determine when the
        optimization has converged. When an iteration decreases the objective
        function by less than this value, the optimization finishes.
    linear_solver: `'KLU'`, `'SPGMR'`, default=`'KLU'`
        Linear solver used by the ODE solver to solve the implicit formula for
        each integration step. Generally this should not be changed from the
        default.
    reltol: `float`, default=1e-6
        Relative tolerance of the integration.
    abstol: `float`, default=1e-9
        Absolute tolerance of the integration.
    maxstep : `float`, default=inf
        Maximum time step allowed during integration. Generally, this should not
        be changed from the default (unbounded).
    maxord: `int`, default=5
        Maximum order of the linear multistep formulas used by the ODE solver.
        Setting to a lower value results in smaller but more stable time steps.
        Generally it is recommended to use the largest value that converges.
    nonnegative: `bool` or `dict[str, bool]`, default=`False`
        Substitute 0 for negative values in the indicated states when evaluating
        the ODE right-hand side. This is useful for avoiding numerical
        difficulties with model expressions like `sqrt` that are not real or not
        defined for negative values. If `False`, no states are substituted if
        negative. If `True`, all states are substituted if negative. If a
        `dict[str, bool]` is provided, any keys with `True` values are
        interpreted as state names to be substituted; any states not appearing
        in the dictionary are not substituted.
    max_steps: `int` or `None`, default=`None`
        If `gradient_method = 'forward'`:
            The maximum number of steps allowed for an integration. If `None`, the
            limit is disabled.
        If `gradient_method = 'adjoint'`:
            The maximum number of steps allowed for a forward integration. If `None`,
            the limit is disabled for a forward integration. Additionally, `max_steps`
            will be used as the limit for internal CVODES backward integration steps
            when integrating a single interval of the adjoint sensitivity equations.
            If `None`, the limit for internal CVODES backward integration steps is
            5000.
        Generally, this should not be changed from default. If an optimization tries
        a parameterization that makes a model hang for a long time, and a crash of the
        optimization is preferred over waiting, this parameter can be used to enforce
        a limit on the amount of time a single integration takes.

    Returns
    -------
    OptimizationResult
    """
    # initial validation and processing of the incoming tables
    measurements = validate_and_process_measurements_table(measurements)
    processed_models = validate_and_process_model_table(models)
    parameters = validate_and_process_fitting_parameter_tables(parameters)
    doses = validate_and_process_dose_table(doses)

    measurements_column_names = OrderedSet(measurements.column_names)

    # find label columns:
    maybe_label_columns_from_models = set(processed_models.column_names) - necessary_model_columns

    maybe_label_columns_from_parameters = set(parameters.column_names) - (
        necessary_fitting_parameter_columns | optional_fitting_parameter_columns
    )
    maybe_label_columns_from_doses = set(doses.column_names) - (necessary_dose_columns | optional_dose_columns)

    # label columns are the intersection of the columns from measurements and unnecessary columns the models,
    # parameters, and doses
    label_columns = OrderedSet(
        measurements_column_names.intersection(
            maybe_label_columns_from_models | maybe_label_columns_from_parameters | maybe_label_columns_from_doses
        )
    )

    # Assign a unique parameter name for each row for defining the global parameters
    parameters = parameters.mutate(global_parameter_name="parameter + '_fit_' + to_string(row_index0())")

    not_label_columns = measurements_column_names - label_columns

    # make a simulation table out of label columns
    simulation_table = measurements.deselect(*not_label_columns)
    unique_simulations = simulation_table.unique()

    # Add id column for each simulation for residuals
    unique_simulations = unique_simulations.mutate(id="row_index0()")
    simulation_labels = LabelSet.from_df(unique_simulations)

    # build measurement map
    measurements_labels = label_columns.intersection(measurements_column_names).items
    measurements_map = create_measurements_map(measurements, measurements_labels)

    # build the parameter map
    parameters_labels = label_columns.intersection(OrderedSet(parameters.column_names)).items
    parameters_map = create_fitting_parameters_map(parameters, parameters_labels)

    # build the dose map
    doses_labels = label_columns.intersection(OrderedSet(doses.column_names)).items
    doses_map = create_doses_map(doses, doses_labels)

    # Parse and store the models
    model_paths = set(processed_models[:, "model"])
    remote_model_map = {
        model_path: get_remote_model(model_path).refresh(include_types=True) for model_path in model_paths
    }
    models_labels = label_columns.intersection(OrderedSet(processed_models.column_names)).items
    models_map = create_models_map(processed_models, models_labels)

    likelihood_functions = []
    global_parameters = {}

    match linear_solver:
        case "KLU":
            linear_solver_obj = KluSolver()
        case "SPGMR":
            linear_solver_obj = SpgmrSolver()
        case unsupported:
            raise ValueError(f"Unsupported linear solver {unsupported}")

    solver_configuration = SolverConfiguration(
        ode_solver=BdfSolver(
            linear_solver=linear_solver_obj,
            relative_tolerance=reltol,
            absolute_tolerance=abstol,
            max_step=maxstep,
            max_order=maxord,
            max_steps=max_steps,
        ),
        nonnegative=nonnegative,
        gradient_method=gradient_method,
    )

    optimization_configuration = OdeOptimizationConfiguration(
        method=method,
        max_iterations=max_iterations,
        max_objective_evaluations=max_objective_evaluations,
        min_objective=min_objective,
        objective_tolerance=opttol,
        seed=seed,
    )

    # building the optimization has the following main steps:
    # 1) get model types
    # 2) get the data for the set of labels and do some validations.
    # 3) get the parameters for the simulation and do some validations.
    # 4) get the doses for the simulation and do some validations.
    # 5) create the OdeModelReference.
    # 6) Create a MeasurementsLikelihoodFunction

    for i_lbs, lbs in enumerate(simulation_labels):
        # Step 1) get model types
        model_list_i = models_map.get_values([lbs.labels.get(k, "*") for k in models_labels])
        model_id, types = get_model_types_i(model_list_i, remote_model_map, lbs.labels)

        # build the reference time unit from the first model:
        if i_lbs == 0:
            reference_time_unit = types.time_unit

        # check if the time unit of the model is the same as the reference time unit
        if not is_equivalent(types.time_unit, reference_time_unit):
            raise ValueError(
                f"all models must have the same time unit but model {model_id} has time unit"
                f" {types.time_unit} which is different from {reference_time_unit}"
            )

        # Step 2) Data matching this set of labels
        data_i = measurements_map.get_values([lbs.labels.get(k, "*") for k in measurements_labels])

        # This is part of step 3 but we need it to update the error expressions with global parameter name
        parameter_list_i = parameters_map.get_values([lbs.labels.get(k, "*") for k in parameters_labels])
        duplicate_parameters = find_duplicate_keys(parameter_list_i)
        if len(duplicate_parameters) > 0:
            raise ValueError(
                "Duplicate parameters found for label(s)"
                f" {', '.join([f'{key}={value}' for key, value in lbs.original_labels.items()])}:"
                f" {', '.join(duplicate_parameters)}"
            )

        parameter_pairs = [
            (value["parameter"], value["global_parameter_name"]) for dict in parameter_list_i for value in dict.values()
        ]

        # Build the Measurement object
        # The name update needs to be done this way so if the error is not the last parameter, it does not get
        # overwritten again by the old name
        measurements_i = []
        for d_i in data_i:
            if "exponential_error" in d_i.keys():
                exponential_error_j = d_i["exponential_error"]
            else:
                exponential_error_j = 0.0
            if "constant_error" in d_i.keys():
                constant_error_j = d_i["constant_error"]
            else:
                constant_error_j = "0.0"
            if "proportional_error" in d_i.keys():
                proportional_error_j = d_i["proportional_error"]
            else:
                proportional_error_j = 0.0

            # update the error expressions with global parameter name
            for old, new in parameter_pairs:
                if "exponential_error" in d_i.keys():
                    exponential_error_measurement_j = str(exponential_error_j)
                    exponential_error_j = re.sub(rf"\b{old}\b", new, exponential_error_measurement_j)
                if "constant_error" in d_i.keys():
                    constant_error_measurement_j = str(constant_error_j)
                    constant_error_j = re.sub(rf"\b{old}\b", new, constant_error_measurement_j)
                if "proportional_error" in d_i.keys():
                    proportional_error_measurement_j = str(proportional_error_j)
                    proportional_error_j = re.sub(rf"\b{old}\b", new, proportional_error_measurement_j)

            time_measurement_j = f"{d_i['time']}:{maybe_add_parentheses(d_i['time_unit'])}"
            target_measurement_j = d_i["output"]
            value_measurement_j = f"{d_i['measurement']}:{maybe_add_parentheses(d_i['measurement_unit'])}"

            if "constant_error" in d_i.keys():
                constant_error_j = f"{constant_error_j}:{maybe_add_parentheses(d_i['measurement_unit'])}"
            else:
                constant_error_j = constant_error_j
            measurements_i.append(
                Measurement(
                    time=time_measurement_j,
                    target=target_measurement_j,
                    measurement=value_measurement_j,
                    constant_error=constant_error_j,
                    proportional_error=proportional_error_j,
                    exponential_error=exponential_error_j,
                )
            )

        # Add a boolean column for model parameters
        for p in parameter_list_i:
            for v in p.values():
                v["is_model_parameter"] = v["parameter"] in types.parameters

        # Get the subset of parameters that is fit
        parameter_list_i_is_fit = [p for p in parameter_list_i for value in p.values() if value["is_fit"]]

        # Get the subset of parameters that are model parameters
        parameter_list_i_in_model = [p for p in parameter_list_i for value in p.values() if value["is_model_parameter"]]

        # Get the subset of parameters that is fit and are model parameters
        parameter_list_is_fit_is_model = [
            p for p in parameter_list_i for value in p.values() if value["is_fit"] and value["is_model_parameter"]
        ]

        mapping_i = {
            value["parameter"]: value["global_parameter_name"]
            for dic in parameter_list_is_fit_is_model
            for value in dic.values()
        }

        # Add this simulation's global parameters to the master dict that will be used as the starting values for the
        # fit, along with bounds and log-scaling information.
        global_params_i = {}
        for p in parameter_list_i_is_fit:
            for v in p.values():
                value = v["value"]
                unit = v["unit"]

                if "prior_distribution" in parameters.column_names:
                    prior_distribution = v["prior_distribution"]
                else:
                    prior_distribution = "loguniform"
                match prior_distribution:
                    case "uniform":
                        prior = UniformPrior(
                            lower=f"{v['lower_bound']}:{maybe_add_parentheses(unit)}",
                            upper=f"{v['upper_bound']}:{maybe_add_parentheses(unit)}",
                        )
                    case "loguniform":
                        prior = LogUniformPrior(
                            lower=f"{v['lower_bound']}:{maybe_add_parentheses(unit)}",
                            upper=f"{v['upper_bound']}:{maybe_add_parentheses(unit)}",
                        )
                    case "normal":
                        prior = NormalPrior(
                            mean=f"{v['location']}:{maybe_add_parentheses(unit)}",
                            standard_deviation=f"{v['scale']}:{maybe_add_parentheses(unit)}",
                            lower=f"{v['lower_bound']}:{maybe_add_parentheses(unit)}",
                            upper=f"{v['upper_bound']}:{maybe_add_parentheses(unit)}",
                        )
                    case "lognormal":
                        prior = LogNormalPrior(
                            geometric_mean=f"{v['location']}:{maybe_add_parentheses(unit)}",
                            logspace_standard_deviation=v["scale"],  # dimensionless
                            lower=f"{v['lower_bound']}:{maybe_add_parentheses(unit)}",
                            upper=f"{v['upper_bound']}:{maybe_add_parentheses(unit)}",
                        )
                    case "laplace":
                        prior = LaplacePrior(
                            mean=f"{v['location']}:{maybe_add_parentheses(unit)}",
                            mean_absolute_deviation=f"{v['scale']}:{maybe_add_parentheses(unit)}",
                            lower=f"{v['lower_bound']}:{maybe_add_parentheses(unit)}",
                            upper=f"{v['upper_bound']}:{maybe_add_parentheses(unit)}",
                        )
                    case "loglaplace":
                        prior = LogLaplacePrior(
                            geometric_mean=f"{v['location']}:{maybe_add_parentheses(unit)}",
                            logspace_mean_absolute_deviation=v["scale"],  # dimensionless
                            lower=f"{v['lower_bound']}:{maybe_add_parentheses(unit)}",
                            upper=f"{v['upper_bound']}:{maybe_add_parentheses(unit)}",
                        )
                    case _:
                        raise ValueError(
                            f"Unsupported prior distribution {prior_distribution} provided"
                            f" for fitted parameter {v['parameter']}."
                        )
                global_params_i[v["global_parameter_name"]] = ScenarioParameter(
                    value=f"{value}:{maybe_add_parentheses(unit)}",
                    unit=unit,
                    prior=prior,
                )

        # Could just update global_parameters in the loop above, but we follow the same pattern as the other dicts.
        global_parameters.update(global_params_i)

        # dictionary of parameters to update the OdeModelReference
        parameter_dict_i = {}
        for p in parameter_list_i_in_model:
            for v in p.values():
                parameter_dict_i[v["parameter"]] = Parameter(v["value"], v["unit"])

        # Step 4: get the doses for the simulation and do some validations.
        dose_i = doses_map.get_values([lbs.labels.get(k, "*") for k in doses_labels])
        route_schedules_i = get_dose_schedules(dose_i, lbs.original_labels)

        parameter_dict_i_values = {
            key: f"{param.value}:{maybe_add_parentheses(param.unit)}" for key, param in parameter_dict_i.items()
        }

        # Step 5: create the OdeModelReference
        model_reference = OdeModelReference(model_id, parameter_dict_i_values, route_schedules_i)

        # Step 6: Create a MeasurementsLikelihoodFunction and add it to the list:
        likelihood_functions.append(
            MeasurementsLikelihoodFunction(
                mapping=mapping_i,
                model=model_reference,
                measurements=measurements_i,
                configuration=solver_configuration,
            )
        )

    scenario = Scenario(global_parameters=global_parameters, likelihood_functions=likelihood_functions)
    optimization = OdeOptimization(scenario=scenario, configuration=optimization_configuration)

    # Store and run jobs
    jobs = client.create_jobs([optimization])
    contract = client.create_contract(jobs, progress=True)

    # Immediately raise if the optimization failed
    job = jobs[0]
    job.raise_if_error()

    return OptimizationResult(
        simulations=unique_simulations,
        models=models,
        parameters=parameters,
        measurements=measurements,
        doses=doses,
        solver_configuration=solver_configuration,
        scenario=scenario,
        label_columns=label_columns,
        _contract=contract,
        _job=job,
        _optimization=optimization,
    )


@dataclass(frozen=True)
class PosteriorSampleResult:
    samples: DataPipeResult
    diagnostics: OdeParameterPosteriorSampleListDiagnosticElement
    n_divergences: list[float]
    _jobs: list[Job[DataFrame, None]]
    _samples: list[OdeParameterPosteriorSample]


@dataclass(frozen=True)
class OptimizationResult:
    """Reference to an optimization and its results.

    Attributes
    ----------
    label_columns: OrderedSet[str]
        The label columns used in the optimization.
    simulations: tabeline.DataFrame
        The table that has all the unique simulations based on the label columns.
    models: DataFrameLike | PathLike:
        The model table used in the optimization.
    parameters: tabeline.DataFrame`
        Parameter table used in the optimization.
    measurements: tabeline.DataFrame
        Measurements table used in the optimization.
    doses: tabeline.DataFrame
        Dose table used in the optimization.
    solver_configuration: SolverConfiguration
        Configuration of the ODE solver
    scenario: Scenario
        The scenario used in the optimization. It has the starting values of the global parameters and the
        likelihood functions.
    _contract: Contract
        Handle to the contract that is running the optimization.
    _job: Job[OdeOptimizationResult, None]
        Optimization job.
    _optimization: Optimization
        Optimization object.
    """

    label_columns: OrderedSet[str]
    simulations: tl.DataFrame
    models: DataFrameLike | PathLike
    parameters: tl.DataFrame
    measurements: tl.DataFrame
    doses: tl.DataFrame
    solver_configuration: SolverConfiguration
    scenario: Scenario
    _contract: Contract
    _job: Job[OdeOptimizationResult, None]
    _optimization: OdeOptimization

    @property
    def _initial_global_parameters(self):
        """The initial global parameters of the optimization."""
        return self.scenario.global_parameters

    @property
    def _fit_global_parameters_dict(self):
        """The fitted global parameters of the optimization as a dictionary of str and value."""
        return {key: value.value for key, value in self._job.output_or_raise().global_parameters.items()}

    @property
    def _fit_global_parameters_unit(self):
        """The fitted global parameters of the optimization as a dictionary of str and value."""
        return {key: value.unit for key, value in self._job.output_or_raise().global_parameters.items()}

    @property
    def _fit_global_parameters(self) -> dict[str, ScenarioParameter]:
        """The fitted global parameters of the optimization."""
        fit_global_parameters = {}
        for key, parameter in self._job.output_or_raise().global_parameters.items():
            fit_global_parameters[key] = ScenarioParameter(
                value=f"{parameter.value}:{maybe_add_parentheses(parameter.unit)}",
                unit=parameter.unit,
                prior=self.scenario.global_parameters[key].prior,
            )
        return fit_global_parameters

    @property
    def _likelihood_functions(self):
        """The likelihood functions of the optimization."""
        return self.scenario.likelihood_functions

    @property
    def _fit_scenario(self):
        """The scenario with the fitted global parameters."""
        return Scenario(
            global_parameters=self._fit_global_parameters,
            likelihood_functions=self._likelihood_functions,
        )

    def _fim(self) -> Job[dict[str, dict[str, UnittedValue]], None]:
        fisher_information = OdeFisherInformationMatrix(scenario=self._fit_scenario)
        jobs = client.create_jobs([fisher_information])
        client.create_contract(jobs)
        return jobs[0].refresh()

    @property
    def fit_parameter_table(self) -> tl.DataFrame:
        """The parameter table with the fitted parameters."""
        new_table = tl.DataFrame.from_dict(self.parameters.to_dict())
        for key, parameter in self._fit_global_parameters_dict.items():
            new_table = new_table.mutate(value=f"if_else(global_parameter_name == '{key}', {parameter}, value)")
        new_table = replace_none_with_asterisk(new_table, self.label_columns)
        return new_table

    def _default_times_table(self) -> tl.DataFrame:
        # set column names, which *must* align with the renames below
        time_column = "times"
        unit_column = "times_unit"
        times_all = (
            self.measurements.select(*self.label_columns, "time", "time_unit")
            .rename(times="time")
            .rename(times_unit="time_unit")
        )
        # Do distinct over all label columns and times to get rid of duplicate time values
        distinct_table = times_all.distinct(*self.label_columns, time_column, unit_column)
        # Drop all non-label columns and get distinct labels
        simulation_table = distinct_table.select(*self.label_columns).unique()
        # Loop over simulations
        times_table_row_list = []
        for i in range(simulation_table.height):
            # Slice simulation_table into a 1-row table.
            tt_slice = simulation_table.slice0([i])
            # Do an inner join between that 1-row table and distinct_table.
            joined_table = distinct_table.inner_join(tt_slice)
            # Pull out the time column and join that into a string.
            tc = joined_table[:, time_column]
            times_str = "[" + ", ".join([str(t) for t in tc]) + "]"
            # ensure that units are all the same and add single unit to row
            uc = joined_table[:, unit_column]
            if not len(set(uc)) == 1:
                raise ValueError("Time units must all be the same in optimization measurements")
            unit_str = str(uc[0])
            # Mutate the 1-row table to add the output times and unit strings.
            tt_slice = tt_slice.mutate(times=f"'{times_str}'", times_unit=f"'{unit_str}'")
            # Append that 1-row table into a list.
            times_table_row_list.append(tt_slice)
        # Concatenate all those 1-row tables into one table, and drop old times column
        return tl.concatenate_rows(*times_table_row_list)

    def simulate(
        self,
        times: DataFrameLike | PathLike | list[float | str] | Times | None = None,
        outputs: list[str] | None = None,
    ) -> SimulationResult:
        """Simulate the fitted model.

        Parameters
        ----------
        times: pd.DataFrame | tl.DataFrame | DataFrame | Path | str | list[float | str] | Times | None
            Times to simulate. It must be Dataframe for a path to a CSV file. It must have a `times` column indicating
            the times to simulate, a `times_unit` column indicating the time unit.
        outputs: list[str] | None
            Outputs to simulate. Outputs must be present in all models or it is an error. If None, it is the
            intersection of all model outputs. Exported outputs across all models must have the same units.

        Returns
        -------
        SimulationResult
        """
        if times is None:
            times = self._default_times_table()

        # simulate will validate the tables and none values are not allowed in the tables
        parameters = replace_none_with_asterisk(self.fit_parameter_table, self.label_columns)
        doses = replace_none_with_asterisk(self.doses, self.label_columns)
        if isinstance(times, tl.DataFrame):
            times = replace_none_with_asterisk(times, self.label_columns)
        if outputs is None:
            outputs = sorted(set(self.measurements[:, "output"]))

        match self.solver_configuration.ode_solver:
            case BdfSolver(
                linear_solver=linear_solver,
                relative_tolerance=relative_tolerance,
                absolute_tolerance=absolute_tolerance,
                max_step=max_step,
                max_order=max_order,
            ):
                # Directly match the defaults in case we expose more options later
                if linear_solver == KluSolver():
                    linear_solver_str = "KLU"
                elif linear_solver == SpgmrSolver():
                    linear_solver_str = "SPGMR"
                else:
                    raise ValueError(f"Unsupported linear solver {linear_solver}")

                return simulate(
                    simulations=self.simulations,
                    models=self.models,
                    parameters=parameters,
                    doses=doses,
                    times=times,
                    outputs=outputs,
                    linear_solver=linear_solver_str,
                    reltol=relative_tolerance,
                    abstol=absolute_tolerance,
                    maxstep=max_step,
                    maxord=max_order,
                    nonnegative=self.solver_configuration.nonnegative,
                )
            case unsupported:
                raise ValueError(f"Unsupported ODE solver {unsupported}")

    def residuals(self) -> DataPipeResult:
        """Calculate the residuals.

        Returns
        -------
        DataPipeResult
        """
        residual = OdeResidual(scenario=self._fit_scenario)
        jobs = client.create_jobs([residual])
        client.create_contract(jobs)

        residual_element = OdeResidualElement(jobs[0].id)
        simulations_data_frame = DataFrame.from_tabeline(self.simulations).to_data_pipe()
        return simulations_data_frame.inner_join(residual_element, by=[("id", "id")]).run()

    def confidence_intervals(
        self,
        fraction: float,
        uncertainty_ceiling: float = float("inf"),
    ) -> DataFrame:
        """Transform information matrix into confidence intervals.

        Parameters
        ----------
        fraction: float
            The fraction of the distribution to contain within the CI. Use 0.95
            for 95% confidence intervals.
        uncertainty_ceiling: float, default = inf
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
        raw_fim = self._fim().output_or_raise()
        fit_global_parameters = self._fit_global_parameters

        # We need the raw float values for the confidence intervals calculation.
        fit_global_parameter_values = self._fit_global_parameters_dict

        annotated_fim: dict[str, AnnotatedFisherRow] = {}
        for name, values in raw_fim.items():
            annotated_fim[name] = AnnotatedFisherRow(
                parameter_value=fit_global_parameter_values[name],
                parameter_prior=fit_global_parameters[name].prior,
                values=values,
            )

        confidence_intervals_data_frame = confidence_intervals(annotated_fim, fraction, uncertainty_ceiling)
        data = confidence_intervals_data_frame.to_data()
        data["columns"]["unit"]["values"] = list(self._fit_global_parameters_unit.values())
        return DataFrame.from_data(data).or_die()

    def parameter_posterior_sample(
        self,
        n: int,
        seeds: list[int],
        method: Literal["NUTS", "HamiltonianMC", "Metropolis", "DEMetropolisZ", "Slice"] = "NUTS",
        tune: int = 1000,
        discard_tuned_samples: bool = True,
        thin: int = 1,
    ) -> PosteriorSampleResult:
        """
        Samples from the parameter posterior distribution given data.

        Parameters
        ----------
        n: int
            Number of samples per seed.
        seeds: list[int]
            List of random number seed to use.
        method: `str`, default="NUTS"
            Algorithm to use for the posterior sampling. The possible methods are
            the following pymc.sample step methods:  NUTS ("No U-Turn Sampler"),
            HamiltonianMC, Metropolis, DEMetropolisZ, and Slice.
        tune: `int`, default=1000
            Number of iterations for method-specific algorithm parameter tuning.
        discard_tuned_samples: `bool`, default=`True`
            Whether to discard the samples used in the tuning phase. Note that tuned
            samples are a biased sample of the underlying posterior distribution and
            should only be used in situations where statistical correctness is not
            required.
        thin: `int`, default=1
            Out of `n` * `thin` raw samples drawn, every `thin` samples are
            retained for the final output table. Can be used to reduce
            auto-correlation among samples.

        Returns
        -------
        PosteriorSampleResult
        """
        configuration = OdePosteriorSampleConfiguration(
            method=method,
            tune=tune,
            discard_tuned_samples=discard_tuned_samples,
            thin=thin,
        )

        samples = [
            OdeParameterPosteriorSample(
                scenario=Scenario(
                    global_parameters=self._initial_global_parameters,
                    likelihood_functions=self._likelihood_functions,
                ),
                n=n,
                seed=seed,
                configuration=configuration,
            )
            for seed in seeds
        ]

        # Store and run jobs
        jobs = client.create_jobs(samples)
        sample_elements = [OdeParameterPosteriorSampleElement(job.id) for job in jobs]
        data_pipe_result = ConcatenateRowsElement(sample_elements).run(progress=True)

        diagnostics = OdeParameterPosteriorSampleListDiagnosticElement([job.id for job in jobs]).run()
        n_divergences = divergences(jobs, on_failure="fill_nan")
        return PosteriorSampleResult(
            samples=data_pipe_result,
            diagnostics=diagnostics,
            n_divergences=n_divergences,
            _jobs=jobs,
            _samples=samples,
        )

    def profile_likelihood(
        self,
        *,
        fraction: float = 0.95,
        simultaneous_intervals: bool = True,
        precision: float = 0.1,
        max_iterations: int | None = None,
        min_step: float = 1e-6,
        max_step: float = 0.18,  # ~log(1.2); from the Raue et. al. default max_step = 0.2 * theta
        reversal_reltol: float | None = None,  # default is 10 * objective_tolerance
        reversal_abstol: float | None = None,  # default is objective_tolerance
        threshold_method: Literal["step_over", "linear_interpolation"] = "linear_interpolation",
        optimization_max_iterations: int | None = None,
    ) -> DataPipeResult:
        """
        Computes the profile likelihood for each fitted parameter using the
        objective G = -2 * log(likelihood) + constant and its gradient.

        Parameters
        ----------
        fraction: `float`, default=0.95
            Desired significance level, e.g. use 0.95 for 95% confidence.  Target
            objective threshold is the corresponding critical value of the
            chi-squared distribution.
        simultaneous_intervals: `bool`, default=`True`
            Determines whether a multiple comparisons correction is applied.  Set
            to `False` for pointwise intervals.
        precision: `float`, default=0.1
            Target increase of G with each step as fraction of the objective
            threshold.  For well-behaved likelihoods, about 1 / precision steps
            are expected to reach the objective threshold if it exists.
        max_iterations: `int` | `None`, default=`None`
            Maximum number of iterations allowed before terminating the algorithm.
            Note this is separate from the underlying optimizations'
            `max_iterations`.  Default is to use 10 / precision.
        min_step: `float`, default=1e-6
            Minimum step in parameter space allowed for each iteration.  Note
            this is in log-space if the parameter is log-scaled.
        max_step: `float`, default=0.18
            Maximum step in parameter space allowed for each iteration.  Note
            this is also is in log-space if the parameter is log-scaled.  The
            default corresponds to about 0.2 * k if k is log-scaled.
        reversal_reltol: `float` | `None`, default=`None`
            The algorithm aims to always increase G with each step.  If a
            decrease is detected up to tolerance, the algorithm is terminated
            (may indicate a local minimum separate from the starting minimum).
            Default is to use 10 * objective_tolerance from the underlying
            optimization configuration.
        reversal_abstol: `float` | `None`, default=`None`
            Absolute tolerance for detecting a decrease in G; see
            `reversal_reltol` above.  Default is to use objective_tolerance from
            the underlying optimization configuration.
        threshold_method: `'step_over'`, `'linear_interpolation'`,
            default=`'linear_interpolation'`.  If the objective threshold is
            crossed, method used to approximate the parameter value at threshold.
            Option `'step_over'` returns the last raw value, while
            `'linear_interpolation'` interpolates over the last step.
        optimization_max_iterations: `int` | None, default=`None`
            Max number of steps allowed for an individual optimization to
            complete.  Default is to use `max_iterations` from the underlying
            optimization configuration.

        Returns
        -------
        DataPipeResult with columns:
            parameter_name: `str`
            parameter_value: `float`
            parameter_unit: `str`
            objective_value: `float`
            direction: "lower" | "upper"
            termination: `str`:
                "threshold":  The profile crossed the target objective threshold
                "bound":  The parameter's lower or upper bound was reached
                "max_iterations": The algorithm exceeded `max_iterations` steps
                "reversal": A decrease in G was detected
                "error": A solver or optimization error occurred
            parameter_threshold: `float`
                Parameter value at the the confidence interval bound.  This is
                NaN except when termination="threshold".
            objective_threshold: `float`
                Corresponding objective value at the confidence interval bound.
                Also NaN except when termination="trheshold".

        For each parameter and profile direction, the table contains the
        parameter and corresponding objective values along the profile.
        `direction`, `termination`, `parameter_threshold` and
        `objective_threshold` are repeated across the profile values.
        """
        scenario = self._fit_scenario
        global_parameter_set = set(scenario.global_parameters.keys())
        unscaled_initial_values = self._fit_global_parameters_dict
        initial_values = {
            name: scale_parameter(scenario.global_parameters[name].prior.is_logscaled, value)
            for name, value in unscaled_initial_values.items()
        }

        configuration = self._optimization.configuration
        if optimization_max_iterations is not None:
            configuration = replace(configuration, max_iterations=optimization_max_iterations)

        # Handle default tolerances
        if reversal_reltol is None:
            reversal_reltol = 10.0 * configuration.objective_tolerance

        if reversal_abstol is None:
            reversal_abstol = configuration.objective_tolerance

        # Collect units, mainly for updating parameters in the scenario
        parameter_units = {}
        parameter_units_with_parentheses = {}
        for name, parameter in scenario.global_parameters.items():
            assert parameter.unit is not None  # The scenario should have beeen constructed as such in optimize()
            parameter_units[name] = parameter.unit
            parameter_units_with_parentheses[name] = maybe_add_parentheses(parameter.unit)

        def G_and_G_dT(name: str, T: float) -> Result[tuple[float, float], None]:
            updated_parameters = scenario.global_parameters.copy()
            U = unscale_parameter(updated_parameters[name].prior.is_logscaled, T)
            updated_parameters[name] = replace(
                updated_parameters[name],
                value=f"{U}:{parameter_units_with_parentheses[name]}",
            )
            updated_scenario = replace(scenario, global_parameters=updated_parameters)

            # Omit the current parameter, and optimize over the rest
            optimization_active_parameters = global_parameter_set - {name}
            optimization = OdeOptimization(
                scenario=updated_scenario,
                active_parameters=optimization_active_parameters,
                configuration=configuration,
            )

            # We only need the derivative with respect to the parameter of interest; the rest are zero
            gradient_active_parameters = {name}
            gradient = OdeGradient(scenario=updated_scenario, active_parameters=gradient_active_parameters)

            # Submit optimization and gradient jobs, wait for both to complete
            jobs = client.create_jobs([optimization, gradient])
            _ = client.create_contract(jobs)

            optimization_job: Job[OdeOptimizationResult, None] = jobs[0].refresh(include_output=True)
            gradient_job: Job[dict[str, UnittedValue], None] = jobs[1].refresh(include_output=True)

            match optimization_job.status:
                case Status.succeeded:
                    G = optimization_job.output.final_objective
                case _:
                    return Failure(None)

            match gradient_job.status:
                case Status.succeeded:
                    G_dU = gradient_job.output[name].value
                    # if log-scaling, U(T) = exp(T), so dU/dT = exp(T) = U
                    U_dT = U if updated_parameters[name].prior.is_logscaled else 1
                    G_dT = G_dU * U_dT
                case _:
                    return Failure(None)

            return Success((G, G_dT))

        # Calculate G threshold from χ^2 critical value
        if simultaneous_intervals:
            target_threshold = stats.chi2.ppf(fraction, df=len(scenario.global_parameters))
        else:
            target_threshold = stats.chi2.ppf(fraction, df=1)

        # Get bound values from the fit parameter dict; the priors' bounds are expressions
        unscaled_lower_bound: dict[str, float] = dict(
            zip(
                self.fit_parameter_table[:, "global_parameter_name"],
                self.fit_parameter_table[:, "lower_bound"],
                strict=True,
            )
        )
        unscaled_upper_bound: dict[str, float] = dict(
            zip(
                self.fit_parameter_table[:, "global_parameter_name"],
                self.fit_parameter_table[:, "upper_bound"],
                strict=True,
            )
        )
        lower_bound = {
            name: scale_parameter(parameter.prior.is_logscaled, unscaled_lower_bound[name])
            for name, parameter in scenario.global_parameters.items()
        }
        upper_bound = {
            name: scale_parameter(parameter.prior.is_logscaled, unscaled_upper_bound[name])
            for name, parameter in scenario.global_parameters.items()
        }

        scaled_results = threaded_profile_likelihood(
            G_and_G_dT,
            initial_values,
            target_threshold=target_threshold,
            precision=precision,
            max_iterations=max_iterations,
            min_step=min_step,
            max_step=max_step,
            lower_bound=lower_bound,
            upper_bound=upper_bound,
            reversal_reltol=reversal_reltol,
            reversal_abstol=reversal_abstol,
            threshold_method=threshold_method,
            max_pool_size=16,  # Enough threads for <= 8 parameters without waiting on other profiles to finish
        )

        check_empty_profiles(scaled_results)

        data_pipe = ConcatenateRowsElement(
            [
                result.to_data_pipe(
                    name=name,
                    unit=parameter_units[name],
                    is_logscaled=scenario.global_parameters[name].prior.is_logscaled,
                )
                for name, result in scaled_results.items()
            ]
        )
        result = data_pipe.run()
        return result
