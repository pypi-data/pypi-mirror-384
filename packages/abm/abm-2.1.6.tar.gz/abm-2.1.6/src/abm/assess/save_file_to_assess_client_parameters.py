import json
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

import tabeline as tl

from abm._sdk.legacy_assess_metadata import Criterion
from abm._sdk.solver_configuration import BdfSolver, KluSolver, SolverConfiguration, SpgmrSolver

from .assess_plot import OutputPlot
from .fetch_assess_model import fetch_legacy_assess_model


@dataclass(frozen=True, kw_only=True)
class AssessParameter:
    scenario: list[str] = field(default_factory=list)
    parameter: list[str] = field(default_factory=list)
    value: list[float] = field(default_factory=list)
    unit: list[str] = field(default_factory=list)


@dataclass(frozen=True, kw_only=True)
class AssessScanParameter:
    scenario: list[str] = field(default_factory=list)
    scan_parameter_1: list[str] = field(default_factory=list)
    unit_1: list[str] = field(default_factory=list)
    lower_1: list[float] = field(default_factory=list)
    upper_1: list[float] = field(default_factory=list)
    scale_1: list[str] = field(default_factory=list)
    n_1: list[int] = field(default_factory=list)
    scan_parameter_2: list[str] = field(default_factory=list)
    unit_2: list[str] = field(default_factory=list)
    lower_2: list[float] = field(default_factory=list)
    upper_2: list[float] = field(default_factory=list)
    scale_2: list[str] = field(default_factory=list)
    n_2: list[int] = field(default_factory=list)


@dataclass(frozen=True, kw_only=True)
class AssessTreatment:
    scenario: list[str] = field(default_factory=list)
    route: list[str] = field(default_factory=list)


@dataclass(frozen=True, kw_only=True)
class AssessCriterion:
    scenario: list[str] = field(default_factory=list)
    biomarker: list[str] = field(default_factory=list)
    statistic: list[str] = field(default_factory=list)
    threshold: list[float] = field(default_factory=list)


@dataclass(frozen=True, kw_only=True)
class AssessClientParameters:
    model: str
    parameters: tl.DataFrame
    treatments: tl.DataFrame
    criteria: tl.DataFrame
    scan_parameters: tl.DataFrame
    output_start: str
    output_stop: str
    output_n: int
    plots: list[OutputPlot]
    optima_method: Literal["brentq", "cubic_spline"]
    configuration: SolverConfiguration


