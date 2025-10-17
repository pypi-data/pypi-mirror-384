from dataclasses import replace

from abm._sdk.legacy import LegacyRouteSchedule, LegacySolverConfiguration
from abm._sdk.ode_model import Schedule
from abm._sdk.solver_configuration import SolverConfiguration

from ..application_model import ApplicationModel


def maybe_legacy_schedule_to_schedule(schedule: Schedule | LegacyRouteSchedule) -> Schedule:
    match schedule:
        case Schedule():
            return schedule
        case LegacyRouteSchedule():
            return schedule.to_v2_schedule()
        case _:
            raise ValueError(f"Unexpected schedule type {type(schedule).__name__}")


def maybe_legacy_solver_configuration_to_solver_configuration(
    solver_configuration: SolverConfiguration | LegacySolverConfiguration,
) -> SolverConfiguration:
    match solver_configuration:
        case SolverConfiguration():
            return solver_configuration
        case LegacySolverConfiguration():
            return solver_configuration.to_v2_solver_configuration()
        case _:
            raise ValueError(f"Unexpected solver configuration type {type(solver_configuration).__name__}")


def normalize_application_model(application_model: ApplicationModel) -> ApplicationModel:
    # Returns a new ApplicationModel with all LegacyRouteSchedules converted to Schedules.
    assess_data = application_model.assess
    if assess_data is None:
        return application_model

    normalized_treatments = {
        key: replace(treatment, schedule=maybe_legacy_schedule_to_schedule(treatment.schedule))
        for key, treatment in assess_data.treatments.items()
    }

    normalized_default_solver_configuration = maybe_legacy_solver_configuration_to_solver_configuration(
        application_model.assess.default_solver_configuration
    )

    normalized_assess_data = replace(
        assess_data,
        treatments=normalized_treatments,
        default_solver_configuration=normalized_default_solver_configuration,
    )
    normalized_application_model = replace(application_model, assess=normalized_assess_data)

    return normalized_application_model
