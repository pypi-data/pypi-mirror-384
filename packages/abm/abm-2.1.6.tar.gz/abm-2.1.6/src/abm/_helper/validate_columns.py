from collections import defaultdict

import tabeline as tl

from .._sdk.expression import Expression
from .._sdk.times import Times
from .get_model import get_models
from .get_table import get_table
from .helper import DataFrameLike, PathLike, UnittedLinSpace, replace_asterisk_with_none

necessary_distributions_columns = {"time", "time_unit", "distribution", "distribution_unit", "target"}
necessary_histogram_dist_columns = {"bin_edges", "bin_probabilities", "smoothness"}
necessary_model_columns = {"model"}
necessary_parameter_columns = {"parameter", "value", "unit"}
necessary_dose_columns = {"route", "times", "time_unit"}
amount_dose_columns = {"amounts", "amount_unit"}
duration_dose_columns = {"durations", "duration_unit"}
optional_dose_columns = amount_dose_columns | duration_dose_columns

necessary_time_columns = {"times", "times_unit"}

necessary_measurements_columns = {"time", "time_unit", "output", "measurement", "measurement_unit"}
necessary_fitting_parameter_columns = necessary_parameter_columns | {"is_fit", "lower_bound", "upper_bound"}

# location and scale are required if prior_distribution includes any priors other than 'uniform' or 'loguniform'
prior_distribution_column = {"prior_distribution"}
prior_parameter_columns = {"location", "scale"}
optional_fitting_parameter_columns = prior_distribution_column | prior_parameter_columns


def validate_columns(
    df: tl.DataFrame,
    table_name: str,
    *,
    disallow_asterisk_in_labels: bool = False,
    necessary_columns: set[str] = {},
    optional_columns: set[str] = {},
) -> None:
    column_names = df.column_names

    if len(necessary_columns) > 0 and not necessary_columns.issubset(set(column_names)):
        raise ValueError(f"{table_name} must have the necessary column(s): {', '.join(sorted(necessary_columns))}.")

    errors = defaultdict(list)
    for column in column_names:
        if column in necessary_columns:
            if "*" in df[:, column]:
                errors["asterisk_in_nonlabel"].append(column)
            if None in df[:, column]:
                errors["none_in_required"].append(column)
        elif column in optional_columns:
            if "*" in df[:, column]:
                errors["asterisk_in_nonlabel"].append(column)
        else:  # It's a label column
            # Always disallow none in label columns
            if None in df[:, column]:
                errors["none_in_label"].append(column)

            if disallow_asterisk_in_labels:
                if "*" in df[:, column]:
                    errors["asterisk_in_label"].append(column)

    if len(errors) > 0:
        error_message = ""
        if len(errors["none_in_label"]) > 0:
            error_message += (
                f"NULL values are not allowed in label columns of {table_name} but found in column(s): "
                f"{', '.join(errors['none_in_label'])}."
            )
        if len(errors["asterisk_in_label"]) > 0:
            error_message += (
                f"'*' is not allowed in label columns of {table_name} but found in column(s): "
                f"{', '.join(errors['asterisk_in_label'])}."
            )
        if len(errors["asterisk_in_nonlabel"]) > 0:
            error_message += (
                f"'*' is not allowed in non-label columns of {table_name} but found in column(s): "
                f"{', '.join(errors['asterisk_in_nonlabel'])}."
            )
        if len(errors["none_in_required"]) > 0:
            error_message += (
                f"NULL values are not allowed in required columns of {table_name} but found in column(s): "
                f"{', '.join(errors['none_in_required'])}."
            )
        raise ValueError(error_message)


def validate_and_process_simulation_table(simulations: DataFrameLike | PathLike | None = None) -> tl.DataFrame:
    if simulations is None:
        return tl.DataFrame.columnless(height=1)
    else:
        simulation_table = get_table(simulations)
        validate_columns(simulation_table, "simulation table", disallow_asterisk_in_labels=True)
        return simulation_table


def validate_and_process_model_table(models: DataFrameLike | PathLike) -> tl.DataFrame:
    models = get_models(models)
    validate_columns(models, "model table", necessary_columns=necessary_model_columns)
    # replace asterisks with None
    models_table = replace_asterisk_with_none(models)
    return models_table


