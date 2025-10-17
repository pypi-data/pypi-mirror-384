import json
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import pandas as pd
import tabeline as tl
from ordered_set import OrderedSet
from serialite import DeserializationFailure

from abm._sdk.assess import TargetCriterion
from abm._sdk.data_frame import DataFrame
from abm._sdk.legacy import LegacyReactionModel
from abm._sdk.ode_model import OdeModel

from .application_model import ApplicationModel, AssessCriterionData
from .fetch_assess_model import fetch_legacy_assess_model
from .shims.assess_metadata_to_application_model import assess_metadata_to_application_model
from .shims.normalize_application_model import normalize_application_model

DataFrameLike = pd.DataFrame | tl.DataFrame | DataFrame
PathLike = str | Path
necessary_parameter_columns = OrderedSet(["scenario", "parameter", "value", "unit"])
necessary_treatment_columns = OrderedSet(["scenario", "route"])
necessary_criteria_columns = OrderedSet(["scenario", "biomarker", "statistic", "threshold"])
necessary_scan_parameter_1_columns = OrderedSet(
    [
        "scenario",
        "scan_parameter_1",
        "unit_1",
        "lower_1",
        "upper_1",
        "scale_1",
        "n_1",
    ]
)
necessary_scan_parameter_2_columns = OrderedSet(
    [
        "scan_parameter_2",
        "unit_2",
        "lower_2",
        "upper_2",
        "scale_2",
        "n_2",
    ]
)


@dataclass(frozen=True, kw_only=True)
class Parameter:
    value: float
    unit: str


@dataclass(frozen=True, slots=True)
class FullTargetCriterion:
    target_criterion: TargetCriterion
    criterion: AssessCriterionData
    reducer_id: str
    modifier_options: dict[str, str]


@dataclass(frozen=True, kw_only=True)
class ScanParameter:
    scan_parameter_1: str
    scan_parameter_1_name: str
    scan_parameter_1_unit: str
    lower_1: float
    upper_1: float
    scale_1: Literal["linear", "log"]
    n_1: int
    scan_parameter_2: str
    lower_2: float
    upper_2: float
    scale_2: Literal["linear", "log"]
    n_2: int
    scan_parameter_2_name: str
    scan_parameter_2_unit: str


def validate_process_parameters(
    parameters: PathLike | DataFrameLike,
    necessary_columns: OrderedSet[str],
) -> dict[str, dict[str, Parameter]]:
    match parameters:
        case tl.DataFrame():
            parameters_table = parameters
        case pd.DataFrame():
            # This is necessary because Pandas columns can have multiple types but tabeline does not support that
            pd_data = parameters.to_dict(orient="list")
            parameters_table = tl.DataFrame.from_dict(cast_to_most_complex_type(pd_data))
        case str() | Path():
            parameters_path = Path(parameters)
            if not parameters_path.is_file():
                raise FileNotFoundError(f"{parameters_path} is not a file")
            # Tabeline can not parse a csv with multiple types in a column. Pandas convert them to the most
            # complex type. Therefore, we read the csv with pandas and then convert to tabeline dataframe
            # TODO: fix this when tabeline could read csv with mixed
            parameters_pd = pd.read_csv(parameters_path)
            parameters_table = tl.DataFrame.from_pandas(parameters_pd)
        case _:
            raise ValueError("scenarios must be a path to a CSV file")

    if not necessary_columns.issubset(set(parameters_table.column_names)):
        raise ValueError(
            f"All of the mandatory columns must be present in parameters table: {', '.join(necessary_columns)}"
        )

    # This is necessary because we are adding `*` at the end and we want same type for all the keys.
    parameters_table = parameters_table.mutate(unit="if_else(unit == None, '', unit)").mutate(
        scenario="to_string(scenario)"
    )
    # get the scenario names including *
    parameter_scenarios_names = OrderedSet(parameters_table[:, "scenario"])
    # build the parameters. if '*' is present, it will be treated as a scenario and later removed from the parameters
    # and used as common parameters
    parameters = {sc: {} for sc in parameter_scenarios_names}
    for row in range(parameters_table.height):
        if parameters_table[row, "parameter"] in parameters[parameters_table[row, "scenario"]]:
            raise ValueError(
                f"There are multiple values for parameter {parameters_table[row, 'parameter']} in scenario "
                f"{parameters_table[row, 'scenario']}"
            )
        parameters[parameters_table[row, "scenario"]][parameters_table[row, "parameter"]] = Parameter(
            value=parameters_table[row, "value"], unit=parameters_table[row, "unit"]
        )
    if "*" not in parameters:
        parameters["*"] = {}

    return parameters


