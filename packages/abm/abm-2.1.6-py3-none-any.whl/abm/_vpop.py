from __future__ import annotations

__all__ = ["VirtualPopulationResult", "virtual_population"]

import ast
import math
from dataclasses import dataclass
from typing import Literal

import pandas as pd
import tabeline as tl
from ordered_set import OrderedSet

from abm._helper.create_map import (
    create_distributions_map,
    create_doses_map,
    create_fitting_parameters_map,
    create_models_map,
)
from abm._helper.get_dose_schedules import get_dose_schedules
from abm._helper.helper import (
    DataFrameLike,
    PathLike,
    find_duplicate_keys,
    maybe_add_parentheses,
)
from abm._helper.parameter import Parameter
from abm._helper.validate_columns import (
    necessary_dose_columns,
    necessary_fitting_parameter_columns,
    necessary_model_columns,
    optional_dose_columns,
    optional_fitting_parameter_columns,
    validate_and_process_distributions_table,
    validate_and_process_dose_table,
    validate_and_process_fitting_parameter_tables,
    validate_and_process_model_table,
)
from abm._labelset import LabelSet
from abm._sdk import client
from abm._sdk.contract import Contract
from abm._sdk.data_pipe import (
    OdeProposalPopulationSampleElement,
    OdeVirtualPopulationSampleElement,
)
from abm._sdk.job import Job
from abm._sdk.likelihood import DistributionsLikelihoodFunction
from abm._sdk.likelihood.distributions import HistogramDistribution, MultivariateNormalDistribution
from abm._sdk.ode_model_reference import OdeModelReference
from abm._sdk.ode_proposal_population_sample import (
    ClassifierSurrogate,
    OdeProposalPopulationSample,
)
from abm._sdk.ode_residual_batch import OdeResidualBatch
from abm._sdk.ode_virtual_population_sample import (
    ExpectedPopulation,
    OdeVirtualPopulationSample,
)
from abm._sdk.scenario import (
    LaplacePrior,
    LogLaplacePrior,
    LogNormalPrior,
    LogUniformPrior,
    NormalPrior,
    Scenario,
    ScenarioParameter,
    UniformPrior,
)
from abm._sdk.solver_configuration import (
    BdfSolver,
    KluSolver,
    SolverConfiguration,
    SpgmrSolver,
)
from abm._units.comparison import is_equivalent

from ._helper.get_model import get_model_types_i, get_remote_model


