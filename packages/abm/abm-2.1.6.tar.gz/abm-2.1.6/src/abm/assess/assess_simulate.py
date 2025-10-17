from ordered_set import OrderedSet

from .._sdk import client
from .._sdk.assess import AssessSimulation, AssessSimulationResult, TransformedParameter
from .._sdk.job import Job
from .._sdk.solver_configuration import SolverConfiguration
from .._sdk.times import LinspaceTimes, ReplicateTimes
from .assess_plot import (
    AssessCriterionPlot,
    AssessOutputPlot,
    OutputPlot,
    get_base_criterion_string,
    get_full_criterion_string,
)
from .assess_tables import (
    necessary_criteria_columns,
    necessary_parameter_columns,
    necessary_treatment_columns,
    validate_process_criteria,
    validate_process_model,
    validate_process_parameters,
    validate_process_treatments,
)


def assess_simulate(
    model: str,
    parameters: str,
    treatments: str | None = None,
    criteria: str | None = None,
    output_start: str | None = None,
    output_stop: str | None = None,
    output_n: int | None = None,
    plots: list[OutputPlot] | None = None,
    configuration: SolverConfiguration | None = None,
) -> dict[str, Job[AssessSimulationResult, None]]:
    # get the application model and compute model id
    application_model, model_id = validate_process_model(model)

    #  get the parameters dictionary with units from the parameters
    parameters = validate_process_parameters(parameters=parameters, necessary_columns=necessary_parameter_columns)

    # build the route schedule
    default_treatment = application_model.assess.default_treatment

    routes = validate_process_treatments(
        treatments=treatments, default_treatment=default_treatment, necessary_columns=necessary_treatment_columns
    )

    if output_start is None:
        output_start = application_model.assess.default_output_start
    if output_stop is None:
        output_stop = application_model.assess.default_output_stop
    if output_n is None:
        output_n = application_model.assess.default_output_n

    times = LinspaceTimes(
        start="0",
        stop=application_model.assess.output_interval,
        n=output_n,
    )
    output_times = ReplicateTimes(
        times=times,
        start=application_model.assess.output_starts[output_start].expression,
        stop=application_model.assess.output_stops[output_stop].expression,
        interval=application_model.assess.output_interval,
    )

    # build the criterion
    default_criterion_id = application_model.assess.default_criterion
    application_model_criteria = application_model.assess.criteria
    full_target_criteria = validate_process_criteria(
        criteria=criteria,
        application_model_criteria=application_model_criteria,
        default_criterion_id=default_criterion_id,
        necessary_columns=necessary_criteria_columns,
    )

    if configuration is None:
        configuration = application_model.assess.default_solver_configuration

    job_definitions = []
    scenario_names = OrderedSet(parameters.keys()) - {"*"}
    for scenario_name in scenario_names:
        # build the transformed parameters
        all_parameters = parameters["*"] | parameters[scenario_name]
        transformed_parameters = {}
        for parameter, value in all_parameters.items():
            if len(application_model.parameters[parameter].units) == 0:
                transformed_parameters[parameter] = TransformedParameter(value=value.value, transform="1")
            else:
                transform = application_model.parameters[parameter].units[value.unit].transform
                transformed_parameters[parameter] = TransformedParameter(value=value.value, transform=transform)

        if scenario_name in routes:
            scenario_route = routes[scenario_name]
        else:
            scenario_route = routes["*"]

        # This is needed because assess models can have no routes. In that case, the default
        # treatment is "" and treatments is an empty dict.
        if scenario_route == "":
            route_schedule = {}
        else:
            route_schedule = {
                application_model.assess.treatments[scenario_route].route_id: application_model.assess.treatments[
                    scenario_route
                ].schedule
            }

        if scenario_name in full_target_criteria:
            full_target_criterion = full_target_criteria[scenario_name]
        else:
            full_target_criterion = full_target_criteria["*"]

        criterion = full_target_criterion.criterion
        modifier_options = full_target_criterion.modifier_options
        reducer_id = full_target_criterion.reducer_id

        # Build plots
        criterion_time_value_name = get_base_criterion_string(criterion=criterion, modifier_options=modifier_options)
        criterion_value_name = get_full_criterion_string(
            criterion=criterion, modifier_options=modifier_options, reducer_id=reducer_id
        )
        output_start_title = application_model.assess.output_starts[output_start].name
        plot_time_unit = application_model.assess.plot_time_unit
        plot_time_transform = application_model.assess.plot_time_transform

        scenario_plots = [
            AssessCriterionPlot(
                type="criterion_plot",
                show_legend=False,
                criterion_value_name=criterion_value_name,
                legend_orientation="h",
                title=f"{criterion_time_value_name} vs. Time",
                x_title=f"Time Since {output_start_title}",
                x_unit=plot_time_unit,
                x_transform=f"{plot_time_transform}",
                y_unit=criterion.unit,
                y_title=criterion_time_value_name,
                y_scale=criterion.scale,
            )
        ]

        if plots is None:
            for output_plot_options_id, output_plot_options in application_model.assess.output_plot_options.items():
                if output_plot_options.default_is_visible:
                    output = application_model.assess.output_plot_options[output_plot_options_id]
                    output_unit = output_plot_options.default_unit_id
                    output_scale = output_plot_options.scale
                    scenario_plots.append(
                        AssessOutputPlot(
                            type="output_plot",
                            show_legend=False,
                            legend_orientation="v",
                            output=output_plot_options_id,
                            title=f"{output.name} vs. Time",
                            x_title=f"Time Since {output_start_title}",
                            x_unit=plot_time_unit,
                            x_transform=f"{plot_time_transform}",
                            y_title=output.name,
                            y_unit=output.units[output_unit].name,
                            y_transform=f"{output.units[output_unit].transform}",
                            y_scale=output_scale,
                        )
                    )
        else:
            for plot in plots:
                output = application_model.assess.output_plot_options[plot.id]
                output_unit = plot.unit
                output_scale = plot.scale
                scenario_plots.append(
                    AssessOutputPlot(
                        type="output_plot",
                        show_legend=True,
                        legend_orientation="v",
                        output=plot.id,
                        title=f"{output.name} vs. Time",
                        x_title=f"Time Since {output_start_title}",
                        x_unit=plot_time_unit,
                        x_transform=f"{plot_time_transform}",
                        y_title=output.name,
                        y_unit=output.units[output_unit].name,
                        y_transform=f"{output.units[output_unit].transform}",
                        y_scale=output_scale,
                    )
                )

        job_definitions.append(
            AssessSimulation(
                model_id=model_id,
                transformed_parameters=transformed_parameters,
                route_schedules=route_schedule,
                output=output_times,
                target_criterion=full_target_criterion.target_criterion,
                plots=[plot.to_sdk_plot() for plot in scenario_plots],
                configuration=configuration,
            )
        )

    jobs = client.create_jobs(job_definitions)
    client.create_contract(jobs, progress=True)
    return {scenario_name: job.refresh() for scenario_name, job in zip(scenario_names, jobs, strict=True)}
