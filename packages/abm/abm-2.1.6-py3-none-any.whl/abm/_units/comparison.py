__all__ = ["is_equivalent"]

from math import isclose

from .ast import Dynamic, Unit
from .to_pint import to_pint


def is_equivalent(first: Unit, second: Unit) -> bool:
    if isinstance(first, Dynamic) or isinstance(second, Dynamic):
        return True

    # Yes, this is how this is done: https://stackoverflow.com/a/69637655/1485877
    ratio = ((1 * to_pint(first)) / (1 * to_pint(second))).to_base_units()
    return ratio.dimensionless and isclose(ratio.magnitude, 1)
