__all__ = ["deparse_unit"]

from fractions import Fraction
from functools import singledispatch

from .ast import *


@singledispatch
def deparse_unit(self: Unit) -> str:
    raise NotImplementedError(f"deparse_unit not implemented for type {type(self).__name__}")


@deparse_unit.register(Dynamic)
def deparse_unit_dynamic(self: Dynamic):
    return "dynamic"


@deparse_unit.register(Atom)
def deparse_unit_atom(self: Atom):
    return self.symbol


@deparse_unit.register(Dimensionless)
def deparse_unit_dimensionless(self: Dimensionless):
    return "1"


@deparse_unit.register(Parenthesis)
def deparse_unit_parenthesis(self: Parenthesis):
    return f"({deparse_unit(self.contents)})"


@deparse_unit.register(Power)
def deparse_unit_power(self: Power):
    match self.base:
        case Multiply() | Divide():
            base_string = f"({deparse_unit(self.base)})"
        case _:
            base_string = deparse_unit(self.base)

    match self.exponent:
        case Fraction(numerator=numerator, denominator=denominator):
            exponent_string = f"({numerator}/{denominator})"
        case _:
            exponent_string = str(self.exponent)

    return f"{base_string}^{exponent_string}"


@deparse_unit.register(Multiply)
def deparse_unit_multiply(self: Multiply):
    return f"{deparse_unit(self.left)}*{deparse_unit(self.right)}"


@deparse_unit.register(Divide)
def deparse_unit_divide(self: Divide):
    match self.right:
        case Multiply() | Divide():
            right_string = f"({deparse_unit(self.right)})"
        case _:
            right_string = deparse_unit(self.right)

    return f"{deparse_unit(self.left)}/{right_string}"
