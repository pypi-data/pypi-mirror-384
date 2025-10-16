"""Helper classes to define transformations contained in NXtransformations."""

from __future__ import annotations

import logging

import numpy
import pint
from silx.utils.enum import Enum as _Enum

# Create a pint unit registry
_ureg = pint.UnitRegistry()
_degree = _ureg.degree
_meter = _ureg.meter
_radian = _ureg.radian
_second = _ureg.second

_logger = logging.getLogger(__name__)

__all__ = [
    "TransformationType",
    "TransformationAxis",
    "Transformation",
    "DetXFlipTransformation",
    "DetYFlipTransformation",
    "DetZFlipTransformation",
    "GravityTransformation",
    "get_lr_flip",
    "get_ud_flip",
    "build_matrix",
]


class TransformationType(_Enum):
    """
    Possible NXtransformations types.
    """

    TRANSLATION = "translation"
    ROTATION = "rotation"
    GRAVITY = "gravity"


class TransformationAxis:
    """
    Predefined axes for tomography acquisitions performed at ESRF.
    Warning: these are stored as (X, Y, Z) and not under the usual NumPy reference (Z, Y, X).

    See: https://tomo.gitlab-pages.esrf.fr/ebs-tomo/master/modelization.html
    """

    AXIS_X = (1, 0, 0)
    AXIS_Y = (0, 1, 0)
    AXIS_Z = (0, 0, 1)


