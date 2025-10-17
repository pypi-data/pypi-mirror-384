__all__ = ["UnitParsers", "parse_unit", "un"]

from fractions import Fraction
from functools import lru_cache
from typing import List

from parsita import ParserContext, Result, lit, opt, pred, reg, rep
from parsita.util import constant, splat

from .ast import Atom, Dimensionless, Divide, Dynamic, Multiply, Parenthesis, Power, Unit
from .valid_units import valid_units

valid_units_error_string = " or ".join(valid_units.keys())


def make_power(base: Unit, maybe_exponent: List[int]):
    if len(maybe_exponent) == 0:
        return base
    else:
        return Power(base, maybe_exponent[0])


def make_compound(first, rest):
    value = first
    for op, term in rest:
        if op == "*":
            value = Multiply(value, term)
        else:
            value = Divide(value, term)
    return value


class UnitParsers(ParserContext, whitespace=r"[ ]*"):
    dimensionless = lit("1") > constant(Dimensionless())
    atom = pred(reg(r"[a-zA-Z]+"), lambda x: x in valid_units, valid_units_error_string) > Atom
    parenthesis = "(" >> compound << ")" > Parenthesis  # noqa: F821

    single = dimensionless | atom | parenthesis

    integer = reg(r"[+-]?[1-9][0-9]*") > int
    fraction = "(" >> integer << "/" & pred(integer, lambda x: x > 0, "positive integer") << ")" > splat(Fraction)
    exponent = integer | fraction
    power = single & opt("^" >> exponent) > splat(make_power)
    compound = power & rep(lit("*", "/") & power) > splat(make_compound)

    dynamic = lit("dynamic") > constant(Dynamic())

    single_unit = dynamic | single
    unit = dynamic | compound


def parse_unit(text: str) -> Result[Unit]:
    return UnitParsers.unit.parse(text)


@lru_cache(maxsize=64)
def un(text: str) -> Unit:
    return parse_unit(text).unwrap()
