from dataclasses import dataclass
from inspect import Parameter
from typing import Any, Generic

from parsita import Parser, lit, reg
from parsita.state import Continue, Output, Reader, State


@dataclass(frozen=True, slots=True)
class ArgumentParserParameter(Generic[Output]):
    name: str
    parser: Parser[str, Output]
    default: Output = Parameter.empty

    def __repr__(self):
        if self.default == Parameter.empty:
            return f"{self.__class__.__name__}({self.name}, {self.parser.name_or_repr()})"
        else:
            return f"{self.__class__.__name__}({self.name}, {self.parser.name_or_repr()}, {self.default})"


class ArgumentParser(Parser[str, dict[str, Any]]):
    def __init__(
        self,
        positional_only: list[ArgumentParserParameter] = [],
        keyword_only: list[ArgumentParserParameter] = [],
        *,
        keyword: Parser = reg(r"[A-Za-z_][A-Za-z_0-9]*"),
        separator: Parser = lit(","),
        equals: Parser = lit("="),
    ):
        super().__init__()
        self.positional_only = positional_only
        self.keyword_only = keyword_only
        self.separator = separator
        self.equals = equals
        self.keyword = keyword
        self.keyword_only_by_name = {parameter.name: parameter for parameter in keyword_only}

    def _consume(self, state: State[str], reader: Reader[str]):
        output_positional = {}
        output_keyword = {}
        remainder = reader

        #  no argument
        if len(self.keyword_only) == 0 and len(self.positional_only) == 0:
            return Continue(remainder, {})

        # positional arguments
        for param in self.positional_only:
            status = param.parser.consume(state, remainder)
            if isinstance(status, Continue):
                remainder = status.remainder
            else:
                break

            output_positional[param.name] = status.value

            status = self.separator.consume(state, remainder)
            if isinstance(status, Continue):
                remainder = status.remainder
            else:
                break

        # keyword arguments
        if len(self.keyword_only) > 0:
            while True:
                # if keywords are following by positional, the comma after positional is not optional anymore
                if len(self.positional_only) > 0 and status is None:
                    break
                status = self.keyword.consume(state, remainder)
                if isinstance(status, Continue):
                    keyword_name = status.value
                    if keyword_name not in self.keyword_only_by_name.keys():
                        break
                    remainder = status.remainder
                else:
                    break

                status = self.equals.consume(state, remainder)
                if isinstance(status, Continue):
                    remainder = status.remainder
                else:
                    break

                status = self.keyword_only_by_name[keyword_name].parser.consume(state, remainder)
                if isinstance(status, Continue):
                    remainder = status.remainder
                else:
                    break

                output_keyword[keyword_name] = status.value

                status = self.separator.consume(state, remainder)
                if isinstance(status, Continue):
                    remainder = status.remainder
                else:
                    break

        must_positional_argument = {
            parameter.name for parameter in self.positional_only if parameter.default is Parameter.empty
        }
        provided_positional_argument = set(output_positional.keys())

        must_keyword_arguments = {
            parameter.name for parameter in self.keyword_only if parameter.default is Parameter.empty
        }
        provided_keyword_arguments = set(output_keyword.keys())

        if not must_positional_argument.issubset(provided_positional_argument):
            state.register_failure(
                f"{must_positional_argument} positional arguments but {provided_positional_argument} are provided",
                reader,
            )
            return None

        if not must_keyword_arguments.issubset(provided_keyword_arguments):
            state.register_failure(
                f"{must_keyword_arguments} keyword arguments but {provided_keyword_arguments} are provided", reader
            )
            return None

        for i, param in enumerate(self.positional_only):
            if param.name not in provided_positional_argument:
                output_positional[param] = self.positional_only[i].default

        for key in self.keyword_only_by_name.keys():
            if key not in provided_keyword_arguments:
                output_keyword[key] = self.keyword_only_by_name[key].default

        output = output_positional | output_keyword

        return Continue(remainder, output)

    def __repr__(self):
        keyword_list = [param.__repr__() for param in self.keyword_only]
        positional_list = [param.__repr__() for param in self.positional_only]
        keyword_arg_strings = f"keyword_only=[{', '.join(keyword_list)}]" if len(keyword_list) > 0 else ""
        positional_arg_strings = f"positional_only=[{', '.join(positional_list)}]" if len(positional_list) > 0 else ""
        return self.name_or_nothing() + f"arguments({','.join([keyword_arg_strings, positional_arg_strings])})"


def arguments(
    positional_only: list[ArgumentParserParameter] = [],
    keyword_only: list[ArgumentParserParameter] = [],
    *,
    keyword: Parser = reg(r"[A-Za-z_][A-Za-z_0-9]*"),
    separator: Parser = lit(","),
    equals: Parser = lit("="),
):
    return ArgumentParser(
        positional_only,
        keyword_only,
        keyword=keyword,
        separator=separator,
        equals=equals,
    )