def validate_and_process_parameter_table(parameters: DataFrameLike | PathLike | None = None) -> tl.DataFrame:
    if parameters is None:
        kw = {key: [] for key in necessary_parameter_columns}
        return tl.DataFrame(**kw)
    else:
        parameters_table = get_table(parameters)
        validate_columns(parameters_table, "parameter table", necessary_columns=necessary_parameter_columns)
        # replace asterisks with None
        parameters_table = replace_asterisk_with_none(parameters_table)
        parameters_table = parameters_table.mutate(unit="to_string(unit)")
        return parameters_table


def validate_and_process_dose_table(doses: DataFrameLike | PathLike | None = None) -> tl.DataFrame:
    if doses is None:
        kw = {key: [] for key in necessary_dose_columns}
        return tl.DataFrame(**kw)
    else:
        doses_table = get_table(doses)

        validate_columns(
            doses_table, "dose table", necessary_columns=necessary_dose_columns, optional_columns=optional_dose_columns
        )

        # replace asterisks with None
        doses_table = replace_asterisk_with_none(doses_table)
        doses_table = doses_table.mutate(time_unit="to_string(time_unit)")
        if "amount_unit" in doses_table.column_names:
            doses_table = doses_table.mutate(amount_unit="to_string(amount_unit)", time_unit="to_string(time_unit)")
        if "duration_unit" in doses_table.column_names:
            doses_table = doses_table.mutate(duration_unit="to_string(duration_unit)")
        return doses_table


def validate_and_process_times(
    times: DataFrameLike | PathLike | list[Expression] | UnittedLinSpace,
) -> tl.DataFrame | Times:
    if isinstance(times, list):
        return times
    if isinstance(times, UnittedLinSpace):
        return times.to_linspace_times()
    else:
        times_table = get_table(times)
        validate_columns(times_table, "time table", necessary_columns=necessary_time_columns)
        # replace asterisks with None
        times_table = replace_asterisk_with_none(times_table)
        times_table = times_table.mutate(times_unit="to_string(times_unit)")
        return times_table


def validate_and_process_measurements_table(measurements: DataFrameLike | PathLike) -> tl.DataFrame:
    measurements_table = get_table(measurements)
    validate_columns(
        measurements_table,
        "measurement table",
        necessary_columns=necessary_measurements_columns,
        disallow_asterisk_in_labels=True,
    )
    measurements_table = measurements_table.mutate(
        time_unit="to_string(time_unit)", measurement_unit="to_string(measurement_unit)"
    )
    return measurements_table


def validate_and_process_distributions_table(distributions):
    distributions_table = get_table(distributions)
    validate_columns(
        distributions_table,
        "distribution table",
        necessary_columns=necessary_distributions_columns,
        disallow_asterisk_in_labels=True,
    )
    distributions_table = distributions_table.mutate(
        time_unit="to_string(time_unit)", distribution_unit="to_string(distribution_unit)"
    )
    return distributions_table


def validate_and_process_fitting_parameter_tables(parameters: DataFrameLike | PathLike) -> tl.DataFrame:
    parameters_table = get_table(parameters)

    # check for optional columns
    necessary_columns = necessary_fitting_parameter_columns
    optional_columns = set()
    if "prior_distribution" in parameters_table.column_names:
        necessary_columns = necessary_columns | prior_distribution_column
        if len(set(parameters_table[:, "prior_distribution"]) - {"uniform", "loguniform"}) > 0:
            necessary_columns = necessary_columns | prior_parameter_columns
        else:
            optional_columns = optional_columns | prior_parameter_columns
    else:
        optional_columns = optional_columns | optional_fitting_parameter_columns

    validate_columns(parameters_table, "parameter table", necessary_columns=necessary_columns)
    # convert is_fit to boolean if it is a string
    if not isinstance(parameters_table[0, "is_fit"], bool):
        not_valid_is_fit = parameters_table.filter("is_fit != 'True' & is_fit != 'False'")
        if not_valid_is_fit.height > 0:
            raise ValueError("Invalid value for is_fit column: Valid values are True or False.")
        parameters_table = parameters_table.mutate(is_fit="is_fit == 'True'")
    parameters_table = replace_asterisk_with_none(parameters_table)
    parameters_table = parameters_table.mutate(unit="to_string(unit)")
    return parameters_table
