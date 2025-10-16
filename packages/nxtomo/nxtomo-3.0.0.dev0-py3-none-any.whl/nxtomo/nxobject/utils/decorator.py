"""
Internal decorator utilities.
"""

from __future__ import annotations

from functools import wraps

import pint

# Initialize the unit registry
ureg = pint.UnitRegistry()


def check_dimensionality(expected_dimension: str, allow_none: bool = True):
    """
    Decorator to check the dimensionality of a pint.Quantity parameter.

    :param expected_dimension: expected dimensionality of the parameter, e.g. "[length]".
    """

    def check_parameter(parameter, parameter_name: str, allow_none: bool):
        # Check if the value is a pint.Quantity and has the expected dimensionality
        if isinstance(parameter, pint.Quantity):
            if parameter.dimensionality != ureg.get_dimensionality(expected_dimension):
                raise TypeError(
                    f"{parameter_name}: expected dimensionality {expected_dimension}, but got {parameter.dimensionality}."
                )
        elif allow_none:
            if parameter is not None:
                raise TypeError(
                    f"{parameter_name} must be a pint.Quantity or None. Got {type(parameter)}."
                )
        else:
            raise TypeError(
                f"{parameter_name} must be a pint.Quantity. Got {type(parameter)}."
            )

    def decorator(func):
        @wraps(func)
        def wrapper(self, value):
            check_parameter(
                parameter=value,
                parameter_name=func.__name__,
                allow_none=allow_none,
            )

            return func(self, value)

        return wrapper

    return decorator