def validate_process_model(model: PathLike) -> ApplicationModel:
    match model:
        case str(x) if ".json" not in x:
            assess_metadata = fetch_legacy_assess_model(x)
            application_model = assess_metadata_to_application_model(assess_metadata)
            model_id = assess_metadata.model_id
        case str() | Path():
            models_path = Path(model)
            if not models_path.is_file():
                raise FileNotFoundError(f"{models_path} is not a file")

            data = json.loads(models_path.read_text(encoding="UTF-8"))
            application_model = ApplicationModel.from_data(data).or_die()

            # Convert v1 schedules to v2 schedules
            application_model = normalize_application_model(application_model)

            # Get the model and convert it to v2 model if it is v1
            model_path = application_model.url.removeprefix("file:./")
            model_path = Path(model).parent.joinpath(model_path)
            model_data = json.loads(model_path.read_text(encoding="UTF-8"))

            maybe_model = OdeModel.from_data(model_data)
            match maybe_model:
                case DeserializationFailure():
                    # Try to deserialize as a v1 ReactionModel and convert
                    if model_data["_type"] != "ReactionModel":
                        raise ValueError(f"Unsupported model type {model_data['_type']} for conversion.")

                    v1_model: LegacyReactionModel = OdeModel.from_data(
                        model_data | {"_type": "LegacyReactionModel"}
                    ).or_die()
                    model = v1_model.to_v2_model()

                case _:
                    model = maybe_model.or_die()

            model_id = model.store().id

        case _:
            raise ValueError(
                "model must be a path to a JSON file or an assess model name that can be fetched from the database"
            )

    return application_model, model_id


def validate_process_treatments(
    treatments: PathLike | DataFrameLike | None,
    default_treatment: str,
    necessary_columns: OrderedSet[str],
) -> dict[str, str]:
    match treatments:
        case None:
            treatments = tl.DataFrame(
                scenario=["*"],
                route=[default_treatment],
            )
        case tl.DataFrame():
            pass
        case pd.DataFrame():
            # This is necessary because Pandas columns can have multiple types but tabeline does not support that
            pd_data = treatments.to_dict(orient="list")
            treatments = tl.DataFrame.from_dict(cast_to_most_complex_type(pd_data))
        case str(x) if not x.endswith(".csv"):
            treatments = tl.DataFrame(
                scenario=["*"],
                route=[x],
            )
        case str() | Path():
            treatments_path = Path(treatments)
            if not treatments_path.is_file():
                raise FileNotFoundError(f"{treatments_path} is not a file")
            # Tabeline can not parse a csv with multiple types in a column. Pandas convert them to the most
            # complex type. Therefore, we read the csv with pandas and then convert to tabeline dataframe
            # TODO: fix this when tabeline could read csv with mixed
            treatments_pd = pd.read_csv(treatments_path)
            treatments = tl.DataFrame.from_pandas(treatments_pd)
        case _:
            raise ValueError("treatments must be a path to a CSV file or a valid treatment id")

    if not necessary_columns.issubset(set(treatments.column_names)):
        raise ValueError(
            f"All of the mandatory columns must be present in treatments table: {', '.join(necessary_columns)}"
        )

    # This is necessary because we are adding `*` at the end and we want same type for all the keys.
    treatments = treatments.mutate(scenario="to_string(scenario)")
    treatment_scenarios_names = OrderedSet(treatments[:, "scenario"])
    routes = {sc: [] for sc in treatment_scenarios_names}
    for row in range(treatments.height):
        if treatments[row, "route"] in routes[treatments[row, "scenario"]]:
            raise ValueError(
                f"There are multiple values for route {treatments[row, 'route']} in scenario "
                f"{treatments[row, 'scenario']}"
            )
        routes[treatments[row, "scenario"]].append(treatments[row, "route"])

    for sc, rt in routes.items():
        if len(rt) > 1:
            raise ValueError(f"There are multiple routes for scenario {sc}: {rt}")
        routes[sc] = rt[0]

    # if there is no common route, add the default route as common.
    if "*" not in routes:
        routes["*"] = default_treatment

    return routes