def save_file_to_assess_client_parameters(save_file: str | Path) -> AssessClientParameters:
    save_file = Path(save_file)

    save_file_data = json.loads(save_file.read_text(encoding="UTF-8"))

    global_parameters = save_file_data["global_model_parameters"]
    model_id = save_file_data["metadata_id"]
    assess_metadata = fetch_legacy_assess_model(model_id)

    assess_parameters = AssessParameter()
    assess_scan_parameters = AssessScanParameter()
    assess_treatments = AssessTreatment()
    assess_criteria = AssessCriterion()

    assess_criteria_modifiers = defaultdict(list)
    for scenario in save_file_data["scenarios_table"]:
        scenario_name = scenario["description"]
        scan_parameter_1 = scenario["scan_parameter_1"]
        scan_parameter_2 = scenario["scan_parameter_2"]
        criteria_parameters = scenario["criteria_parameters"]

        for parameter_name, parameter_value in scenario["model_parameters"].items():
            assess_parameters.scenario.append(scenario_name)
            assess_parameters.parameter.append(parameter_name)
            assess_parameters.value.append(parameter_value)
            assess_parameters.unit.append(global_parameters[parameter_name]["unit"])

        assess_scan_parameters.scenario.append(scenario_name)
        assess_scan_parameters.scan_parameter_1.append(scan_parameter_1["param_id"])
        assess_scan_parameters.unit_1.append(global_parameters[scan_parameter_1["param_id"]]["unit"])
        assess_scan_parameters.lower_1.append(scan_parameter_1["lower_limit"])
        assess_scan_parameters.upper_1.append(scan_parameter_1["upper_limit"])
        assess_scan_parameters.scale_1.append(scan_parameter_1["scale"])
        assess_scan_parameters.n_1.append(scan_parameter_1["n"])
        assess_scan_parameters.scan_parameter_2.append(scan_parameter_2["param_id"])
        assess_scan_parameters.unit_2.append(global_parameters[scan_parameter_2["param_id"]]["unit"])
        assess_scan_parameters.lower_2.append(scan_parameter_2["lower_limit"])
        assess_scan_parameters.upper_2.append(scan_parameter_2["upper_limit"])
        assess_scan_parameters.scale_2.append(scan_parameter_2["scale"])
        assess_scan_parameters.n_2.append(scan_parameter_2["n"])

        assess_treatments.scenario.append(scenario_name)
        assess_treatments.route.append(scenario["route"])

        assess_criteria.scenario.append(scenario_name)
        criterion_id = criteria_parameters["id"]
        assess_criteria.biomarker.append(criterion_id)
        assess_criteria.threshold.append(criteria_parameters["target"])

        all_criteria = assess_metadata.criteria
        reducer_id = find_reducer(criteria_parameters["reducer"], criterion_id, all_criteria)

        assess_criteria.statistic.append(reducer_id)
        if len(criteria_parameters["modifiers"]) > 0:
            for modifier_id, modifier_value in criteria_parameters["modifiers"].items():
                assess_criteria_modifiers[modifier_id].append(modifier_value)

    parameter_table = tl.DataFrame(
        scenario=assess_parameters.scenario,
        parameter=assess_parameters.parameter,
        value=assess_parameters.value,
        unit=assess_parameters.unit,
    )

    scan_parameter_table = tl.DataFrame(
        scenario=assess_scan_parameters.scenario,
        scan_parameter_1=assess_scan_parameters.scan_parameter_1,
        unit_1=assess_scan_parameters.unit_1,
        lower_1=assess_scan_parameters.lower_1,
        upper_1=assess_scan_parameters.upper_1,
        scale_1=assess_scan_parameters.scale_1,
        n_1=assess_scan_parameters.n_1,
        scan_parameter_2=assess_scan_parameters.scan_parameter_2,
        unit_2=assess_scan_parameters.unit_2,
        lower_2=assess_scan_parameters.lower_2,
        upper_2=assess_scan_parameters.upper_2,
        scale_2=assess_scan_parameters.scale_2,
        n_2=assess_scan_parameters.n_2,
    )

    treatment_table = tl.DataFrame(
        scenario=assess_treatments.scenario,
        route=assess_treatments.route,
    )

    criteria_table = tl.DataFrame(
        scenario=assess_criteria.scenario,
        biomarker=assess_criteria.biomarker,
        statistic=assess_criteria.statistic,
        threshold=assess_criteria.threshold,
        **assess_criteria_modifiers,
    )

    output_plots = [
        OutputPlot(
            id=plot_id,
            unit=assess_metadata.output_plot_options[plot_id].unit,
            scale=assess_metadata.output_plot_options[plot_id].scale,
        )
        for plot_id in save_file_data["selected_output_plots"]
    ]

    match save_file_data["linear_solver"]:
        case "KLU":
            linear_solver = KluSolver()
        case "SPGMR":
            linear_solver = SpgmrSolver()
        case unsupported:
            raise ValueError(f"Unsupported linear solver {unsupported}")

    assess_client_parameters = AssessClientParameters(
        model=model_id,
        parameters=parameter_table,
        treatments=treatment_table,
        criteria=criteria_table,
        scan_parameters=scan_parameter_table,
        output_start=save_file_data["output_start"],
        output_stop=save_file_data["output_stop"],
        output_n=save_file_data["output_n"],
        plots=output_plots,
        optima_method=save_file_data["scan_1d_root_method"],
        configuration=SolverConfiguration(
            ode_solver=BdfSolver(
                linear_solver=linear_solver,
                relative_tolerance=save_file_data["reltol"],
                absolute_tolerance=save_file_data["abstol"],
                max_order=save_file_data["maxord"],
            )
        ),
    )

    return assess_client_parameters


def find_reducer(expression_template: str, criterion_id: str, all_criteria: list[Criterion]) -> str:
    for criterion in all_criteria:
        if criterion.id == criterion_id:
            for reducer in criterion.reducers:
                if reducer.expression_template == expression_template:
                    return reducer.id
    raise ValueError(f"Could not find reducer for {criterion_id} with expression template {expression_template}")
