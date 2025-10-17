__all__ = ["TypeParsers", "parse_data_type"]

from parsita import ParserContext, Result, lit, reg
from parsita.util import constant

from .data_type import Boolean, DataType, Dynamic, Float64, Integer64, Nothing, String


class TypeParsers(ParserContext):
    boolean = lit("Boolean") > constant(Boolean())
    integer = lit("Integer64") > constant(Integer64())
    float64 = lit("Float64") > constant(Float64())
    # Units in the Python client are just strings
    unitted = lit("Float64") >> "[" >> reg(r"[^]]+") << "]" > Float64
    string = lit("String") > constant(String())
    nothing = lit("Nothing") > constant(Nothing())
    dynamic = lit("dynamic") > constant(Dynamic())

    data_type = boolean | integer | unitted | float64 | string | nothing | dynamic


def parse_data_type(text: str) -> Result[DataType]:
    return TypeParsers.data_type.parse(text)