class Transformation:
    """
    Define a transformation applied along an axis.

    :param axis_name: name of the transformation.
    :param transformation_type: type of the transformation (the type should not change once created).
    :param vector: transformation vector as a tuple of three values or an instance of TransformationAxis.
    :param depends_on: name of another transformation on which this transformation depends.
    .. warning:: For rotations, values given in radians are automatically converted to degrees when comparing.
    """

    __isfrozen = False

    def __init__(
        self,
        axis_name: str,
        value: pint.Quantity | None,
        transformation_type: TransformationType,
        vector: tuple[float, float, float] | TransformationAxis,
        depends_on: str | None = None,
    ) -> None:
        self._axis_name = axis_name
        # Set the transformation type first so the setter can use it.
        self._transformation_type = TransformationType(transformation_type)
        self._transformation_values: pint.Quantity | None = None
        self.transformation_values = value
        if isinstance(vector, TransformationAxis):
            self._vector = vector.value()
        elif not isinstance(vector, (tuple, list, numpy.ndarray)) or len(vector) != 3:
            raise TypeError(
                f"vector should be a tuple of three elements. {vector} provided"
            )
        else:
            self._vector = tuple(vector)
        self._offset = (0, 0, 0)
        self._depends_on = None
        self.depends_on = depends_on
        self._equipment_component = None
        self._set_freeze()

    def _set_freeze(self, freeze=True):
        self.__isfrozen = freeze

    @property
    def axis_name(self) -> str:
        return self._axis_name

    @axis_name.setter
    def axis_name(self, axis_name: str):
        self._axis_name = axis_name

    @property
    def transformation_values(self) -> pint.Quantity | None:
        return self._transformation_values

    @transformation_values.setter
    def transformation_values(self, values: None | pint.Quantity):
        if isinstance(values, pint.Quantity):
            valid_dimensionalities = (
                _meter.dimensionality,
                _degree.dimensionality,
                (_meter / _second**2).dimensionality,
            )
            if values.dimensionality not in valid_dimensionalities:
                raise TypeError(
                    f"Unsupported dimensionality. Got {values.dimensionality} when should in {valid_dimensionalities}"
                )
        elif values is not None:
            raise TypeError(
                f"'values' is expected to be None or a pint.Quantity. Got {type(values)}"
            )
        self._transformation_values = values

    @property
    def transformation_type(self) -> TransformationType:
        return self._transformation_type

    @property
    def vector(self) -> tuple[float, float, float]:
        return self._vector

    @property
    def offset(self) -> tuple:
        return self._offset

    @offset.setter
    def offset(self, offset: tuple | list | numpy.ndarray):
        if not isinstance(offset, (tuple, list, numpy.ndarray)):
            raise TypeError(
                f"offset is expected to be a vector of three elements. {type(offset)} provided"
            )
        elif not len(offset) == 3:
            raise TypeError(
                f"offset is expected to be a vector of three elements. {offset} provided"
            )
        self._offset = tuple(offset)

    @property
    def depends_on(self):
        return self._depends_on

    @depends_on.setter
    def depends_on(self, depends_on):
        if not (depends_on is None or isinstance(depends_on, str)):
            raise TypeError(
                f"depends_on is expected to be None or str. {type(depends_on)} provided"
            )
        self._depends_on = depends_on

    @property
    def equipment_component(self) -> str | None:
        return self._equipment_component

    @equipment_component.setter
    def equipment_component(self, equipment_component: str | None):
        if not (equipment_component is None or isinstance(equipment_component, str)):
            raise TypeError(
                f"equipment_component is expected to be None or a str. {type(equipment_component)} provided"
            )
        self._equipment_component = equipment_component

    def to_nx_dict(self, transformations_nexus_paths, data_path: str):
        def join(my_list):
            my_list = tuple(filter(bool, my_list))
            return "" if len(my_list) == 0 else "/".join(my_list)

        quantity = self.transformation_values
        if quantity is None:
            _logger.error(f"no values defined for {self.axis_name}")
            transformation_values = None
            unit_str = ""
        else:
            if self.transformation_type is TransformationType.ROTATION:
                export_unit = _degree
            elif self.transformation_type is TransformationType.TRANSLATION:
                export_unit = _meter
            elif self.transformation_type is TransformationType.GRAVITY:
                export_unit = _meter / _second**2
            else:
                export_unit = quantity.units
                quantity_converted = quantity

            quantity_converted = quantity.to(export_unit)
            unit_str = f"{export_unit:~}"

            transformation_values = quantity_converted.magnitude

        res = {
            join((data_path, self.axis_name)): transformation_values,
            join(
                (
                    data_path,
                    self.axis_name + transformations_nexus_paths.TRANSFORMATION_TYPE,
                )
            ): self.transformation_type.value,
            join((data_path, f"{self.axis_name}@units")): unit_str,
        }

        # vector is mandatory
        res[
            join((data_path, f"{self.axis_name}{transformations_nexus_paths.VECTOR}"))
        ] = self.vector
        if self.offset is not None:
            res[
                join(
                    (data_path, f"{self.axis_name}{transformations_nexus_paths.OFFSET}")
                )
            ] = self.offset
        if self.depends_on:
            res[
                join(
                    (
                        data_path,
                        f"{self.axis_name}{transformations_nexus_paths.DEPENDS_ON}",
                    )
                )
            ] = self.depends_on
        if self.equipment_component:
            res[
                join(
                    (
                        data_path,
                        f"{self.axis_name}{transformations_nexus_paths.EQUIPMENT_COMPONENT}",
                    )
                )
            ] = self.equipment_component
        return res

    @staticmethod
    def from_nx_dict(axis_name: str, dict_: dict, transformations_nexus_paths):
        if transformations_nexus_paths is None:
            _logger.warning(
                "no transformations_nexus_paths (not implemented on this version of nexus - too old)"
            )
            return None
        value = dict_.get(axis_name, None)
        if isinstance(value, numpy.ndarray) and value.ndim == 0:
            value = value[()]
        vector = dict_.get(f"{axis_name}{transformations_nexus_paths.VECTOR}", None)
        transformation_type = dict_.get(
            f"{axis_name}{transformations_nexus_paths.TRANSFORMATION_TYPE}", None
        )
        if vector is None or transformation_type is None:
            raise ValueError(
                "Unable to find mandatory vector and/or transformation_type"
            )
        transformation_type = TransformationType(transformation_type)

        units_str = dict_.get(f"{axis_name}@units", None) or dict_.get(
            f"{axis_name}@unit", None
        )
        if units_str is not None and value is not None:
            if units_str == "m/s2":
                # backward with nxtomo < 2.0 (nxtomo writer version == 1.4)
                # note: the unit was typed differently, not recognized by pint
                # and the transformation type (gravity) was not existing
                units_str = "m / s ** 2"
                if transformation_type is TransformationType.TRANSLATION:
                    transformation_type = TransformationType.GRAVITY

            value = value * _ureg(units_str)

        transformation = Transformation(
            axis_name=axis_name,
            value=value,
            transformation_type=transformation_type,
            vector=vector,
        )

        offset = dict_.get(f"{axis_name}{transformations_nexus_paths.OFFSET}", None)
        if offset is not None:
            transformation.offset = offset

        depends_on = dict_.get(
            f"{axis_name}{transformations_nexus_paths.DEPENDS_ON}", None
        )
        if depends_on is not None:
            transformation.depends_on = depends_on

        equipment_component = dict_.get(
            f"{axis_name}{transformations_nexus_paths.EQUIPMENT_COMPONENT}", None
        )
        if equipment_component is not None:
            transformation.equipment_component = equipment_component

        return transformation

    def __setattr__(self, name, value):
        if self.__isfrozen and not hasattr(self, name):
            raise AttributeError("can't set attribute", name)
        else:
            super().__setattr__(name, value)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Transformation):
            return False
        same_dependence = self._depends_on == other.depends_on or (
            self._depends_on in (None, GravityTransformation(), "gravity")
            and other._depends_on in (None, GravityTransformation(), "gravity")
        )
        if not (
            self.vector == other.vector
            and self.transformation_type == other.transformation_type
            and self.offset == other.offset
            and same_dependence
            and self.equipment_component == other.equipment_component
        ):
            return False

        q1 = self.transformation_values
        q2 = other.transformation_values
        if q1 is None or q2 is None:
            return q1 is q2
        try:
            if self.transformation_type is TransformationType.GRAVITY:
                v1 = q1.to(_ureg("m/s^2")).magnitude
                v2 = q2.to(_ureg("m/s^2")).magnitude
            if self.transformation_type is TransformationType.ROTATION:
                v1 = q1.to(_degree).magnitude % 360
                v2 = q2.to(_degree).magnitude % 360
            elif self.transformation_type is TransformationType.TRANSLATION:
                v1 = q1.to(_meter).magnitude
                v2 = q2.to(_meter).magnitude
            else:
                v1 = q1.magnitude
                v2 = q2.to(q1.units).magnitude
        except Exception:
            return False

        if isinstance(v1, numpy.ndarray) or isinstance(v2, numpy.ndarray):
            return numpy.array_equal(v1, v2)
        else:
            return v1 == v2

    def as_matrix(self):
        if self.transformation_values is None:
            raise ValueError(f"missing transformation values for {self}")
        # Use the magnitude from the pint.Quantity
        if numpy.isscalar(self.transformation_values.magnitude):
            if self.transformation_type is TransformationType.ROTATION:
                theta = self.transformation_values.to(_radian).magnitude
                if self.offset != (0, 0, 0):
                    raise ValueError("offset not handled")
                if self.vector == (1, 0, 0):
                    return numpy.array(
                        [
                            [1, 0, 0],
                            [0, numpy.cos(theta), -numpy.sin(theta)],
                            [0, numpy.sin(theta), -numpy.cos(theta)],
                        ],
                        dtype=numpy.float32,
                    )
                elif self.vector == (0, 1, 0):
                    return numpy.array(
                        [
                            [numpy.cos(theta), 0, numpy.sin(theta)],
                            [0, 1, 0],
                            [-numpy.sin(theta), 0, numpy.cos(theta)],
                        ],
                        dtype=numpy.float32,
                    )
                elif self.vector == (0, 0, 1):
                    return numpy.array(
                        [
                            [numpy.cos(theta), -numpy.sin(theta), 0],
                            [numpy.sin(theta), numpy.cos(theta), 0],
                            [0, 0, 1],
                        ],
                        dtype=numpy.float32,
                    )
                else:
                    raise ValueError(f"vector {self.vector} not handled")
            elif self.transformation_type is TransformationType.TRANSLATION:
                val = self.transformation_values.to(_meter).magnitude
                if self.vector == (1, 0, 0):
                    return numpy.array(
                        [
                            [val, 0, 0],
                            [0, 1, 0],
                            [0, 0, 1],
                        ],
                        dtype=numpy.float32,
                    )
                elif self.vector == (0, 1, 0):
                    return numpy.array(
                        [
                            [1, 0, 0],
                            [0, val, 0],
                            [0, 0, 1],
                        ],
                        dtype=numpy.float32,
                    )
                elif self.vector == (0, 0, 1):
                    return numpy.array(
                        [
                            [1, 0, 0],
                            [0, 1, 0],
                            [0, 0, val],
                        ],
                        dtype=numpy.float32,
                    )
            else:
                raise RuntimeError(
                    f"unknown transformation type: {self.transformation_type}"
                )
        else:
            raise ValueError(
                f"transformations as a list of values is not handled for now ({self})"
            )

    def __str__(self):
        return f"transformation: {self.axis_name} -" + ", ".join(
            [
                f"type: {self.transformation_type.value}",
                f"value: {self.transformation_values}",
                f"vector: {self.vector}",
                f"offset: {self.offset}",
                f"depends_on: {self.depends_on}",
                f"equipment_component: {self.equipment_component}",
            ]
        )


