"""
Utility helpers for NXobject concatenation.
"""

from typing import Iterable, Optional, Tuple

import numpy
import pint

from nxtomo.nxobject.nxobject import NXobject


def concatenate(nx_objects: Iterable, **kwargs) -> NXobject:
    """
    Concatenate a list of NXobjects.

    :param Iterable nx_objects: objects to be concatenated. They are expected to be of the same type.
    :param kwargs: extra parameters
    :return: concatenated object, of the same type as ``nx_objects``.
    :rtype: :class:`~nxtomo.nxobject.nxobject.NXobject`
    """
    if len(nx_objects) == 0:
        return None
    else:
        if not isinstance(nx_objects[0], NXobject):
            raise TypeError("nx_objects are expected to be instances of NXobject")
        return type(nx_objects[0]).concatenate(nx_objects=nx_objects, **kwargs)


def concatenate_pint_quantities(
    quantities: Tuple[pint.Quantity, ...],
) -> Optional[pint.Quantity]:
    """
    Helper function to concatenate pint quantities while ensuring unit consistency.
    """
    if len(quantities) == 0:
        return None
    if len(quantities) == 1:
        return quantities[0]
    for q in quantities:
        if not isinstance(q, pint.Quantity):
            import traceback

            traceback.print_stack(limit=5)
            raise TypeError(
                f"All elements must be pint.Quantity objects. got {type(q)}"
            )
    units = {val.units for val in quantities if isinstance(val, pint.Quantity)}
    if len(units) > 1:
        raise ValueError(f"Inconsistent units {units}")
    unit = units.pop() if units else None
    magnitudes = [val.magnitude for val in quantities]
    concatenated = numpy.concatenate(magnitudes)
    return concatenated * unit if unit else concatenated
