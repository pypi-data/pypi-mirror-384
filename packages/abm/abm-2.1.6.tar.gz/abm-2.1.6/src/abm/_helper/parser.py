from typing import Callable, TypeVar

from parsita import ParserContext, lit, opt, reg
from parsita.util import splat

Value = TypeVar("Value")
Default = TypeVar("Default")


def or_else(default: Default) -> Callable[[tuple[()]], Value | Default]:
    def or_else_inner(maybe_value: tuple[()]) -> Value | Default:
        if len(maybe_value) != 0:
            return maybe_value[0]
        else:
            return default

    return or_else_inner


def make_function(values: list) -> str:
    arguments = [str(arg) if not isinstance(arg, list) else make_function(arg) for arg in values[1]]
    return f"{values[0]}({', '.join(arguments)})"


def _parse_list_str(string: str) -> list[str]:
    if not string.startswith("[") and not string.endswith("]"):
        raise ValueError(f"Invalid list: {input}")
    string = string[1:-1]
    output = []
    depth = 0
    start = 0
    for i in range(len(string)):
        if string[i] == "(":
            depth += 1
            continue
        if string[i] == ")":
            depth -= 1
            continue
        if string[i] == "," and depth == 0:
            output.append(string[start:i].strip())
            start = i + 1
    return [*output, string[start:].strip()]


# parse a string to a list of numbers
# the string could be a number "1" or with the pattern of "[1, 2, 3]"
#  "1" -> ["1"]
#  "[1, 2, 3]" -> ["1", "2", "3"]
#  "[1, pow(2,3), 3+4]" -> ["1", "pow(2,3)", "3+4"]
def make_list(input: int | float | str) -> list[str]:
    match input:
        case int() | float():
            return [str(input)]
        case str():
            if input.startswith("[") and input.endswith("]"):
                return _parse_list_str(input)
            else:
                return [input]
        case _:
            raise ValueError(f"Invalid number or list: {input}")


class UnittedExpressionParsers(ParserContext, whitespace=r"[ \t]*"):
    numeric_literal = reg(r"[+-]?\d+(\.\d+)?([Ee][+-]?\d+)?") > float

    no_colon_string_literal = reg(r"[^:]+")

    unit = opt(":" >> no_colon_string_literal) > or_else(None)

    unitted_expression = numeric_literal & unit > splat(lambda v, u: (v, u))


# parse a string with the form of float:str to its value and unit
# This is only being used for scans where for value you can have float:str
def parse_unitted_number(string: str) -> tuple[float, str | None]:
    return UnittedExpressionParsers.unitted_expression.parse(string).unwrap()


class UnittedNanParsers(ParserContext, whitespace=r"[ \t]*"):
    no_colon_string_literal = reg(r"[^:]+")

    unit = opt(":" >> no_colon_string_literal) > or_else(None)

    unitted_nan = lit("nan") & unit > splat(lambda v, u: (v, u))
