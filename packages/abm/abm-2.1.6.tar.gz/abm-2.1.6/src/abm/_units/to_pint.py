__all__ = ["to_pint"]

from functools import singledispatch

import pint

from .ast import *
from .valid_units import dimensionless_unit, valid_units


def to_pint(self: Unit) -> pint.Unit | Dynamic:
    return _to_pint(self)


@singledispatch
def _to_pint(self: Unit) -> pint.Unit | Dynamic:
    raise NotImplementedError(f"to_pint not implemented for type {type(self).__name__}")


@_to_pint.register(Dynamic)
def to_pint_dynamic(self: Dynamic):
    return self


@_to_pint.register(Atom)
def to_pint_atom(self: Atom):
    return valid_units[self.symbol]


@_to_pint.register(Dimensionless)
def to_pint_dimensionless(self: Dimensionless):
    return dimensionless_unit


@_to_pint.register(Parenthesis)
def to_pint_parenthesis(self: Parenthesis):
    return to_pint(self.contents)


@_to_pint.register(Power)
def to_pint_power(self: Power):
    return to_pint(self.base) ** self.exponent


@_to_pint.register(Multiply)
def to_pint_multiply(self: Multiply):
    return to_pint(self.left) * to_pint(self.right)


@_to_pint.register(Divide)
def to_pint_divide(self: Divide):
    return to_pint(self.left) / to_pint(self.right)