def _build_scenario(
    distributions,
    models,
    parameters,
    doses,
    solver_configuration,
) -> Scenario:
    distributions = validate_and_process_distributions_table(distributions)
    processed_models = validate_and_process_model_table(models)
    parameters = validate_and_process_fitting_parameter_tables(parameters)
    doses = validate_and_process_dose_table(doses)

    distributions_column_names = OrderedSet(distributions.column_names)

    # find label columns:
    maybe_label_columns_from_models = set(processed_models.column_names) - necessary_model_columns
    maybe_label_columns_from_parameters = set(parameters.column_names) - (
        necessary_fitting_parameter_columns | optional_fitting_parameter_columns
    )
    maybe_label_columns_from_doses = set(doses.column_names) - (necessary_dose_columns | optional_dose_columns)

    # label columns are the intersection of the columns from measurements and unnecessary columns the models,
    # parameters, and doses
    label_columns = OrderedSet(
        distributions_column_names.intersection(
            maybe_label_columns_from_models | maybe_label_columns_from_parameters | maybe_label_columns_from_doses
        )
    )

    # Assign a unique parameter name for each row for defining the global parameters
    parameters = parameters.mutate(global_parameter_name="parameter + '_fit_' + to_string(row_index0())")

    not_label_columns = distributions_column_names - label_columns

    # make a simulation table out of label columns
    simulation_table = distributions.deselect(*not_label_columns)
    unique_simulations = simulation_table.unique()

    # Add id column for each simulation for residuals
    unique_simulations = unique_simulations.mutate(id="row_index0()")
    simulation_labels = LabelSet.from_df(unique_simulations)

    distributions_labels = label_columns.intersection(distributions_column_names).items
    distributions_map = create_distributions_map(distributions, distributions_labels)

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

    # Optim configuration here? method configuration?

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
        data_i = distributions_map.get_values([lbs.labels.get(k, "*") for k in distributions_labels])

        # This is part of step 3 but we need it to update the error expressions with global parameter name
        parameter_list_i = parameters_map.get_values([lbs.labels.get(k, "*") for k in parameters_labels])
        duplicate_parameters = find_duplicate_keys(parameter_list_i)
        if len(duplicate_parameters) > 0:
            raise ValueError(
                "Duplicate parameters found for label(s)"
                f" {', '.join([f'{key}={value}' for key, value in lbs.original_labels.items()])}:"
                f" {', '.join(duplicate_parameters)}"
            )

        # Build the Distributions object
        distributions_i = []
        for d_i in data_i:
            match d_i["time"]:
                case int() | float():
                    time_measurement_j = f"{d_i['time']}:{maybe_add_parentheses(d_i['time_unit'])}"
                case str() if not d_i["time"].startswith("["):
                    time_measurement_j = f"{d_i['time']}:{maybe_add_parentheses(d_i['time_unit'])}"
                case str() if d_i["time"].startswith("["):
                    time_i = ast.literal_eval(d_i["time"])
                    time_unit_i = ast.literal_eval(d_i["time_unit"])
                    time_measurement_j = [
                        f"{t}:{maybe_add_parentheses(u)}" for t, u in zip(time_i, time_unit_i, strict=True)
                    ]

            match d_i["target"]:
                case str() if not d_i["target"].startswith("["):
                    target_j = d_i["target"]
                case str() if d_i["target"].startswith("["):
                    target_j = ast.literal_eval(d_i["target"])
                case _:
                    raise NotImplementedError(f"{d_i['target']} not correctly formatted.")

            match d_i["distribution"]:
                case "HistogramDistribution":
                    bin_edges_bare_j = ast.literal_eval(d_i["bin_edges"])
                    bin_edges_j = [
                        f"{edge}:{maybe_add_parentheses(d_i['distribution_unit'])}" for edge in bin_edges_bare_j
                    ]
                    bin_probabilities_j = ast.literal_eval(d_i["bin_probabilities"])
                    smoothness_j = f"{d_i['smoothness']}:{maybe_add_parentheses(d_i['distribution_unit'])}"

                    distributions_i.append(
                        HistogramDistribution(
                            time=time_measurement_j,
                            target=target_j,
                            bin_edges=bin_edges_j,
                            bin_probabilities=bin_probabilities_j,
                            smoothness=smoothness_j,
                        )
                    )

                case "MultivariateNormalDistribution":
                    measurements_bare_j = ast.literal_eval(d_i["measurements"])
                    measurements_unit_bare_j = ast.literal_eval(d_i["measurements_unit"])
                    measurements_j = [
                        f"{m}:{maybe_add_parentheses(u)}"
                        for m, u in zip(measurements_bare_j, measurements_unit_bare_j, strict=True)
                    ]
                    cov_mat = ast.literal_eval(d_i["variance"])

                    distributions_i.append(
                        MultivariateNormalDistribution(
                            times=time_measurement_j,
                            measurements=measurements_j,
                            variance=cov_mat,
                            targets=target_j,
                        )
                    )

                case _:
                    raise NotImplementedError(f"{d_i['distribution']} not implemented")

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
            DistributionsLikelihoodFunction(
                mapping=mapping_i,
                model=model_reference,
                distributions=distributions_i,
                configuration=solver_configuration,
            )
        )

    scenario = Scenario(global_parameters=global_parameters, likelihood_functions=likelihood_functions)

    return scenario, label_columns, unique_simulations, parameters


def virtual_population(
    *,
    distributions: DataFrameLike | PathLike,
    models: DataFrameLike | PathLike,
    parameters: DataFrameLike | PathLike,
    doses: DataFrameLike | PathLike | None = None,
    proposal_method: Literal["TruncatedSSE", "ClassifierSurrogate"],
    virtual_method: Literal["ExpectedPopulation", "FixedBeta"] = "ExpectedPopulation",
    proposal_distributions: DataFrameLike | PathLike | None = None,
    proposal_options: dict = {},
    virtual_options: dict = {},
    gradient_method: Literal["forward", "adjoint"] = "forward",
    linear_solver: Literal["KLU", "SPGMR"] = "KLU",
    reltol: float = 1e-6,
    abstol: float = 1e-9,
    maxstep: float = math.inf,
    maxord: int = 5,
    nonnegative: bool | dict[str, bool] = False,
    max_steps: int | None = None,
    seed: int | None = None,
) -> VirtualPopulationResult:
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

    if proposal_distributions is None:
        proposal_distributions = distributions

    # Build the two scenarios
    (
        proposal_scenario,
        proposal_label_columns,
        proposal_unique_simulations,
        _,
    ) = _build_scenario(
        distributions=proposal_distributions,
        models=models,
        parameters=parameters,
        doses=doses,
        solver_configuration=solver_configuration,
    )

    (vpop_scenario, virtual_label_columns, virtual_unique_simulations, virtual_parameters) = _build_scenario(
        distributions=distributions,
        models=models,
        parameters=parameters,
        doses=doses,
        solver_configuration=solver_configuration,
    )

    # TODO: other methods
    if proposal_method != "ClassifierSurrogate":
        raise NotImplementedError(f"proposal method {proposal_method} not implemented")

    proposal_method = ClassifierSurrogate(**proposal_options)

    proposal = OdeProposalPopulationSample(seed=seed, method=proposal_method, scenario=proposal_scenario)
    proposal_jobs = client.create_jobs([proposal], deduplicate=True)
    proposal_contract = client.create_contract(proposal_jobs, progress=True)

    proposal_sample = OdeProposalPopulationSampleElement(proposal_population_sample_id=proposal_jobs[0].id)

    # TODO: other methods
    if virtual_method != "ExpectedPopulation":
        raise NotImplementedError(f"virtual method {virtual_method} not implemented")

    vpop_method = ExpectedPopulation(**virtual_options)

    virtual_population = OdeVirtualPopulationSample(
        seed=seed,
        data_pipe=proposal_sample,
        method=vpop_method,
        scenario=vpop_scenario,
    )

    vpop_sample_job = client.create_jobs([virtual_population], deduplicate=True)
    virtual_population_contract = client.create_contract(vpop_sample_job, progress=True)

    return VirtualPopulationResult(
        proposal_label_columns=proposal_label_columns,
        proposal_simulations=proposal_unique_simulations,
        virtual_label_columns=virtual_label_columns,
        virtual_simulations=virtual_unique_simulations,
        models=models,
        parameters=virtual_parameters,
        distributions=distributions,
        proposal_distributions=proposal_distributions,
        doses=doses,
        solver_configuration=solver_configuration,
        proposal_scenario=proposal_scenario,
        virtual_scenario=vpop_scenario,
        _proposal_job=proposal_jobs[0],
        _proposal_contract=proposal_contract,
        _virtual_job=vpop_sample_job[0],
        _virtual_contract=virtual_population_contract,
        _proposal_population=proposal,
        _virtual_population=virtual_population,
    )


