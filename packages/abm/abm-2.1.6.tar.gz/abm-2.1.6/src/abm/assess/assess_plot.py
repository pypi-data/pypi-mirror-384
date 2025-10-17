from abc import abstractmethod
from dataclasses import dataclass
from typing import Literal

from abm._sdk.assess import Plot, PlotOptions


@dataclass(frozen=True, kw_only=True)
class OutputPlot:
    id: str | None = None
    unit: str | None = None
    scale: Literal["linear", "log"] | None = None


@dataclass(frozen=True, kw_only=True)
class AssessPlot:
    type: Literal[
        "scan1d_response",
        "scan2d_contour",
        "scan2d_feasible_contour",
        "criterion_plot",
        "output_plot",
    ]
    show_legend: bool = True
    legend_title: str | None = None
    legend_orientation: str | None = None

    title: str | None = None

    x_scale: Literal["linear", "log"] | None = None
    x_title: str | None = None
    x_transform: str | None = "1"
    x_unit: str | None = None

    y_scale: Literal["linear", "log"] | None = None
    y_title: str | None = None
    y_transform: str | None = "1"
    y_unit: str | None = None

    @abstractmethod
    def to_sdk_plot(self) -> Plot:
        pass


@dataclass(frozen=True, kw_only=True)
class AssessScan1dResponsePlot(AssessPlot):
    type: Literal["scan1d_response"]
    criterion_value_name: str

    def to_sdk_plot(self) -> Plot:
        return Plot(
            type="scan1d_response",
            options=PlotOptions(
                criterion_value_name=self.criterion_value_name,
                title=self.title,
                x_title=self.x_title,
                y_scale=self.y_scale,
                y_title=self.y_title,
            ),
        )


@dataclass(frozen=True, kw_only=True)
class AssessScan2dResponsePlot(AssessPlot):
    type: Literal["scan2d_contour", "scan2d_feasible_contour"]
    criterion_value_name: str
    criterion_value_min: float
    criterion_value_max: float

    def to_sdk_plot(self) -> Plot:
        return Plot(
            type=self.type,
            options=PlotOptions(
                criterion_value_name=self.criterion_value_name,
                criterion_value_min=self.criterion_value_min,
                criterion_value_max=self.criterion_value_max,
                title=self.title,
                x_title=self.x_title,
                y_title=self.y_title,
            ),
        )


@dataclass(frozen=True, kw_only=True)
class AssessCriterionPlot(AssessPlot):
    type: Literal["criterion_plot"]
    criterion_value_name: str

    def to_sdk_plot(self) -> Plot:
        return Plot(
            type="criterion_plot",
            options=PlotOptions(
                show_legend=self.show_legend,
                legend_title=self.legend_title,
                legend_orientation=self.legend_orientation,
                title=self.title,
                x_title=self.x_title,
                x_unit=self.x_unit,
                x_transform=self.x_transform,
                y_unit=self.y_unit,
                y_title=self.y_title,
                y_scale=self.y_scale,
            ),
        )


@dataclass(frozen=True, kw_only=True)
class AssessOutputPlot(AssessPlot):
    type: Literal["output_plot"]
    output: str

    def to_sdk_plot(self) -> Plot:
        return Plot(
            type="output_plot",
            options=PlotOptions(
                show_legend=self.show_legend,
                legend_title=self.legend_title,
                legend_orientation=self.legend_orientation,
                output=self.output,
                title=self.title,
                x_title=self.x_title,
                x_unit=self.x_unit,
                x_transform=self.x_transform,
                y_title=self.y_title,
                y_unit=self.y_unit,
                y_transform=self.y_transform,
                y_scale=self.y_scale,
            ),
        )


def format_unit(remove_space: bool, unit: str) -> str:
    if remove_space:
        if len(unit) > 0:
            return f"({unit})"
        else:
            return ""
    else:
        if len(unit) > 0:
            return f" ({unit})"
        else:
            return " "


def get_base_criterion_string(criterion, modifier_options) -> str:
    modifier_string = ""
    for modifier_id, option_id in modifier_options.items():
        modifier_string += f"{criterion.modifiers[modifier_id].options[option_id].name} "
    modifier_string = modifier_string.strip()

    criterion_name = criterion.name + " "
    base_criterion_string = (criterion_name + modifier_string).strip()

    return base_criterion_string


def get_full_criterion_string(criterion, modifier_options, reducer_id) -> str:
    base_criterion_string = get_base_criterion_string(criterion, modifier_options)
    selected_reducer = criterion.reducers[reducer_id]
    reducer_name = selected_reducer.name
    full_criterion_string = f"{reducer_name} {base_criterion_string}"

    return full_criterion_string


def legend_title(
    plot_id, scan_parameter_1_name, scan_parameter_1_unit, scan_parameter_2_name=None, scan_parameter_2_unit=None
):
    if plot_id == "assess_simulation":
        return ""
    elif plot_id == "scan_1d":
        return f"{scan_parameter_1_name} {format_unit(True, scan_parameter_1_unit)}"
    elif plot_id == "scan_2d":
        if scan_parameter_2_name is None:
            raise ValueError("scan_parameter_2_name must be provided")
        if scan_parameter_2_unit is None:
            raise ValueError("scan_parameter_2_unit must be provided")
        return (
            f"{scan_parameter_1_name} {format_unit(True, scan_parameter_1_unit)} ::"
            f" {scan_parameter_2_name} {format_unit(True, scan_parameter_2_unit)}"
        )
