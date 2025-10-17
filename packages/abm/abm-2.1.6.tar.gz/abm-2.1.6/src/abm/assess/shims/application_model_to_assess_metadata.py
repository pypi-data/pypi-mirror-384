from abm._sdk.legacy_assess_metadata import (
    Criterion,
    DropDown,
    LegacyAssessMetadata,
    LegacyMetadataParameter,
    OutputPlotOption,
    OutputPlotUnit,
    UnitOption,
)

from ..application_model import ApplicationModel


def report_url_to_id(report):
    if report is not None:
        return report.removeprefix("file:./").split(".")[0]
    else:
        return "basic_report"


def application_model_to_assess_parameters(data: ApplicationModel):
    assess_parameters = []

    for key_param, param in data.assess.parameters.items():
        model_param = data.parameters[key_param]

        default_value = str(model_param.default_value)
        default_unit_id = model_param.default_unit_id
        if default_unit_id == "":
            default_unit = ""
        else:
            default_unit = model_param.units[default_unit_id].name

        units = [
            UnitOption(
                unit=key,
                transform=model_param.units[key].transform,
                default_lower_limit=value.default_lower,
                default_upper_limit=value.default_upper,
            )
            for key, value in param.units.items()
        ]

        if param.enum is not None:
            dropdowns = [DropDown(label=enum.label, value=enum.value) for enum in param.enum]
        else:
            dropdowns = []

        asssess_param = LegacyMetadataParameter(
            id=key_param,
            name=model_param.name,
            description=model_param.description,
            symbol=model_param.symbol,
            default_value=default_value,
            is_global=param.default_is_global,
            default_unit=default_unit,
            units=units,
            dropdown_items=dropdowns,
        )

        assess_parameters.append(asssess_param)

    return assess_parameters


def assess_data_to_assess_criteria(assess_data):
    return [
        Criterion.from_data(
            {
                "id": key,
                "time_value_template": criterion.time_value_template,
                "modifiers": (
                    [
                        {
                            "id": key,
                            "name": modifier.name,
                            "options": [
                                {"name": option.name, "value": key} for key, option in modifier.options.items()
                            ],
                        }
                        for key, modifier in criterion.modifiers.items()
                    ]
                    if criterion.modifiers
                    else []
                ),
                "reducers": (
                    [
                        {
                            "id": key,
                            "name": reducer.name,
                            "expression_template": reducer.expression_template,
                            "description": reducer.description,
                        }
                        for key, reducer in criterion.reducers.items()
                    ]
                    if criterion.reducers
                    else []
                ),
                "name": criterion.name,
                "default_threshold": criterion.default_threshold,
                "description": criterion.description if criterion.description is not None else "",
                "value_unit": criterion.unit,
                "value_min": criterion.min,
                "value_max": criterion.max,
                "value_scale": criterion.scale,
            }
        ).or_die()
        for key, criterion in assess_data.criteria.items()
    ]


def application_model_to_assess_metadata(data: ApplicationModel, id: str):
    assess_parameters = application_model_to_assess_parameters(data)
    assess_criteria = assess_data_to_assess_criteria(data.assess)
    selected_output_plots = [
        key for key, value in data.assess.output_plot_options.items() if value.default_is_visible is True
    ]

    output_plot_options = {
        key: OutputPlotOption(
            title=value.name,
            unit=value.default_unit_id,
            units={k: OutputPlotUnit(transform=v.transform) for k, v in value.units.items()},
            scale=value.scale,
            description=value.description,
        )
        for key, value in data.assess.output_plot_options.items()
    }

    routes = {key: value.schedule for key, value in data.assess.treatments.items()}

    metadata = LegacyAssessMetadata(
        parameters=assess_parameters,
        pack=data.assess.pack,
        default_scan_parameter_1=data.assess.default_scan_parameter_1,
        default_scan_parameter_2=data.assess.default_scan_parameter_2,
        default_n_1=data.assess.default_n_1,
        default_n_2=data.assess.default_n_2,
        default_scale_1=data.assess.default_scale_1,
        default_scale_2=data.assess.default_scale_2,
        routes=routes,
        default_route=data.assess.default_treatment,
        criteria=assess_criteria,
        default_criterion=data.assess.default_criterion,
        default_optima_method=data.assess.default_optima_method,
        output_starts=data.assess.output_starts,
        default_output_start=data.assess.default_output_start,
        output_stops=data.assess.output_stops,
        default_output_stop=data.assess.default_output_stop,
        output_n=data.assess.default_output_n,
        output_interval=data.assess.output_interval,
        id=id,
        model_id="",
        name=data.name,
        tags=data.tags,
        description=data.brief,
        headline=data.headline,
        thumbnail=data.thumbnail_url.removeprefix("file:./") if data.thumbnail_url is not None else "thumbnail.png",
        diagram=(
            data.drug_diagram_url.removeprefix("file:./") if data.drug_diagram_url is not None else "drug_diagram.png"
        ),
        pharmacology_diagram=(
            data.pharmacology_diagram_url.removeprefix("file:./") if data.pharmacology_diagram_url is not None else None
        ),
        documentation=data.documentation,
        selected_output_plots=selected_output_plots,
        output_plot_options=output_plot_options,
        plot_time_transform=data.assess.plot_time_transform,
        plot_time_unit=data.assess.plot_time_unit,
        report_id=report_url_to_id(data.assess.report_url),
        default_linear_solver=data.assess.default_solver_configuration.linear_solver,
        default_reltol=data.assess.default_solver_configuration.reltol,
        default_abstol=data.assess.default_solver_configuration.abstol,
        default_maxord=data.assess.default_solver_configuration.maxord,
    )

    return metadata