@dataclass
class VirtualPopulationResult:
    proposal_label_columns: OrderedSet[str]
    proposal_simulations: tl.DataFrame
    virtual_label_columns: OrderedSet[str]
    virtual_simulations: tl.DataFrame

    models: DataFrameLike | PathLike
    parameters: tl.DataFrame
    distributions: tl.DataFrame
    proposal_distributions: tl.DataFrame | None
    doses: tl.DataFrame

    solver_configuration: SolverConfiguration
    proposal_scenario: Scenario
    virtual_scenario: Scenario

    _proposal_contract: Contract
    _virtual_contract: Contract
    _proposal_job: Job[OdeProposalPopulationSample, None]
    _virtual_job: Job[OdeVirtualPopulationSample, None]

    _proposal_population: OdeProposalPopulationSample
    _virtual_population: OdeVirtualPopulationSample

    # residual job fields
    _residual_batch_definition: OdeResidualBatch | None = None
    _residual_batch_job: Job[OdeResidualBatch, None] | None = None
    _residual_batch_contract: Contract | None = None

    @property
    def _initial_global_parameters_proposal(self):
        return self.proposal_scenario.global_parameters

    @property
    def _initial_global_parameters_virtual(self):
        return self.virtual_scenario.global_parameters

    def _residual_batch(self):
        vpop_sample_pipe = OdeVirtualPopulationSampleElement(virtual_population_sample_id=self._virtual_job.id)

        self._residual_batch_definition = OdeResidualBatch(
            data_pipe=vpop_sample_pipe,
            scenario=self.virtual_scenario,
        )

        self._residual_batch_job = client.create_jobs([self._residual_batch_definition], deduplicate=True)
        self._residual_batch_contract = client.create_contract(self._residual_batch_job, progress=True)

        return self._residual_batch_job[0].output_or_raise()

    def _targets(self):
        output = []
        for i, lf in enumerate(self.virtual_scenario.likelihood_functions):
            labels = ""
            if len(self.virtual_label_columns) > 0:
                simulation_records = self.virtual_simulations[i, :]
                labels = "_".join(str(v) for _, v in simulation_records.items())
            for dist in lf.distributions:
                if hasattr(dist, "target"):
                    targets = [f"{dist.target}_{labels}_{dist.time}"]
                elif hasattr(dist, "targets"):
                    targets = [f"{d}_{labels}_{t}" for (d, t) in zip(dist.targets, dist.times, strict=False)]
                else:
                    raise ValueError("Distribution does not have target or targets attribute")
                output.extend(targets)
        return output

    def virtual_population_predictions(self):
        residuals = self._residual_batch()

        likelihood_function_residuals = [
            Job.from_id(res).output_or_raise().likelihood_function_residuals for res in residuals
        ]

        output = []
        for lf_residual in likelihood_function_residuals:
            aggregate = []
            for residuals in lf_residual:
                for residual in residuals.residuals:
                    match residual:
                        case _ if hasattr(residual, "prediction"):
                            predictions = [residual.prediction]
                        case _ if hasattr(residual, "predictions"):
                            predictions = residual.predictions

                    aggregate.extend(predictions)

            output.append(aggregate)

        targets = self._targets()

        return pd.DataFrame(output, columns=targets)