def validate_process_scan_parameters(
    scan_parameters: PathLike | DataFrameLike | None,
    application_model: ApplicationModel,
    necessary_columns: OrderedSet[str],
) -> dict[str, ScanParameter]:
    match scan_parameters:
        case None:
            default_scan_parameters = get_default_scan_parameters(application_model)
            return {"*": default_scan_parameters}
        case tl.DataFrame():
            scan_parameters_table = scan_parameters
        case pd.DataFrame():
            # This is necessary because Pandas columns can have multiple types but tabeline does not support that
            pd_data = scan_parameters.to_dict(orient="list")
            scan_parameters_table = tl.DataFrame.from_dict(cast_to_most_complex_type(pd_data))
        case str() | Path():
            scan_parameters_path = Path(scan_parameters)
            if not scan_parameters_path.is_file():
                raise FileNotFoundError(f"{scan_parameters_path} is not a file")
            # Tabeline can not parse a csv with multiple types in a column. Pandas convert them to the most
            # complex type. Therefore, we read the csv with pandas and then convert to tabeline dataframe
            # TODO: fix this when tabeline could read csv with mixed
            scan_parameters_pd = pd.read_csv(scan_parameters_path)
            scan_parameters_table = tl.DataFrame.from_pandas(scan_parameters_pd)
        case _:
            raise ValueError("scan_parameters must be a path to a CSV file")

    if not necessary_columns.issubset(set(scan_parameters_table.column_names)):
        raise ValueError(
            f"All of the mandatory columns must be present in scan parameters table: {', '.join(necessary_columns)}"
        )
    has_scan_parameter_2 = "scan_parameter_2" in scan_parameters_table.column_names

    if not has_scan_parameter_2:
        default_scan_parameters = get_default_scan_parameters(application_model)
        scan_parameter_2 = default_scan_parameters.scan_parameter_2
        scan_parameter_2_name = default_scan_parameters.scan_parameter_2_name
        scan_parameter_2_unit = default_scan_parameters.scan_parameter_2_unit
        lower_2 = default_scan_parameters.lower_2
        upper_2 = default_scan_parameters.upper_2
        scale_2 = default_scan_parameters.scale_2
        n_2 = default_scan_parameters.n_2

    # This is necessary because we are adding `*` at the end and we want same type for all the keys.
    scan_parameters_table = scan_parameters_table.mutate(scenario="to_string(scenario)")

    scan_parameters_dict = {}
    for row in range(scan_parameters_table.height):
        scenario_id = scan_parameters_table[row, "scenario"]

        scan_parameter_1 = scan_parameters_table[row, "scan_parameter_1"]
        scan_parameter_1_name = application_model.parameters[scan_parameter_1].name
        scan_parameter_1_unit = scan_parameters_table[row, "unit_1"]
        lower_1 = scan_parameters_table[row, "lower_1"]
        upper_1 = scan_parameters_table[row, "upper_1"]
        scale_1 = scan_parameters_table[row, "scale_1"]
        n_1 = scan_parameters_table[row, "n_1"]

        if has_scan_parameter_2:
            scan_parameter_2 = scan_parameters_table[row, "scan_parameter_2"]
            scan_parameter_2_name = application_model.parameters[scan_parameter_2].name
            scan_parameter_2_unit = scan_parameters_table[row, "unit_2"]
            lower_2 = scan_parameters_table[row, "lower_2"]
            upper_2 = scan_parameters_table[row, "upper_2"]
            scale_2 = scan_parameters_table[row, "scale_2"]
            n_2 = scan_parameters_table[row, "n_2"]

        scan_parameter = ScanParameter(
            scan_parameter_1=scan_parameter_1,
            scan_parameter_1_name=scan_parameter_1_name,
            scan_parameter_1_unit=scan_parameter_1_unit,
            lower_1=lower_1,
            upper_1=upper_1,
            scale_1=scale_1,
            n_1=n_1,
            scan_parameter_2=scan_parameter_2,
            scan_parameter_2_name=scan_parameter_2_name,
            scan_parameter_2_unit=scan_parameter_2_unit,
            lower_2=lower_2,
            upper_2=upper_2,
            scale_2=scale_2,
            n_2=n_2,
        )
        scan_parameters_dict[scenario_id] = scan_parameter

    if "*" not in scan_parameters_dict:
        default_scan_parameters = get_default_scan_parameters(application_model)
        scan_parameters_dict["*"] = default_scan_parameters

    return scan_parameters_dict


