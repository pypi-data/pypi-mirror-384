__all__ = ["parse_times"]

from dataclasses import dataclass

from parsita import ParserContext, Success, reg

from abm._sdk.times import LinspaceTimes, ListTimes

from .argument_parser import ArgumentParserParameter, arguments
from .helper import maybe_add_parentheses
from .parser import make_list


@dataclass
class PartialLinspaceTimes:
    start: float
    stop: float
    n: int


class LinspaceTimeParser(ParserContext, whitespace=r"[ \t]*"):
    number = reg(r"[+-]?\d+(\.\d+)?([Ee][+-]?\d+)?") > float
    integer = reg(r"\d+") > int
    name = reg(r"[A-Za-z_][A-Za-z_0-9]*")
    times_column = arguments(
        keyword_only=[
            ArgumentParserParameter("start", number, default=0.0),
            ArgumentParserParameter("stop", number),
            ArgumentParserParameter("n", integer, 51),
        ],
        keyword=name,
    ) > (lambda args: PartialLinspaceTimes(**args))


def parse_times(time: dict) -> ListTimes | LinspaceTimes:
    times_column = LinspaceTimeParser.times_column.parse(str(time["times"]))
    if isinstance(times_column, Success):
        partial_linspace_time = times_column.unwrap()
        return LinspaceTimes(
            start=f"{partial_linspace_time.start}:{maybe_add_parentheses(time['times_unit'])}",
            stop=f"{partial_linspace_time.stop}:{maybe_add_parentheses(time['times_unit'])}",
            n=partial_linspace_time.n,
        )
    else:
        time_values = make_list(time["times"])
        time_unit = time["times_unit"]
        output_times_expressions = [f"{value}:{maybe_add_parentheses(time_unit)}" for value in time_values]
        return ListTimes(times=output_times_expressions)