class DetXFlipTransformation(Transformation):
    """
    Convenient class to a flip with X (1, 0, 0) as the rotation axis.
    """

    def __init__(self, flip: bool, axis_name="rx", depends_on=None) -> None:
        value = 180 if flip else 0
        super().__init__(
            axis_name=axis_name,
            value=value * _degree,
            transformation_type=TransformationType.ROTATION,
            vector=TransformationAxis.AXIS_X,
            depends_on=depends_on,
        )


class DetYFlipTransformation(Transformation):
    """
    Convenient class to a flip with Y (0, 1, 0) as the rotation axis.
    """

    def __init__(self, flip: bool, axis_name="ry", depends_on=None) -> None:
        value = 180 if flip else 0
        super().__init__(
            axis_name=axis_name,
            value=value * _degree,
            transformation_type=TransformationType.ROTATION,
            vector=TransformationAxis.AXIS_Y,
            depends_on=depends_on,
        )


class DetZFlipTransformation(Transformation):
    """
    Convenient class to a flip with Z (0, 0, 1) as the rotation axis.
    """

    def __init__(self, flip: bool, axis_name="rz", depends_on=None) -> None:
        value = 180 if flip else 0
        super().__init__(
            axis_name=axis_name,
            value=value * _degree,
            transformation_type=TransformationType.ROTATION,
            vector=TransformationAxis.AXIS_Z,
            depends_on=depends_on,
        )