def get_default_scan_parameters(application_model: ApplicationModel) -> ScanParameter:
    default_scan_parameter_1 = application_model.assess.default_scan_parameter_1
    scan_parameter_1_name = application_model.parameters[default_scan_parameter_1].name
    scan_parameter_1_unit = application_model.parameters[default_scan_parameter_1].default_unit_id
    default_scan_parameter_2 = application_model.assess.default_scan_parameter_2
    scan_parameter_2_name = application_model.parameters[default_scan_parameter_2].name
    scan_parameter_2_unit = application_model.parameters[default_scan_parameter_2].default_unit_id

    lower_limit_1 = (
        application_model.assess.parameters[default_scan_parameter_1].units[scan_parameter_1_unit].default_lower
    )
    upper_limit_1 = (
        application_model.assess.parameters[default_scan_parameter_1].units[scan_parameter_1_unit].default_upper
    )
    lower_limit_2 = (
        application_model.assess.parameters[default_scan_parameter_2].units[scan_parameter_2_unit].default_lower
    )
    upper_limit_2 = (
        application_model.assess.parameters[default_scan_parameter_2].units[scan_parameter_2_unit].default_upper
    )
    n_1 = application_model.assess.default_n_1
    n_2 = application_model.assess.default_n_2
    scale_1 = application_model.assess.default_scale_1
    scale_2 = application_model.assess.default_scale_2
    return ScanParameter(
        scan_parameter_1=default_scan_parameter_1,
        scan_parameter_1_name=scan_parameter_1_name,
        scan_parameter_1_unit=scan_parameter_1_unit,
        lower_1=lower_limit_1,
        upper_1=upper_limit_1,
        scale_1=scale_1,
        n_1=n_1,
        scan_parameter_2=default_scan_parameter_2,
        scan_parameter_2_name=scan_parameter_2_name,
        scan_parameter_2_unit=scan_parameter_2_unit,
        lower_2=lower_limit_2,
        upper_2=upper_limit_2,
        scale_2=scale_2,
        n_2=n_2,
    )


