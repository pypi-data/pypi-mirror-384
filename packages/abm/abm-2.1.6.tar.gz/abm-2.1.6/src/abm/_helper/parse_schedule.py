__all__ = ["parse_schedule"]

from dataclasses import dataclass

from parsita import ParserContext, Success, reg

from abm._sdk.reaction_model import ListSchedule, RepeatSchedule, Schedule

from .argument_parser import ArgumentParserParameter, arguments
from .helper import broadcast, maybe_add_parentheses
from .parser import make_list


@dataclass
class PartialRepeatSchedule:
    start: float
    interval: float
    n: int | str


class PartialRepeatScheduleParser(ParserContext, whitespace=r"[ \t]*"):
    number = reg(r"[+-]?\d+(\.\d+)?([Ee][+-]?\d+)?") > float
    integer = reg(r"\d+") > int
    name = reg(r"[A-Za-z_][A-Za-z_0-9]*")
    times_column = arguments(
        keyword_only=[
            ArgumentParserParameter("start", number, default=0.0),
            ArgumentParserParameter("interval", number),
            ArgumentParserParameter("n", integer, "inf"),
        ],
        keyword=name,
    ) > (lambda args: PartialRepeatSchedule(**args))


def parse_schedule(dose: dict[str, int | float | str]) -> Schedule:
    match PartialRepeatScheduleParser.times_column.parse(str(dose["times"])):
        case Success(times_column):
            unitted_start = f"{times_column.start}:{maybe_add_parentheses(dose['time_unit'])}"
            unitted_interval = f"{times_column.interval}:{maybe_add_parentheses(dose['time_unit'])}"
            n = times_column.n

            match dose.get("amounts", None):
                case None:
                    unitted_amount = None
                case amount:
                    unitted_amount = f"{amount}:{maybe_add_parentheses(dose['amount_unit'])}"

            match dose.get("durations", None):
                case None:
                    unitted_duration = None
                case maybe_zero if float(maybe_zero) == 0.0:
                    # Also treat explicit zeros (even as strings) as the default (None)
                    unitted_duration = None
                case duration:
                    unitted_duration = f"{duration}:{maybe_add_parentheses(dose['duration_unit'])}"

            return RepeatSchedule(
                start=unitted_start,
                interval=unitted_interval,
                n=n,
                amount=unitted_amount,
                duration=unitted_duration,
            )

        case _:  # Failure: make a list schedule
            dose_times = make_list(dose["times"])
            time_unit = dose["time_unit"]

            match dose.get("amounts", None):
                case None:
                    amounts = None
                    amount_unit = None
                    n_amounts = 0
                case amounts:
                    amounts = make_list(dose["amounts"])
                    n_amounts = len(amounts)

            # Check for durations.  If default, use n_durations = 0 for broadcasting other fields.
            match dose.get("durations", None):
                case None as durations:
                    n_durations = 0

                case found:
                    match make_list(found):
                        case maybe_zeros if all(float(d) == 0.0 for d in maybe_zeros):
                            # Normalize all explicit zeros to the default (None)
                            durations = None
                            n_durations = 0
                        case _ as durations:
                            n_durations = len(durations)

            # durations: None | list[str].  Broadcast and ascribe units to the other fields, then handle durations last.
            max_length = max(n_amounts, len(dose_times), n_durations)

            dose_times = broadcast(dose_times, max_length, "dose_times")
            time_unit = broadcast([time_unit], max_length, "time_unit")

            unitted_times = [f"{t}:{maybe_add_parentheses(tu)}" for t, tu in zip(dose_times, time_unit, strict=True)]

            match amounts:
                case None:
                    unitted_amounts = None
                case _:  # list[str]
                    amount_unit = dose.get("amount_unit", None)
                    if amount_unit is None:
                        raise ValueError("amount_unit must be provided if amounts is provided.")
                    amounts = broadcast(amounts, max_length, "amounts")
                    amount_unit = broadcast([amount_unit], max_length, "amount_unit")
                    unitted_amounts = [
                        f"{amt}:{maybe_add_parentheses(amtu)}" for amt, amtu in zip(amounts, amount_unit, strict=True)
                    ]

            match durations:
                case None:
                    unitted_durations = None
                case _:  # list[str]
                    duration_unit = dose.get("duration_unit", None)
                    if duration_unit is None:
                        raise ValueError("duration_unit must be provided if durations is provided.")
                    durations = broadcast(durations, max_length, "durations")
                    duration_unit = broadcast([duration_unit], max_length, "duration_unit")
                    unitted_durations = [
                        f"{dur}:{maybe_add_parentheses(duru)}"
                        for dur, duru in zip(durations, duration_unit, strict=True)
                    ]

            return ListSchedule(
                times=unitted_times,
                amounts=unitted_amounts,
                durations=unitted_durations,
            )