class GravityTransformation(Transformation):
    """
    Gravity is used to solve the transformation chain (acting as the chain endpoint).
    The direction is set to -Z, and the dimension is unitless because it is used to
    resolve the transformation chain.
    """

    def __init__(self) -> None:
        super().__init__(
            axis_name="gravity",
            value=9.80665 * (_meter / _second**2),
            transformation_type=TransformationType.GRAVITY,
            vector=(0, 0, -1),
        )


def get_lr_flip(transformations: tuple) -> tuple:
    """
    Check all transformations for those matching a left-right detector flip and return them.
    """
    if not isinstance(transformations, (tuple, list)):
        raise TypeError(
            f"transformations is expected to be a tuple. {type(transformations)} provided"
        )
    res = []
    for transformation in transformations:
        if transformation in (
            DetYFlipTransformation(flip=True),
            DetYFlipTransformation(flip=False),
        ):
            res.append(transformation)
    return tuple(res)


def get_ud_flip(transformations: tuple) -> tuple:
    """
    Check all transformations for those matching an up-down detector flip and return them.
    """
    if not isinstance(transformations, (tuple, list)):
        raise TypeError(
            f"transformations is expected to be a tuple. {type(transformations)} provided"
        )
    res = []
    for transformation in transformations:
        if transformation in (
            DetXFlipTransformation(flip=True),
            DetXFlipTransformation(flip=False),
        ):
            res.append(transformation)
    return tuple(res)


def build_matrix(transformations: set):
    """
    Build a matrix from a set of Transformations.
    """
    transformations = {
        transformation.axis_name: transformation for transformation in transformations
    }
    already_applied_transformations = set(["gravity"])

    def handle_transformation(transformation: Transformation, matrix):
        if not isinstance(transformation, Transformation):
            raise TypeError(
                f"transformation is expected to be an instance of Transformation. {type(transformation)} provided"
            )
        # Handle dependencies
        if transformation.axis_name in already_applied_transformations:
            return matrix
        elif transformation.transformation_values is None:
            if transformation.axis_name.lower() == "gravity":
                return numpy.identity(3, dtype=numpy.float32)
            else:
                _logger.error(
                    f"transformation value not provided for {transformation.axis_name}. Ignoring transformation"
                )
                return matrix
        elif (
            transformation.depends_on is not None
            and transformation.depends_on not in already_applied_transformations
        ):
            if transformation.depends_on not in transformations:
                raise ValueError(
                    f"Unable to find transformation {transformation.depends_on}. "
                    "Broken dependency chain."
                )
            else:
                matrix = handle_transformation(
                    transformations[transformation.depends_on], matrix
                )
        matrix = numpy.matmul(matrix, transformation.as_matrix())
        already_applied_transformations.add(transformation.axis_name)
        return matrix

    matrix = numpy.identity(3, dtype=numpy.float32)
    for transformation in transformations.values():
        matrix = handle_transformation(transformation, matrix)
    return matrix