def validate_process_criteria(
    criteria: PathLike | DataFrameLike | None,
    application_model_criteria: dict[str, AssessCriterionData],
    default_criterion_id: str,
    necessary_columns: OrderedSet[str],
) -> dict[str, FullTargetCriterion]:
    match criteria:
        case None:
            criteria_table = build_default_criterion_table(
                application_model_criteria=application_model_criteria,
                default_criterion_id=default_criterion_id,
            )
        case tl.DataFrame():
            criteria_table = criteria
        case pd.DataFrame():
            # This is necessary because Pandas columns can have multiple types but tabeline does not support that
            pd_data = criteria.to_dict(orient="list")
            criteria_table = tl.DataFrame.from_dict(cast_to_most_complex_type(pd_data))
        case str() | Path():
            criteria_table_path = Path(criteria)
            if not criteria_table_path.is_file():
                raise FileNotFoundError(f"{criteria_table_path} is not a file")
            # Tabeline can not parse a csv with multiple types in a column. Pandas convert them to the most
            # complex type. Therefore, we read the csv with pandas and then convert to tabeline dataframe
            # TODO: fix this when tabeline could read csv with mixed
            criteria_pd = pd.read_csv(criteria_table_path)
            criteria_table = tl.DataFrame.from_pandas(criteria_pd)
        case _:
            raise ValueError("criteria must be a path to a CSV file")

    if not necessary_columns.issubset(set(criteria_table.column_names)):
        raise ValueError(
            f"All of the mandatory columns must be present in criteria table: {', '.join(necessary_columns)}"
        )

    # This is necessary because we are adding `*` at the end and we want same type for all the keys.
    kw = {}
    for col in criteria_table.column_names:
        kw[col] = f"to_string({col})"
    del kw["threshold"]
    criteria_table = criteria_table.mutate(**kw)
    criteria_table = criteria_table.mutate(threshold="to_float(threshold)")

    common_criterion = criteria_table.filter("scenario=='*'")
    if common_criterion.height == 0:
        default_criterion_table = build_default_criterion_table(
            application_model_criteria=application_model_criteria,
            default_criterion_id=default_criterion_id,
            column_order=list(criteria_table.column_names),
        )
        criteria_table = tl.concatenate_rows(criteria_table, default_criterion_table)

    target_criteria = {}
    for row in range(criteria_table.height):
        scenario_id = criteria_table[row, "scenario"]
        criteria_id = criteria_table[row, "biomarker"]
        criterion = application_model_criteria[criteria_id]
        criterion_time_value = criterion.time_value_template
        reducer_id = criteria_table[row, "statistic"]

        modifier_options = {}
        if len(criterion.modifiers) > 0:
            for modifier_id in criterion.modifiers.keys():
                option_id = criteria_table[row, modifier_id]
                criterion_time_value = criterion_time_value.replace(f"{{{{{{{modifier_id}}}}}}}", option_id)
                modifier_options[modifier_id] = option_id

        reducer_expression = criterion.reducers[reducer_id].expression_template
        reducer_expression = reducer_expression.replace("{{{time_value}}}", f"({criterion_time_value})")

        target_criterion = TargetCriterion(
            value=reducer_expression,
            time_value=criterion_time_value,
            target=criteria_table[row, "threshold"],
        )

        full_target_criterion = FullTargetCriterion(
            target_criterion=target_criterion,
            criterion=criterion,
            reducer_id=reducer_id,
            modifier_options=modifier_options,
        )

        target_criteria[scenario_id] = full_target_criterion

    return target_criteria


def build_default_criterion_table(
    application_model_criteria: dict[str, AssessCriterionData],
    default_criterion_id: str,
    column_order: list[str] | None = None,
):
    data = {"scenario": "*"}
    default_criterion = application_model_criteria[default_criterion_id]
    data["biomarker"] = default_criterion_id
    reducer_id = next(iter(default_criterion.reducers.keys()))
    data["statistic"] = reducer_id
    if len(default_criterion.modifiers) > 0:
        for modifier_id, modifier in default_criterion.modifiers.items():
            option_id = next(iter(modifier.options.keys()))
            data[modifier_id] = option_id
    data["threshold"] = float(default_criterion.default_threshold)

    if column_order is not None:
        # Column order may contain columns for modifiers that are from a non-default criterion.
        # Provide a default value for these columns.
        # TODO 1: 2024-08-12, unsure if '-' is a default value.
        # TODO 2: 2024-08-12, unsure if extra columns in table will be handled correctly, but this should've been in original tests.
        ordered_data = {key: data.get(key, "-") for key in column_order}
    else:
        ordered_data = data

    criteria_table = tl.DataFrame.from_dict(ordered_data)

    return criteria_table


def find_most_complex_type(lst: list) -> type:
    if len(lst) == 0:
        raise ValueError("Can't find the most complex type of an empty list")
    complex_types = [type(None), bool, int, float]
    most_complex_type = type(lst[0])
    for element in lst:
        element_type = type(element)
        if isinstance(element, list | str):
            return str
        elif isinstance(element, (float, int)):
            if complex_types.index(element_type) > complex_types.index(most_complex_type):
                most_complex_type = element_type
        elif element is None:
            # Nones are handled later with a better error message
            continue
        else:
            raise ValueError(f"Unsupported type {element_type}")
    return most_complex_type


def cast_to_most_complex_type(data: dict[str, list]) -> dict[str, list]:
    for column, values in data.items():
        most_complex_type = find_most_complex_type(values)
        data[column] = [most_complex_type(value) if value is not None else None for value in values]
    return data
