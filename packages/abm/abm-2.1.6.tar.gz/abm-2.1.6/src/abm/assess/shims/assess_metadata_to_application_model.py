from abm._sdk.legacy_assess_metadata import LegacyAssessMetadata
from abm._sdk.solver_configuration import BdfSolver, SolverConfiguration

from ..application_model import (
    ApplicationModel,
    AssessCriterionData,
    AssessData,
    AssessModifierData,
    AssessOutputTime,
    AssessParameterData,
    AssessReducerData,
    AssessTreatment,
    AssessUnitData,
    EnumeratedParameterValue,
    ModelParameterData,
    ModelRouteData,
    ModifierOption,
    OutputPlotOption,
    OutputPlotUnit,
    UnitData,
)
from .normalize_application_model import maybe_legacy_schedule_to_schedule


def assess_metadata_parameter_to_application_model_parameter(
    data: LegacyAssessMetadata,
) -> tuple[dict[str, ModelParameterData], dict[str, AssessParameterData]]:
    metadata_parameters = data.parameters

    model_parameters = {}
    assess_parameters = {}
    for parameter in metadata_parameters:
        model_parameter = ModelParameterData(
            name=parameter.name,
            units={unit.unit: UnitData(name=unit.unit, transform=unit.transform) for unit in parameter.units},
            default_unit_id=parameter.default_unit,
            default_value=parameter.default_value,
            symbol=parameter.symbol,
            description=parameter.description,
        )

        model_parameters[parameter.id] = model_parameter

        assess_parameter = AssessParameterData(
            default_is_global=parameter.is_global,
            units={
                unit.unit: AssessUnitData(
                    default_lower=unit.default_lower_limit, default_upper=unit.default_upper_limit
                )
                for unit in parameter.units
            },
            enum=[
                EnumeratedParameterValue(value=dropdown.value, label=dropdown.label)
                for dropdown in parameter.dropdown_items
            ],
        )

        assess_parameters[parameter.id] = assess_parameter

    return model_parameters, assess_parameters


def assess_metadata_to_application_model(data: LegacyAssessMetadata) -> ApplicationModel:
    model_parameters, assess_parameters = assess_metadata_parameter_to_application_model_parameter(data)
    criteria = {}
    for criterion in data.criteria:
        modifiers = {}
        for modifier in criterion.modifiers:
            assess_modifier = AssessModifierData(
                name=modifier.name,
                options={option.value: ModifierOption(name=option.name) for option in modifier.options},
                description=modifier.description,
            )
            modifiers[modifier.id] = assess_modifier

        reducers = {}
        for reducer in criterion.reducers:
            assess_reducer = AssessReducerData(
                name=reducer.name,
                expression_template=reducer.expression_template,
                description=reducer.description,
            )
            reducers[reducer.id] = assess_reducer

        assess_criterion = AssessCriterionData(
            name=criterion.name,
            time_value_template=criterion.time_value_template,
            modifiers=modifiers,
            reducers=reducers,
            default_threshold=criterion.default_threshold,
            unit=criterion.value_unit,
            min=criterion.value_min,
            max=criterion.value_max,
            scale=criterion.value_scale,
            description=criterion.description,
        )
        criteria[criterion.id] = assess_criterion

    selected_output_plots = set(data.selected_output_plots)
    output_plot_options = {}
    for key, value in data.output_plot_options.items():
        output_plot_option = OutputPlotOption(
            name=value.title,
            units={
                unit_id: OutputPlotUnit(name=unit_id, transform=unit_option.transform)
                for unit_id, unit_option in value.units.items()
            },
            default_unit_id=value.unit,
            scale=value.scale,
            default_is_visible=key in selected_output_plots,
        )
        output_plot_options[key] = output_plot_option

    assess_data = AssessData(
        parameters=assess_parameters,
        default_scan_parameter_1=data.default_scan_parameter_1,
        default_scan_parameter_2=data.default_scan_parameter_2,
        default_n_1=data.default_n_1,
        default_n_2=data.default_n_2,
        default_scale_1=data.default_scale_1,
        default_scale_2=data.default_scale_2,
        treatments={
            key: AssessTreatment(name=key, route_id=key, schedule=maybe_legacy_schedule_to_schedule(schedule))
            for key, schedule in data.routes.items()
        },
        default_treatment=data.default_route,
        criteria=criteria,
        default_criterion=data.default_criterion,
        default_optima_method=data.default_optima_method,
        default_solver_configuration=SolverConfiguration(
            ode_solver=BdfSolver(
                absolute_tolerance=data.default_abstol,
                relative_tolerance=data.default_reltol,
                max_order=data.default_maxord,
            ),
        ),
        output_starts={
            key: AssessOutputTime(name=value.name, expression=value.expression)
            for key, value in data.output_starts.items()
        },
        default_output_start=data.default_output_start,
        output_stops={
            key: AssessOutputTime(name=value.name, expression=value.expression)
            for key, value in data.output_stops.items()
        },
        default_output_stop=data.default_output_stop,
        default_output_n=data.output_n,
        output_interval=data.output_interval,
        output_plot_options=output_plot_options,
        plot_time_transform=data.plot_time_transform,
        plot_time_unit=data.plot_time_unit,
        pack=data.pack,
    )
    application_model = ApplicationModel(
        url="file:./model.json",
        name=data.name,
        parameters=model_parameters,
        routes={key: ModelRouteData(name=key) for key in data.routes.keys()},
        tags=data.tags,
        brief=data.description,
        headline=data.headline,
        thumbnail_url="file:./thumbnail.png",
        drug_diagram_url="file:./drug_diagram.png",
        pharmacology_diagram_url="file:./pharmacology_diagram.png" if data.pharmacology_diagram is not None else None,
        documentation=data.documentation,
        assess=assess_data,
    )

    return application_model
